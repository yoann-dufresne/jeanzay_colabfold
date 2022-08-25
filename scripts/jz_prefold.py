from os import path, listdir, rename, mkdir, remove, chdir, getcwd
from shutil import copy
import subprocess
from time import time
from sys import stderr, argv


# Return false on command error
def run_cmd(cmd):
    print(cmd)
    complete_process = subprocess.run(cmd.split(' '))
    if complete_process.returncode != 0:
        print("Error: sbatch command finished on non 0 return value", file=stderr)
        print("error code", complete_process.returncode, file=stderr)
        return False
    return True


def get_libs():
    libs = []
    with open("libs.txt") as lfp:
        for line in lfp:
            line = line.strip()
            if len(line) > 0:
                lib_path = path.join("data", f"{line}_split")
                if path.exists(lib_path) and path.isdir(lib_path):
                    libs.append(line)

    return libs


def split_existing():
    print("\t\tAnalyse and split already decompressed samples")
    data_path = "data"
    nb_splits = 0

    for lib in get_libs():
        lib_dir = f"{lib}_split"
        lib_path = path.join(data_path, lib_dir)
        if (not path.exists(lib_path)) or (not path.isdir(lib_path)):
            continue

        print("\tLib", lib)

        for sample_dir in listdir(lib_path):
            sample_path = path.join(lib_path, sample_dir)
            if (not sample_dir.startswith("res_")) or (not path.isdir(sample_path)):
                continue

            sample = sample_dir[4:]
            print(sample_path)

            fold_path = path.join(sample_path, "fold_split")
            if not path.exists(fold_path):
                split_sample(sample_path)
            local_splits = len(listdir(fold_path))
            nb_splits += local_splits
            print("Splits: ", local_splits, "->", nb_splits)

    return nb_splits


def split_sample(sample_path):
    print("Split", sample_path)
    max_mol_per_split = 20

    fold_path = path.join(sample_path, "fold_split")
    mkdir(fold_path)
    split_idx = -1
    split_path = None
    current_split_mols = max_mol_per_split

    for file in listdir(sample_path):
        if not file.endswith(".a3m"):
            continue

        # Verify split dir is complete to create new splits
        if current_split_mols == max_mol_per_split:
            split_idx += 1
            split_path = path.join(fold_path, f"split_{split_idx}")
            mkdir(split_path)
            current_split_mols = 0

        # Move to current split dir
        rename(path.join(sample_path, file), path.join(split_path, file))
        current_split_mols += 1


def decompress_samples(max_splits=0):
    if max_splits <= 0:
        return

    print("\t\tDecompressions...")
    scp_path = "/gpfswork/rech/yph/uep61bl/scp_data"

    saved_path = getcwd()

    for lib in get_libs():
        scp_lib_path = path.join(scp_path, lib)
        if not path.isdir(scp_lib_path):
            continue
        lib_path = path.join("data", f"{lib}_split")
        if not path.exists(lib_path):
            mkdir(lib_path)
        chdir(lib_path)

        print("Lib", lib)

        for file in listdir(scp_lib_path):
            if not file.endswith(".tar.gz"):
                continue

            if max_splits <= 0:
                chdir(saved_path)
                print("Max splitted folders reached. Quitting...")
                return
            
            sample = file[:-7]
            print("Sample", sample)

            copy(path.join(scp_lib_path, file), path.join(file))
            # decompress
            cmd = f"tar -xzf {file}"
            ok = run_cmd(cmd)
            if not ok:
                print("Skipping sample", sample, file=stderr)
            # remove dest tar
            remove(file)
            # remove origin tar
            remove(path.join(scp_lib_path, file))
            # Split the sample
            split_sample(f"res_{sample}")
            local_splits = len(listdir(f"res_{sample}/fold_split"))
            max_splits -= local_splits
            print("Splits: ", local_splits, "Remaining", max_splits)
        
        chdir(saved_path)


def recursive_submit():
    outdir = path.join("out", "prefold")
    if not path.exists(outdir):
        mkdir(prefold)
        
    cmd = f"sbatch -c 1 --qos=qos_cpu-t3 -p prepost,archive,cpu_p1 -A mrb@cpu --begin=now+14400 --time=20:00:00 --job-name=prefold --hint=nomultithread --output=out/prefold/%j.out --error=out/prefold/%j.err ./scripts/jz_prefold.sh"
    run_cmd(cmd)


if __name__ == "__main__":
    max_splits = 10000
    max_splits -= split_existing()
    decompress_samples(max_splits)
    recursive_submit()
