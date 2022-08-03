#generates the pdb files list, keeping the realigned file if it exists
# assumes:
#  find ./GMGCL/ > GMGCL.list.txt && sort GMGCL.list.txt > a && mv a GMGCL.list.txt


from collections import defaultdict
d = defaultdict(list)
for line in open("GMGCL.list.txt"):
    line = line.strip()
    if line.startswith('./'):
        line = line[2:]
    if len(line) == 0: continue
    identifier = line.split('_')[0].split('.')[0]
    d[identifier] += [line]

for identifier in d:
    model_file=None
    realign_file=None
    for elt in d[identifier]:
        if elt.endswith('pdb'):
            if "_model_" in elt and "realign" not in elt:
                model_file=elt
            if "realign" in elt:
                realign_file=elt
    if realign_file is not None:
        print(realign_file)
    else:
        print(model_file)
