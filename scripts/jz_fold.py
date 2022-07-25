#!/bin/python3

from os import listdir, path, mkdir
from sys import stderr, argv

fold_dir = argv[1]
if fold_dir[-1] == '/':
    fold_dir[:-1]

if not path.exists(fold_dir):
    print("No directory", fold_dir, file=stderr)
    exit(1)

# data/lib_split/res_sample/fold_split/split_x
splitted_path = fold_dir.split('/')
sample = splitted_path[-3][4:]
lib = splitted_path[-4][:-6]

# Colabfold
cmd = f"colabfold_batch --stop-at-score 85 {fold_dir} {fold_dir}"
complete_process = subprocess.run(cmd.split(' '))
if complete_process.returncode != 0:
    print("Error: Colabfold command finished on non 0 return value", file=stderr)
    print(complete_process.stderr, file=stderr)
    exit(complete_process.returncode)


# Clean
for file in listdir(fold_dir):
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
        remove(path.join(fold_dir, file))


# No direct successor script. The following script has been launched by split