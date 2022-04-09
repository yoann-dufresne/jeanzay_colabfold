#find ./GMGCL/ > GMGCL.list.txt && sort GMGCL.list.txt > a && mv a GMGCL.list.txt
#python delivery.package.py | tar -cvzf GMGCL.pdbs.tar.gz -T -
find ./GMGCL/ -name "*.json" -o -name "*.tm" -o -name "*.fa" | tar -cvzf GMGCL.aux.tar.gz -T -
