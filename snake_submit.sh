#!/bin/bash


running=$(squeue -u $UID | wc -l)

JID=""
if [ $running -le 2 ]; then
	JID=$(sbatch -p prepost -A mrb@cpu ./run_snakemake.sh --output=out/submit_%j.out --error=out/submit_%j.err | cut -d " " -f 4)
fi


#sleep 60m
sbatch --begin=now+3600 -p prepost -A mrb@cpu ./snake_submit.sh --output=out/submit_%j.out --error=out/submit_%j.err
