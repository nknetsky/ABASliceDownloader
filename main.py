# %%
# #! python3
# downloadAllenBrainSlice - download brain slices from the Allen Brain Atlas
from function import *
import sys

# %%
path = "/Users/erikliu/Desktop/"

# '-s' followed by a keyword
# search for the experiment using the keyword
if "-s" in sys.argv:
    # use the keyword after '-s' for the search
    try:
        global results_df
        keyword = sys.argv[sys.argv.index("-s") + 1]
        results_df = get_info_by_search_gene_name(keyword)
        print("Keyword: " + keyword)
        print(results_df, end="\n")
    except ValueError:
        print("Place an input name after -s.")

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
