import requests
from lxml import html
import sys
import os
import re

URL = 'https://core.ac.uk/search?q=language%3A%22en%22+AND+fieldsOfStudy%3A%22computer+science%22&page='

def download(url, filename):
    headers = {
        'User-Agent': 'Mozilla/5.0'}
    print(f"Downloading {filename} ...")

    try:
        with requests.get(url, headers=headers, stream=True) as response:
            response.raise_for_status()
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        return True
    except requests.RequestException as e:
        print(f"Error downloading {url}: {e}", file=sys.stderr)
        return False

def get_content(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        with requests.get(url, headers=headers, stream=True) as response:
            response.raise_for_status()
            return html.fromstring(response.content)
    except requests.RequestException as e:
        print(f"Error from {url}: {e}", file=sys.stderr)
        return None

def fetch_data(pages, pdf_folder="../data/pdf_downloads", txt_folder="../data/txt"):
    for i in range(pages):
        tree = get_content(URL + str(i + 1))
        pdf_links = tree.xpath('//a[contains(@href, ".pdf")]/@href')
        divs_with_pdf = tree.xpath('//div[figure/a[contains(@href, ".pdf")]]')
        links = [str(div.xpath('.//h3[@class="styles-title-1k6Ib"]/a/@href')[0]) for div in divs_with_pdf]

        if len(pdf_links) != len(links):
            raise ValueError("Lists have not the same lenght.")

        for pdf_link, link in zip(pdf_links, links):
            detail_tree = get_content(link)
            pdf_name = detail_tree.xpath('//h1/span/text()')[0]
            pdf_name= re.sub(r'[\\/]', '', pdf_name)
            pdf_path = os.path.join(pdf_folder, pdf_name + ".pdf")
            #print(f"Downloading {pdf_name}...")
            download_success = download(pdf_link, pdf_path)
            if download_success:
                abstract = detail_tree.xpath('//section[@id="abstract"]/span/text()')[0]
                abstract_path = os.path.join(txt_folder, pdf_name + ".txt")
                with open(abstract_path, "w") as file:
                    file.write(abstract)
            else:
                print(f"Error for {pdf_name}")
    
if __name__ == '__main__':
    pages_limit = 50
    fetch_data(pages_limit)