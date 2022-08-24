from os import path, listdir, rename, mkdir, remove, chdir, getcwd, getenv
from shutil import copy, rmtree
import subprocess
from sys import stderr, argv
from random import randint



def run_cmd(cmd, stdout=False):
    print(cmd)
    
    complete_process = None
    if stdout:
        complete_process = subprocess.run(cmd, shell=True, capture_output=stdout, text=True)
    else:
        complete_process = subprocess.run(cmd, shell=True)
    if complete_process.returncode != 0:
        print("Error: Command finished on non 0 return value", file=stderr)
        print("error code", complete_process.returncode, file=stderr)
        if stdout:
            return False, None
        else:
            return False
    if stdout:
        return True, complete_process.stdout
    else:
        return True


def send_cmd(cmd, stdout=False):
    cmd = f'ssh ydufresn@192.168.148.50 -t "{cmd}"'
    return run_cmd(cmd, stdout)


def recursive_submit():
    cmd = "sbatch -p seqbio -A seqbio --qos seqbio -c 1 --mem 20G --begin=now+86400  --job-name=\"upload\" --output=\"out/upload/%j.out\" --error=\"out/upload/%j.err\" ./scripts/pasteur_upload.sh"
    ok = run_cmd(cmd)
    if not ok:
        print("Impossible to recursively submit the script. Quitting...", file=stderr)


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


def remaining_files(data_path):
    to_upload = {}
    libs = get_libs()

    for lib in libs:
        to_upload[lib] = []
        lib_dir = f"{lib}_split"
        lib_path = path.join(data_path, lib_dir)

        for tar in listdir(lib_path):
            if not tar.endswith(".tar.gz"):
                continue
            tar_path = path.join(lib_path, tar)
            to_upload[lib].append(tar_path)

    return to_upload


def space_used():
    print("Ask Jean Zay for space left on the cluster")
    ok, res_stdout = send_cmd(f'ssh uep61bl@jean-zay.idris.fr -t \\"du -sh /gpfswork/rech/yph/uep61bl\\"', stdout=True)
    if not ok:
        print("Impossible so reach Jean Zay. Wait for 1 hour", file=stderr)
        recursive_submit()
        exit(0)
    space_used = float(res_stdout[:3])
    print("Space used on JZ:", space_used)
    return space_used


def upload(files):
    libs = get_libs()

    for lib in libs:
        while len(files[lib]) > 0:
            # Verify space
            remaining_space = 5 - space_used()
            if remaining_space <= 0.1:
                break

            print("upload 100 files")
            for i in range(min(100, len(files[lib]))):
                # Get file names
                tar_path = files[lib][i]
                splitted_path = tar_path.split('/')
                lib = splitted_path[-2][:-6]
                lib_path = path.join(*splitted_path[:-1])
                sample = splitted_path[-1][:-7]
                # Send 1 file
                ok = send_cmd(f"rsync {path.join(getcwd(), tar_path)} uep61bl@jean-zay.idris.fr:/gpfswork/rech/yph/uep61bl/scp_data/{lib}/")
                # remove tar on upload
                if ok:
                    remove(tar_path)
                    remove(f"{lib_path}/{sample}.fa")

            # Update file list
            files[lib] = files[lib][100:]
            print()

    return sum([len(x) for x in files.values()])


if __name__ == "__main__":
    # Sync libs
    send_cmd("rsync /pasteur/zeus/projets/p02/seqbio/yoann/softwares/jeanzay_colabfold/libs.txt uep61bl@jean-zay.idris.fr:/gpfswork/rech/yph/uep61bl/software/jeanzay_colabfold/libs.txt")
    files = remaining_files("data")
    nb_files = upload(files)
    recursive_submit()
