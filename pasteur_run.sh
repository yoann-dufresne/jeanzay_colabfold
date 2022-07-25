#!/bin/bash

set -e

module load Python/3.8.3 cuda/11.2

lib_path=data/CFDL_split
mkdir -p out && mkdir -p out/upload

sbatch -c 1 --mem="20G" --qos="seqbio" -p "seqbio" -A "seqbio" --job-name="upload" --output="out/upload/%j.out" --error="out/upload/%j.err" ./scripts/pasteur_upload.sh

for file in $lib_path/*.fa
do
	# name=$(basename $file)
	# id_list="$id_list,${name::-3}"
	# # echo ${id_list:1}
	sbatch -c 16 --mem="240G" --qos="fast" -p "common,dedicated,human_hidden" --job-name="msa" --output=out/msa_%j.out --error=out/msa_%j.err ./scripts/pasteur_msa.sh $file
done



