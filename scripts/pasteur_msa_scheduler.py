from os import path, listdir, rename, mkdir, remove, chdir, getcwd, getenv
from shutil import copy, rmtree
import subprocess
from sys import stderr, argv
from random import randint
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


def recursive_submit():
    cmd = "sbatch -p seqbio -A seqbio --qos seqbio -c 1 --mem 20G --begin=now+3600  --job-name=\"upload\" --output=\"out/upload/%j.out\" --error=\"out/upload/%j.err\" ./scripts/pasteur_msa_scheduler.sh"
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


def nb_jobs():
    ok, out = run_cmd("squeue -h -u ydufresn", stdout=True)

    if not ok:
        exit(1)

    out.replace('\t', ' ')
    nb = 0
    for line in out.split('\n'):
        line = re.sub('\\s+', ' ', line.strip())
        if " msa " in line:
            nb += 1
    
    return nb


def currently_stored(libs):
    nb_running = nb_jobs()
    print(nb_running, "running msa")

    total_tars = 0
    for lib in libs:
        tars = [file for file in listdir(path.join("data", f"{lib}_split")) if file.endswith(".tar.gz")]
        total_tars += len(tars)
    print(total_tars, "already computed samples")

    return nb_running + total_tars


def todo_msa(lib):
    lib_path = path.join("data", f"{lib}_split")
    
    tars = []
    fas = []
    locks = []
    dirs = []

    for file in listdir(lib_path):
        if file.startswith("res_"):
            dirs.append(file[4:])
        elif file.endswith(".tar.gz"):
            tars.append(file[:-7])
        elif file.endswith('.fa'):
            fas.append(file[:-3])
        elif file.endswith(".lock"):
            locks.append(file[:-5])

    return ((frozenset(fas) - frozenset(tars)) - frozenset(dirs)) - frozenset(locks)


def lib_submition(lib, samples, max_submit):
    out_path = path.join("out", "msa")
    if not path.exists(out_path):
        mkdir(out_path)

    max_submit = min(max_submit, len(samples))
    nb_submitted = 0
    for i in range(max_submit):
        current_file = path.join("data", f"{lib}_split", f"{samples[i]}.fa")
        ok = run_cmd(f'sbatch -c 16 --mem="240G" --qos="fast" -p "common,dedicated,human_hidden" --job-name="msa" --output=out/msa/msa_%j.out --error=out/msa/msa_%j.err --export=FILE={current_file} ./scripts/pasteur_msa.sh')
        if ok:
            open(path.join("data", f"{lib}_split", f"{samples[i]}.lock"), 'a').close()
            nb_submitted += 1

    return nb_submitted


def recursive_submit():
    cmd = "sbatch -p seqbio -A seqbio --qos seqbio -c 1 --mem 20G --begin=now+86400  --job-name=\"mas_sched\" --output=\"out/msa_sched/%j.out\" --error=\"out/mas_sched/%j.err\" ./scripts/pasteur_msa_scheduler.sh"
    ok = run_cmd(cmd)
    if not ok:
        print("Impossible to recursively submit the script. Quitting...", file=stderr)


if __name__ == "__main__":
    libs = get_libs()
    remaining_computation = 5000 - currently_stored(libs)

    # Get all the tar.gz
    for lib in libs:
        samples = todo_msa(lib)
        print(lib, len(samples))
        remaining_computation -= lib_submition(lib, list(samples), remaining_computation)

    recursive_submit()
    