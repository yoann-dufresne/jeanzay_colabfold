#!/bin/bash

set -e

module load python/3.9.12 cuda/11.2
python3 fold_scheduler.py

