#!/bin/bash

module load python/3.9.12 cuda/11.2
mkdir -p /gpfsscratch/rech/yph/uep61bl/data/tmp/
RAND_DIR="/gpfsscratch/rech/yph/uep61bl/data/tmp/$RANDOM$RANDOM$RANDOM$RANDOM"
export TMPDIR=$RAND_DIR

python3 scripts/jz_fold.py $sample_path $SLURM_ARRAY_TASK_ID

rm -rf $RAND_DIR
