from os import path, listdir, mkdir
from shutil import rmtree

import sys
import argparse
import random
import subprocess as sp
import shutil




def generate_submit(submit_dir, subdir_prefix, status_file, submit_template, args):
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
            # TODO: Remove molecule done from an unfinished job

    if len(job_idxs) == 0:
        print("No job to be done", file=sys.stderr)
        exit(0)

    job_idxs = list(job_idxs)
    job_idxs.sort()
    # Group jobs for submition
    start_job_idx = job_idxs[0]
    end_job_idx = start_job_idx
    grouped_job = []
    for i, job_idx in enumerate(job_idxs[:-1]):
        # if directly the next
        if job_idxs[i+1] == job_idx +1:
            end_job_idx = job_idxs[i+1]
        # Create new segment
        else:
            grouped_job.append((start_job_idx, end_job_idx))
            start_job_idx = end_job_idx = job_idxs[i+1]
    grouped_job.append((start_job_idx, end_job_idx))
    grouped_job = [str(x[0]) if x[0] == x[1] else f"{x[0]}-{x[1]}" for x in grouped_job]

    # Write the submition script
    logdir = path.join(submit_dir, "logs")
    if not path.exists(logdir): mkdir(logdir)
    slurmfile = path.join(submit_dir, "submit.slurm")
    with open(submit_template) as template, open(slurmfile, "w") as slurm:
        for line in template:
            key = line.strip().split("# ")[-1]
            if key == "RAM": print(f"#SBATCH --mem={args.ram}", file=slurm)
            elif key == "CPU": print(f"#SBATCH --cpus-per-task={args.num_cores}", file=slurm)
            elif key == "TIME":
                print(f"#SBATCH --time={min(100, args.max_mol_per_job)}:00:00", file=slurm)
            elif key == "STDOUT":
                print(f"#SBATCH --output={path.abspath(path.join(logdir, '%a.out'))}", file=slurm)
            elif key == "STDERR":
                print(f"#SBATCH --output={path.abspath(path.join(logdir, '%a.err'))}", file=slurm)
            elif key == "ARRAY":
                print(f"#SBATCH --array={','.join(grouped_job)}%{args.num_gpu}", file=slurm)
            elif key == "WORKDIR": print(f"cd {path.abspath(submit_dir)}", file=slurm)
            elif key == "JOB": print(f"srun sh ./job.sh", file=slurm)
            else:
                print(line.strip(), file=slurm)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate the scripts needed to run colabfold in parallel on a slurm cluster. The a3m files needs to be splited into subdirectories (One subdirectory by job to run)')
    parser.add_argument('--input-dir', '-i', type=str, default='./', help="The working directory.")
    parser.add_argument('--subdir-prefix', '-p', type=str, default='split_', help="Prefix used for the subdirectories to process.")
    parser.add_argument('--results-prefix', '-r', type=str, default='result_', help="Prefix used for the results subdirectories.")
    parser.add_argument('--num-gpu', '-g', type=int, default=4, help='Number of GPU tu use in parallel')
    parser.add_argument('--ram', type=int, default=16, help='Number of RAM Go for each job')
    parser.add_argument('--num-cores', type=int, default=4, help='Number of cores to use per job')
    parser.add_argument('--max-mol-per-job', '-m', type=int, default=10, help='Maximum number of molecule to fold using the same job')

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
    slurm_template = path.join(script_directory, "submit_array_template.sh")
    generate_submit(args.input_dir, args.subdir_prefix, path.join(tmp_stats, "status.tsv"), slurm_template, args)
    shutil.copyfile(path.join(script_directory, "job.sh"), path.join(args.input_dir, "job.sh"))

    # Step 4 - Clean dir
    rmtree(tmp_stats)
