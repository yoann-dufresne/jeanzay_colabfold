from os import listdir, path, mkdir, rmdir, rename
from shutil import rmtree
from sys import stderr

import argparse
import datetime


class Statistics:
    def __init__(self, global_dir, in_prefix, res_prefix, res_dir):
        self.global_dir = global_dir
        self.in_prefix = in_prefix
        self.res_prefix = res_prefix
        self.res_dir = res_dir

        # Generate output directory
        if not path.exists(self.res_dir):
            mkdir(self.res_dir)


    def check_idx(self, subdir_idx):
        """ Check the presence of subdirectories linked with an exec id
        """
        in_path = path.join(self.global_dir, f"{self.in_prefix}{subdir_idx}")
        res_path = path.join(self.global_dir, f"{self.res_prefix}{subdir_idx}")

        if not path.exists(in_path):
            print(f"Directory {in_path} does not exist", file=stderr)
            return False
        if not path.exists(res_path):
            print(f"Directory {res_path} does not exist", file=stderr)
            return False

        return True


    def exec_status(self, subdir_idx):
        """ List all the proteins folded by a subprocess and check if the job is done.
        """
        if not self.check_idx(subdir_idx):
            return []

        in_path = path.join(self.global_dir, f"{self.in_prefix}{subdir_idx}")
        res_path = path.join(self.global_dir, f"{self.res_prefix}{subdir_idx}")

        status = {}
        inputs = [file for file in listdir(in_path) if file.endswith(".a3m")]
        for file in inputs:
            status[file[:-4]] = path.exists(path.join(res_path, f"{file[:-4]}.done.txt"))

        return status


    def exec_time_extract(self, subdir_idx):
        """ Extract the time consumed by each model for each molecule of the directory
        """
        if not self.check_idx(subdir_idx):
            return []

        # Check the logfile
        log_file = path.join(self.global_dir, f"{self.res_prefix}{subdir_idx}", "log.txt")
        if not path.exists(log_file):
            print(f"Logfile {log_file} is missing", file=stderr)
            return []

        time_stats = {}

        current_prot = None
        durations = [0]*6
        length = 0
        # Read the logfile
        for line in open(log_file):
            # New prot, register start time
            if "Query" in line:
                str_date1, str_date2, _, _, current_prot, _, length = line.split(" ")
                date = f"{str_date1} {str_date2}"
                durations[0] = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S,%f')
                length = int(length[:-2])
            # End of current prot, register total time
            elif "reranking" in line:
                str_date1, str_date2, _, _, _, _ = line.split(" ")
                # Total time compuration
                date = f"{str_date1} {str_date2}"
                date_diff = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S,%f') - durations[0]
                durations[0] = date_diff.total_seconds()
                # Register the stats
                time_stats[current_prot] = (durations, length)
            # End of model exec, register time
            elif "took" in line:
                _, _, model, _, duration, _, _, _, _, _ = line.split(" ")
                model = int(model[-1:])
                duration = float(duration[:-1])
                durations[model] = duration

        return time_stats


    def compute_all_stats(self):
        # Search for all the relevant subdirectories
        subdir_valid_indexes = [int(file.split('_')[-1]) for file in listdir(self.global_dir) if file.startswith(self.in_prefix)]

        status = {}
        durations = {}
        # Compute the stats directory by directory
        for idx in subdir_valid_indexes:
            status.update(stat_obj.exec_status(idx))
            durations.update(stat_obj.exec_time_extract(idx))

        # Write a tsv to analyse durations
        tsv_file = path.join(self.res_dir, "durations.tsv")
        with open(tsv_file, "w") as fp:
            print("protein\tlength\texec_duration\tmodel1_duration\tmodel2_duration\tmodel3_duration\tmodel4_duration\tmodel5_duration", file=fp)
            for protein in durations:
                prot_durations, length = durations[protein]
                str_durations = '\t'.join(str(x) for x in prot_durations)
                print(f"{protein}\t{length}\t{str_durations}", file=fp)
        self.plot_durations(tsv_file)

        return status, durations


    def plot_durations(self, duration_tsv):
        import pandas as pd
        import matplotlib.pyplot as plt

        df = pd.read_csv(duration_tsv, sep="\t")

        df.plot(kind="scatter", x="length", y="model1_duration")
        plt.savefig(path.join(self.res_dir, "model1.png"))
        df.plot(kind="scatter", x="length", y="model2_duration")
        plt.savefig(path.join(self.res_dir, "model2.png"))
        df.plot(kind="scatter", x="length", y="model3_duration")
        plt.savefig(path.join(self.res_dir, "model3.png"))
        df.plot(kind="scatter", x="length", y="model4_duration")
        plt.savefig(path.join(self.res_dir, "model4.png"))
        df.plot(kind="scatter", x="length", y="model5_duration")
        plt.savefig(path.join(self.res_dir, "model5.png"))
        df.plot(kind="scatter", x="length", y="exec_duration")
        plt.savefig(path.join(self.res_dir, "total_exec_time.png"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract statistics from a colab splited directory')
    parser.add_argument('--directory', '-d', type=str, default="./", help='Directory to inspect')
    parser.add_argument('--results-prefix', '-r', type=str, default="result_", help='Prefix name of the results subdirectories')
    parser.add_argument('--inputs-prefix', '-i', type=str, default="split_", help='Prefix name of the input subdirectories used to compute the results')
    parser.add_argument('--outdir', '-o', type=str, default="result_stats", help='Stats output directory')

    args = parser.parse_args()

    stat_obj = Statistics(args.directory, args.inputs_prefix, args.results_prefix, args.outdir)
    status, durations = stat_obj.compute_all_stats()

