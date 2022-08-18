from os import path, listdir, rename, mkdir, remove, chdir, getcwd, getenv
from shutil import copy, rmtree
import subprocess
from sys import stderr, argv
from random import randint



def send_cmd(cmd, stdout=False)
    cmd = f'ssh ydufresn@192.168.148.50 -t "{cmd}"'
    print(cmd)
    complete_process = None
    if stdout:
        complete_process = subprocess.run(cmd.split(' '), capture_output=stdout, text=True)
    else:
        complete_process = subprocess.run(cmd.split(' '))
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


def remaining_files(data_path):
    to_upload = []

    for lib_dir in listdir(data_dir):
        if not lib_dir.endswith("_split"):
            continue
        lib_path = path.join(data_dir, lib_dir)
        lib = lib_dir[:lib_dir.find('_')]

        for tar in listdir(lib_path):
            if not tar.endswith(".tar.gz"):
                continue
            tar_path = path.join(lib_path, tar)
            to_upload.append(tar_path)

    return to_upload


def space_used():
    ok, res_stdout = send_cmd('ssh uep61bl@jean-zay.idris.fr -t "du -sh /gpfswork/rech/yph/uep61bl"', stdout=True)
    if not ok:
        exit(0)
    space_used = float(res_stdout[:3])
    print("Space used on JZ:", space_used)
    exit(0)
    return space_used


def upload(files):
    while len(files) > 0:
        # Verify space
        remaining_space = 5 - space_used()
        if remaining_space <= 0.1:
            break

        # upload 100 files
        for i in range(min(100, len(files))):
            # Get file names
            tar_path = files[i]
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
        files = files[100:]

    return len(files)


if __name__ == "__main__":
    files = remaining_files("data")
    nb_files = upload(files)

#     files = remaining_files("data")
#     if len(files) > 0:



# # Prepare upload
# uploads = f"uploads_{randint(0, 1000000000)}.sh"

# with open(uploads, 'w') as up:
#     data_dir = "data"
#     for lib_dir in listdir(data_dir):
#         if not lib_dir.endswith("_split"):
#             continue
#         lib_path = path.join(data_dir, lib_dir)
#         lib = lib_dir[:lib_dir.find('_')]

#         for tar in listdir(lib_path):
#             if not tar.endswith(".tar.gz"):
#                 continue
#             sample = tar[:-6]
#             tar_path = path.join(lib_path, tar)
            
#             # Send to JZ
#             cmd = f"ssh ydufresn@192.168.148.50 -t \"rsync {path.join(getcwd(), tar_path)} {getenv('JZ')}:/gpfswork/rech/yph/uep61bl/scp_data/{lib}/\""
#             print(cmd, file=up)
#             print(f"rm {path.join(getcwd(), tar_path)}", file=up)

#             fa = path.join(lib_path, f"{sample}.fa")
#             if path.exists(fa):
#                 print(f"rm {fa}", file=up)

# # Exec upload
# complete_process = subprocess.run(["sh", uploads])
# if complete_process.returncode != 0:
#     print("Error: Rsync teminated on non 0 return value", file=stderr)
#     print(complete_process.stderr, file=stderr)
#     exit(complete_process.returncode)

# remove(uploads)
