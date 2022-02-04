#!/bin/bash

mkdir result_${SLURM_ARRAY_TASK_ID}
echo "colabfold_batch split_${SLURM_ARRAY_TASK_ID} result_${SLURM_ARRAY_TASK_ID}"
# Run colabfold
colabfold_batch split_${SLURM_ARRAY_TASK_ID} result_${SLURM_ARRAY_TASK_ID}
# Delete unneeded files
cd "result_${SLURM_ARRAY_TASK_ID}"
rm cite.bibtex config.json *.png *_rank_[2-5]_*
PATH=$PATH:~/.local/bin
python3 /gpfswork/rech/rep/ubu39dm/softwares/palmfold/palmfold.py -p /gpfswork/rech/rep/ubu39dm/softwares/palmfold/pol/ -t 0.9 -d .
cd ..
tar -czf result_${SLURM_ARRAY_TASK_ID}.tar.gz result_${SLURM_ARRAY_TASK_ID}/ --remove-files
rm -r split_${SLURM_ARRAY_TASK_ID}