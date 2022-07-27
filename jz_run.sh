#!/bin/bash

set -e


sbatch -c 1 --qos=qos_cpu-t3 -p prepost,archive,cpu_p1 -A mrb@cpu --time=2:30:00 --job-name=scheduler --hint=nomultithread --output=out/scheduler/%j.out --error=out/scheduler/%j.err ./scripts/jz_fold_scheduler.sh