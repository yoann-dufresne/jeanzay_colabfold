from os import path, listdir

import sys
import argparse
import subprocess as sp


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate the scripts needed to run colabfold in parallel on a slurm cluster. The a3m files needs to be splited into subdirectories (One subdirectory by job to run)')
    parser.add_argument('--input-dir', '-i', type=str, default='./', help="The directory where to find the subdirectories per job.")
    parser.add_argument('--subdir-prefix', '-p', type=str, default='split_', help="Prefix used for the subdirectories to process.")
    parser.add_argument('--num-gpu', '-g', type=int, default=4, help='Number of GPU tu use in parallel')
    parser.add_argument('--ram', '-r', type=int, default=16, help='Number of RAM Go for each job')
    parser.add_argument('--num-cores', '-c', type=int, default=4, help='Number of cores to use per job')
    parser.add_argument('--max-mol-per-job', '-m', type=int, default=10, help='Maximum number of molecule to fold using the same job')
    parser.add_argument('--outdir', '-o', type=str, default="./", help='Directory where the scripts will be generated.')

    args = parser.parse_args()

    # Extract the directory where the scripts are
    script_directory = path.realpath(__file__)
    script_directory = script_directory[:script_directory.rfind('/')]

    # Step 1 - Split new files in subdir
    command = f"python3 {path.join(script_directory, 'split_job.py')} --directory {args.input_dir} --split-num 3 --subdir-prefix {args.subdir_prefix}"
    print(">", command)
    sp.run(command.split(" "), stdin=sys.stdin, stderr=sys.stderr)

    # Step 2 - Check status of previous runs
    

    # Step 3 - Generate slum files

