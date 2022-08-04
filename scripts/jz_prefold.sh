#!/bin/bash

set -e

export https_proxy="http://prodprox.idris.fr:3128"
module load python/3.9.12

python3 scripts/jz_prefold.py
