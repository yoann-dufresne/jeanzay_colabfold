#!/bin/bash

set -e

mkdir -p out && mkdir -p out/unzip

module load python/3.9.12 cuda/11.2

srun -c 1 --qos=qos_cpu-t3 -p prepost,archive,cpu_p1 -A mrb@cpu --time=1:00:00 --job-name=scheduler --hint=nomultithread python3 fold_scheduler.py

