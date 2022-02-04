#!/bin/bash

mkdir result_${SLURM_ARRAY_TASK_ID}
echo "colabfold_batch split_${SLURM_ARRAY_TASK_ID} result_${SLURM_ARRAY_TASK_ID}"
# Run colabfold
colabfold_batch split_${SLURM_ARRAY_TASK_ID} result_${SLURM_ARRAY_TASK_ID}
# Delete unneeded files
cd "result_${SLURM_ARRAY_TASK_ID}"
rm cite.bibtex config.json *.png *_rank_[2-5]_*
# TODO: TM-Align
cd ..
tar -czf result_${SLURM_ARRAY_TASK_ID}.tar.gz result_${SLURM_ARRAY_TASK_ID}/ --remove-files
rm -r split_${SLURM_ARRAY_TASK_ID}