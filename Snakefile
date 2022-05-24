from os import rename, listdir, mkdir, path, remove, popen
from math import ceil
from time import sleep
from random import randint
from sys import stderr


cluster = "jean_zay"
# cluster = "pasteur"


# Variables for exec
libname = "TST2"
mol_per_fold = 2

db = "/dev/null"
if cluster == "jean_zay":
    db = "$SCRATCH/ColabFold/"
elif cluster == "pasteur":
    db = "/pasteur/appa/scratch/rchikhi/colabfold_db/"

global_inputs = [str(f) for f in listdir(f"data/{libname}_split/") if f.endswith(".fa")]
global_samples = [f[:f.rfind('.')] for f in global_inputs]


# --- Soft versions ---
python = None
cuda = "cuda/11.2"
if cluster == "pasteur":
    python = "Python/3.8.3"
elif cluster == "jean_zay":
    python = "python/3.9.12"

#mrb@v100, yph@v100, mrb@cpu, yph@cpu,

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
        expand(f"data/{libname}_split/res_{{sample}}/{libname}-{{sample}}.tar.gz", sample=global_samples)
    params:
        time = "2:00:00",
        job_name="output_Serratus",
        #mem = "20G",
	cpus = "1",
        options = "",
	qos = "qos_cpu-t3",
        partition = "prepost",
        account = "mrb@cpu"
    threads: 1
    

rule msa:
    input:
        fa = "data/{libname}_split/{sample}.fa"
    output:
        splited_a3m = "data/{libname}_split/res_{sample}/aligned.lock"
    params:
        time = "20:00:00",
        job_name="alignment_Serratus",
        #mem = "250G",
	cpus = "5",
        options = "",
        qos = "qos_cpu-t4",
	partition = "prepost",
        account = "mrb@cpu"
    resources:
        io = 1
    threads: 16
    run:
        # Align
        shell(f"module load {python} && colabfold_search {{input.fa}} {db} data/{{wildcards.libname}}_split/res_{{wildcards.sample}}/ && touch {{output.splited_a3m}}")


rule folding_split:
    input:
        "data/{libname}_split/res_{sample}/aligned.lock"
    output:
        mol_ready = dynamic("data/{libname}_split/res_{sample}/fold_split/split_0/ready.lock")
    priority: 8
    params:
        time = "12:00:00",
        job_name="splitdata_Serratus",
        #mem = "20G",
	cpus = "1",
        options = "",
	partition = "prepost",
        qos = "qos_cpu-t3",
        account = "mrb@cpu"
    threads: 1
    run:
        split_num = 0
        num_moved = 0
        fold_dir = f"data/{wildcards.libname}_split/res_{wildcards.sample}/fold_split"
        if not path.exists(fold_dir):
            mkdir(fold_dir)

        a3ms = [f for f in listdir(f"data/{wildcards.libname}_split/res_{wildcards.sample}") if f.endswith("a3m")]
        for f in a3ms:
            dirname = path.join(fold_dir, f"split_{split_num}/")
            # Create new bucket
            if num_moved == 0 and split_num != 0:
                mkdir(dirname)
            # Move file into the current bucket
            rename(
                f"data/{wildcards.libname}_split/res_{wildcards.sample}/" + f,
                path.join(dirname, f)
            )

            # Update the numbers
            num_moved += 1
            if num_moved == mol_per_fold:
                if split_num != 0:
                    shell(f"touch {path.join(dirname, 'ready.lock')}")
                num_moved = 0
                split_num += 1
        if num_moved != 0:
            shell(f"touch data/{wildcards.libname}_split/res_{wildcards.sample}/fold_split/split_{split_num}/ready.lock")
        if not path.exists(path.join(fold_dir, "split_0", "ready.lock")):
            shell(f"touch {path.join(fold_dir, 'split_0', 'ready.lock')}")


rule fold:
    input:
        "data/{libname}_split/res_{sample}/fold_split/split_0/ready.lock",
    output:
        "data/{libname}_split/res_{sample}/fold_split/split_{fold_split}/folded.lock"
    priority: 9
    params:
        time = f"{min(20, mol_per_fold)}:00:00",
        job_name="folding_Serratus",
        #mem = "20G",
	cpus = "10",
        options = "--gres=gpu:1",
	partition = "gpu_p13",
        qos = "qos_gpu-t3",
        account = "mrb@v100"
    resources:
        gpu = 1
    threads: 1
    run:
        # Fold proteins
        folding_dir = str(output)[:str(output).rfind('/')]
        shell(f"module load {python} {cuda} && colabfold_batch --stop-at-score 85 {folding_dir} {folding_dir}")
        shell(f"cd {folding_dir} && rm -f cite.bibtex config.json *.png *_rank_[2-5]_* *_error_* *.done.txt && cd -")
        shell("touch {output}")




rule compress_sample:
    input:
        lambda wildcards: expand(f"data/{wildcards.libname}_split/res_{wildcards.sample}/fold_split/split_{{fold_split}}/folded.lock", fold_split=range(ceil(seq_per_sample[wildcards.sample] / mol_per_fold)))
    output:
        "data/{libname}_split/res_{sample}/{libname}-{sample}.tar.gz"
    priority: 10
    params:
        time = "20:00:00",
        job_name="compress_Serratus",
        #mem = "50G",
	cpus = "1",
        options = "--ntasks=1 --cpus-per-task=1 --hint=nomultithread",
	partition = "prepost",
        qos = "qos_cpu-t3",
        account = "mrb@cpu"
    threads: 1
    run:
        sample_dir = path.join("data", f"{wildcards.libname}_split", f"res_{wildcards.sample}", "fold_split")
        sample_compress_dir = path.join("data", f"{wildcards.libname}_split", f"res_{wildcards.sample}", "molecules")
        if not path.exists(sample_compress_dir):
            mkdir(sample_compress_dir)

        for split_dir in [f for f in listdir(sample_dir) if path.isdir(path.join(sample_dir, f))]:
            split_dir = path.join(sample_dir, split_dir)
            # Realign molecules
            shell(f"module load {python} && python3 palmfold/palmfold.py -p palmfold/pol/ -t 0 -d {split_dir}")
        
            # Compress by molecule
            for mol_file in [f for f in listdir(split_dir) if f.endswith("a3m")]:
                # Create 1 dir per molecule
                mol_name = mol_file[:mol_file.rfind(".")]
                mol_dir = path.join(split_dir, f"{wildcards.sample}-{mol_name}")
                mkdir(mol_dir)
                # Move usefull files into the corresponding dir
                rename(path.join(split_dir, f"{mol_name}.a3m"), path.join(mol_dir, f"{mol_name}.a3m"))
                rename(path.join(split_dir, f"{mol_name}.tm"), path.join(mol_dir, f"{mol_name}.tm"))
                for file in [f for f in listdir(split_dir) if f.startswith(mol_name) and "_rank_1_" in f]:
                    rename(path.join(split_dir, file), path.join(mol_dir, file))
            # Compress mol dirs
            for mol_dir in [d for d in listdir(split_dir) if path.isdir(path.join(split_dir, d)) and '-' in d]:
                mol_name = mol_dir[mol_dir.rfind('-') + 1:]
                tar_file = f"{wildcards.sample}-{mol_name}.tar.gz"
                shell(f"cd {split_dir} && tar -czf {tar_file} {mol_dir} --remove-files && mv {tar_file} ../../molecules/ && cd -")

        # Compress full sample
        res_dir = path.join("data", f"{wildcards.libname}_split", f"res_{wildcards.sample}")
        tar_file = f"{wildcards.libname}-{wildcards.sample}.tar.gz"
        shell(f"cd {res_dir} && tar -czf {tar_file} molecules --remove-files && cd -")
        shell(f"rm -rf {path.join(res_dir, 'aligned.lock')} {path.join(res_dir, 'fold_split')}")

