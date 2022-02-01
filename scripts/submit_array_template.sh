#!/bin/bash
#SBATCH --job-name=Serratus-Colabfold
#SBATCH --ntasks=1                     # total number of process
#SBATCH --ntasks-per-node=1            # Number of process per node
#SBATCH --gres=gpu:1                   # GPU
#SBATCH --cpus-per-task=8              # CPU
#SBATCH --hint=nomultithread           # No hyperthreading
#SBATCH --time=00:30:00                # Max exec time (HH:MM:SS) TIME
#SBATCH --output=/linkhome/rech/genpro01/ubu39dm/yoann/test2/%a.out  # STDOUT
#SBATCH --error=/linkhome/rech/genpro01/ubu39dm/yoann/test2/%a.err   # STDERR
#SBATCH --array=0-49%30                # 50 travaux en tout mais 30 travaux max dans la file

module load python/3.8.8 cuda/11.2
export PATH=$PATH:/gpfs7kw/linkhome/rech/genpro01/ubu39dm/.local/bin/

cd /linkhome/rech/genpro01/ubu39dm/yoann # WORKDIR

srun sh /linkhome/rech/genpro01/ubu39dm/yoann/scripts/job.sh # JOB
