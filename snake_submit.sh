#!/bin/bash


running=$(squeue -u $UID | wc -l)

JID=""
if [ $running -le 2 ]; then
    last_out=$(ls -t *.out | head -1)
    if [ -f "$T"]; then
	if grep "all requested files are present and up to date" slurm-2097226.out > /dev/null; then
	    echo "Exec terminated"
            exit 0
	fi
    fi
    JID=$(sbatch -p prepost -A mrb@cpu ./run_snakemake.sh --output=out/submit_%j.out --error=out/submit_%j.err | cut -d " " -f 4)
fi


#sleep 60m
sbatch --begin=now+3600 -p prepost -A mrb@cpu ./snake_submit.sh --output=out/submit_%j.out --error=out/submit_%j.err
