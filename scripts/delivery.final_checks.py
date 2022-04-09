# does a check that all the files are indeed there
# assumes that this command was run:
# cd delivery && find > ../delivery.list.txt && sort delivery.list.txt > a && mv a delivery.list.txt

from collections import defaultdict
d = defaultdict(list)
for line in open("delivery.list.txt"):
    line = line.strip()
    if line.startswith('./'):
        line = line[2:]
    if len(line) == 0: continue
    identifier = line.split('_')[0].split('.')[0]
    d[identifier] += [line]

a3m_but_no_model_pdb = []
a3m_but_no_tm = []
for identifier in d:
    has_a3m = False
    has_model_pdb = False
    has_tm = False
    has_realign_pdb = False
    has_pp_fa = False
    has_rc_fa = False
    for elt in d[identifier]:
        if elt.endswith('a3m'):
            has_a3m = True
        if elt.endswith('pdb'):
            if "_model_" in elt and "realign" not in elt:
                has_model_pdb = True
            if "realign" in elt:
                has_realign_pdb = True
        if elt.endswith('pp.fa'):
            has_pp_fa = True
        if elt.endswith('rc.fa'):
            has_rc_fa = True
        if elt.endswith('.tm'):
            has_tm = True

    if has_a3m and not has_model_pdb:
        a3m_but_no_model_pdb += [identifier]

    if has_a3m and not has_tm:
        a3m_but_no_tm += [identifier]

if len(a3m_but_no_model_pdb) > 0:
    print("those identifiers have a3m but no model pdb:")
    print(a3m_but_no_model_pdb)

if len(a3m_but_no_tm) > 0:
    print("those identifiers have a3m but no tm file:")
    #generates a list of prefixes to process by palmfold -f
    print('.,'.join(a3m_but_no_tm)+".,"+'_,'.join(a3m_but_no_tm)+"_")
