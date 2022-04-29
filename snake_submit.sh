#!/bin/bash


running=$(squeue -u $UID | wc -l)

if [ $running -le 2 ]; then
	sbatch -p hubbioit --qos=hubbioit ./run_snakemake.sh --output=out/%a.out --error=out/%a.err
fi


sleep 3m
sbatch -p hubbioit --qos=hubbioit ./snake_submit.sh --output=out/%a.out --error=out/%a.err
