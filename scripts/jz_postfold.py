from os import listdir, mkdir, path, getcwd, chdir, remove
from shutil import rmtree
from sys import stderr
import sys
from time import time, sleep
import subprocess

# Import the root directory to be able to call palmfold
root_dir = path.dirname(path.dirname(path.abspath(__file__)))
sys.path.append(root_dir)
from palmfold.palmfold import main as palmfold_main


start_time = time()
previous_submit = time()
min_delay = 2


def submit_cmd(cmd):
    global previous_submit, min_delay
    # Avoid sbatch spam by delaying submits
    current_time = time()
    if current_time - previous_submit <= min_delay:
        sleep(current_time - previous_submit)

    run_cmd(cmd)

    previous_submit = time()


# Return false on command error
def run_cmd(cmd):
    print(cmd)
    complete_process = subprocess.run(cmd.split(' '))
    if complete_process.returncode != 0:
        print("Error: sbatch command finished on non 0 return value", file=stderr)
        print("error code", complete_process.returncode, file=stderr)
        return False
    return True


def recursive_submit():
    outdir = path.join("out", "postprocess")
    if not path.exists(outdir):
        mkdir(outdir)

    cmd = f"sbatch -c 1 --qos=qos_cpu-t3 -p prepost,archive,cpu_p1 -A mrb@cpu --begin=now+72000 --time=20:00:00 --job-name=postprocess --hint=nomultithread --output=out/postprocess/%j.out --error=out/postprocess/%j.err ./scripts/jz_postfold.sh"
    submit_cmd(cmd)

    # srun --pty --ntasks=1 --cpus-per-task=1 --hint=nomultithread --qos=qos_cpu-t3 -p prepost,archive,cpu_p1 -A mrb@cpu --time=20:00:00 --job-name=postprocess

def explore_directories():
    data_dir = "data"

    for lib_dir in listdir(data_dir):
        lib_path = path.join(data_dir, lib_dir)

        # verifications
        if not path.isdir(lib_path):
            continue

        print("\t\tLib", lib_dir)
        for sample_dir in listdir(lib_path):
            sample_path = path.join(lib_path, sample_dir)

            # verifications
            if not sample_dir.startswith("res_"):
                continue
            if not path.isdir(sample_path):
                continue

            sample_dir = "res_10129"
            sample_path = path.join(lib_path, sample_dir)

            print("\tsample", sample_dir)
            explore_sample(sample_path)

            print()
            # Current time check
            current_time = time()
            if current_time - start_time > 3600 * 19:
                print("Out of time. Will wait until the next recursive call")
                exit(0)


def explore_sample(sample_path):
    fold_path = path.join(sample_path, "fold_split")
    # If fold dir not present : No post-computing
    if not path.exists(fold_path):
        print("Not splitted")
        return False

    compressible = True
    # Individual check of each split dir
    for split_dir in listdir(fold_path):
        split_path = path.join(fold_path, split_dir)
        if not split_dir.startswith("split_"):
            continue

        is_over = explore_split(split_path)
        print(split_path, is_over)
        if not is_over:
            compressible = False
    print("compressible", compressible)
    if compressible:
        return compress_and_upload_sample(sample_path)

    print("Not all molecules folded")
    exit(0)
    return False


def compress_and_upload_sample(sample_path):
    # Extract names
    splitted = sample_path.split('/')
    sample = splitted[-1][4:]
    lib = splitted[-2][:-6]

    # Go to the compression dir
    path_save = getcwd()
    chdir(sample_path)

    # Names
    archive = f"{lib}_{sample}.tar.gz"

    # Compress
    print("should compress but debug stop")
    exit(0)
    cmd = f"tar -czf {archive} molecules_{sample}"
    ok = run_cmd(cmd)
    if ok:
        rmtree(f"molecules_{sample}")
    else:
        if path.exists(archive):
            remove(archive)

    # Upload
    if ok:
        cmd = f"aws s3 cp {archive} s3://serratus-fold/CFDL/{archive}"
        print("sending", sample_path)
        ok = run_cmd(cmd)
    
    chdir(path_save)
    
    # Clean
    if ok:
        rmtree(sample_path)

    exit(0)
    return ok


# Return False if some work is still needed. True if everything is over
def explore_split(split_path):
    content = listdir(split_path)
    if len(content) == 2 and "log.txt" in content and "ready.lock" in content:
        return True
    folded_lock = path.join(split_path, "folded.lock")
    if not path.exists(folded_lock):
        return False

    # Sort the files per molecule
    files_per_mol = {}
    for file in content:
        # Get the file extention and reject unwanted files
        extention = file[file.find('.')+1:]
        if extention == 'fa':
            extention = file[-5:]
        if extention not in ["a3m", "json", "pdb", "tm", "pp.fa", "rc.fa"]:
            continue
        
        # Get the molecule name
        mol = None
        if extention == 'a3m' or extention == 'tm':
            mol = file[:file.rfind('.')]
        else:
            mol = file[:file.find('_')]

        if mol not in files_per_mol:
            files_per_mol[mol] = {}
        files_per_mol[mol][extention] = file

    everything_ok = True
    # Score the molecules if needed
    for mol in files_per_mol:
        if ('pdb' not in files_per_mol[mol]) or ('json' not in files_per_mol[mol]):
            print("Warning: missing pdb or json file for", split_path, mol, file=stderr)
            print("Skipping molecule")
            everything_ok = False
            continue
        if 'tm' not in files_per_mol[mol]:
            # Missing score => compute scores
            score_molecules(split_path)
            # Add score files to molecules
            for mol in files_per_mol:
                tm_file = path.join(split_path, f"{mol}.tm")
                # Exit on error if missing tm files
                if not path.exists(mol):
                    print(f"Error: Score not computed for molecule {mol} in {split_path}", file=stderr)
                    return False
                files_per_mol[mol]['tm'] = f"{mol}.tm"

    # Compress the uncompressed molecules
    splitted = split_path.split("/")
    lib = splitted[-4][:-6]
    sample = splitted[-3][4:]
    molecules_path = path.join(*splitted[:-2], f"molecules_{sample}")

    save_path = getcwd()
    for mol in files_per_mol:
        chdir(split_path)
        # Creating molecule directory to compress
        tar_dir = f"{sample}_{mol}"
        if not path.exists(tar_dir):
            mkdir(tar_dir)
        # Move the files inside the dir
        for file in files_per_mol[mol]:
            rename(file, path.join(tar_dir, file))
        # Compress the dir
        archive = f"{sample}_{mol}.tar.gz"
        cmd = f"tar -czf {archive} {tar_dir}"
        ok = run_cmd(cmd)
        if not ok:
            everything_ok = False
            for file in files_per_mol[mol]:
                rename(path.join(tar_dir, file), file)
        # Remove useless files
        rmtree(tar_dir)
        chdir(save_path)

        tar_path = path.join(split_path, archive)
        if path.exists(tar_path):
            rename(tar_path, path.join(molecules_path, archive))

    return everything_ok


def score_molecules(split_path):
    splitted = split_path.split("/")
    lib = splitted[-4][:-6]
    sample = splitted[-3][4:]
    mol_path = path.join(*splitted[:-2], f"molecules_{sample}")

    # Create molecule directory and global tm file
    if not path.exists(mol_path):
        mkdir(mol_path)

    # Score and compress all the molecules
    palmfold_main(split_path, path.join(root_dir, "palmfold", "pol"), 0)

    # Update the global tm file
    global_tm = path.join(mol_path, f"{lib}_{sample}.tm")
    if not path.exists(global_tm):
        with open(global_tm, "a") as gtm:
            print("PDBchain1\tPDBchain2\tTM1\tTM2\tRMSD\tID1\tID2\tIDali\tL1\tL2\tLali", file=gtm)

    lines = []
    for file in [x for x in listdir(split_path) if x.endswith(".tm")]:
        with open(file) as tm:
            tm.readline()
            for line in readlines():
                lines.append(line.strip())
    with open(global_tm, "a") as gtm:
        print("\n".join(lines), file=gtm)


if __name__ == "__main__":
    #recursive_submit()
    current_time = time()
    while current_time - start_time < 3600 * 19:
        explore_directories()
        break
        sleep(600)

    print("Time out")
