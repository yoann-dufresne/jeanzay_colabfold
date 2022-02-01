#!/bin/bash
#SBATCH --job-name=job-array   # nom du job
#SBATCH --ntasks=1             # Nombre total de processus MPI
#SBATCH --ntasks-per-node=1    # Nombre de processus MPI par noeud
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
# Dans le vocabulaire Slurm "multithread" fait référence à l'hyperthreading.
#SBATCH --hint=nomultithread   # 1 processus MPI par coeur physique (pas d'hyperthreading)
#SBATCH --time=00:30:00        # Temps d’exécution maximum demande (HH:MM:SS)
#SBATCH --output=/linkhome/rech/genpro01/ubu39dm/yoann/test2/%a.out  # Nom du fichier de sortie contenant l'ID et l'indice
#SBATCH --error=/linkhome/rech/genpro01/ubu39dm/yoann/test2/%a.err   # Nom du fichier d'erreur (ici commun avec la sortie)
#SBATCH --array=0-49%30        # 50 travaux en tout mais 30 travaux max dans la file

# on se place dans le répertoire de soumission
cd /linkhome/rech/genpro01/ubu39dm/yoann

# Execution du binaire "mon_exe" avec des donnees differentes pour chaque travail
# La valeur de ${SLURM_ARRAY_TASK_ID} est differente pour chaque travail.
srun sh /linkhome/rech/genpro01/ubu39dm/yoann/scripts/folder_run.sh
