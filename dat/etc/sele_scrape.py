from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import TimeoutException
#from selenium.webdriver.support.expected_conditions import presence_of_element_located
import time
import sys
import bs4 as bs
import pandas as pd
import numpy as np
import json
import re
import requests
from tika import parser
import os

#--------Controls--------
# scrape product info from website? (produces json)
scrape_covestro = False
# download pdfs? (loads json from file and downloads pds for each entry)
download_pdfs = False
#------------------------


# Prompt user to specify the type of product desired
# Note: All product types containing this word will be scraped
product_type = str(input("Enter type of Covestro product: "))
if(product_type == "") :
    product_type = "polyol"

# Just some helper vars
prod_dir = f'../dat/{product_type}'
prod_tds_dir = f'{prod_dir}/tds'
prod_sds_dir = f'{prod_dir}/sds'

# Supplying website and driver locations
URL = 'https://solutions.covestro.com/en/products/?query=:relevance:countries:US'
chrome_driver_path = '../chromedriver'

# If we want to scrape Covestro
if(scrape_covestro) :
    print("Looking for " + product_type)

    # Specify this web browser will be headless and incognito
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--incognito')

    # Pass necessary webdriver args into a Chrome webdriver object
    webdriver = webdriver.Chrome(executable_path=chrome_driver_path, options=chrome_options)

    with webdriver as driver:
        # Set timeout
        wait = WebDriverWait(driver, 200)

        # Fetch page in headless browser
        driver.get(URL)

        # Wait for javascript to render page
        try:
            myElem = WebDriverWait(driver, 200).until(expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "#productTypes .m-filter-multiselect__item-link--main")))
            print("Product types queried!")
        #In case it never loads...
        except TimeoutException:
            print("Loading took too much time!")

        # Capture page source using driver
        product_types_source = driver.page_source

        # Parse HTML (page source) with beautifulsoup
        product_types_soup = bs.BeautifulSoup(product_types_source, 'html.parser')

        # Get product types
        results = product_types_soup.find("ul", {"id": "productTypes"}).findAll('label', class_='a-input-checkbox__label')

        # Construct query URL from relevant product types
        queryURL = URL
        for product in results:
            if product_type in str(product).lower():
                #print(product.contents, end='\n' * 2)
                queryURL += ":productTypes:"
                queryURL += str(product.contents).replace(" ", "%20").removeprefix("['").removesuffix("']")

        # Scrape total # of products
        maxProducts = str(product_types_soup.find("h2", {"class": "a-heading a-heading--style4 o-product-finder__products-count-headline"}).contents).removeprefix("['").removesuffix(" Products']")

        # Include up to maxProducts in query (ensures all results are requested)
        queryURL += "&pageSize=" + maxProducts
        #print(queryURL)

        # Fetch page with relevant constructed query
        driver.get(queryURL)

        # Wait for javascript to render entire page (sds comes last! :?)
        try:
            myElem = WebDriverWait(driver, 200).until(expected_conditions.presence_of_element_located(
                (By.CSS_SELECTOR, ".m-table__row:nth-child(1) .m-table__datasheet-wrapper:nth-child(2) .a-button")))
            print("Products found!")
        # In case it never loads...
        except TimeoutException:
            print("Loading took too much time!")

        # Capture page source (including relevant products)
        product_query_source = driver.page_source

        # close the driver after source is captured
        driver.close()

    # Parse HTML with beautifulsoup
    products_soup = bs.BeautifulSoup(product_query_source, 'html.parser')

    # Get products (table entries)
    product_results = products_soup.findAll("tr", {"class": "m-table__row"})
    #print(product_query_source)

    # Remove table category row
    product_results = product_results[1:]

    # New empty list to add products to
    cleaned_product_list = []

    # Add product details, and tds and sds links to dataframe
    for product in product_results:
        # Find links within this table entry
        datasheets = product.findAll("a", {"data-t-name": "Button"})
        # configure tds link
        tds = f"https://solutions.covestro.com{datasheets[0]['href']}"
        # if there is a sds datasheet to render, configure sds link
        # note: why does one entry not have one? not sure...
        if(len(datasheets) == 2) :
            sds = f"https://solutions.covestro.com{datasheets[1]['href']}"
        #print(tds)
        #print(sds)

        # Format product details
        product_details = product.text.replace("Add to compare", "").removeprefix(" ").replace("Technical DatasheetenenSafety Datasheet", "").replace("Technical DatasheetenesenSafety Datasheet", "").split("\n")
        #print(product_details)

        #Add everything to the list
        product_details.append(tds)
        product_details.append(sds)
        cleaned_product_list.append(product_details)


    print(str(len(product_results)) + " results parsed!")

    # Create a pandas dataframe from results list
    products_df = pd.DataFrame(np.array(cleaned_product_list).reshape(len(cleaned_product_list), 4), columns=["name", "raw_description", "tds", "sds"]) #, "tds", "sds"

    products_df = products_df.sort_values('name').reset_index(drop=True)

    # and add an id column so we can keep track of our products
    products_df['id'] = products_df.index

    #print(products_df)

    # pandas df to json obj
    products_json = products_df.to_json(orient="records")

    # write json obj for user input product query results to a file
    with open(f'../dat/covestro_{product_type}.json', 'w') as json_file:
        json.dump(products_json, json_file)


# If we aren't scraping let's grab the local copy of the specified dataframe
if scrape_covestro == False:
    json_path = f"../dat/covestro_{product_type}.json"
    with open(json_path, 'r') as f:
        data = json.load(f)
    #print(json_path)
    products_df = pd.read_json(data, orient="records")
    products_df = products_df.sort_values('id')


# If we want to download pdfs for products
if download_pdfs:
    # Make necessary directories if they don't exist
    if not os.path.exists(prod_dir):
        os.makedirs(prod_dir)
    if not os.path.exists(prod_tds_dir):
        os.makedirs(prod_tds_dir)
    if not os.path.exists(prod_sds_dir):
        os.makedirs(prod_sds_dir)
    # Write pdfs to appropriate dir where name = id
    for index, sheet in products_df.iterrows():
        print(f"pulling sds and tds for {sheet['id']}, {sheet['name']}")
        tds_pdf = requests.get(sheet['tds'])
        sds_pdf = requests.get(sheet['sds'])
        with open(f"../dat/{product_type}/tds/{sheet['id']}.pdf", 'wb') as f:
            f.write(tds_pdf.content)
        with open(f"../dat/{product_type}/sds/{sheet['id']}.pdf", 'wb') as f:
            f.write(sds_pdf.content)





#--------Parsing description paragraphs-------------------------------------
#---------------------------------------------------------------------------

# A function to remove the largest common phrase between two strings from the first string
# smallest_phrase: smallest size I consider to be a phrase
def remove_phrase(pdf_desc, site_desc, smallest_phrase):
    #print("removing phrase \n")

    # Decrementing i from (len(site_desc)) to 0
    for i in range(len(site_desc), smallest_phrase, -1) :
        # print(site_desc[0:i])
        # If if this substring of site_disc exists within our pdf_desc
        if(site_desc[0:i].replace("-", " ") in pdf_desc) :
            # We found a common phrase, remove it! (and any annoying messy prefixes)
            site_desc_with_colon = site_desc[i:len(site_desc)]
            site_desc = site_desc_with_colon.removeprefix("; ").removeprefix("-").removeprefix(" ")
            #print(f"i: {i}, site_desc: {site_desc}")
            break

    #print(site_desc

    return site_desc

# returns attributes in site_desc (phrases in site_desc not contained within pdf_desc)
def get_attributes(pdf_desc, site_desc, max_components, smallest_phrase) :
    shorter_site_desc = site_desc
    if max_components == 1:
        return ""
    # Remove a char that doesn't render in the website description
    pdf_desc = pdf_desc.replace("™", "")

    # Remove phrases until max_components
    for i in range(0, max_components):
        shorter_site_desc = remove_phrase(pdf_desc.replace("-", " "), shorter_site_desc, smallest_phrase)
        #print("--------------------")
        #print(shorter_site_desc)

    return shorter_site_desc



# Reading in a sample pdf (THIS WILL CHANGE LATER)-------------
index = 82
pdf_path = f'{prod_tds_dir}/{index}.pdf'
with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
    print(products_df)

# parse the sample pdf to a string without egregious white space
raw = parser.from_file(pdf_path)
pdf_desc = raw['content'].strip().replace("\n", " ")
# Read raw_description from dataframe for parsing
site_desc = products_df.iloc[index]['raw_description']
# Read raw_description from dataframe for debugging
prod_name = products_df.iloc[index]['name']
#--------------------------------------------------------------


print("-------")
print(f"initial description of {prod_name} from pdf:\n{pdf_desc}")
print("-------")
print(site_desc)
print(f"initial description of {prod_name} from website:\n{site_desc}")
print("-------")

# We will say max components is number of semicolons (0 indexed so +1)
max_components = site_desc.count(';') + 1
#if max_components == 1:
    #max_components += 1

print(f"max_components: {max_components}")

# And that a description phrase is at least this long
smallest_phrase = 10

# Strip bothersome occasional description (temp)
site_desc_wo_bad_str = site_desc.removeprefix("polyether polyol; ")

# Get string with attributes
parsed_attributes = get_attributes(pdf_desc, site_desc_wo_bad_str, max_components, smallest_phrase)

# Remove attributes from site_desc to get description (and irksome suffixes)
parsed_description = site_desc.removesuffix(parsed_attributes).removesuffix("enen").removesuffix("enesen").removesuffix("; ")

# and irksome suffixes from attributes
parsed_attributes = parsed_attributes.removesuffix("enen").removesuffix("enesen").removesuffix(";").removeprefix(";")

print(f"parsed description for {prod_name} :\n{parsed_description}")
print("-------")
print(f"parsed attributes for {prod_name} :\n{parsed_attributes}")
print("-------")
