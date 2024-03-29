from os import listdir, mkdir, path, getcwd, chdir, stat, remove
from shutil import rmtree
from sys import stderr
import re
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

    run_cmd(cmd, stdout)

    previous_submit = time()


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


def squeue():
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
    nb_jobs = 0
    for line in stdout.split('\n'):
        line = re.sub(' +', ' ', line.strip())
        split = line.split(' ')
        if "_[" in split[0]:
            nb_jobs += 20
        else:
            nb_jobs += 1

    previous_submit = time()

    return nb_jobs


# Return false on command error
def run_cmd(cmd, stdout=False):
    print(cmd)
    complete_process = None
    if stdout:
        complete_process = subprocess.run(cmd.split(' '), capture_output=stdout, text=True)
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
    outdir = path.join("out", "fold_sched")
    if not path.exists(outdir):
        mkdir(outdir)

    cmd = f"sbatch -c 1 --qos=qos_cpu-t3 -p prepost,archive,cpu_p1 -A mrb@cpu --begin=now+72000 --time=20:00:00 --job-name=fold_sched --hint=nomultithread --output=out/fold_sched/%j.out --error=out/fold_sched/%j.err ./scripts/jz_fold_scheduler.sh"
    submit_cmd(cmd)


def explore_directories():
    global start_time
    data_dir = "data"
    number_of_submit = 5000 - squeue()

    for lib in get_libs():
        lib_dir = f"{lib}_split"
        lib_path = path.join(data_dir, lib_dir)

        # verifications
        if (not path.exists(lib_path)) or (not path.isdir(lib_path)):
            continue

        print("\t\tLib", lib_dir)
        for sample_dir in listdir(lib_path):
            sample_path = path.join(lib_path, sample_dir)

            # verifications
            if not sample_dir.startswith("res_"):
                continue
            if not path.isdir(sample_path):
                continue

            print("\tsample", sample_dir)
            status, submitted = explore_sample(sample_path, number_of_submit)
            number_of_submit -= submitted

            print()
            # Current time check
            current_time = time()
            if (current_time - start_time) > (3600 * 19):
                print("Out of time. Will wait until the next recursive call")
                exit(0)

            if number_of_submit <= 0:
                return


def explore_sample(sample_path, max_submit=0):
    if max_submit <= 0:
        return False, 0

    fold_path = path.join(sample_path, "fold_split")
    # If fold dir not present : No post-computing
    if not path.exists(fold_path):
        print("No fold_split directory")
        return False, 0

    splits_to_fold = []
    split_dirs = listdir(fold_path)
    
    # Individual check of each split dir
    for split_dir in split_dirs:
        split_path = path.join(fold_path, split_dir)
        if not split_dir.startswith("split_"):
            continue

        submited = path.join(split_path, "submited.lock")
        if path.exists(submited):
            creation_time = path.getctime(submited)
            # If submitted less than 24h ago, continue to wait
            if (time() - creation_time < 72 * 3600):
                continue
            else:
                remove(submited)

        to_fold = is_to_fold(split_path)
        if to_fold:
            splits_to_fold.append(split_dir[6:])
            open(submited, 'a').close()

    # Start foldings
    if len(splits_to_fold) > 0:
        outdir = path.join("out", "fold")
        if not path.exists(outdir):
            mkdir(outdir)

        cmd = f"sbatch -c 9 --gres=gpu:1 --qos=qos_gpu-t3 -p gpu_p13 -A mrb@v100 --time=20:00:00 --job-name=fold --hint=nomultithread --output=out/fold/%j.out --error=out/fold/%j.err --export=sample_path={sample_path} --array={','.join(splits_to_fold)} ./scripts/jz_fold.sh"
        ok = submit_cmd(cmd)
        return ok, len(splits_to_fold)
    else:
        print("Nothing to fold")
    
    return False, 0


# Return False if some work is still needed. True if everything is over
def is_to_fold(split_path):
    folded_lock = path.join(split_path, "folded.lock")
    if path.exists(folded_lock):
        return False

    # Sort the files per molecule
    for file in listdir(split_path):
        if file.endswith("a3m"):
            return True

    return False


if __name__ == "__main__":
    recursive_submit()
    current_time = time()
    while (current_time - start_time) < (3600 * 19):
        explore_directories()
        sleep(600)

    print("Time out")
