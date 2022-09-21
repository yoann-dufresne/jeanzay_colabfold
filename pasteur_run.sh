#!/bin/bash

set -e

module load Python/3.8.3 cuda/11.2


mkdir -p out && mkdir -p out/upload
sbatch -c 1 --mem="20G" --qos="seqbio" -p "seqbio" -A "seqbio" --job-name="upload" --output="out/upload/%j.out" --error="out/upload/%j.err" ./scripts/pasteur_upload.sh
mkdir -p out/scheduler
sbatch -c 1 --mem="20G" --qos="seqbio" -p "seqbio" -A "seqbio" --job-name="scheduler" --output=out/scheduler/%j.out --error=out/scheduler/%j.err ./scripts/pasteur_msa_scheduler.sh



