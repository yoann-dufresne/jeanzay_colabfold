#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd $SCRIPT_DIR/in
find -name "res*.tar.gz" -size -5000k > $SCRIPT_DIR/unfinished_results.txt

for f in `cat $SCRIPT_DIR/unfinished_results.txt`
do
	n=$(echo $f |cut -d"_" -f2 | cut -d. -f1)
	echo $n
	ln -s ../out/split_$n ./GMGCL_$n
	break
done
