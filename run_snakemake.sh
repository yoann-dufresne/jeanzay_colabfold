#!/bin/bash

module load Python/3.9.12

snakemake --snakefile=Snakefile --cluster "sbatch -c {threads} --mem {params.mem} --qos={params.qos} -A {params.account} {params.options} --time={params.time} --job-name={params.job_name} --output=out/%a.out --error=out/%a.err" --jobs=5 --max-jobs-per-second=5 --max-status-checks-per-second=0.1 --restart-times=1 --show-failed-logs --resources io=2 --resources gpu=2 --output="out/%a.out" --error="out/%a.err"
