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
def search_by_keywords(keywords):
    
    # create a browser
    driver = webdriver.Chrome()

    result = pd.DataFrame()

    for keyword in keywords:

        url = "https://mouse.brain-map.org/search/show?search_term=" + keyword
        driver.get(url)

        # make sure the page is correcly loaded using explict wait
        try:
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "div[row='22']"))
            )
        except:
            print("An exception occurred: an element could not be found.\nThe Internet speed may be too slow.")
            exit()

        # the index of necessary columns in the table
        column_index = [1, 2, 3, 6]

        # use selenium to find the header
        elements = driver.find_elements_by_class_name("slick-column-name")
        header = []
        for element in elements:
            header.append(element.text)
        header = [header[i] for i in column_index]

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
        result = pd.concat([result, table])

    # print the search results
    print(result)

    driver.quit()


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
