#!/bin/python3

# From a sample directory given in argument, compress the molecule set into a unique tar.gz
# then upload it to s3

from os import path, listdir, rename, getenv, remove, chdir
from sys import stderr, argv
from shutil import rmtree
import subprocess


# Analyse a result directory to determine if everything is folded.
# If yes, compress the sample and upload it on the s3 server


# Extract the sample name
sample_dir = argv[1][:-1] if argv[1][-1] == '/' else argv[1]
sample = sample_dir[sample_dir.rfind("_")+1:]

# Search the fold_split directory of the sample
fold_dir = path.join(sample_dir, "fold_split")
if path.exists(fold_dir):
    # Verify that all the molecules are compressed
    for split_dir in listdir(fold_dir):
        split_dir = path.join(fold_dir, split_dir)

        for file in listdir(split_dir):
            if file.endswith(".a3m"):
                print("Warning: Not all molecules as been included in tars.", file=stderr)
                print("Molecule", file, "still present in", split_dir, file=stderr)
                exit(0)

lib = sample_dir.split('/')[-2]
lib = lib[:lib.find('_')]

mol_dir = path.join(sample_dir, f"molecules_{sample}")
if not path.exists(mol_dir):
    print("Warning: No molecule to compress", file=stderr)
    exit(0)

chdir(sample_dir)

# Compress the molecules directory
archive = f"{lib}_{sample}.tar.gz"
complete_process = subprocess.run(["tar", "--remove-files", "-czf", archive, f"molecules_{sample}"])
if complete_process.returncode != 0:
    print("Error: Compression command finished on non 0 return value", file=stderr)
    print(complete_process.stderr, file=stderr)
    exit(complete_process.returncode)


# debug command
rename(archive, path.join(getenv("WORK"), "results", archive))
# # real command
# complete_process = subprocess.run(["/gpfswork/rech/yph/uep61bl/software/aws/dist/aws", "s3", "cp", archive, f"s3://serratus-fold/{lib}/{lib}-{sample}.tar.gz"])
# if complete_process.returncode != 0:
#     print("Error: s3 upload finished on non 0 return value", file=stderr)
#     print(complete_process.stderr, file=stderr)
#     exit(complete_process.returncode)
# remove(archive)
# rmtree(sample_dir)


# End of pipeline \o/
