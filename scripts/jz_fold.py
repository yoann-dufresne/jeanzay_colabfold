#!/bin/python3

from os import listdir, path, mkdir, remove, rename
from sys import stderr, argv
import subprocess

# Import the root directory to be able to call palmfold
root_dir = path.dirname(path.dirname(path.abspath(__file__)))
sys.path.append(root_dir)
from palmfold.palmfold import main as palmfold_main




def score_molecules(split_path):
    # Score and compress all the molecules
    palmfold_main(split_path, path.join(root_dir, "palmfold", "pol"), 0)
    # Rename realigned files
    for file in listdir(split_path):
        if file.endswith("_realign.pdb"):
            rename(path.join(split_path, file), path.join(split_path, file[:-12]))





sample_path = argv[1]
if sample_path[-1] == '/':
    sample_path[:-1]

fold_path = path.join(sample_path, "fold_split")
if not path.exists(fold_path):
    print("No folder", fold_path, file=stderr)
    exit(1)

split_dir = f"split_{argv[2]}"
split_path = path.join(fold_path, split_dir)
if not path.exists(fold_path):
    print("No folder", fold_path, file=stderr)
    exit(1)


# data/lib_split/res_sample/fold_split/split_x
splitted_path = sample_path.split('/')
sample = splitted_path[-1][4:]
lib = splitted_path[-2][:-6]

# Colabfold
cmd = f"colabfold_batch --stop-at-score 85 {split_path} {split_path}"
complete_process = subprocess.run(cmd.split(' '))
if complete_process.returncode != 0:
    print("Error: Colabfold command finished on non 0 return value", file=stderr)
    print(complete_process.stderr, file=stderr)
    exit(complete_process.returncode)


# Clean
for file in listdir(split_path):
    to_delete = False
    if file == "cite.bibtex":
        to_delete = True
    elif file == "config.json":
        to_delete = True
    elif file.endswith(".png"):
        to_delete = True
    elif file.endswith(".done.txt"):
        to_delete = True
    elif "_error_" in file:
        to_delete = True
    elif "_rank_" in file and not "_rank_1_" in file:
        to_delete = True

    if to_delete:
        remove(path.join(split_path, file))

# Remove duplicates jsons and pdbs
files_per_mol = {}
for file in listdir(split_path):
    if not (file.endswith(".json") or file.endswith(".pdb")):
        continue

    file_path = path.join(split_path, file)
    mol = file[:file.find("_")]
    if mol not in files_per_mol:
        files_per_mol[mol] = {"json":None, "pdb":None}

    extention = file[file.rfind(".")+1:]

    if files_per_mol[mol][ext] is None:
        files_per_mol[mol][ext] = file
    elif path.getctime(file_path) - path.getctime(path.join(split_path, files_per_mol[mol][ext])) > 0:
        remove(path.join(split_path, files_per_mol[mol][ext]))
        files_per_mol[mol][ext] = file


# Score the alignments
score_molecules(split_path)

# Create a lock file
open(path.join(split_path, "folded.lock"), 'a').close()

