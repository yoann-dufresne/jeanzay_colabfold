#!/bin/bash

module load python/3.9.12 cuda/11.2
mkdir -p /gpfsscratch/rech/yph/uep61bl/data/tmp/
export TMPDIR=/gpfsscratch/rech/yph/uep61bl/data/tmp/

python3 scripts/jz_fold.py $sample_path $SLURM_ARRAY_TASK_ID