#!/bin/bash

set -e

module load python/3.9.12 cuda/11.2
python3 scripts/jz_fold_scheduler.py

# srun --pty --ntasks=1 --cpus-per-task=4 --hint=nomultithread --time=20:00:00 --qos=qos_cpu-t3 -p prepost,archive,cpu_p1 -A mrb@cpu bash