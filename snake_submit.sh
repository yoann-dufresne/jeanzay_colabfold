#!/bin/bash


running=$(squeue -u $UID | wc -l)

if [ $running -le 2 ]; then
	sbatch -p prepost -A mrb@cpu ./run_snakemake.sh --output=out/%a.out --error=out/%a.err
fi


sleep 60m
sbatch -p prepost -A mrb@cpu ./snake_submit.sh --output=out/%a.out --error=out/%a.err
