#!/bin/bash
# Process an input multifasta to split it into multiple reasonnable size slices



if [ $# -lt 2 ]; then
    echo "command should be: sh preprocess.sh input.fasta output_dir/"
    exit 1
fi

mkdir -p $2
awk '/^>/ {printf("%s%s\t",(N>0?"\n":""),$0);N++;next;} {printf("%s",$0);} END {printf("\n");}' $1 |\
awk -F '\t' '{printf("%d\t%s\n",length($2),$0);}' |\
sort -k1,1n | cut -f 2- | tr "\t" "\n" |
./scripts/faSplit about /dev/stdin 100000 $2

for var in "00" "01" "02" "03" "04" "05" "06" "07" "08" "09"
do
    if [ -f "${2%/}/$var.fa" ]; then
        echo "mv ${2%/}/$var.fa ${2%/}/${var:1}.fa"
        mv ${2%/}/$var.fa ${2%/}/${var:1}.fa
    fi
done