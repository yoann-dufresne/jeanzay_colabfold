from os import listdir, mkdir, path, getcwd, chdir
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


def submit_cmd(cmd, stdout=False):
    global previous_submit, min_delay
    # Avoid sbatch spam by delaying submits
    current_time = time()
    if current_time - previous_submit <= min_delay:
        sleep(current_time - previous_submit)

    run_cmd(cmd, stdout, stderr)

    previous_submit = time()


def squeue(cmd):
    global previous_submit, min_delay
    # Avoid sbatch spam by delaying submits
    current_time = time()
    if current_time - previous_submit <= min_delay:
        sleep(current_time - previous_submit)

    ok, stdout = run_cmd("squeue -u uep61bl -h", stdout=True)
    if not ok:
        print("squeue error", file=stderr)
        return None

    # Read all the currently running jobs
    print(stdout.readlines())

    previous_submit = time()


# Return false on command error
def run_cmd(cmd, stdout=False):
    print(cmd)
    complete_process = None
    if stdout:
        complete_process = subprocess.run(cmd.split(' '), stdout=subprocess.PIPE)
    else:
        complete_process = subprocess.run(cmd.split(' '))
    if complete_process.returncode != 0:
        print("Error: sbatch command finished on non 0 return value", file=stderr)
        print("error code", complete_process.returncode, file=stderr)
        if stdout:
            return False, None
        else:
            return False
    if stdout:
        return True, complete_process.stdout
    else:
        return True


def recursive_submit():
    outdir = path.join("out", "postprocess")
    if not path.exists(outdir):
        mkdir(outdir)

    cmd = f"sbatch -c 1 --qos=qos_cpu-t3 -p prepost,archive,cpu_p1 -A mrb@cpu --begin=now+72000 --time=20:00:00 --job-name=postprocess --hint=nomultithread --output=out/postprocess/%j.out --error=out/postprocess/%j.err ./scripts/jz_fold_scheduler.sh"
    submit_cmd(cmd)


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
            if not lib_path.startswith("res_"):
                continue
            if not path.isdir(sample_path):
                continue

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
        return False

    splits_to_fold = []
    # Individual check of each split dir
    for split_dir in listdir(fold_path):
        split_path = path.join(fold_path, split_dir)
        if not split_dir.startswith("split_"):
            continue

        submited = path.join(split_path, "submited.lock")
        if path.exists(submited):
            # TODO: Verify submission delay (remove lock after a certain time without folding)
            continue

        to_fold = explore_split(split_path)
        if to_fold:
            splits_to_fold.append(split_dir[6:])
            open(submited, 'a').close()

    # Start foldings
    if len(splits_to_fold) > 0:
        cmd = f"sbatch -c 10 --gres=gpu:1 --qos=qos_gpu-t3 -p gpu_p13 -A mrb@v100 --time=20:00:00 --job-name=fold --hint=nomultithread --output=out/fold/%j.out --array= --error=out/fold/%j.err --export=sample_path={sample_path} --array={'.'.join(splits_to_fold)} ./scripts/jz_fold.sh"
        ok = submit_cmd(cmd)
        if not ok:
            for
        return ok
    
    return False


# Return False if some work is still needed. True if everything is over
def explore_split(split_path):
    folded_lock = path.join(split_path, "folded.lock")
    if not path.exists(folded_lock):
        return False

    # Sort the files per molecule
    files_per_mol = {}
    for file in listdir(split_path):
        # Get the file extention and reject unwanted files
        extention = file[split_path.find('.')+1:]
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
            print("Warning: missing pdb or json file for" split_path, mol, file=stderr)
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


if __name__ == "__main__":
    # recursive_submit()
    current_time = time()
    while current_time - start_time < 3600 * 19:
        # print("TODO: Explore squeue first to know how many submit are possible")
        # exit(1)
        explore_directories()
        break
        sleep(600)

    print("Time out")
