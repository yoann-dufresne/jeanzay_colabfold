from os import listdir, path, mkdir, rmdir, rename, getcwd, chdir, remove
from shutil import rmtree, copyfile
from sys import stderr
from tqdm import tqdm
from multiprocessing import Pool

import argparse
import subprocess


def get_scores(tm_file):
    best_rdrp_score = 0
    best_rdrp = None
    best_xdxp_score = 0
    best_xdxp = None

    with open(tm_file) as fp:
        fp.readline()
        # RdRP
        for _ in range(18):
            _, domain, _, score, _, _, _, _, _, _, _ = fp.readline().strip().split("\t")
            score = float(score)
            if score > best_rdrp_score:
                best_rdrp_score = score
                best_rdrp = domain
        # XdXp
        for _ in range(8):
            _, domain, _, score, _, _, _, _, _, _, _ = fp.readline().strip().split("\t")
            score = float(score)
            if score > best_xdxp_score:
                best_xdxp_score = score
                best_xdxp = domain

    return {"domain":best_rdrp, "score":best_rdrp_score}, {"domain":best_xdxp, "score":best_xdxp_score}


def process_sample(batch_path, sample, args):
    if not path.exists(batch_path):
        return False

    script_dir = path.dirname(path.realpath(__file__))
    current_dir = getcwd()
    chdir(batch_path)

    # Get scores
    rdrp, xdxp = get_scores(path.join(batch_path, f"{sample}.tm"))


    # Ralign process
    if rdrp["score"] >= args.rdrp_threshold:
        # Get the molecule pdb file
        pdb_file = [f for f in listdir(batch_path) if f.startswith(sample) and f.endswith(".pdb")]
        pdb_file = path.join(batch_path, pdb_file[0])
        # Get the rdrp pdb file
        palmdir = path.join(script_dir, "..", "palmfold")
        palmprint_path = path.join(palmdir, 'pol', 'palmprint', f"{rdrp['domain']}.pdb")
        # Realign the protein with the ref
        realign_cmd = f"TMalign -outfmt 1 {pdb_file} {palmprint_path} -o {pdb_file}_tmpalign"
        with open(f"{pdb_file}.tmp", "w") as output:
            subprocess.run(realign_cmd.split(" "), stdout=output)
        # Get the realign
        try:
            rename(f"{pdb_file}_tmpalign.pdb", f"{pdb_file}_realign.pdb")
        except OSError:
            print(f"{pdb_file}_tmpalign.pdb", file=stderr)
            print("Filename too long. Skipping...", file=stderr)
            return False

        for file in listdir(batch_path):
            if f"{pdb_file}_tmpalign" in file:
                remove(file)
        # Get the fastas
        subprocess.run(['python3', path.join(script_dir, "..", "palmfold", "palmgrab.py"), f"{pdb_file}.tmp", f"{pdb_file}.pp.fa", f"{pdb_file}.rc.fa"])
        remove(f"{pdb_file}.tmp")

    # Compress output
    outsample = path.join(batch_path, sample)
    tar_sample = path.join(batch_path, f"{sample}.tar.gz")
    if path.exists(outsample):
        rmtree(outsample)
    mkdir(outsample)
    for file in listdir("."):
        if file.startswith(sample) and not path.isdir(file):
            copyfile(file, path.join(outsample, file))

    subprocess.run(["tar", "-czf", tar_sample, sample])
    chdir(current_dir)
    rename(tar_sample, path.join(args.outdir, f"{sample}.tar.gz"))

    return True


def preprocess_files(directory, max_size=150):
    tm_files = [f for f in listdir(directory) if f.endswith(".tm")]
    
    # Reduce file names rearding the tm file
    corresponding_names = {}
    for tm in tm_files:
        name = tm[:-3]
        if len(name) > max_size + 3:
            corresponding_names[name] = name[:max_size]

    # rewrite files
    for file in listdir(directory):
        for name in corresponding_names:
            # If filename too long
            if file.startswith(name):
                gap_size = len(name) - len(corresponding_names[name])
                # Rename the file omitting the middle of the filename
                new_name = file[:max_size] + file[max_size+gap_size:]
                rename(path.join(directory, file), path.join(directory, new_name))


def recompress(batch, args):
    batch_path = path.join(args.directory, batch)
    workdir = batch_path
    # Uncompress if needed
    compressed = False
    if not path.isdir(batch_path):
        if batch_path.endswith(".tar.gz"):
            compressed = True

            workdir = batch_path[:-7]
            if len(workdir) > 100:
                workdir = workdir[:100]
            if path.exists(workdir):
                rmtree(workdir)
            mkdir(workdir)
            subprocess.run(["tar", "-xzf", batch_path, "-C", args.directory])


        else:
            print(f"unknown format for file {batch_path}. Skipping...", file=stderr)
            return

    # Preprocess the file names to reduce their size
    preprocess_files(workdir)

    # Get the samples from the directory
    processed = True
    for f in listdir(workdir):
        if f.endswith(".tm"):
            processed &= process_sample(path.abspath(workdir), f[:-3], args)

    # Clean the directory
    if compressed and path.exists(workdir):
        rmtree(workdir)
    if processed and not args.keep:
        if path.isdir(batch_path):
            rmtree(batch_path)
        else:
            remove(batch_path)





if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Compress results in one tar.gz per molecule from a set of output runs of collabfold.')
    parser.add_argument('--directory', '-d', type=str, default="./", help='Directory to inspect')
    parser.add_argument('--batch-prefix', '-b', type=str, default="result_", help='Prefix name of the results subdirectories')
    parser.add_argument('--outdir', '-o', type=str, default="result_stats", help='Directory where to put compressed results')
    parser.add_argument('--rdrp-threshold', type=float, default=0, help='Rdrp threshold to realign molecules')
    parser.add_argument('--threads', '-t', type=int, default=1, help='Number of threads to use')
    parser.add_argument('--keep', '-k', action="store_true", default=False, help="Keep the input files after compression")

    args = parser.parse_args()


    # Verify inputs
    if not path.exists(args.directory):
        print(f"Data directory {args.directory} absent", file=stderr)
        exit(1)

    # Create output directory if needed
    if not path.exists(args.outdir):
        mkdir(args.outdir)
    elif not path.isdir(args.outdir):
        print(f"Destination path {args.outdir} is not a directory", file=stderr)
        exit(1)

    # Collect batchs
    batchs = frozenset(f for f in listdir(args.directory) if f.startswith(args.batch_prefix))
    duplicate = frozenset(f for f in batchs if f"{f}.tar.gz" in batchs)
    batchs -= duplicate

    # 
    def recompress_pool(batch):
        return recompress(batch, args)

    # Process each batch independantly
    with Pool(processes=args.threads) as pool:
        for batch in tqdm(pool.imap_unordered(recompress_pool, batchs), total=len(batchs)):
            pass
