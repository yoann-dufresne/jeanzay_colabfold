from os import path, listdir, rename, mkdir, remove, chdir, getcwd, getenv
from shutil import copy, rmtree
import subprocess
from sys import stderr, argv
from random import randint

# Prepare upload
uploads = f"uploads_{randint(0, 1000000000)}.sh"

with open(uploads, 'w') as up:
    data_dir = "data"
    for lib_dir in listdir(data_dir):
        if not lib_dir.endswith("_split"):
            continue
        lib_path = path.join(data_dir, lib_dir)
        lib = lib_dir[:lib_dir.find('_')]

        for tar in listdir(lib_path):
            if not tar.endswith(".tar.gz"):
                continue
            sample = tar[:-6]
            tar_path = path.join(lib_path, tar)
            
            # Send to JZ
            cmd = f"ssh ydufresn@192.168.148.50 -t \"rsync {path.join(getcwd(), tar_path)} {getenv('JZ')}:/gpfswork/rech/yph/uep61bl/scp_data/{lib}/\""
            print(cmd, file=up)
            print(f"rm {path.join(getcwd(), tar_path)}", file=up)

            fa = path.join(lib_path, f"{sample}.fa")
            if path.exists(fa):
                print(f"rm {fa}", file=up)

# Exec upload
complete_process = subprocess.run(["sh", uploads])
if complete_process.returncode != 0:
    print("Error: Rsync teminated on non 0 return value", file=stderr)
    print(complete_process.stderr, file=stderr)
    exit(complete_process.returncode)

remove(uploads)
