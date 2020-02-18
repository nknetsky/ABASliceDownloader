from bs4 import BeautifulSoup
from selenium import webdriver
import pandas as pd
import sys

from allensdk.api.queries.image_download_api import ImageDownloadApi
from allensdk.api.queries.svg_api import SvgApi
from allensdk.config.manifest import Manifest

import matplotlib.pyplot as plt
from skimage.io import imread

import logging
import os
from base64 import b64encode

from IPython.display import HTML, display

def get_gene_by_id(results_df,ExperimentID):
    gene_name = results_df["Gene Symbol"][results_df["ExperimentID"] == ExperimentID].iloc[0]
    print("You are requesting for downloading brain lices of " + gene_name + " (" + ExperimentID + ")")
    print('The downloaded brain lices will be placed in the dir "' + gene_name + '".')
    return gene_name

def get_info_by_search_gene_name(gene_name):
    
    driver = webdriver.Chrome()
    url = "https://mouse.brain-map.org/search/show?search_term=" + gene_name
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    # Get the search results as dataframe

    for ii, col in enumerate([1, 2, 3, 6]):
        results = []
        for row in soup.select("div[row]"):
            if col == 1 or col == 2:
                result = row.select("div.c" + str(col))[0].select("a")[0].getText().strip()
            else:
                result = row.select("div.c" + str(col))[0].getText().strip()
            if result == "":
                break
            results.append(result)
        if ii:
            results = pd.Series(results)
            results_df = pd.concat([results_df, results], axis=1)
        else:
            results_df = pd.DataFrame(results)

    header = ["ExperimentID", "Gene Symbol", "Gene Name", "Plane"]
    results_df.columns = header
    
    return results_df

def download_brain_slice(exp_id,dirname,path):
    
    # We will want to look at the images we download in this notebook. Here are a couple of functions that do this:
    def verify_image(file_path, figsize=(18, 22)):
        image = imread(file_path)

        fig, ax = plt.subplots(figsize=figsize)
        ax.imshow(image)


    def verify_svg(file_path, width_scale, height_scale):
        # we're using this function to display scaled svg in the rendered notebook.
        # we suggest that in your own work you use a tool such as inkscape or illustrator to view svg

        with open(file_path, "rb") as svg_file:
            svg = svg_file.read()
        encoded_svg = b64encode(svg)
        decoded_svg = encoded_svg.decode("ascii")

        st = r'<img class="figure" src="data:image/svg+xml;base64,{}" width={}% height={}%></img>'.format(
            decoded_svg, width_scale, height_scale
        )
        display(HTML(st))


    # Finally, we will need an instance of `ImageDownloadApi` and an instance of `SvgApi`:
    image_api = ImageDownloadApi()
    svg_api = SvgApi()

    section_data_set_id = int(exp_id)
    downsample = 0
    
    section_image_directory = path + dirname
    format_str = ".jpg"

    # get the image ids for all of the images in this data set
    section_images = image_api.section_image_query(
        section_data_set_id
    )  # Should be a dicionary of the features of section images
    section_image_ids = [
        si["id"] for si in section_images
    ]  # Take value of 'id' from the dictionary

    print("There are " + str(len(section_image_ids)) + " slices.")

    # You have probably noticed that the AllenSDK has a logger which notifies you of file downloads.
    # Since we are downloading ~300 images, we don't want to see messages for each one.
    # The following line will temporarily disable the download logger.
    logging.getLogger("allensdk.api.api.retrieve_file_over_http").disabled = True

    print("Downloads initiated", end="...")
    sys.stdout.flush()

    for index, section_image_id in enumerate(section_image_ids):
        print(str(index + 1) + "/" + str(len(section_image_ids)), end="...")
        file_name = str(section_image_id) + format_str
        file_path = os.path.join(section_image_directory, file_name)

        Manifest.safe_make_parent_dirs(file_path)

        # Check if the file is already downloaded, which happens if the downloads have been interrupated.
        saved_file_names = os.listdir(section_image_directory)
        if file_name in saved_file_names:
            continue

        image_api.download_section_image(
            section_image_id, file_path=file_path, downsample=downsample
        )

    # re-enable the logger
    logging.getLogger("allensdk.api.api.retrieve_file_over_http").disabled = False
    print("Downloads completed")