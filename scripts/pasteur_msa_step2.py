#!/bin/python3

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


# Extract paths and names
split_dirpath = argv[1]


# If nothing to do, direct exit
if not path.exists(split_dirpath):
    exit(0)
# Else, recursivly schedule the same script
# run_cmd("sbatch ...", "Impossible to recursively submit this job")

# index the a3m files locks and the ready files
a3ms = []


# a3m by a3m in a split directory
    # protect the a3m with a lock
    # exect the a3m mmseq pipeline
    # add a molecule.ready
    # clean the directory
    # remove lock