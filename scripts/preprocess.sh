#!/bin/bash



if [ $# -lt 2 ]; then
    echo "command should be: sh preprocess.sh input.fasta output_dir/"
    exit 1
fi


mkdir -p $2
awk '/^>/ {printf("%s%s\t",(N>0?"\n":""),$0);N++;next;} {printf("%s",$0);} END {printf("\n");}' $1 |\
awk -F '\t' '{printf("%d\t%s\n",length($2),$0);}' |\
sort -k1,1n | cut -f 2- | tr "\t" "\n" |
faSplit about /dev/stdin 1500000 $2