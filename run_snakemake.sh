#!/bin/bash

module load Python/3.8.3

snakemake --snakefile=Snakefile --cluster "sbatch -c {threads} --mem {params.mem} --qos={params.qos} -p {params.qos} {params.gres} --time={params.time} --job-name={params.job_name} --output=out/%a.out --error=out/%a.err" --jobs=5 --max-jobs-per-second=0.1 --max-status-checks-per-second=0.1 --restart-times=1 --show-failed-logs --resources io=4 --resources gpu=2
