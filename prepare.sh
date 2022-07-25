#!/bin/bash

set -e

rm -rf data/TST_split tmp/*
# mkdir -p data/TST_split tmp/ tmp/TST/
# cp data/CFDL_split/8490.tar.gz tmp/TST/
# python3 scripts/jz_unzip.py tmp/TST/8490.tar.gz

# rm -rf data/CFDL_split/res_3378/fold_split
# cp save.tar.gz data/CFDL_split/res_3378/split_9.tar.gz
# cd data/CFDL_split/res_3378
# mkdir -p fold_split
# mv split_9.tar.gz fold_split/
# cd fold_split
# tar -xzf split_9.tar.gz
# rm split_9.tar.gz split_9/67* split_9/340* split_9/170* split_9/305*
