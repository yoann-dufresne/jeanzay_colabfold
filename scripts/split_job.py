from os import listdir, path, mkdir, rmdir, rename
from shutil import rmtree
from sys import stderr
from tqdm import tqdm

import argparse


def mol_sizes(directory, filenames, verbose=False):
    sizes = {}

    for filename in tqdm(filenames):
        filepath = path.join(directory, filename)

        with open(filepath) as file:
            name = None
            seqsize = 0
            for line in file:
                if line.startswith('>'):
                    name = line.strip()[1:]
                elif name is not None:
                    seqsize = len(line.strip())
                    break

            sizes[name] = seqsize

    return sizes



def split_directory(dirpath, num_files, subdir_prefix="split_", length_factor=1.1, verbose=False):
    """ Split the a3m files from a directory into multiple directories containing num_files
    """
    if verbose:
        print("Get the file names")
    files = [name for name in listdir(dirpath) if name.endswith('.a3m')]
    if verbose:
        print(len(files), "files collected")

    # Extract molecule size from a3m files
    if verbose:
        print("Get the molecule sizes")
    sizes = mol_sizes(dirpath, files)
    if verbose:
        print("Sort the files by size")
    files.sort(key=lambda x:sizes[x[:-4]])

    # Check subdir id availability
    subdirs = [d for d in listdir(dirpath) if d.startswith(subdir_prefix)]
    reserved_subdir_idxs = frozenset([int(x[len(subdir_prefix):]) for x in subdirs])

    if verbose:
        print("Subdirectory creations")
    # Split files into subdir
    subdir_idx = 0  # idx of the subdir
    subdir_size = 0 # Number of files in the subdir
    min_prot_size = sizes[files[0][:-4]] if len(sizes) > 0 else 0
    for filename in tqdm(files):
        # print(f"Split status: {1+i//num_files}/{total_files//num_files}")
        prot_name = filename[:-4]
        prot_size = sizes[prot_name]

        # Is the current protein size in the current range ?
        if prot_size > (length_factor * min_prot_size):
            min_prot_size = prot_size
            subdir_size = 0
            subdir_idx += 1
        # Is the current subdir full ?
        if subdir_size == num_files:
            min_prot_size = prot_size
            subdir_size = 0
            subdir_idx += 1
        # Is the subdir idx available ?
        while subdir_idx in reserved_subdir_idxs:
            subdir_idx += 1

        subdir_path = path.join(dirpath, f"{subdir_prefix}{str(subdir_idx)}")

        # Create directory
        if not path.exists(subdir_path):
            # Create subdir
            mkdir(subdir_path)

        # Move the file
        rename(path.join(dirpath, filename), path.join(subdir_path, filename))
        subdir_size += 1


def unsplit_directory(dirpath, subdir_prefix="split_"):
    subdirs = [name for name in listdir(dirpath) if name.startswith(subdir_prefix)]

    for subname in subdirs:
        subdir = path.join(dirpath, subname)
        for file in listdir(subdir):
            rename(path.join(subdir, file), path.join(dirpath, file))
        rmdir(subdir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Split/Unsplit a3m files from a directory')
    parser.add_argument('--directory', '-d', type=str, default="./", help='Directory to inspect')
    parser.add_argument('--split-num', '-n', type=int, default=10, help='Maximum number of file per subdir')
    parser.add_argument('--subdir-prefix', '-p', type=str, default="split_", help='Prefix name of the subdirectories to create')
    parser.add_argument('--revert', '-r', default=False, action='store_true', help='Revert the splitting by moving the a3m files to the main directory and remove subdir.')
    parser.add_argument('--verbose', '-v', default=False, action='store_true', help='Verbose mode.')

    args = parser.parse_args()

    if not args.revert:
        split_directory(args.directory, args.split_num, subdir_prefix=args.subdir_prefix, verbose=args.verbose)
    else:
        unsplit_directory(args.directory, args.subdir_prefix)
