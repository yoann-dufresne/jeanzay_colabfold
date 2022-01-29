from os import listdir, path, mkdir, rename
from shutil import rmtree
from sys import stderr

import argparse


def split_directory(dirpath, num_files, subdir_prefix="split_", force_del=False):
    """ Split the a3m files from a directory into multiple directories containing num_files
    """
    files = [name for name in listdir(dirpath) if name.endswith('.a3m')]
    total_files = len(files)

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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Split/Unsplit a3m files from a directory')
    parser.add_argument('--directory', '-d', type=str, default="./", help='Directory to inspect')
    parser.add_argument('--split-num', '-n', type=int, default=10, help='Number of file per subdir')
    parser.add_argument('--subdir-prefix', '-p', type=str, default="split_", help='Prefix name of the subdirectories to create')
    parser.add_argument('--force', '-f', default=False, action='store_true', help='Force subdirectories deletion if exist. Will force deletation of all the subtrees.')

    args = parser.parse_args()

    split_directory("/home/yoann/Softwares/ColabFold/dir_001", 10, force_del=args.force)
