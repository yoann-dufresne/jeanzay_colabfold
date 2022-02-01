#!/bin/bash

module load python/3.8.8 cuda/11.2
export PATH=$PATH:/gpfs7kw/linkhome/rech/genpro01/ubu39dm/.local/bin/
cd /linkhome/rech/genpro01/ubu39dm/yoann/test2/
mkdir result_${SLURM_ARRAY_TASK_ID}
echo "colabfold_batch split_${SLURM_ARRAY_TASK_ID} result_${SLURM_ARRAY_TASK_ID}"
colabfold_batch split_${SLURM_ARRAY_TASK_ID} result_${SLURM_ARRAY_TASK_ID}