from pyvirtualdisplay import Display
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




def scrape_page(url,name):

    try:
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

    except Exception as e:
        fail_urls_path = f"data/{name}_failed_links.txt"
        with open(fail_urls_path, 'a') as file:
            file.write(url + '\n')

        print(f"Skipping {url} due to too an exception.",e)

        data = "failed to scrape url"


    return data



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
            fail_urls_path = f"data/{name}_failed_links.txt"
            with open(fail_urls_path, 'a') as file:
                file.write(url + '\n')
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
            fail_urls_path = f"data/{name}_failed_links.txt"
            with open(fail_urls_path, 'a') as file:
                file.write(url + '\n')

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

    
