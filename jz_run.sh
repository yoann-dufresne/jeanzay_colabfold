#!/bin/bash

set -e

mkdir -p out && mkdir -p out/unzip

sbatch -c 1 --qos=qos_cpu-t3 -p prepost,archive,cpu_p1 -A mrb@cpu --time=1:00:00 --job-name=unzip --hint=nomultithread --output=out/unzip/%j.out --error=out/unzip/%j.err --export=tar_file=$WORK/scp_data/CFDL/100.tar.gz ./scripts/jz_unzip.sh








# running=$(squeue -u $UID | wc -l)

# if [ $running -le 2 ]; then
#     # last_out=$(ls -t out/ | grep *.out | head -1)
#     # if [ -f "$T"]; then
#     # 	if grep "all requested files are present and up to date" slurm-*.out > /dev/null; then
#     # 	    echo "Exec terminated"
#     #             exit 0
#     # 	fi
#     # fi

#     mkdir -p out/snakemake
#     sbatch -p prepost -A mrb@cpu --qos="qos_cpu-t4" --time="20:00:00" --output="out/snakemake/run_%j.out" --error="out/snakemake/run_%j.err" ./run_snakemake.sh
# fi


# mkdir -p out/submit
# sbatch --begin=now+600 -p prepost -A mrb@cpu --output="out/submit/submit_%j.out" --error="out/submit/submit_%j.err" ./jz_run_snakemake.sh
