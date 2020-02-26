# %%
# #! python3
# downloadAllenBrainSlice - download brain slices from the Allen Brain Atlas
from function import *
import sys
import argparse


# %%
def main():

    # user argparse to parse input string
    # set up a parser
    parser = argparse.ArgumentParser(
        description="Search experiments and download images from ABA"
    )

    # add arguments for keywords
    parser.add_argument(
        "-k",
        "--keywords",
        metavar="keyword",
        nargs="*",
        help="keywords for the search in ABA",
    )

    # add arguments for output file path
    parser.add_argument(
        "-o",
        "--outfile",
        metavar="outfile",
        nargs="?",
        default="search_result.csv",
        help="Specify the name of output.csv",
    )
    
    # add arguments for reading previous results
    parser.add_argument(
        "-r",
        "--read",
        action='store_true',
        help="Read previous results from a file",
    )

    # add arguments for input file path
    parser.add_argument(
        "-i",
        "--infile",
        metavar="infile",
        nargs="?",
        default="search_result.csv",
        help="Specify the file to read",
    )

    # add arguments for download images
    parser.add_argument(
        "-d",
        "--download",
        action='store_true',
        help="Download images. -k or -r is required for this flag.",
    )
    
    # parse the input string
    args = parser.parse_args()

    try:
        if args.keywords:
            df= search_by_keywords(args.keywords, args.outfile)
        elif args.read:
            df=read_previous_results(args.infile)
        
        if args.download:
            try:
                if not df.empty:
                    download_brain_slice(exp_id, dirname, path)
            except Exception:
                print("-k or -r is required for downloading images. Use --help to see the command use.")
            
    except Exception:
        print("Something went wrong. Use --help to see the command use.")

if __name__ == "__main__":
    main()
