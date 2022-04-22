

libname = TST
db = "/pasteur/zeus/projets/p02/seqbio/yoann/colabfold_db/"


rule msa:
    inputs:
        fa = "data/{libname}_split/{sample}.fa"
    outputs:

    params:
        mem = "20G",
        qos = "dedicated"
    threads: 16
    script:
        f"colabfold_search {{inputs.fa}} {db} data/{{wildcards.libname}}_split/res"