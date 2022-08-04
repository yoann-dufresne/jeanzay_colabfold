#!/bin/bash

set -e

module load python/3.9.12

python3 scripts/jz_compress_molecules.py $split_dir
