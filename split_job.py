from os import listdir, path, mkdir, rmdir, rename
from shutil import rmtree
from sys import stderr

import argparse


def split_directory(dirpath, num_files, subdir_prefix="split_", force_del=False):
    """ Split the a3m files from a directory into multiple directories containing num_files
    """
    files = [name for name in listdir(dirpath) if name.endswith('.a3m')]
    total_files = len(files)

    if total_files == 0:
        print("No a3m file found", file=stderr)
        exit(1)

    for i in range(0, len(files), num_files):
        print(f"Split status: {1+i//num_files}/{total_files//num_files}")
        subdir_path = path.join(dirpath, f"{subdir_prefix}{str(i//num_files)}")
        # If dir exists
        if path.exists(subdir_path):
            if force_del:
                rmtree(subdir_path)
            else:
                print(f"Subtirectory {subdir_path} already present. Aborted.", file=stderr)
                print(f"To force replacment restart the command with the force flag", file=stderr)
                exit(1)
        
        # Create subdir
        mkdir(subdir_path)
        # Else create dir
        for file in files[i : i + num_files]:
            rename(path.join(dirpath, file), path.join(subdir_path, file))


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
    parser.add_argument('--split-num', '-n', type=int, default=10, help='Number of file per subdir')
    parser.add_argument('--subdir-prefix', '-p', type=str, default="split_", help='Prefix name of the subdirectories to create')
    parser.add_argument('--force', '-f', default=False, action='store_true', help='Force subdirectories deletion if exist. Will force deletation of all the subtrees.')
    parser.add_argument('--revert', '-r', default=False, action='store_true', help='Revert the splitting by moving the a3m files to the main directory and remove subdir.')

    args = parser.parse_args()

    if not args.revert:
        split_directory(args.directory, args.split_num, subdir_prefix=args.subdir_prefix, force_del=args.force)
    else:
        unsplit_directory(args.directory, args.subdir_prefix)
