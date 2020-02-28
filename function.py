# %%
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import pandas as pd
import sys

from allensdk.api.queries.image_download_api import ImageDownloadApi
from allensdk.config.manifest import Manifest

import logging
import os
from tqdm import tqdm


# %%
def get_gene_by_id(results_df, ExperimentID):
    gene_name = results_df["Gene Symbol"][
        results_df["ExperimentID"] == ExperimentID
    ].iloc[0]
    print(
        "You are requesting for downloading brain lices of "
        + gene_name
        + " ("
        + ExperimentID
        + ")",
        file=sys.stderr,
        flush=True,
    )
    print(
        'The downloaded brain lices will be placed in the dir "' + gene_name + '".',
        file=sys.stderr,
        flush=True,
    )
    return gene_name


# %%
def search_by_keywords(keywords, outfile):

    # create a browser
    driver = webdriver.Chrome()

    # create a result DataFrame to store results
    result = pd.DataFrame()
    
    # the index of necessary columns in the table
    column_index = [1, 2, 3, 6]

    for ii, keyword in enumerate(keywords):

        url = "https://mouse.brain-map.org/search/show?search_term=" + keyword
        driver.get(url)

        # make sure the page is correcly loaded using explict wait
        try:
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "slick-column-name"))
            )
        except:
            print(
                "An exception occurred: an element could not be found.\nThe Internet speed may be too slow."
            )
            driver.quit()
            exit()

        # get header at the first loop
#         if ii == 0:
        # use selenium to find the header
        elements = driver.find_elements_by_class_name("slick-column-name")
        header = []
        for element in elements:
            header.append(element.text)
        if len(header) == 8:
            header = [header[i] for i in column_index]
        else:
            raise Exception("Something went wrong when accessing the header.")

        # user selenium to find the search results in the cells of the table
        elements = driver.find_elements_by_tag_name("div[row]")
        rows = []
        for element in elements:
            if element.text:
                rows.append([element.text.split("\n")[i - 1] for i in column_index])

        # If the search result is present, make it a dataframe
        if rows:
            table = pd.DataFrame(rows, columns=header)
            table.insert(0, "Keyword", keyword)
        # If no search result, make an empty dataframe
        else:
            table = pd.DataFrame([keyword], columns=["Keyword"])

        # concatenate the search results of each keyword
        result = pd.concat([result, table], ignore_index=True)

    # print the search results
    print(result)

    driver.quit()

    result.to_csv(outfile)

    return result


# %%
def download_brain_slice(df):

    # create an image download API
    image_api = ImageDownloadApi()
    format_str = ".jpg"

    # You have probably noticed that the AllenSDK has a logger which notifies you of file downloads.
    # Since we are downloading ~300 images, we don't want to see messages for each one.
    # The following line will temporarily disable the download logger.
    logging.getLogger("allensdk.api.api.retrieve_file_over_http").disabled = True

    # get parameters
    path, downsample, indices = ask_parameters_for_downloading(df)

    print(
        "Downloads initiated", end="...", file=sys.stderr, flush=True,
    )

    for index in indices:

        # from indices, get experiment id and gene symbol from df
        exp_id = df["Experiment"][index]

        # set the dirname as the gene symbol
        dirname = df["Gene Symbol"][index]

        plane = df["Plane"][index]
        section_data_set_id = exp_id
        section_image_directory = os.path.join(path, dirname)

        # get the image ids for all of the images in this data set
        section_images = image_api.section_image_query(
            section_data_set_id
        )  # Should be a dicionary of the features of section images
        section_image_ids = [
            si["id"] for si in section_images
        ]  # Take value of 'id' from the dictionary

        # Create a progress bar
        pbar_image = tqdm(total=len(section_image_ids), desc=dirname + " " + plane)

        for section_image_id in section_image_ids:

            file_name = str(section_image_id) + format_str
            file_path = os.path.join(section_image_directory, file_name)

            Manifest.safe_make_parent_dirs(file_path)

            # Check if the file is already downloaded, which happens if the downloads have been interrupted.
            saved_file_names = os.listdir(section_image_directory)
            if file_name in saved_file_names:
                pass
            else:
                image_api.download_section_image(
                    section_image_id, file_path=file_path, downsample=downsample
                )

            pbar_image.update()

        pbar_image.close()

    # re-enable the logger
    logging.getLogger("allensdk.api.api.retrieve_file_over_http").disabled = False
    print(
        "Downloads completed.", file=sys.stderr, flush=True,
    )


# %%
def read_previous_results(infile):
    
    result = pd.read_csv(infile, index_col=0)
    print(result)

    return result


# %%
def customized_settings():

    path = "."
    downsample = 0
    downsample_limit = 7

    # make a prompt for path
    while True:
        print(
            "Enter a path to store brain slices (default: \033[1m[current directory]\033[0;0m)."
        )
        path = input(">")

        # assess the input

        # q
        if path == "q":
            sys.exit("The program has been stopped by the user.")
        # if no input, set default
        elif not path:
            break
        # user input
        else:
            # expanduser, "~" is usable
            path = os.path.expanduser(path)
            # correct path
            if os.path.isdir(path):
                break
            # unvalid input
            else:
                print('Error: the path "' + path + '" is not present.')

    # make a prompt for downsample
    while True:
        print(
            "Downsample number? 0 indicates full size of slices. ([0]-"
            + str(downsample_limit - 1)
            + ") "
        )
        downsample = input(">")

        # assess the input

        # q
        if downsample == "q":
            sys.exit("The program has been stopped by the user.")
        # if no input, set default
        elif not downsample:
            break
        # user input
        else:
            # convert input to integer
            try:
                downsample = int(downsample)
            except ValueError:
                print("Error: the input should be an integer.")
                continue
            # within downsample_limit
            if downsample in range(downsample_limit):
                break
            else:
                print("Error: the input is out of downsample limit.")

    return path, downsample


def ask_parameters_for_downloading(df):

    print(
        "Before downloading brain slices, some parameters are need to be set.\nIf defaults settings are preferable, press \033[1mEnter\033[0;0m key.\nTo stop the program, enter \033[1mq\033[0;0m ."
    )

    # make a prompt for default settings
    while True:
        print("Use default settings? ([y]/n)")
        default = input(">")

        # assess the input

        # q
        if default == "q":
            sys.exit("The program has been stopped by the user.")
        # # if no input or  input y
        elif not default or default == "y":
            path = "."
            downsample = 0
            break
        # n
        elif default == "n":
            path, downsample = customized_settings()
            break
        # unvalid input
        else:
            print("Error: the input should be y or n.")

    # make a prompt for index
    while True:
        print(
            "Enter index of the experiments to be downloaded. A list is allowed. For example, enter \033[1m0\033[0;0m or \033[1m0 1 2\033[0;0m, in which every index should be separated by at least one space (No default)."
        )
        index = input(">")

        # assess the input

        # q
        if index == "q":
            sys.exit("The program has been stopped by the user.")
        # if no input, set default
        elif not index:
            continue
        # user input
        else:
            # separate indices
            index = index.split()
            # convert indices from string to interger
            try:
                index = [int(n) for n in index]
            except ValueError:
                print("Error: the input should be integers.")
                continue
            # remove repeated numbers
            index = list(set(index))
            # sort the input
            index.sort()
            # check if all the numbers in index is within df.index
            if all(n in df.index for n in index):
                break
            else:
                print("Error: the input is out of index.")

    return path, downsample, index
