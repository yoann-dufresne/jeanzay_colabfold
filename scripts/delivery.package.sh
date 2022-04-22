#find ./GMGCL/ > GMGCL.list.txt && sort GMGCL.list.txt > a && mv a GMGCL.list.txt
#python delivery.package.py | tar -cvzf GMGCL.pdbs.tar.gz -T -
#find ./GMGCL/ -name "*.json" -o -name "*.tm" -o -name "*.fa" > GMGCL.list.aux.txt
cat GMGCL.list.aux.txt | tar -cvf GMGCL.aux.tar -T -
