from os import listdir, rename, path

lib_path = path.join("data", "CFDL_split")

for sample_dir in listdir(lib_path):
    sample_path = path.join(lib_path, sample_dir)
    fold_path = path.join(sample_path, "fold_split")

    if not path.exists(fold_path):
        continue

    for split_dir in listdir(fold_path):
        split_path = path.join(fold_path, split_dir)

        for file in listdir(split_path):
            if "realign.pdb" in file:
                rename(
                    path.join(split_path, file),
                    path.join(split_path, file[:file.find(".pdb")+4])
                )