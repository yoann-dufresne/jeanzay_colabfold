from os import path, listdir, rename, mkdir, remove, chdir, getcwd
from shutil import copy
import subprocess
from sys import stderr, argv

# Get a tar.gz sample from the scp_dir and decompress it on the right place (data directory)


# $SCP_DIR/libname/sample.tar.gz
tar_file = argv[1]
splitted_path = tar_file.split('/')

sample = splitted_path[-1]
sample = sample[:sample.find('.')]
lib = splitted_path[-2]

# Create the lib dir if not already created
data_dir = "data"
lib_dir = path.join(data_dir, f"{lib}_split")
if not path.exists(lib_dir):
    mkdir(lib_dir)

# Move the file
copy(tar_file, path.join(lib_dir, splitted_path[-1]))
remove(tar_file)
tar_file = splitted_path[-1]

current_path = getcwd()
chdir(lib_dir)

# unzip
complete_process = subprocess.run(["tar", "-xzf", tar_file])
if complete_process.returncode != 0:
    print("Error: Decompression command finished on non 0 return value", file=stderr)
    print(complete_process.stderr, file=stderr)
    exit(complete_process.returncode)
remove(tar_file)

chdir(current_path)

# SBATCH fold split
out = path.join("out")
if not path.exists(out):
    mkdir(out)

out = path.join(out, "split")
if not path.exists(out):
    mkdir(out)

res_dir = path.join(lib_dir, f"res_{sample}")

cmd = f"sbatch -c 1 --qos=qos_cpu-t3 -p prepost -A mrb@cpu --time=1:00:00 --job-name=split --hint=nomultithread --output=out/split/%j.out --error=out/split/%j.err --export=res_dir={res_dir} ./scripts/jz_split.sh"
complete_process = subprocess.run(cmd.split(' '))
if complete_process.returncode != 0:
    print("Error: Decompression command finished on non 0 return value", file=stderr)
    print(complete_process.stderr, file=stderr)
    exit(complete_process.returncode)