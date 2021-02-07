from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import TimeoutException
import time
import sys
import bs4 as bs
import pandas as pd
import numpy as np
import json
import requests
import os

#-------------------Options--------------------
# scrape product info from website? (produces json)
scrape_covestro = True
# download pdfs? (loads json from file and downloads pds for each entry)
download_pdfs = True
# Parse most current json product after execution?
display_first_x_entries = 1500
# which json to view
display_first_x_entries_verbose = False
#----------------------------------------------


#----Supplying website and driver locations----
URL = 'https://solutions.covestro.com/en/products/?query=:relevance:countries:US'
chrome_driver_path = '../chromedriver'
#----------------------------------------------

#-Get a product's information by parsing 'product' html and querying its specific information page-
def get_product_information(product, driver):
    # Empty lists to fill with product information
    attributes_list = []
    product_details = []

    # Record product name
    product_name = product.find("a", {"class": "a-link"}).text.lstrip().rstrip()
    print(f"Fetching records for {product_name} from: ")

    # Grab link to product site
    product_info_rel_url = product.findAll("a", {"data-t-name": "Link"})[0]['href']
    product_info_url = f"https://solutions.covestro.com{product_info_rel_url}"
    print(product_info_url)

    # Find and record tds and sds links
    datasheets = product.findAll("a", {"data-t-name": "Button"})
    # configure tds link
    tds = f"https://solutions.covestro.com{datasheets[0]['href']}"
    # if there is a sds datasheet to render, configure sds link
    # note: why does one entry not have one? not sure...
    if (len(datasheets) == 2):
        sds = f"https://solutions.covestro.com{datasheets[1]['href']}"
    else:
        sds = ""
        print(f"No sds found for {product_name}")
    # print(tds)
    # print(sds)

    # Fetch details page with relevant query
    driver.get(product_info_url)

    # Wait for javascript to render entire page (sds comes last! :?)
    try:
        myElem = WebDriverWait(driver, 5).until(expected_conditions.presence_of_element_located(
            (By.CSS_SELECTOR,
             ".m-table:nth-child(3) .m-table__row:nth-child(1) > .m-table__body-cell:nth-child(1)")))
        print("Product description found!")
    # In case there aren't any attributes
    except:
        print("No product attributes found")
        pass
    # except TimeoutException:
    # print("Loading took too much time!")

    # Capture product page source
    product_desc_source = driver.page_source

    # Parse product page HTML with beautifulsoup
    product_desc_soup = bs.BeautifulSoup(product_desc_source, 'html.parser')

    # Grab product description from page
    product_desc = product_desc_soup.find("div", {"class": "a-richtext a-richtext--copy"}).text.lstrip().rstrip()

    # Grab tables on product page
    product_tables = product_desc_soup.findAll("tbody", {"class": "m-table__body"})

    # print(product_tables)

    # Create a list of attributes from tables on product page
    for dirty_table in product_tables:
        entries = dirty_table.findAll("tr", {"class": "m-table__row"})
        for entry in entries:
            cells = entry.findAll("td", {"class": "m-table__body-cell"})
            for cell in cells:
                attributes_list.append(cell.text)

    # Create a pandas dataframe from attributes list
    attributes_df = pd.DataFrame(np.array(attributes_list).reshape(int(len(attributes_list) / 4), 4),
                                 columns=["name", "test_method", "unit", "value"])

    # Add product entry to list of products
    product_details.append(product_name)
    product_details.append(product_desc)
    product_details.append(tds)
    product_details.append(sds)
    product_details.append(product_info_url)
    product_details.append(attributes_df)
    return product_details
#--------------------------------------------------------------------------------------------------


#------parse product details from html table and return pandas df----------------------------------
def get_products_details_from_table(products_page_soup, driver):

    # Get products (table entries)
    products_html = products_page_soup.findAll("tr", {"class": "m-table__row"})

    # Remove table category row
    product_rows = products_html[1:]

    # New empty list to add products to
    cleaned_product_list = []

    # Iterate through product results table
    for product in product_rows:
        # print(product)

        # Get product information by parsing product html and querying specific information page
        product_info_list = get_product_information(product, driver)
        cleaned_product_list.append(product_info_list)

    print(str(len(product_rows)) + " results parsed!")
    return cleaned_product_list
#--------------------------------------------------------------------------------------------------


#------------re scrape Covestro--------------------------------------------------------------------
def re_scrape_covestro(chrome_driver_path, product_type, webdriver) :
    print("Initializing scrape for " + product_type)

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
            print("Product types parsed!")
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

        # Parse HTML with beautifulsoup
        products_soup = bs.BeautifulSoup(product_query_source, 'html.parser')

        #print(product_query_source)

        cleaned_products_list = get_products_details_from_table(products_soup, driver)

        # close the driver after source is captured
        driver.close()

    # Create a pandas dataframe from results list
    products_df = pd.DataFrame(np.array(cleaned_products_list, dtype='object').reshape(len(cleaned_products_list), 6),
                               columns=["name", "description", "tds", "sds", "details_url", "outputs"]) #, "tds", "sds"

    products_df = products_df.sort_values('name').reset_index(drop=True)

    # and add an id column so we can keep track of our products
    products_df['id'] = products_df.index

    return products_df
#--------------------------------------------------------------------------------------------------


# Print out information about deliverable----------------------------------------------------------
def parse_and_print_json(product_type_dir_path, products_df, display_first_x_entries, display_first_x_entries_verbose):
    for i in range(0, display_first_x_entries):
        if i < len(products_df):
            print(f"---------------Entry {i:02d}---------------------------------------------------------------")
            with pd.option_context('display.max_rows', None, 'display.max_columns', None):
                print(f"id: {products_df.iloc[i]['id']}")
                print(f"name: {products_df.iloc[i]['name']}")
                print(f"description: {products_df.iloc[i]['description']}")
                if display_first_x_entries_verbose:
                    print("")
                    print(f"technical datasheet url: {products_df.iloc[i]['tds']}")
                    print(
                        f"technical datasheet local: {product_type_dir_path}/tds/{products_df.iloc[i]['id']}.pdf")
                    print("")
                    print(f"safety datasheet url: {products_df.iloc[i]['sds']}")
                    print(
                        f"safety datasheet local: {product_type_dir_path}/sds/{products_df.iloc[i]['id']}.pdf")
                    print("")
                    print(f"outputs:\n{pd.DataFrame(products_df.iloc[i]['outputs'])}")
                    print(f"details_url: {products_df.iloc[i]['details_url']}")
                else:
                    print(f"outputs:\n{pd.DataFrame(products_df.iloc[i]['outputs'])}")
            print("--------------------------------------------------------------------------------------")
#--------------------------------------------------------------------------------------------------

# If we want to download pdfs for products---------------------------------------------------------
# pdfs will be downloaded to {product_dir}/{tds||sds}
def download_products_pdfs(products_df, product_dir):
    prod_tds_dir = f'{product_dir}/tds'
    prod_sds_dir = f'{product_dir}/sds'
    # Make necessary directories if they don't exist
    if not os.path.exists(product_dir):
        os.makedirs(product_dir)
    if not os.path.exists(prod_tds_dir):
        os.makedirs(prod_tds_dir)
    if not os.path.exists(prod_sds_dir):
        os.makedirs(prod_sds_dir)
    # Write pdfs to appropriate dir where name = id
    for index, sheet in products_df.iterrows():
        print(f"Requesting sds and tds for {sheet['id']}, {sheet['name']}")

        # If the tds exists, download it
        if sheet['tds'] == "":
            print(f"Technical datasheet not available for {sheet['name']}, \nIf manually located, save as: {prod_tds_dir}/{sheet['id']}.pdf")
        else:
            tds_pdf = requests.get(sheet['tds'])
            with open(f"{prod_tds_dir}/{sheet['id']}.pdf", 'wb') as f:
                f.write(tds_pdf.content)
        # If the tds exists, download it
        if sheet['sds'] == "":
            print(f"Safety datasheet not available for {sheet['name']}, \nIf manually located, save as: {prod_sds_dir}/{sheet['id']}.pdf")
        else:
            sds_pdf = requests.get(sheet['sds'])
            with open(f"{prod_sds_dir}/{sheet['id']}.pdf", 'wb') as f:
                f.write(sds_pdf.content)
#--------------------------------------------------------------------------------------------------

#----Save products_df as a json deliverable--------------------------------------------------------
def save_products_df(products_df, json_path, save_deliverable = True):
    # pandas df to json obj
    products_json = products_df.to_json(orient="records")

    print(f"verbose json: {products_json}")

    # write json obj for user input product query results to a file
    with open(json_path, 'w') as json_file:
        json.dump(products_json, json_file)

    # If we want to save a more concise version of the json
    if save_deliverable:
        concise_products_df = products_df[['id', 'name', 'description', 'outputs']]
        # pandas df to json obj
        products_json = concise_products_df.to_json(orient="records")
        print(f"requested json: {products_json}")
        deliverable_path = f"{json_path.removesuffix('.json')}_deliverable.json"
        # write json obj for user input product query results to a file
        with open(deliverable_path, 'w') as json_file:
            json.dump(products_json, json_file)

#--------------------------------------------------------------------------------------------------

#----Read json deliverable back to products_df-----------------------------------------------------
def read_products_df(json_path):
    with open(json_path, 'r') as f:
        data = json.load(f)
    # print(json_path)
    products_df = pd.read_json(data, orient="records")
    # Return sorted products_df
    return products_df.sort_values('id')
#--------------------------------------------------------------------------------------------------

#--Main Method-------------------------------------------------------------------------------------
def main(scrape_covestro, download_pdfs, display_first_x_entries, display_first_x_entries_verbose, webdriver):
    # Prompt user to specify the type of product desired
    # Note: All product types containing this word will be scraped
    print("Full list of product types available at https://solutions.covestro.com/en/products/?query=:relevance:countries:US")
    product_type = str(input("Enter desired Covestro product type (default: polyol)... "))
    if (product_type == ""):
        product_type = "polyol"

    #--------All Path Specifications------------------------------
    # Grab the absolute project base directory path
    abs_proj_dir = f"{os.getcwd().removesuffix('/src')}"
    # Define path to json deliverable based on input product_type
    json_path = f"{abs_proj_dir}/dat/{product_type}/covestro_{product_type}.json"
    # Define path to pdfs for product type
    product_type_dir_path = f'{abs_proj_dir}/dat/{product_type}'
    #-------------------------------------------------------------

    # Scrape covestro for json to update else load in local copy
    if scrape_covestro:
        products_df = re_scrape_covestro(chrome_driver_path, product_type, webdriver)
        save_products_df(products_df, json_path)
    else:
        # If we aren't scraping let's grab the local copy of the specified dataframe
        products_df = read_products_df(json_path)

    # Download sds and tds pdfs to {product_type_dir_path}/{sds && tds} dirs
    if download_pdfs:
        download_products_pdfs(products_df, product_type_dir_path)

    parse_and_print_json(product_type_dir_path, products_df, display_first_x_entries, display_first_x_entries_verbose)
#--------------------------------------------------------------------------------------------------


#Execute program-----------------------------------------------------------------------------------
main(scrape_covestro, download_pdfs, display_first_x_entries, display_first_x_entries_verbose, webdriver)
