from os import listdir, path
from sys import stderr


data_folder = "data"
scp_folder = "/gpfswork/rech/yph/uep61bl/scp_data"


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
            print("split", sample_dir)
            continue

        mol_dir = path.join(fold_dir, f"molecules_{sample}")
        fold_splits = [x for x in listdir(fold_dir) if x.startswith("split_")]

        compress_sample = path.exists(mol_dir)

        for fold_split in fold_splits:
            fold_split_dir = path.join(fold_dir, fold_split)
            folded_lock = path.join(fold_split_dir, "folded.lock")

            # Folding not done yet
            if not path.exists(folded_lock):
                print("fold", fold_split_dir)
            else:
                a3ms = [x[:-4] for x in listdir(fold_split_dir) if x.endswith(".a3m")]
                to_compress = frozenset(x[:x.find("_")] for x in listdir(fold_split_dir) if x.endswith(".pdb"))
                if len(to_compress) > 0:
                    print("compress_mol", fold_split_dir, " ".join(to_compress))
                    compress_sample = False
                for a3m in a3ms:
                    if a3m not in to_compress:
                        print("folding error", fold_split_dir, a3m, file=stderr)
        if compress_sample:
            print("compress_sample", sample_dir)



# =========================================================================
# =========================================================================
#                           To decompress data
# =========================================================================
# =========================================================================

lib_names = [x for x in listdir(scp_folder) if path.isdir(path.join(scp_folder, x))]
for lib_name in lib_names:
    lib_dir = path.join(scp_folder, lib_name)

    for f in listdir(lib_dir):
        if f.endswith(".tar.gz"):
            print("untar", lib_name, f)
