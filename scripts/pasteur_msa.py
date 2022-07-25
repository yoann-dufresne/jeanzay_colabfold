from os import path, listdir, rename, mkdir, remove, chdir, getcwd, getenv
from shutil import copy, rmtree
import subprocess
from sys import stderr, argv



db = "/pasteur/appa/scratch/rchikhi/colabfold_db/"
fa = argv[1]

if not path.exists(fa):
    print(f"Error: No file named", fa, file=stderr)
    exit(1)

splitted_path = fa.split('/')

sample = splitted_path[-1][:-3]
lib = splitted_path[-2]
lib = lib[:lib.find('_')]
lib_dir = path.join(*splitted_path[:-1])

tar = f"{sample}.tar.gz"
if path.exists(path.join(lib_dir, tar)):
    print("Already aligned")
    exit(0)

# MSA Colabfold
out_dir = path.join(lib_dir, f"res_{sample}")
if path.exists(out_dir):
    rmtree(out_dir)
cmd = f"colabfold_search {fa} {db} {out_dir} --db-load-mode 2 --threads 16"
complete_process = subprocess.run(cmd.split(' '))
if complete_process.returncode != 0:
    print("Error: Colabfold teminated on non 0 return value", file=stderr)
    print(complete_process.stderr, file=stderr)
    exit(complete_process.returncode)

# # Compress
copy(fa, path.join(out_dir, splitted_path[-1]))
path_save = getcwd()
chdir(lib_dir)
complete_process = subprocess.run(["tar", "--remove-files", "-czf", tar, f"res_{sample}"])
if complete_process.returncode != 0:
    print("Error: MSA compression teminated on non 0 return value", file=stderr)
    print(complete_process.stderr, file=stderr)
    exit(complete_process.returncode)
# open("aligned.lock", 'a').close()

# Send to JZ
# cmd = f"ssh ydufresn@192.168.148.50 -t \"rsync {getcwd()}/{tar} {getenv('JZ')}:/gpfswork/rech/yph/uep61bl/scp_data/{lib}/\""
# print(cmd)
# complete_process = subprocess.run(cmd.split(' '))
# if complete_process.returncode != 0:
#     print("Error: Rsync teminated on non 0 return value", file=stderr)
#     print(complete_process.stderr, file=stderr)
#     exit(complete_process.returncode)

# # clean
# rmove(tar)
