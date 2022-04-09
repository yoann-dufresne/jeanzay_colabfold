#!/bin/bash
#SBATCH -A yph@cpu
#SBATCH --job-name=Serratus-Delivery
#SBATCH --ntasks=1                     # total number of process
#SBATCH --ntasks-per-node=1            # Number of process per node
#SBATCH --hint=nomultithread           # No hyperthreading
#SBATCH --mem=10G
#SBATCH --cpus-per-task=1
#SBATCH --time=20:00:00
#SBATCH --output=/gpfsssd/scratch/rech/rep/ubu39dm/TSAL/delivery.package.%a.out
#SBATCH --error=/gpfsssd/scratch/rech/rep/ubu39dm/TSAL/delivery.package.%a.err

module load python/3.8.8
export PATH=$PATH:/gpfs7kw/linkhome/rech/genpro01/ubu39dm/.local/bin/

srun bash -c "cd /gpfsssd/scratch/rech/rep/ubu39dm/GMGCL_MSAs && \time ./delivery.package.sh"
