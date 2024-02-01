from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.service import Service
from urllib3.exceptions import MaxRetryError, NewConnectionError
import time


from typing import Iterable
from  langchain.schema import Document
import json
from datetime import datetime
import os
import time
import numpy as np


from langchain.document_loaders import WebBaseLoader

# import pandas as pd
# from tqdm import tqdm
from trafilatura.sitemaps import sitemap_search
from trafilatura import fetch_url, extract, extract_metadata
import trafilatura

trafilatura.settings.VERIFY_SSL_CERTIFICATES = False

def get_urls_from_sitemap(resource_url: str, name: str) -> list:
    """
    Recovers the sitemap through Trafilatura
    """
    urls = sitemap_search(resource_url)
    print("found ", len(urls), " urls")

        # Write the filtered links to a text file
    links_path = f'data/{name}_filtered_links.txt'
    with open(links_path, 'w') as file:
        for link in urls:
            file.write(link + '\n')

    return urls


def give_new_links(resource_url: str, name: str) -> list:
    """
    Recovers the sitemap through Trafilatura
    """
    urls = sitemap_search(resource_url)
    print("found ", len(urls), " urls")

    return urls


# # Set up virtual display
# display = Display(visible=0, size=(800, 600))
# display.start()


def load_driver():

    # Specify the path to the ChromeDriver executable
    chrome_driver_path = 'chromedriver-win64/chromedriver.exe'

    # Create a new instance of the Chrome driver with the virtual display
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')

    # # Provide the path to the ChromeDriver executable
    # driver = webdriver.Chrome(executable_path=chrome_driver_path, options=options)

    service = Service(executable_path=chrome_driver_path, )
    driver = webdriver.Chrome(service=service, options=options, )

    return service , driver

def scrape_links(url, retry_attempts=2, retry_delay=2):
    for attempt in range(retry_attempts):
        try:
            driver = load_driver()
            # Perform the web scraping
            driver[1].get(url)
            all_links = driver[1].find_elements(By.TAG_NAME, 'a')
            base_urls = [link.get_attribute('href') for link in all_links]

            # Close the browser
            driver[1].quit()

            # Return the scraped links
            return base_urls

        except (WebDriverException, MaxRetryError, NewConnectionError) as e:
            print(f"Error while scraping links from {url}: {e}")
            
            # If it's the last attempt, return an empty list
            if attempt == retry_attempts - 1:
                return []

            # If not the last attempt, wait and retry
            print(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)


def scrape_page(url,name):

    data = WebBaseLoader(url)
    data.requests_kwargs = {"verify": False}
    data = data.load()
    json_path = f'data/{name}_data.json'

    if os.path.exists(json_path):
        old_data = load_docs_from_jsonl(json_path)
        for doc in old_data:
            if doc not in data:
                data.append(doc)
        save_docs_to_jsonl(data,json_path)

        # Write the filtered links to a text file
        links_path = f'data/{name}_filtered_links.txt'
        with open(links_path, 'a') as file:
            file.write(url + '\n')

    else:
        save_docs_to_jsonl(data,json_path)

        # Write the filtered links to a text file
        links_path = f'data/{name}_filtered_links.txt'
        with open(links_path, 'a') as file:
            file.write(url + '\n')


    return data




def filter_valid_links(base_url, links):
    filtered_links = []

    for link in links:
        # Check if the link is empty or None
        if not link:
            continue

        # Check if the link starts with the base URL
        if not link.startswith(base_url):
            continue

        # Check if the link contains an image or document file extension
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
        document_extensions = {'.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx'}

        if any(link.lower().endswith(ext) for ext in image_extensions.union(document_extensions)):
            continue

        # If all checks pass, add the link to the filtered list
        filtered_links.append(link)

    return filtered_links


def save_docs_to_jsonl(array:Iterable[Document], file_path:str)->None:
    with open(file_path, 'w') as jsonl_file:
        for doc in array:
            jsonl_file.write(doc.json() + '\n')

def load_docs_from_jsonl(file_path)->Iterable[Document]:
    array = []
    with open(file_path, 'r') as jsonl_file:
        for line in jsonl_file:
            data = json.loads(line)
            obj = Document(**data)
            array.append(obj)
    return array




def working(url,name):
    
    print("scraping links started")
    initial_links = list(set(scrape_links(url)))
    final_links = []
    final_links.append(initial_links)

    print(initial_links)

    initial_links = filter_valid_links(url, initial_links)
    print(initial_links)

    print("scraping links done now loop started for sub links scraping")
    for link in initial_links:
        found_urls = list(set(scrape_links(link)))
        final_links.append(found_urls)
    

    # Convert to 1D list using nested list comprehension
    list_1d = [item for sublist in final_links for item in sublist]

    l = list(set(list_1d))

    print("filtering valid links now")

    # Filter the links
    filtered_links = filter_valid_links(url, l)

    # # Print the result
    # print("Filtered Links:", filtered_links)


    # Write the filtered links to a text file
    links_path = f'data/{name}_filtered_links.txt'
    with open(links_path, 'w') as file:
        for link in filtered_links:
            file.write(link + '\n')

    return filtered_links


def create_data(name):
    file_path = f"data/{name}_filtered_links.txt"
    
    with open(file_path, 'r') as file:
    # Read the entire content of the file as a string
        file_contents_str = file.read()

    # Split the string into a list and remove empty strings
    urls = list(filter(None, file_contents_str.split()))
    print(len(urls))

    documents = []
    for url in urls:
        try:
          document = WebBaseLoader(url)
          document.requests_kwargs = {"verify": False}
          time.sleep(1)
          d = document.load()
          documents.append(d)
        except Exception as e:
          print(f"Skipping {url} due to too an exception.",e)

    flattened_list = np.array(documents).flatten()

    docs = list(flattened_list)

    json_path = f'data/{name}_data.json'

    save_docs_to_jsonl(docs,json_path)


    print("done")   


def create_new_data(name):

    file_path = f"data/{name}_new_links.txt"
    
    with open(file_path, 'r') as file:
    # Read the entire content of the file as a string
        file_contents_str = file.read()

    # Split the string into a list and remove empty strings
    urls = list(filter(None, file_contents_str.split()))
    print(urls)

    documents = []
    for url in urls:
        try:
          document = WebBaseLoader(url)
          document.requests_kwargs = {"verify": False}
          time.sleep(1)
          d = document.load()
          documents.append(d)
        except Exception as e:
          print(f"Skipping {url} due to too an exception.",e)

    flattened_list = np.array(documents).flatten()

    docs = list(flattened_list)

    json_path = f'data/{name}_data.json'

    if os.path.exists(json_path):
        old_data = load_docs_from_jsonl(json_path)
        for doc in old_data:
            if doc not in docs:
                docs.append(doc)
        save_docs_to_jsonl(docs,json_path)

    else:
        save_docs_to_jsonl(docs,json_path)


    print("done")   




def for_new_data(url,name):

    # working(url,name)
    get_urls_from_sitemap(url,name)
    create_data(name)


def for_updating_data(url,name):

    new_urls = give_new_links(url,name)

    print("new url: ",len(new_urls))

    file_path = f"data/{name}_filtered_links.txt"
    
    with open(file_path, 'r') as file:
    # Read the entire content of the file as a string
        file_contents_str = file.read()

    # Split the string into a list and remove empty strings
    old_urls = list(filter(None, file_contents_str.split()))

    print("old url: ",len(old_urls))

    set1 = set(old_urls)
    set2 = set(new_urls)

    urls = list(set2 - set1)
    print("all urls: ",len(urls))
    print(urls)

    with open(file_path, 'a') as file:
        for link in urls:
            file.write(link + '\n')
        
    new_urls_path = f"data/{name}_new_links.txt"

    with open(new_urls_path, 'w') as file:
        for link in urls:
            file.write(link + '\n')


    create_new_data(name)

    
