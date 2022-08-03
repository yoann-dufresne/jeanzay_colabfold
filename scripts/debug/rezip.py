from os import path, listdir, rename, remove, chdir
from shutil import rmtree
import subprocess
from sys import stderr


def run_cmd(cmd):
    print(cmd)
    complete_process = subprocess.run(cmd.split(' '))
    if complete_process.returncode != 0:
        print("Error: sbatch command finished on non 0 return value", file=stderr)
        print("error code", complete_process.returncode, file=stderr)
        return False
    return True


sample_path = path.join("data", "CFDL_split", "res_10129")
mols_path = path.join(sample_path, "molecules_10129")
fold_path = path.join(sample_path, "fold_split")

files_per_mol = {}

# Register all missing files per molecule
for split_dir in listdir(fold_path):
    if not split_dir.startswith("split_"):
        continue

    split_path = path.join(fold_path, split_dir)

    for file in listdir(split_path):
        if file.endswith(".fa"):
            mol = file[:file.find("_")]
            if mol not in files_per_mol:
                files_per_mol[mol] = []
            files_per_mol[mol].append(path.join("fold_split", split_dir, file))

# Move to the mol directory to decompress/recompress
chdir(mols_path)
for mol in files_per_mol:
    print(files_per_mol[mol])
    continue
    # decompress the molecule
    archive = f"10129_{mol}.tar.gz"
    ok = run_cmd(f"tar -xzf {archive}")
    if ok:
        remove(archive)
    else:
        print("Problem on molecule", mol, file=stderr)
        exit(1)

    # add the files
    for file in files_per_mol[mol]:
        rename(path.join("..", file), file[file.rfind('/')+1:])

    # recompress the molecule
    mol_dir = f"10129_{mol}"
    ok = run_cmd(f"tar -czf {archive} {mol_dir}")
    if ok:
        rmtree(mol_dir)
    else:
        print("Recompression failed for", mol_dir)
        exit(1)