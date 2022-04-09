#!/bin/bash
#SBATCH -A yph@cpu
#SBATCH --job-name=Serratus-Colabfold-Gather
#SBATCH --ntasks=1                     # total number of process
#SBATCH --ntasks-per-node=1            # Number of process per node
#SBATCH --hint=nomultithread           # No hyperthreading
#SBATCH --mem=10G
#SBATCH --cpus-per-task=1
#SBATCH --time=20:00:00
#SBATCH --output=/gpfsssd/scratch/rech/rep/ubu39dm/GMGCL_MSAs/delivery.%a.out
#SBATCH --error=/gpfsssd/scratch/rech/rep/ubu39dm/GMGCL_MSAs/delivery.%a.err

module load python/3.8.8 cuda/11.2
export PATH=$PATH:/gpfs7kw/linkhome/rech/genpro01/ubu39dm/.local/bin/

cd /gpfsssd/scratch/rech/rep/ubu39dm/GMGCL_MSAs/

srun sh delivery.sh
