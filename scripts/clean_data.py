# Check files on JZ and aws to find samples already processed. The processed that are still present in pasteur are removed.

from os import path, listdir, rename, mkdir, remove, chdir, getcwd, getenv
from shutil import copy, rmtree
import subprocess
from sys import stderr, argv
import re



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


def get_jz_scpdir_files(lib):
    ok, out = send_cmd(f"ssh uep61bl@jean-zay.idris.fr -t \"ls /gpfswork/rech/yph/uep61bl/scp_data/{lib}/\"", stdout=True)

    if not ok:
        print("Impossible to connect Jean Zay", file=stderr)
        return []

    out = out.replace('\t', ' ')
    out = out.replace('\n', ' ')
    out = re.sub('\\s+', ' ', out.strip())

    return out.split(' ')[:-4]


def get_jz_datadir_files(lib):
    ok, out = send_cmd(f"ssh uep61bl@jean-zay.idris.fr -t \"ls /gpfsscratch/rech/yph/uep61bl/data/{lib}_split/\"", stdout=True)

    if not ok:
        print("Impossible to connect Jean Zay", file=stderr)
        return []

    out = out.replace('\t', ' ')
    out = out.replace('\n', ' ')
    out = re.sub('\\s+', ' ', out.strip())

    return out.split(' ')[:-4]


def get_jz_samples(lib):
    samples = set([x[:x.find('.')] for x in get_jz_scpdir_files(lib)])
    samples = samples.union(set([x[4:] for x in get_jz_datadir_files(lib)]))
    return samples


def get_aws_files(lib):
    ok, out = send_cmd(f"aws s3 ls s3://serratus-fold/{lib}/", stdout=True)

    if not ok:
        print("Impossible to reach aws servers", file=stderr)
        return []

    files = []
    for line in out.split('\n'):
        line = re.sub('\\s+', ' ', line.strip())
        line = line.split(' ')

        if len(line) == 4:
            files.append({"date":line[0], "hour":line[1], "size":line[2], "filename":line[3]})
        
    return files


def get_all_distant_samples(lib):
    samples = get_jz_samples(lib)
    for file in get_aws_files(lib):
        sample = file["filename"]
        sample = sample[sample.find('_')+1:sample.find('.')]
        if sample not in samples:
            samples.add(sample)

    return samples


def get_fastas(lib):
    return [file for file in listdir(path.join("data", f"{lib}_split")) if file.endswith(".fa")]


def clean_lib(lib, fas, samples):
    nb = 0
    for sample in samples:
        if f"{sample}.fa" in fas:
            nb += 1
            remove(path.join("data", f"{lib}_split", f"{sample}.fa"))
    print("Num removed", nb)
    

if __name__ == "__main__":
    libs = get_libs()
    for lib in libs:
        fas = frozenset(get_fastas(lib))

        if len(fas) == 0:
            continue
            
        print(lib, "fa", len(fas))
        samples = get_all_distant_samples(lib)
        print(lib, len(samples))
        clean_lib(lib, fas, samples)
        