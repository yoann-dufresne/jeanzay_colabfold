from os import listdir, mkdir, path, getcwd, chdir, remove, rename
from shutil import rmtree
from sys import stderr
import sys
from time import time, sleep
from datetime import datetime as dt
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


def recursive_submit():
    outdir = path.join("out", "postprocess")
    if not path.exists(outdir):
        mkdir(outdir)

    cmd = f"sbatch -c 1 --qos=qos_cpu-t3 -p prepost -A mrb@cpu --begin=now+72000 --time=20:00:00 --job-name=postprocess --hint=nomultithread --output=out/postprocess/%j.out --error=out/postprocess/%j.err ./scripts/jz_postfold.sh"
    submit_cmd(cmd)

    # srun --pty --ntasks=1 --cpus-per-task=1 --hint=nomultithread --qos=qos_cpu-t3 -p prepost,archive,cpu_p1 -A mrb@cpu --time=20:00:00 --job-name=postprocess

def explore_directories():
    data_dir = "data"

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

        print(split_path)
        is_over = explore_split(split_path)
        print(split_path, is_over)
        if not is_over:
            compressible = False
    if compressible:
        return compress_and_upload_sample(sample_path)

    print("Not all molecules folded")
    return False


def compress_and_upload_sample(sample_path):
    # Extract names
    splitted = sample_path.split('/')
    sample = splitted[-1][4:]
    lib = splitted[-2][:-6]

    # Go to the compression dir
    path_save = getcwd()
    chdir(sample_path)

    # Verify molecule path
    ok = True
    if path.exists(f"molecules_{sample}"):
        # Names
        archive = f"{lib}_{sample}.tar.gz"

        # Compress
        cmd = f"tar -czf {archive} molecules_{sample}"
        ok = run_cmd(cmd)
        if ok:
            rmtree(f"molecules_{sample}")
        else:
            if path.exists(archive):
                remove(archive)

        # Upload
        if ok:
            cmd = f"/gpfswork/rech/yph/uep61bl/software/aws/dist/aws s3 cp {archive} s3://serratus-fold/{lib}/{archive}"
            print("sending", sample_path)
            ok = run_cmd(cmd)
    
    chdir(path_save)

    # Clean
    if ok:
        rmtree(sample_path)

    return ok


# Return False if some work is still needed. True if everything is over
def explore_split(split_path):
    content = listdir(split_path)
    contains_mol = False
    for file in content:
        if file.endswith("a3m"):
            contains_mol = True
            break
    if not contains_mol:
        return True

    folded_lock = path.join(split_path, "folded.lock")
    if not path.exists(folded_lock):
        return False

    # Sort the files per molecule
    files_per_mol = {}
    for file in content:
        # Get the file extention and reject unwanted files
        extention = file[file.rfind('.')+1:]
        if extention == 'fa':
            extention = file[-5:]
        if extention not in ["a3m", "json", "pdb", "tm", "pp.fa", "rc.fa"]:
            continue

        file_path = path.join(split_path, file)
        
        # Get the molecule name
        mol = None
        if extention == 'a3m' or extention == 'tm':
            mol = file[:file.rfind('.')]
        else:
            mol = file[:file.find('_')]

        if mol not in files_per_mol:
            files_per_mol[mol] = {}
        if extention not in files_per_mol[mol]:
            files_per_mol[mol][extention] = file
        elif path.getctime(file_path) > path.getctime(path.join(split_path, files_per_mol[mol][extention])):
            remove(path.join(split_path, files_per_mol[mol][extention]))
            files_per_mol[mol][extention] = file
        else:
            remove(file_path)


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
            print("score")
            score_molecules(split_path)
            # Add score files to molecules
            for mol in files_per_mol:
                tm_file = path.join(split_path, f"{mol}.tm")
                # Exit on error if missing tm files
                if not path.exists(tm_file):
                    print(f"Error: Score not computed for molecule {mol} in {split_path}", file=stderr)
                    return False
                files_per_mol[mol]['tm'] = f"{mol}.tm"

    # Compress the uncompressed molecules
    splitted = split_path.split("/")
    lib = splitted[-4][:-6]
    sample = splitted[-3][4:]
    molecules_path = path.join(*splitted[:-2], f"molecules_{sample}")
    if not path.exists(molecules_path):
        mkdir(molecules_path)

    save_path = getcwd()
    for mol in files_per_mol:
        chdir(split_path)
        # Creating molecule directory to compress
        tar_dir = f"{sample}_{mol}"
        if not path.exists(tar_dir):
            mkdir(tar_dir)
        # Move the files inside the dir
        for ext in files_per_mol[mol]:
            file = files_per_mol[mol][ext]
            rename(file, path.join(tar_dir, file))
        # Compress the dir
        archive = f"{sample}_{mol}.tar.gz"
        cmd = f"tar -czf {archive} {tar_dir}"
        ok = run_cmd(cmd)
        if not ok:
            everything_ok = False
            for ext in files_per_mol[mol]:
                file = files_per_mol[mol][ext]
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
    # print(path.join(root_dir, "palmfold", "pol"))
    palmfold_main(split_path, path.join(root_dir, "palmfold", "pol"), 0)
    # Rename realigned files
    for file in listdir(split_path):
        if file.endswith("_realign.pdb"):
            rename(path.join(split_path, file), path.join(split_path, file[:-12]))

    # Update the global tm file
    global_tm = path.join(mol_path, f"{lib}_{sample}.tm")
    if not path.exists(global_tm):
        with open(global_tm, "a") as gtm:
            print("PDBchain1\tPDBchain2\tTM1\tTM2\tRMSD\tID1\tID2\tIDali\tL1\tL2\tLali", file=gtm)

    lines = []
    for file in [x for x in listdir(split_path) if x.endswith(".tm")]:
        with open(path.join(split_path, file)) as tm:
            tm.readline()
            for line in tm.readlines():
                lines.append(line.strip())
    with open(global_tm, "a") as gtm:
        print("\n".join(lines), file=gtm)


def get_sorted_files(dir_path):
    print("analysing logs")
    files = [(path.getctime(path.join(dir_path, f)), f) for f in listdir(dir_path) if (not path.isdir(path.join(dir_path, f))) and (not f.endswith(".tar.gz"))]
    files.sort()

    return files


def filter_files(file_tuples, min_age):
    '''
    Filter a date/file tuple liste to keep only the oldest with at least min_age age.
    Parameters:
        file_tuples: A list of tuples (date of creation (timestamp), file name)
        min_age: Minimum elapsed time since the date of creation to keep the file in the list
    Return:
        A list of file names
    '''
    print("filter log by date")
    current_time = time()
    filtered = [f for t, f in file_tuples if current_time - t >= min_age]
    return filtered


def compress_files(dir_path, file_list):
    path_saved = getcwd()
    chdir(dir_path)

    first_date = path.getctime(file_list[0])
    last_date = path.getctime(file_list[-1])

    first_date = dt.fromtimestamp(first_date)
    last_date = dt.fromtimestamp(last_date)

    name = f"logs_{first_date.year}-{first_date.month}-{first_date.day},{first_date.hour}.{first_date.minute:02d}_{last_date.year}-{last_date.month}-{last_date.day},{last_date.hour}.{last_date.minute:02d}"
    mkdir(name)

    for file in file_list:
        rename(file, path.join(name, file))

    run_cmd(f"tar -czf {name}.tar.gz {name}")
    rmtree(name)

    chdir(path_saved)


def compress_logs():
    folds_out_path = path.join("out", "fold")

    to_compress = get_sorted_files(folds_out_path)
    files = filter_files(to_compress, 3600*24)
    while len(files) > 50000:
        print("Logs compression")
        compress_files(folds_out_path, files[:50000])
        files = files[50000:]


if __name__ == "__main__":
    recursive_submit()
    current_time = time()
    while current_time - start_time < 3600 * 19:
        compress_logs()
        explore_directories()
        sleep(600)

    print("Time out")
