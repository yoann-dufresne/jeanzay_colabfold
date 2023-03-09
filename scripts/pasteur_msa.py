from os import path, listdir, rename, mkdir, remove, chdir, getcwd, getenv
from shutil import copy, rmtree
import subprocess
from sys import stderr, argv



def run_cmd(cmd, err_msg, on_error=None):
    complete_process = subprocess.run(cmd.split(' '))
    if complete_process.returncode != 0:
        print(err_msg, file=stderr)
        print(complete_process.stderr, file=stderr)
        if on_error is not None:
            on_error()
        exit(complete_process.returncode)



db = "/pasteur/appa/scratch/rchikhi/colabfold_db/"
tdb = "/pasteur/appa/scratch/ydufresn/id90/pssm_and_intact_suggested_db"
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
run_cmd(cmd, "Error: Colabfold teminated on non 0 return value")


# Add neighbor rdrp to each of the msa
for msa_filename in [f for f in listdir(out_dir) if f.endswith(".a3m")]:
    mol_name = msa_filename[:-4]
    a3m_path = path.join(out_dir, msa_filename)
    a3mfa_path = f"{a3m_path[:-4]}.a3mfa"

    # Extract the molecule of interest from the a3m
    with open(a3m_path) as a3m, open(a3mfa_path, "w") as a3mfa:
        print(a3m.readline().strip(), file=a3mfa)
        print(a3m.readline().strip(), file=a3mfa)

    qdb = path.join(out_dir, f"qdb.{mol_name}.fa")
    res = path.join(out_dir, f"res.{mol_name}.fa")
    tmp = path.join(out_dir, f"tmp.{mol_name}.fa")

    # index sequence inside of the msa
    cmd = f"mmseqs createdb {a3mfa_path} {qdb}"
    run_cmd(cmd, "Error: mmseqs createdb teminated on non 0 return value")
    # Search the a3m seq into the rdrp db
    cmd = f"mmseqs search --threads 1 {qdb} {tdb} {res} {tmp}"
    run_cmd(cmd, "Error: mmseqs search terminated on non 0 return value")
    
    # Move and protect the old a3m
    rename(a3m_path, f"{a3m_path}.old")
    def rollback():
        rename(f"{a3m_path}.old", a3m_path)

    # Extract the msa into an a3m file
    cmd = f"mmseqs result2msa --threads 1 {qdb} {tdb} {res} {a3m_path}.new --msa-format-mode 5"
    run_cmd(cmd, "Error: mmseqs msa extraction failed", on_error=rollback)

    # Concatenated the a3m files
    with open(f"{a3m_path}.old") as a3mold, open(f"{a3m_path}.new") as a3mnew, open(a3m_path, "w") as a3m:
        for line in a3mold:
            print(line.strip(), file=a3m)
        for line in a3mnew:
            print(line.strip(), file=a3m)

    # Clean the directory
    rmtree(tmp)
    for file in [f for f in listdir(out_dir) if f.startswith(f"qdb.{mol_name}.fa")]:
        remove(path.join(out_dir, file))
    for file in [f for f in listdir(out_dir) if f.startswith(f"res.{mol_name}.fa")]:
        remove(path.join(out_dir, file))
    for file in [f for f in listdir(out_dir) if f.startswith(f"{mol_name}.a3m.new")]:
        remove(path.join(out_dir, file))
    remove(f"{a3m_path}.old")
    remove(a3mfa_path)



# Compress
copy(fa, path.join(out_dir, splitted_path[-1]))
path_save = getcwd()
chdir(lib_dir)
cmd = f"tar --remove-files -czf {tar} res_{sample}"
run_cmd(cmd, "tar creation failed")
if (path.exists(f"{sample}.lock")):
    remove(f"{sample}.lock")
