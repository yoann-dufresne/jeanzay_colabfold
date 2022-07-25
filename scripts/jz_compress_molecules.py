#!/bin/python3

# Compress each individual molecules from the sample into a tar.gz and move it to the molecule dir

from os import path, listdir, mkdir, remove
from shutil import copy
import sys, subprocess
from sys import stderr, argv
# Import the root directory to be able to call palmfold
root_dir = path.dirname(path.dirname(path.abspath(__file__)))
sys.path.append(root_dir)
from palmfold.palmfold import main as palmfold_main


# Extract the sample name and the needed paths
split_dir = argv[1]
if split_dir[-1] == '/':
    split_dir = split_dir[:-1]
split_path = split_dir.split("/")
sample = split_path[-3]
sample = sample[sample.find("_")+1:]
lib = split_path[-4]
lib = lib[:lib.find("_")]
mol_dir = path.join(*split_path[:-2], f"molecules_{sample}")

# Search for unfolded molecules
molecules = [x[:-4] for x in listdir(split_dir) if x.endswith(".a3m")]
pdbs = frozenset([x[:x.find("_")] for x in listdir(split_dir) if x.endswith(".pdb")])
for mol in molecules:
    if mol not in pdbs:
        print("missing folding for", mol, "in", split_dir, file=stderr)
        exit(1)

# Create molecule directory and global tm file
if not path.exists(mol_dir):
    mkdir(mol_dir)
global_tm = path.join(mol_dir, f"{lib}_{sample}.tm")
if not path.exists(global_tm):
    with open(global_tm, "a") as gtm:
        print("PDBchain1\tPDBchain2\tTM1\tTM2\tRMSD\tID1\tID2\tIDali\tL1\tL2\tLali", file=gtm)


# Score and compress all the molecules
palmfold_main(split_dir, path.join(root_dir, "palmfold", "pol"), 0)

# Sort the files by molecules and filetype
mol_files = {mol:{} for mol in molecules}
for file in listdir(split_dir):
    if file.endswith(".a3m"):
        mol_files[file[:-4]]["a3m"] = file
    elif file.endswith(".pdb"):
        mol = file[:file.find("_")]
        if "pdb" in mol_files[mol]:
            print("Error: Multiple pdb files for molecule", mol, "in", split_dir, file=stderr)
            exit(1)
        mol_files[mol]["pdb"] = file
    elif file.endswith(".json"):
        mol = file[:file.find("_")]
        if "json" in mol_files[mol]:
            print("Error: Multiple json files for molecule", mol, "in", split_dir, file=stderr)
            exit(1)
        mol_files[mol]["json"] = file
    elif file.endswith(".tm"):
        mol_files[file[:-3]]["tm"] = file
    elif file.endswith(".fa"):
        mol_files[file[:-3]][file[-5:]] = file

missing_error = False
scores = []
for mol in molecules:
    file_missing = False
    # Files check for this molecule
    if "tm" not in mol_files[mol]:
        print("Warning: missing tm file for molecule", mol, file=stderr)
        file_missing = True
    if "a3m" not in mol_files[mol]:
        print("Warning: missing a3m file for molecule", mol, file=stderr)
        file_missing = True
    if "json" not in mol_files[mol]:
        print("Warning: missing json file for molecule", mol, file=stderr)
        file_missing = True
    if "pdb" not in mol_files[mol]:
        print("Warning: missing pdb file for molecule", mol, file=stderr)
        file_missing = True
    # Set global error
    if file_missing:
        missing_error = True
        continue
    # read the molecule tm file
    with open(path.join(split_dir, mol_files[mol]["tm"])) as tmf:
        tmf.readline()
        scores.extend([x.strip() for x in tmf.readlines()])
    # Create a tar.gz
    tar_dir = f"{sample}_{mol}"
    archive = f"{sample}_{mol}.tar.gz"
    if not path.exists(tar_dir):
        mkdir(tar_dir)
    for ext in mol_files[mol]:
        file = mol_files[mol][ext]
        copy(path.join(split_dir, file), path.join(tar_dir, file))
        remove(path.join(split_dir, file))
    complete_process = subprocess.run(["tar", "--remove-files", "-czf", archive, tar_dir])
    if complete_process.returncode != 0:
        print("Error: Compression command finished on non 0 return value", file=stderr)
        print(complete_process.stderr, file=stderr)
        exit(complete_process.returncode)
    # move the tar to the right dir
    copy(archive, path.join(mol_dir, archive))
    remove(archive)

# Write the global tm file
with open(global_tm, "a") as gtm:
    print("\n".join(scores), file=gtm)

if missing_error:
    print("Error: some files are missing, quitting compression step", file=stderr)
    exit(1)

