from os import rename, listdir, mkdir, path, remove, popen
from math import ceil
from time import sleep
from random import randint
from sys import stderr


libname = "TST2"
# db = "/pasteur/zeus/projets/p02/seqbio/yoann/colabfold_db/"
db = "/pasteur/appa/scratch/rchikhi/colabfold_db/"
mol_per_fold = 2

global_inputs = [str(f) for f in listdir(f"data/{libname}_split/") if f.endswith(".fa")]
global_samples = [f[:f.rfind('.')] for f in global_inputs]



def count_sequences_per_sample():
    counts = {}
    dir_path =  path.join("data", f"{libname}_split")
    for f in [x for x in listdir(dir_path) if x.endswith(".fa")]:
        sample_path = path.join(dir_path, f)
        stream = popen(f"grep '>' {sample_path} | wc -l")
        counts[f[:f.rfind(".")]] = int(stream.read())
    return counts
seq_per_sample = count_sequences_per_sample()


rule all:
    input:
        # expand(f"data/{libname}_split/res_{{sample}}/fold_split/ready.lock", sample=global_samples)
        expand(f"data/{libname}_split/res_{{sample}}/fold_split/folded.lock", sample=global_samples)
        # expand("data/{libname}_split/res_{sample}/fold_split/folded.lock", sample=global_samples)

rule msa:
    input:
        fa = "data/{libname}_split/{sample}.fa"
    output:
        final_a3m = "data/{libname}_split/res_{sample}/final.a3m",
        splited_a3m = "data/{libname}_split/res_{sample}/a3m_split/done.lock"
    params:
        mem = "20G",
        qos = "dedicated"
    threads: 16
    run:
        # Align
        shell(f"colabfold_search {{input.fa}} {db} data/{{wildcards.libname}}_split/res_{{wildcards.sample}}/")
        # Split the multiple msa into multiple files
        print("python3 scripts/split_msas.py {output.final_a3m} data/{wildcards.libname}_split/res_{wildcards.sample}/a3m_split/ && touch {output.splited_a3m}")
        shell("python3 scripts/split_msas.py {output.final_a3m} data/{wildcards.libname}_split/res_{wildcards.sample}/a3m_split/ && touch {output.splited_a3m}")


rule folding_split:
    input:
        "data/{libname}_split/res_{sample}/a3m_split/done.lock"
    output:
        mol_ready = dynamic("data/{libname}_split/res_{sample}/fold_split/split_0/ready.lock")
    run:
        split_num = 0
        num_moved = 0
        a3ms = [f for f in listdir(f"data/{wildcards.libname}_split/res_{wildcards.sample}/a3m_split/") if f.endswith("a3m")]
        for f in a3ms:
            dirname = f"data/{wildcards.libname}_split/res_{wildcards.sample}/fold_split/split_{split_num}/"
            # Create new bucket
            if num_moved == 0 and split_num != 0:
                mkdir(dirname)
            # Move file into the current bucket
            rename(
                f"data/{wildcards.libname}_split/res_{wildcards.sample}/a3m_split/" + f,
                f"data/{wildcards.libname}_split/res_{wildcards.sample}/fold_split/split_{split_num}/{f}"
            )

            # Update the numbers
            num_moved += 1
            if num_moved == mol_per_fold:
                shell(f"touch data/{wildcards.libname}_split/res_{wildcards.sample}/fold_split/split_{split_num}/ready.lock")
                num_moved = 0
                split_num += 1
        if num_moved != 0:
            shell(f"touch data/{wildcards.libname}_split/res_{wildcards.sample}/fold_split/split_{split_num}/ready.lock")


rule fold:
    input:
        "data/{libname}_split/res_{sample}/fold_split/split_0/ready.lock",
    output:
        "data/{libname}_split/res_{sample}/fold_split/split_{fold_split}/folded.lock"
    run:
        # Fold proteins
        folding_dir = str(output)[:str(output).rfind('/')]
        shell(f"colabfold_batch --stop-at-score 85 {folding_dir} {folding_dir}")
        shell(f"cd {folding_dir} && rm cite.bibtex config.json *.png *_rank_[2-5]_* && cd -")
        shell("touch {output}")




rule compress_sample:
    input:
        lambda wildcards: expand(f"data/{wildcards.libname}_split/res_{wildcards.sample}/fold_split/split_{{fold_split}}/folded.lock", fold_split=range(ceil(seq_per_sample[wildcards.sample] / mol_per_fold)))
    output:
        "data/{libname}_split/res_{sample}/fold_split/folded.lock"
    run:
        sample_dir = path.join("data", f"{wildcards.libname}_split", f"res_{wildcards.sample}", "fold_split")

        # Compress by molecule

        # Move compressed molecules

        # Compress sample

        # acknowledge
        shell("touch {output}")

