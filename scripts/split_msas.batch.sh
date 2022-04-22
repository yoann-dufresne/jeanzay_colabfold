#!/bin/bash
#SBATCH -A yph@gpu
#SBATCH --qos=qos_gpu-t3
#SBATCH --job-name=Serratus-Colabfold-Split
#SBATCH --ntasks=1                     # total number of process
#SBATCH --ntasks-per-node=1            # Number of process per node
#SBATCH --gres=gpu:1                   # GPU
#SBATCH --hint=nomultithread           # No hyperthreading
#SBATCH --mem=10G
#SBATCH --cpus-per-task=1
#SBATCH --time=20:00:00
#SBATCH --output=/gpfsssd/scratch/rech/rep/ubu39dm/TSAL/split.%a.out
#SBATCH --error=/gpfsssd/scratch/rech/rep/ubu39dm/TSAL/split.%a.err

module load python/3.8.8
export PATH=$PATH:/gpfs7kw/linkhome/rech/genpro01/ubu39dm/.local/bin/

srun bash -c "cd /gpfsssd/scratch/rech/rep/ubu39dm/TSAL/ && lz4 -d ../TSAL.final.a3m.lz4  | python split_msas.py /dev/stdin out"
