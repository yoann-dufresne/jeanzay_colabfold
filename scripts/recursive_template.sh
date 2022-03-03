#!/bin/bash
#SBATCH --job-name=recursive-Serratus-Colabfold
#SBATCH --ntasks=1                     # total number of process
#SBATCH --ntasks-per-node=1            # Number of process per node
#SBATCH --gres=gpu:1                   # GPU
#SBATCH --hint=nomultithread           # No hyperthreading
#SBATCH --mem=2G                       # RAM
#SBATCH --cpus-per-task=1              # CPU
#SBATCH --time=00:25:00                # Max exec time (HH:MM:SS) 
#SBATCH --output=/linkhome/rech/genpro01/ubu39dm/yoann/test2/recur.out  # STDOUT
#SBATCH --error=/linkhome/rech/genpro01/ubu39dm/yoann/test2/recur.err   # STDERR


SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Read the properties file. This file keeps track on where we are during the exec.
# It defines MAX_JOB_ID (last job id to run), CURRENT_JOB_ID (next job to run), MAX_SIMULTANEOUS
# (maximum number of simultaneous jobs), MAX_SUBMIT (maximum number of jobs allowed in the queue)
source $SCRIPT_DIR/properties.sh


SUBMIT_BATCH=$(($MAX_SUBMIT / 2))

# modify the submit array job
START=$CURRENT_JOB_ID
STOP=$(($START + $MAX_SIMULTANEOUS - 1))
sed -i '/# ARRAY/c\${START}-${STOP}:${MAX_SIMULTANEOUS} # ARRAY'
# Submit array


# modify the properties for next array submition


# Compress outputs

# Send to pasteur


sleep 1200

sbatch recursive_template.sh
