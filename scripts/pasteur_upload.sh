#!/bin/bash

set -e

module load Python/3.8.3
python3 scripts/pasteur_upload.py

#mkdir -p out && mkdir -p out/upload
#sbatch -p seqbio -A seqbio --qos seqbio -c 1 --mem 20G --begin=now+600  --job-name="upload" --output="out/upload/%j.out" --error="out/upload/%j.err" ./scripts/pasteur_upload.sh