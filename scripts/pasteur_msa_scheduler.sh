#!/bin/bash

set -e

module load Python/3.8.3 cuda/11.2

python3 scripts/pasteur_msa_scheduler.py
