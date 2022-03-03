#!/bin/bash
#SBATCH --job-name=Serratus-Colabfold
#SBATCH --ntasks=1                     # total number of process
#SBATCH --ntasks-per-node=1            # Number of process per node
#SBATCH --gres=gpu:1                   # GPU
#SBATCH --hint=nomultithread           # No hyperthreading
#SBATCH --mem=2G                       # RAM
#SBATCH --cpus-per-task=1              # CPU
#SBATCH --time=00:30:00                # Max exec time (HH:MM:SS) # TIME
#SBATCH --output=/linkhome/rech/genpro01/ubu39dm/yoann/test2/%a.out  # STDOUT
#SBATCH --error=/linkhome/rech/genpro01/ubu39dm/yoann/test2/%a.err   # STDERR
#SBATCH --array=0-49%30                # 50 travaux en tout mais 30 travaux max dans la file # ARRAY


SCRIPT_DIR=/pasteur/zeus/projets/p02/seqbio/yoann/jeanzay_colabfold/test # SCRDIR
# Read the properties file. This file keeps track on where we are during the exec.
# It defines MAX_JOB_ID (last job id to run), MAX_SIMULTANEOUS (maximum number of simultaneous 
# jobs), MAX_SUBMIT (maximum number of jobs allowed in the queue) CURRENT_START (First ID of the
# current job array) CURRENT_STOP (Last ID of the current job array)
source $SCRIPT_DIR/properties.sh



echo $SLURM_ARRAY_TASK_ID

# --- Time to submit new jobs recursively ---
if (( $SLURM_ARRAY_TASK_ID == $CURRENT_STOP )) && (($CURRENT_STOP != $MAX_JOB_ID)); then
  # modify the submit array job
  SUBMIT_BATCH=$(($MAX_SUBMIT / 2))
  START=$(($CURRENT_STOP+1))
  STOP=$(($START + $SUBMIT_BATCH - 1))
  STOP=$(($MAX_JOB_ID < $STOP ? $MAX_JOB_ID : $STOP))
  sed -i "/--array=$CURRENT_START/c\#SBATCH --array=$START-$STOP%$MAX_SIMULTANEOUS # ARRAY" $SCRIPT_DIR/submit.slurm

  # modify the properties for next array submition
  sed -i "/CURRENT_START/c\CURRENT_START=$START" $SCRIPT_DIR/properties.sh
  sed -i "/CURRENT_STOP/c\CURRENT_STOP=$STOP" $SCRIPT_DIR/properties.sh

  # Submit recursive array
  sbatch $SCRIPT_DIR/submit.slurm
fi


# --- Run the job ---

module load python/3.8.8 cuda/11.2
export PATH=$PATH:/gpfs7kw/linkhome/rech/genpro01/ubu39dm/.local/bin/

cd /linkhome/rech/genpro01/ubu39dm/yoann # WORKDIR

srun sh /linkhome/rech/genpro01/ubu39dm/yoann/scripts/job.sh # JOB

