# jeanzay_colabfold

Scripts to run colabfold on jean zay supercomputer for multi millions of molecules.

# Installation

- python3 and cuda 11.2 modules have to be loaded
- MMSeq2 (last github version, not last realese) must be installed and present in the path. WARNING: Do not forget the --recursive on cloning operations.
- colabfold must be installed on the system and present in the path
- Install the database for collabfold in a fast access directory
- TMalign C++ version must be present in the path

# Usage

- Add your data in the data directory of the project (a multi-fasta file)
- Use ```preprocess.sh data/myfasta.fa data/output_dir/ ``` to prepare your data. The output_dir must end with "\_split" for the following step.
The process will sort your fasta by sequence length and then split it in managable size fastas.
- Open the snakefile and change the 3 variables libname, db and mol_per_fold (will be a command line later).
libname must be the name of your previous output dir without "\_split".
db is the path to the database downloaded on fast access directory.
mol_per_fold is the number of molecule to fold for each instance of collabfold (we recommand around 20 per batch).
- Start the snakemake using ```./snake_submit.sh```

# Current work

- Example data for the snakemake testing
- More command line friendly deployment process
