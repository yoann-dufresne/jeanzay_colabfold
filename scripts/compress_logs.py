from os import path, listdir, getcwd, chdir, mkdir, rename

from shutil import rmtree, copy
from time import time
from datetime import datetime as dt
import subprocess as sp


def get_sorted_files(dir_path):
    print("analysing logs")
    files = [(path.getctime(path.join(dir_path, f)), f) for f in listdir(dir_path) if (not path.isdir(path.join(dir_path, f))) and (not f.endswith(".tar.gz"))]
    files.sort()

    return files


def filter_files(file_tuples, min_age):
    '''
    Filter a date/file tuple liste to keep only the oldest with at least min_age age.
    Parameters:
        file_tuples: A list of tuples (date of creation (timestamp), file name)
        min_age: Minimum elapsed time since the date of creation to keep the file in the list
    Return:
        A list of file names
    '''
    print("filter log by date")
    current_time = time()
    filtered = [f for t, f in file_tuples if current_time - t >= min_age]
    return filtered


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
    log_path = "out"
    folds_out_path = path.join(log_path, "fold")

    to_compress = get_sorted_files(folds_out_path)
    files = filter_files(to_compress, 3600)
    i = 1
    while len(files) > 50000:
        print("Compression", i)
        compress_files(folds_out_path, files[:50000])
        files = files[50000:]
        i += 1