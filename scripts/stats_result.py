from os import listdir, path, mkdir, rmdir, rename
from shutil import rmtree
from sys import stderr
from copy import copy
from tqdm import tqdm

import argparse
import datetime
import subprocess


class Statistics:
    def __init__(self, global_dir_path, in_prefix, res_prefix, res_dir, verbose=False):
        self.global_dir = global_dir_path
        self.in_prefix = in_prefix
        self.res_prefix = res_prefix
        self.res_dir = res_dir
        self.verbose = verbose

        # Is global dir an existing directory ?
        if not path.exists(self.global_dir):
            print(f"{self.global_dir} does not exists", file=stderr)
            exit(1)
        elif not path.isdir(self.global_dir):
            print(f"{self.global_dir} is a file, not a directory", file=stderr)
            exit(1)

        # Analyse in data directories
        self.in_directories = frozenset(int(d[len(in_prefix):]) for d in listdir(self.global_dir) if d.startswith(self.in_prefix))

        # Analyse res data directories
        self.res_directories = frozenset(int(d[len(res_prefix):]) if not d.endswith(".tar.gz") else int(d[len(res_prefix):-7]) for d in listdir(self.global_dir) if d.startswith(self.res_prefix))

        # Generate output directory
        if not path.exists(self.res_dir):
            mkdir(self.res_dir)


    def exec_status(self, subdir_idx):
        """ List all the proteins folded by a subprocess and check if the job is done.
        """
        # Are they input files ?
        inputs = frozenset()
        in_path = path.join(self.global_dir, f"{self.in_prefix}{subdir_idx}")
        if path.exists(in_path):
            inputs = frozenset(file for file in listdir(in_path) if file.endswith(".a3m"))

        # Detect result files
        res_path = path.join(self.global_dir, f"{self.res_prefix}{subdir_idx}")
        results = frozenset(file for file in listdir(res_path) if file.endswith(".a3m"))

        status = {}
        # Register inputs without outputs
        for file in (inputs - results):
            status[file[:-4]] = False

        # Register outputs status
        for file in results:
            status[file[:-4]] = path.exists(path.join(res_path, f"{file[:-4]}.done.txt"))

        return status


    def exec_time_extract(self, subdir_idx):
        """ Extract the time consumed by each model for each molecule of the directory
        """

        # Check the logfile
        log_file = path.join(self.global_dir, f"{self.res_prefix}{subdir_idx}", "log.txt")
        if not path.exists(log_file):
            if verbose:
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
                time_stats[current_prot] = (copy(durations), length)
            # End of model exec, register time
            elif "took" in line:
                _, _, model, _, duration, _, _, _, _, _ = line.split(" ")
                model = int(model[-1:])
                duration = float(duration[:-1])
                durations[model] = duration

        return time_stats


    def scores_extract(self, subdir_idx):
        num_rdrp = 18
        num_xdxp = 8
        scores = {}

        # Get all the tm files
        tm_files = [x for x in listdir(path.join(self.global_dir, f"{self.res_prefix}{subdir_idx}")) if x.endswith(".tm")]
        
        # For each tm file extract the best rdrp score and xdxp score
        for tmf in tm_files:
            tm_path = path.join(self.global_dir, f"{self.res_prefix}{subdir_idx}", tmf)
            with open(tm_path) as tmp:
                # Skip header
                tmp.readline()
                # Read rdrp lines
                best_rdrp_score = 0.0
                mol = None
                for _ in range(num_rdrp):
                    mol, _, _, score, _, _, _, _, _, _, _ = tmp.readline().strip().split("\t")
                    score = float(score)
                    if score > best_rdrp_score:
                        best_rdrp_score = score
                # Read xdxp lines
                best_xdxp_score = 0.0
                for _ in range(num_xdxp):
                    _, _, _, score, _, _, _, _, _, _, _ = tmp.readline().strip().split("\t")
                    score = float(score)
                    if score > best_xdxp_score:
                        best_xdxp_score = score
                scores[mol] = (best_rdrp_score, best_xdxp_score)

        return scores


    def compute_all_stats(self):
        status = {}
        durations = {}

        status_file = path.join(self.res_dir, "status.tsv")
        tsv_file = path.join(self.res_dir, "durations.tsv")
        scores_file = path.join(self.res_dir, "scores.tsv")
        with open(status_file, "w") as sf, open(tsv_file, "w") as fp, open(scores_file, "w") as sp:
            print("run\tnum_prot\tfolded", file=sf)
            print("protein\tlength\texec_duration\tmodel1_duration\tmodel2_duration\tmodel3_duration\tmodel4_duration\tmodel5_duration", file=fp)
            print("max rdrp\tmax xdxp", file=sp)

            # Molecules not folded
            for d in self.in_directories - self.res_directories:
                # Count the numbrer of proteins inside of the durectory
                nump_rots = 0
                for file in listdir(path.join(self.global_dir, f"{self.in_prefix}{d}")):
                    if file.endswith(a3m):
                        num_pots += 1
                print(f"{d}\t{num_pots}\t{0}", file=sf)

            # Res folder without input
            for idx in tqdm(self.res_directories):
                # Untar directory if needed
                clean_needed = self.untar(idx)
                sample_dir = path.join(self.global_dir, f"{self.res_prefix}{idx}")

                # Update status
                dir_status = self.exec_status(idx)
                status.update(dir_status)
                # Write status file
                num_ok = 0
                for s in dir_status.values():
                    num_ok += 1 if s else 0
                print(f"{self.in_prefix}{idx}\t{len(dir_status)}\t{str(num_ok)}", file=sf)

                # update durations
                extracted = self.exec_time_extract(idx)
                durations.update(extracted)
                for protein in extracted:
                    prot_durations, length = extracted[protein]
                    str_durations = '\t'.join(str(x) for x in prot_durations)
                    print(f"{protein}\t{length}\t{str_durations}", file=fp)

                # Get scores
                scores = self.scores_extract(idx)
                for protein in scores:
                    rdrp, xdxp = scores[protein]
                    print(f"{rdrp}\t{xdxp}", file=sp)

                # Clean directory
                if clean_needed:
                    rmtree(sample_dir)

        return status, durations


    def untar(self, idx):
        # Is the directory expanded ?
        dir_path = path.join(self.global_dir, f"{self.res_prefix}{idx}")
        if path.exists(dir_path):
            return False

        tar_path = path.join(self.global_dir, f"{self.res_prefix}{idx}.tar.gz")
        if path.exists(tar_path):
            subprocess.run(["tar", "-xzf", tar_path, "-C", self.global_dir])
            return True

        return False


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

    def plot_scores(self, scores_tsv):
        import pandas as pd
        import matplotlib.pyplot as plt

        df = pd.read_csv(scores_tsv, sep="\t")

        df.plot(kind="scatter", x="max rdrp", y="max xdxp")
        plt.savefig(path.join(self.res_dir, "scores.png"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract statistics from a colab splited directory')
    parser.add_argument('--directory', '-d', type=str, default="./", help='Directory to inspect')
    parser.add_argument('--results-prefix', '-r', type=str, default="result_", help='Prefix name of the results subdirectories')
    parser.add_argument('--inputs-prefix', '-i', type=str, default="split_", help='Prefix name of the input subdirectories used to compute the results')
    parser.add_argument('--outdir', '-o', type=str, default="result_stats", help='Stats output directory')
    parser.add_argument('--plots', '-p', action="store_true", default=False, help='Create the plots')

    args = parser.parse_args()

    stat_obj = Statistics(args.directory, args.inputs_prefix, args.results_prefix, args.outdir)
    status, durations = stat_obj.compute_all_stats()
    if args.plots:
        stat_obj.plot_durations(path.join(stat_obj.res_dir, "durations.tsv"))
        stat_obj.plot_scores(path.join(stat_obj.res_dir, "scores.tsv"))
