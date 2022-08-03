# cd delivery &&  find . -type f -printf '%P\n' > ../GMGCL.folds.list.txt

#checks that we have the required files for each a3m


from collections import defaultdict
d = defaultdict(list)
for line in open("GMGCL.folds.list.txt"):
    line = line.strip()
    ls = line.split('.')
    identifier_str = ls[0].split('_')[0]
    if not identifier_str.isdigit():
        print("bad identifier:",line)
        continue
    identifier = int(identifier_str)
    d[identifier] += [line]

print(d[0])

for identifier in d:
    has_a3m = False
    has_pdb = False
    is_done = False
    nb_json = 0
    for elt in d[identifier]:
        if "done.txt" in elt:
            is_done = True
        if ".pdb" in elt:
            has_pdb = True
        if ".json" in elt:
            nb_json += 1
        if ".a3m" in elt:
            has_a3m = True
    if (not has_a3m) or (not has_pdb) or (not is_done) or (nb_json < 2):
        print("missing elements in",identifier,":",d[identifier])

print("done",len(d),"a3m's processed")
