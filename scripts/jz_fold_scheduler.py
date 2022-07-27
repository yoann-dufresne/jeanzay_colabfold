from os import listdir, path, getenv
from sys import stderr
import subprocess
import re


data_folder = "data"
scp_folder = "/gpfswork/rech/yph/uep61bl/scp_data"


jobs = {
    "unzip": [],
    "split": [],
    "fold": [],
    "compress_mol": [],
    "compress_sample": []
}

# =========================================================================
# =========================================================================
#                           Already decompressed data
# =========================================================================
# =========================================================================

lib_dirs = [x for x in listdir(data_folder) if x.endswith("_split")]

for lib_dir in lib_dirs:
    lib_name = lib_dir[:-6]
    lib_dir = path.join(data_folder, lib_dir)

    # extract samples
    samples = [x[4:] for x in listdir(lib_dir) if x.startswith("res_")]

    for sample in samples:
        sample_dir = path.join(lib_dir, f"res_{sample}")

        # Fold split directory to decide if we have to split or to fold
        fold_dir = path.join(sample_dir, "fold_split")
        if not path.exists(fold_dir):
            # print("split", sample_dir)
            jobs["split"].append(sample_dir)
            continue

        mol_dir = path.join(fold_dir, f"molecules_{sample}")
        fold_splits = [x for x in listdir(fold_dir) if x.startswith("split_")]

        compress_sample = path.exists(mol_dir)

        for fold_split in fold_splits:
            fold_split_dir = path.join(fold_dir, fold_split)
            folded_lock = path.join(fold_split_dir, "folded.lock")

            # Folding not done yet
            if not path.exists(folded_lock):
                jobs["fold"].append(fold_split_dir)
                # print("fold", fold_split_dir)
            else:
                a3ms = [x[:-4] for x in listdir(fold_split_dir) if x.endswith(".a3m")]
                to_compress = frozenset(x[:x.find("_")] for x in listdir(fold_split_dir) if x.endswith(".pdb"))
                if len(to_compress) > 0:
                    jobs["compress_mol"].append(fold_split_dir)
                    # print("compress_mol", fold_split_dir, " ".join(to_compress))
                    compress_sample = False
                for a3m in a3ms:
                    if a3m not in to_compress:
                        print("folding error", fold_split_dir, a3m, file=stderr)
        if compress_sample:
            jobs["compress_sample"].append(sample_dir)
            # print("compress_sample", sample_dir)



# =========================================================================
# =========================================================================
#                           To decompress data
# =========================================================================
# =========================================================================

if path.exists(scp_folder):
    lib_names = [x for x in listdir(scp_folder) if path.isdir(path.join(scp_folder, x))]
    for lib_name in lib_names:
        lib_dir = path.join(scp_folder, lib_name)

        for f in listdir(lib_dir):
            if f.endswith(".tar.gz"):
                jobs["unzip"].append(path.join(lib_dir, f))
                # print("untar", lib_name, f)


# print(jobs)



# =========================================================================
# =========================================================================
#                           Currently running
# =========================================================================
# =========================================================================

runnings = {
    "unzip": 0,
    "split": 0,
    "fold": 0,
    "compress_mol": 0,
    "compress_sample": 0,
    "other": 0
}

cmd = f"squeue -u ydufresn"
ret = subprocess.run(cmd.split(' '), universal_newlines=True, stdout=subprocess.PIPE)
if ret.returncode != 0:
    print("Error: squeue command finished on non 0 return value", file=stderr)
    print(ret.stderr, file=stderr)
    exit(ret.returncode)

dependancies = 0
for line in ret.stdout.split('\n')[1:]:
    if "Dependency" in line:
        dependancies += 1
        continue
    line = re.sub('\\s+', ' ', line.strip()).split(' ')
    if len(line) < 3:
        continue
    name = line[2]

    if name.startswith("sample"):
        runnings["compress_sample"] += 1
    elif name.startswith("mol"):
        runnings["compress_mol"] += 1
    elif name.startswith("fold"):
        runnings["fold"] += 1
    elif name.startswith("split"):
        runnings["split"] += 1
    elif name.startswith("unzip"):
        runnings["unzip"] += 1
    else:
        runnings["other"] += 1

prefold = runnings["unzip"] * 70 + runnings["split"] * 70 + runnings["fold"]
total = prefold + runnings["compress_mol"] + runnings["compress_sample"] + runnings["other"]

available = 9999 - dependancies - total



# recursive start
if not path.exists("out/scheduler"):
    mkdir("out/scheduler")
cmd = f"sbatch -c 1 --qos=qos_cpu-t3 -p prepost,archive,cpu_p1 -A mrb@cpu --time=2:30:00 --job-name=scheduler --hint=nomultithread --output=out/scheduler/%j.out --error=out/scheduler/%j.err --begin=now+7200 ./jz_run.sh"
ret = subprocess.run(cmd.split(' '))
if ret.returncode != 0:
    print("Error: sbatch command finished on non 0 return value", file=stderr)
    print(ret.stderr, file=stderr)
    exit(ret.returncode)


# New unzips
if not path.exists("out"):
    mkdir("out")
if not path.exists(path.join("out", "unzip")):
    mkdir(path.join("out", "unzip"))

while available > 100 and len(jobs["unzip"]) > 0:
    available -= 70
    file = jobs["unzip"].pop()
    cmd = f"sbatch -c 1 --qos=qos_cpu-t3 -p prepost,archive,cpu_p1 -A mrb@cpu --time=1:00:00 --job-name=unzip --hint=nomultithread --output=out/unzip/%j.out --error=out/unzip/%j.err --export=tar_file={file} ./scripts/jz_unzip.sh"
    print("start",file)
    ret = subprocess.run(cmd.split(' '))
    if ret.returncode != 0:
        print("Error: sbatch command finished on non 0 return value", file=stderr)
        print(ret.stderr, file=stderr)
        exit(ret.returncode)


