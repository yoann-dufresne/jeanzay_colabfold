#!/bin/bash

module load Python/3.8.3 cuda/11.2

snakemake --snakefile=Snakefile_align --unlock
snakemake --snakefile=Snakefile_align --cluster "sbatch -c {threads} --qos=seqbio -p seqbio -A seqbio --job-name={params.job_name} --mem={params.mem} --output=out/{params.job_name}_%j.out --error=out/{params.job_name}_%j.err" --jobs=1200 --restart-times=1 --show-failed-logs


for f in data/*.ready
do
	TAR=${f%.ready*}.tar.gz
	rsync -az $TAR $JZ:/gpfswork/rech/yph/uep61bl/scp_data
	rsync -az $f $JZ:/gpfswork/rech/yph/uep61bl/scp_data
done