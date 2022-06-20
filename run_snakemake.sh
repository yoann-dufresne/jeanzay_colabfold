#!/bin/bash

module load python/3.9.12 cuda/11.2

snakemake --unlock
snakemake --snakefile=Snakefile --cluster "sbatch -c {threads} --cpus-per-task={params.cpus} --qos={params.qos} -p {params.partition} -A {params.account} {params.options} --time={params.time} --job-name={params.job_name} --output=out/{params.job_name}_%j.out --hint=nomultithread --error=out/{params.job_name}_%j.err" --jobs=1200 --max-jobs-per-second=10 --max-status-checks-per-second=10 --restart-times=1 --show-failed-logs --resources io=20 --resources gpu=1100
