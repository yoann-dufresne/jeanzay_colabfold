from os import path, listdir, getcwd, chdir, mkdir, rename

from shutil import rmtree, copy
from time import time
from datetime import datetime as dt
import subprocess as sp


def get_sorted_files(dir_path):
    files = [(path.getctime(path.join(dir_path, f)), f) for f in listdir(dir_path) if not path.isdir(path.join(dir_path, f))]
    files.sort()

    return files


def filter_files(file_tuples, max_files, min_age):
    '''
    Filter a date/file tuple liste to keep only the oldest with at least min_age age.
    Parameters:
        file_tuples: A list of tuples (date of creation (timestamp), file name)
        max_files: Maximum number of files to keep
        min_age: Minimum elapsed time since the date of creation to keep the file in the list
    Return:
        A list of file names
    '''
    current_time = time()
    file_tuples = [f for t, f in file_tuples if current_time - t >= min_age]
    return file_tuples[:max_files]


def compress_files(dir_path, file_list):
    path_saved = getcwd()
    chdir(dir_path)

    first_date = path.getctime(file_list[0])
    last_date = path.getctime(file_list[-1])

    first_date = dt.fromtimestamp(first_date)
    last_date = dt.fromtimestamp(last_date)

    name = f"logs_{first_date.year}-{first_date.month}-{first_date.day},{first_date.hour}.{first_date.minute:02d}_{last_date.year}-{last_date.month}-{last_date.day},{last_date.hour}.{last_date.minute:02d}"
    print(name)
    mkdir(name)

    for file in file_list:
        # copy(file, path.join(name, file))
        rename(file, path.join(name, file))

    print(f"tar -czf {name}.tar.gz {name}")
    sp.run(f"tar -czf {name}.tar.gz {name}".split())
    rmtree(name)

    chdir(path_saved)


if __name__ == "__main__":
    log_path = "/mnt/zeus/seqbio/yoann/serratus_data/CFDL/out"
    folds_out_path = path.join(log_path, "fold")

    files = get_sorted_files(folds_out_path)
    files = filter_files(files, 10, 3600)
    print(files)
    compress_files("scripts", files)