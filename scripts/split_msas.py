"""
input:
    The result of all concatenated colabdfold_search a3m files, which contain null-separated msa in them.

    This script splits into one a3m file per msa.

usage:

    lz4 -d ../GMGCL.final.a3m.lz4  | python split_msas.py /dev/stdin out    

"""
import logging
from argparse import ArgumentParser
from pathlib import Path

from tqdm import tqdm

logger = logging.getLogger(__name__)

# from https://stackoverflow.com/questions/9237246/python-how-to-read-file-with-nul-delimited-lines
def fileLineIter(inputFile,
                 inputNewline="\n",
                 outputNewline=None,
                 readSize=819200):
   """Like the normal file iter but you can set what string indicates newline.
   
   The newline string can be arbitrarily long; it need not be restricted to a
   single character. You can also set the read size and control whether or not
   the newline string is left on the end of the iterated lines.  Setting
   newline to '\0' is particularly good for use with an input file created with
   something like "os.popen('find -print0')".
   """
   if outputNewline is None: outputNewline = inputNewline
   partialLine = ''
   while True:
       charsJustRead = inputFile.read(readSize)
       if not charsJustRead: break
       partialLine += charsJustRead
       lines = partialLine.split(inputNewline)
       partialLine = lines.pop()
       for line in lines: yield line + outputNewline
   if partialLine: yield partialLine


def split_msa(input_file, output_folder: Path):
    counter = 0
    corresp = open("identifiers.tsv","w")
    #for msa in tqdm(merged_msa.read_text().split("\0")):
    for msa in fileLineIter(open(input_file),'\0'):
        if not msa.strip():
            continue
        #filename = msa.split("\n", 1)[0][1:].split(" ")[0].replace("/", "_") 
        #filename = str(counter)+"_"+filename[:235] + ".a3m"
        filename = str(counter)+".a3m"
        orig_filename = msa.split('\n', 1)[0][1:]
        corresp.write(f"{counter}\t{orig_filename}\n")
        if counter % 100 == 0:
            print("output path",output_folder.with_name(filename))
        output_folder.joinpath(filename).write_text(msa)
        counter += 1
    corresp.close()


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

    parser = ArgumentParser(
        description="Take an a3m database from the colabdb search and turn it into a folder of a3m files"
    )
    parser.add_argument(
        "input_file",
        help="The final.a3m file, may also be stdin",
    )
    parser.add_argument("output_folder", help="Will contain all the a3m files")
    args = parser.parse_args()
    output_folder = Path(args.output_folder)
    output_folder.mkdir(exist_ok=True)
    print("output folder:",output_folder)

    logger.info("Splitting MSAs")
    split_msa(args.input_file, output_folder)
    logger.info("Done")


if __name__ == "__main__":
    main()
