# %%
# #! python3
# downloadAllenBrainSlice - download brain slices from the Allen Brain Atlas
from function import *
import sys
import argparse

# %%
path = "/Users/erikliu/Desktop/"

# user argparse to parse input string
try:
    # set up a parser
    parser = argparse.ArgumentParser(
        description="Search experiments in ABA using keywords"
    )
    
    # add arguments for keywords
    parser.add_argument(
        "-k",
        "--keywords",
        metavar="keywords",
        nargs="*",
        help="keywords for the search in ABA",
    )
    
    # parse the input string
    args = parser.parse_args()
    search_by_keywords(args.keywords)

except ValueError:
    print("Please see --help for the command use")

# change the following arguments fit to argparse
    
# '-p' followed by a path
# specify the path to store the images
if "-p" in sys.argv:
    try:
        path = sys.argv[sys.argv.index("-p") + 1]
    except ValueError:
        print("Place an input name after -p.")

# '-d' followed by an experiment id
# download the images of the experiment id
if "-d" in sys.argv:
    exp_id = sys.argv[sys.argv.index("-d") + 1]
    gene_name = get_gene_by_id(results_df, exp_id)

    # '-dir' followed by a directory name
    # specify the directory name to store the images
    # if not specified, the gene name of the experiment id is used
    if "--dir" in sys.argv:
        try:
            dirname = sys.argv[sys.argv.index("--dir") + 1]
        except ValueError:
            print("Place an input name after --dir.")
    else:
        dirname = gene_name

    download_brain_slice(exp_id, dirname, path)
