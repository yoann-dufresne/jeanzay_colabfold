from os import path, listdir
from shutil import rmtree

import sys
import argparse
import random
import subprocess as sp
import shutil




def generate_submit(submit_dir, subdir_prefix, status_file):
    # Detect job candidates
    job_idxs = [int(f[len(subdir_prefix):]) for f in listdir(submit_dir) if f.startswith(subdir_prefix)]
    job_idxs = set(job_idxs)

    # Remove finished jobs
    with open(status_file) as sf:
        sf.readline()

        for line in sf:
            run, num_mol, num_done = line.strip().split("\t")
            num_mol = int(num_mol)
            num_done = int(num_done)

            # Check finished
            if num_mol == num_done:
                job_idx = int(run[len(subdir_prefix):])
                job_idxs.remove(job_idx)

    # Group jobs for submition
    job_idxs = list(job_idxs)
    job_idxs.sort()

    print(job_idxs)

    # Write the submition script



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate the scripts needed to run colabfold in parallel on a slurm cluster. The a3m files needs to be splited into subdirectories (One subdirectory by job to run)')
    parser.add_argument('--input-dir', '-i', type=str, default='./', help="The working directory.")
    parser.add_argument('--subdir-prefix', '-p', type=str, default='split_', help="Prefix used for the subdirectories to process.")
    parser.add_argument('--results-prefix', '-r', type=str, default='result_', help="Prefix used for the results subdirectories.")
    parser.add_argument('--num-gpu', '-g', type=int, default=4, help='Number of GPU tu use in parallel')
    parser.add_argument('--ram', type=int, default=16, help='Number of RAM Go for each job')
    parser.add_argument('--num-cores', type=int, default=4, help='Number of cores to use per job')
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
    tmp_stats = path.join(args.input_dir, f"tmp_{random.randrange(2<<20)}")
    command = f"python3 {path.join(script_directory, 'stats_result.py')} --directory {args.input_dir} --inputs-prefix {args.subdir_prefix} --results-prefix {args.results_prefix} --outdir {tmp_stats}"
    print(">", command)
    sp.run(command.split(" "), stdin=sys.stdin, stderr=sys.stderr)    

    # Step 3 - Generate slum files
    generate_submit(args.input_dir, args.subdir_prefix, path.join(tmp_stats, "status.tsv"))
    shutil.copyfile(path.join(script_directory, "job.sh"), path.join(args.input_dir, "job.sh"))

    # Step 4 - Clean dir
    rmtree(tmp_stats)
