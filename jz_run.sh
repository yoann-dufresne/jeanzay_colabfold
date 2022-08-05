#!/bin/bash

set -e


mkdir -p out

mkdir -p out/prefold
sbatch -c 1 --qos=qos_cpu-t3 -p prepost,archive,cpu_p1 -A mrb@cpu --time=20:00:00 --job-name=prefold --hint=nomultithread --output=out/prefold/%j.out --error=out/prefold/%j.err ./scripts/jz_prefold.sh

mkdir -p out/fold_sched
sbatch -c 1 --qos=qos_cpu-t3 -p prepost,archive,cpu_p1 -A mrb@cpu --time=20:00:00 --job-name=fold_sched --hint=nomultithread --output=out/fold_sched/%j.out --error=out/fold_sched/%j.err ./scripts/jz_fold_scheduler.sh

mkdir -p out/postprocess
sbatch -c 1 --qos=qos_cpu-t3 -p prepost -A mrb@cpu --time=20:00:00 --job-name=postprocess --hint=nomultithread --output=out/postprocess/%j.out --error=out/postprocess/%j.err ./scripts/jz_postfold.sh
