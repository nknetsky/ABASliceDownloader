# %%
# #! python3
# downloadAllenBrainSlice - download brain slices from the Allen Brain Atlas
from downloadAllenBrainSlice_function import *
import sys

# %%
path = "/Users/erikliu/Desktop/"

# '-s' indicat search for the experiment using the input name
if "-s" in sys.argv:
    # use the keyword after '-s' for the search
    try:
        global results_df
        results_df = get_info_by_search_gene_name(sys.argv[sys.argv.index("-s") + 1])
        print(results_df)
    except ValueError:
        print("Place an input name after -s.")

if "-p" in sys.argv:
    try:
        path = sys.argv[sys.argv.index("-p") + 1]
    except ValueError:
        print("Place an input name after -p.")

if "-d" in sys.argv:
    exp_id = sys.argv[sys.argv.index("-d") + 1]
    gene_name = get_gene_by_id(results_df, exp_id)
    if "--dir" in sys.argv:
        try:
            dirname = sys.argv[sys.argv.index("--dir") + 1]
        except ValueError:
            print("Place an input name after --dir.")
    else:
        dirname = gene_name

    download_brain_slice(exp_id, dirname, path)
