#!/bin/bash

SLURM_ARRAY_TASK_ID="28"

module load Python/3.8.3 cuda/11.2
python3 scripts/pasteur_msa.py "${1/ID/"$SLURM_ARRAY_TASK_ID"}"
echo "${1/ID/"$SLURM_ARRAY_TASK_ID"}"
