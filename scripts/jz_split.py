from os import path, listdir, rename, mkdir, remove, chdir, getcwd
from shutil import copy
import subprocess
from sys import stderr, argv


# Split the molecules from a sample into multiple computable buckets


mol_per_fold = 20

# data/lib_split/res_sample/
sample_dir = argv[1]
splitted_path = sample_dir.split('/')

sample = splitted_path[-1]
sample = sample[sample.find('_')+1:]
lib = splitted_path[-2]
lib = lib[:lib.find('_')]


fold_dir = path.join(sample_dir, "fold_split")
if not path.exists(fold_dir):
    mkdir(fold_dir)
    
# Complete ready.lock in existing directories
for d in listdir(fold_dir):
    candidate_dir = path.join(fold_dir, d)
    if path.isdir(candidate_dir):
        split_num = i+1
        ready = path.join(candidate_dir, "ready.lock")
        if not path.exists(ready):
            open(ready, "a").close()

# Add new files into split directories
a3ms = [f for f in listdir(sample_dir) if f.endswith("a3m")]
split_num = 0
# Select the first available directory
split_dir = path.join(fold_dir, f"split_{split_num}")
# select next dir
while path.exists(split_dir):
    split_num += 1
    split_dir = path.join(fold_dir, f"split_{split_num}")

num_moved = 0
for f in a3ms:
    # Create new bucket
    if num_moved == 0 and not path.exists(split_dir):
        mkdir(split_dir)
    # Move file into the current bucket
    rename(path.join(sample_dir, f), path.join(split_dir, f))

    # Update the numbers
    num_moved += 1
    if num_moved == mol_per_fold:
        open(path.join(split_dir, "ready.lock"), 'a').close()
        num_moved = 0
        split_num += 1
        # Search for next directory
        while path.exists(split_dir):
            split_num += 1
            split_dir = path.join(fold_dir, f"split_{split_num}")

if num_moved != 0:
    open(path.join(split_dir, "ready.lock"), 'a').close()


# SBATCH folds
out = path.join("out")
if not path.exists(out):
    mkdir(out)

f_path = path.join(out, "fold")
if not path.exists(f_path):
    mkdir(f_path)

c_path = path.join(out, "compress")
if not path.exists(c_path):
    mkdir(c_path)


ids = []
for fold_split in listdir(fold_dir):
    # Create one fold sbatch per fold directory
    fold_path = path.join(fold_dir, fold_split)

    cmd = f"sbatch -c 10 --gres=gpu:1 --qos=qos_gpu-t3 -p gpu_p13 -A mrb@v100 --time=20:00:00 --job-name=fold --hint=nomultithread --output=out/fold/%j.out --error=out/fold/%j.err --export=fold_dir={fold_path} ./scripts/jz_fold.sh"
    complete_process = subprocess.run(cmd.split(' '), universal_newlines=True, stdout=subprocess.PIPE)
    if complete_process.returncode != 0:
        print("Error: sbatch command finished on non 0 return value", file=stderr)
        print(complete_process.stderr, file=stderr)
        exit(complete_process.returncode)

    fold_job_id = complete_process.stdout.split('\n')[0].strip().split(' ')[-1]

    # Trigger a compression per split directory after folding completed
    cmd = f"sbatch -c 1  --qos=qos_cpu-t3 -p prepost -A mrb@cpu --time=1:00:00 --job-name=mol_compress --hint=nomultithread --output=out/compress/mol_%j.out --error=out/compress/mol_%j.err --dependency=afterok:{fold_job_id} --export=split_dir={fold_path} ./scripts/jz_compress_molecules.sh"
    if complete_process.returncode != 0:
        print("Error: sbatch command finished on non 0 return value", file=stderr)
        print(complete_process.stderr, file=stderr)
        exit(complete_process.returncode)
    ids.append(complete_process.stdout.split('\n')[0].strip().split(' ')[-1])

# Compress the full sample after all foldings/molecule compression completion
cmd = f"sbatch -c 1  --qos=qos_cpu-t3 -p prepost -A mrb@cpu --time=6:00:00 --job-name=sample_compress --hint=nomultithread --output=out/compress/sample_%j.out --error=out/compress/sample_%j.err --dependency=afterok:{','.join(ids)} --export=split_dir={sample_dir} ./scripts/jz_compress_sample.sh"
if complete_process.returncode != 0:
    print("Error: sbatch command finished on non 0 return value", file=stderr)
    print(complete_process.stderr, file=stderr)
    exit(complete_process.returncode)
