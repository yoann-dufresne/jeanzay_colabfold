#!/bin/bash

set -e

module load python/3.9.12

python3 scripts/jz_split.py $res_dir
