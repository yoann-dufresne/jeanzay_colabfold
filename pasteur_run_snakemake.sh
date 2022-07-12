#!/bin/bash

module load Python/3.8.3 cuda/11.2

snakemake --snakefile=Snakefile_align --unlock
snakemake --snakefile=Snakefile_align --debug-dag --cluster "sbatch -c {threads} --qos={params.qos} -p {params.partition} --job-name={params.job_name} --mem={params.mem} --output=out/{params.job_name}_%j.out --error=out/{params.job_name}_%j.err" --jobs=5000 --restart-times=3 --show-failed-logs


# for f in data/*.ready
# do
# 	TAR=${f%.ready*}.tar.gz
# 	rsync -az $TAR $JZ:/gpfswork/rech/yph/uep61bl/scp_data
# 	rsync -az $f $JZ:/gpfswork/rech/yph/uep61bl/scp_data
# done

# /!\ 14089525
