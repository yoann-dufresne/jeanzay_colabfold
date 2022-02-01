#!/bin/bash

mkdir result_${SLURM_ARRAY_TASK_ID}
echo "colabfold_batch split_${SLURM_ARRAY_TASK_ID} result_${SLURM_ARRAY_TASK_ID}"
colabfold_batch split_${SLURM_ARRAY_TASK_ID} result_${SLURM_ARRAY_TASK_ID}