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
tdb = "/pasteur/appa/scratch/ydufresn/id90/pssm_intact_and_permuted_suggested_db"
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
msa_colab = path.join(out_dir, "final.a3m")


qdb = path.join(out_dir, f"qdb")
res = path.join(out_dir, f"res")
tmp = path.join(out_dir, f"tmp")

# Create query database for mmseq
cmd = f"mmseqs createdb {fa} {qdb}"
print(cmd)
run_cmd(cmd, f"Error: Impossible to create the query database for {sample}")

# Search the queries into rdrps
cmd = f"mmseqs search --threads 16 {qdb} {tdb} {res} {tmp}"
run_cmd(cmd, f"Error: mmseqs search terminated on non 0 return value for sample {sample}")
# Extract the msa
msa_rdrp = path.join(out_dir, "msa2")
cmd = f"mmseqs result2msa --threads 16 {qdb} {tdb} {res} {msa_rdrp}"
run_cmd(cmd, f"Impossible to convert result to msa for sample {sample}")

# Generate final alignment
align = path.join(out_dir, "final_msa")
cmd = f"mmseqs mergedbs {qdb} {align} {msa_colab} {msa_rdrp}"
run_cmd(cmd, f"Impossible to merge msas for sample {sample}")
remove(msa_colab)

#unpack msas
cmd = f"mmseqs unpackdb {align} {out_dir} --unpack-name-mode 0 --unpack-suffix .a3m"
run_cmd(cmd, f"Impossible to unpack databases into a3m files for sample {sample}")

# Clean directory
for file in listdir(out_dir):
    if not file.endswith(".a3m"):
        if path.isdir(path.join(out_dir, file)):
            rmtree(path.join(out_dir, file))
        else:
            remove(path.join(out_dir, file))

# Compress
copy(fa, path.join(out_dir, splitted_path[-1]))
path_save = getcwd()
chdir(lib_dir)
cmd = f"tar --remove-files -czf {tar} res_{sample}"
run_cmd(cmd, "tar creation failed")
if (path.exists(f"{sample}.lock")):
    remove(f"{sample}.lock")
