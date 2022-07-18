#!/bin/bash


mkdir -p out

running=$(squeue -u $UID | wc -l)

if [ $running -le 2 ]; then
    # last_out=$(ls -t out/ | grep *.out | head -1)
    # if [ -f "$T"]; then
    # 	if grep "all requested files are present and up to date" slurm-*.out > /dev/null; then
    # 	    echo "Exec terminated"
    #             exit 0
    # 	fi
    # fi

    mkdir -p out/snakemake
    sbatch -p prepost -A mrb@cpu --qos="qos_cpu-t4" --time="20:00:00" --output="out/snakemake/run_%j.out" --error="out/snakemake/run_%j.err" ./run_snakemake.sh
fi


mkdir -p out/submit
sbatch --begin=now+600 -p prepost -A mrb@cpu --output="out/submit/submit_%j.out" --error="out/submit/submit_%j.err" ./jz_run_snakemake.sh
