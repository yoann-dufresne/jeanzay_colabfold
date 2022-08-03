# script that re-runs palmfold.py on results in delivery/ folder, but does it in a partitioned way using cluster

taskid=${SLURM_ARRAY_TASK_ID}

cd delivery
python3 /gpfswork/rech/rep/ubu39dm/softwares/palmfold/palmfold.py -p /gpfswork/rech/rep/ubu39dm/softwares/palmfold/pol/ -t 0.3 -d . -f $taskid
