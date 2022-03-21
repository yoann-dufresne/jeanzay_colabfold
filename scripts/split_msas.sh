module load python
#python $WORK/softwares/ColabFold/colabfold/mmseqs/split_msas.py in out/
#python split_msas_nomem.py in out/
lz4 -d ../GMGCL.final.a3m.lz4  | python split_msas_nomem.py /dev/stdin out

