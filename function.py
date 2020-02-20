# %%
from bs4 import BeautifulSoup
from selenium import webdriver
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
def get_info_by_search_gene_name(gene_name):

    driver = webdriver.Chrome()
    url = "https://mouse.brain-map.org/search/show?search_term=" + gene_name
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    # Get the search results as dataframe

    # store the info of a search
    results_df = pd.DataFrame()
    
    # iterate necessary columns
    for ii, col in enumerate([1, 2, 3, 6]):
        
        # store the info of a column
        results = []

        # iterate rows
        for row in soup.select("div[row]"):
            if col == 1 or col == 2:
                result = row.select("div.c" + str(col))[0].select("a")[0].getText().strip()
            else:
                result = row.select("div.c" + str(col))[0].getText().strip()
            if result == "":
                break
                
            # store a result (an item) in the results list
            results.append(result)

        # integrate the results list into a results_df
        results_df = pd.concat([results_df, pd.Series(results)], axis=1)

    # create a list of names of columns
    header = ["ExperimentID", "Gene Symbol", "Gene Name", "Plane"]
    
    # assign the header to the results_df
    results_df.columns = header

    return results_df


# %%
def download_brain_slice(exp_id, dirname, path):

    # create an image download API
    image_api = ImageDownloadApi()

    section_data_set_id = int(exp_id)
    downsample = 0

    section_image_directory = os.path.join(path, dirname)
    format_str = ".jpg"

    # get the image ids for all of the images in this data set
    section_images = image_api.section_image_query(
        section_data_set_id
    )  # Should be a dicionary of the features of section images
    section_image_ids = [
        si["id"] for si in section_images
    ]  # Take value of 'id' from the dictionary

    print(
        "There are " + str(len(section_image_ids)) + " slices.",
        file=sys.stderr,
        flush=True,
    )

    # You have probably noticed that the AllenSDK has a logger which notifies you of file downloads.
    # Since we are downloading ~300 images, we don't want to see messages for each one.
    # The following line will temporarily disable the download logger.
    logging.getLogger("allensdk.api.api.retrieve_file_over_http").disabled = True

    print(
        "Downloads initiated", end="...", file=sys.stderr, flush=True,
    )
    
    # Create a progress bar
    pbar = tqdm(total=len(section_image_ids), desc="Downloading...")

    for index, section_image_id in enumerate(section_image_ids):

        file_name = str(section_image_id) + format_str
        file_path = os.path.join(section_image_directory, file_name)

        Manifest.safe_make_parent_dirs(file_path)

        # Check if the file is already downloaded, which happens if the downloads have been interrupted.
        saved_file_names = os.listdir(section_image_directory)
        if file_name in saved_file_names:
            continue

        image_api.download_section_image(
            section_image_id, file_path=file_path, downsample=downsample
        )
        
        pbar.update()

    pbar.close()
    
    # re-enable the logger
    logging.getLogger("allensdk.api.api.retrieve_file_over_http").disabled = False
    print(
        "Downloads completed.", file=sys.stderr, flush=True,
    )
