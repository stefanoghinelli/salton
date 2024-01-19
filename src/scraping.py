import requests
import sys
import os
import re
from lxml import html

URL = 'https://core.ac.uk/search?q=language%3A%22en%22+AND+fieldsOfStudy%3A%22computer+science%22&page='
HEADERS = {'User-Agent': 'Mozilla/5.0'}

def get_content(url):
    try:
        with requests.get(url, headers=HEADERS, stream=True) as response:
            response.raise_for_status()
            return html.fromstring(response.content)
    except requests.RequestException as e:
        print(f"Error from {url}: {e}", file=sys.stderr)
        return None

def fetch_data(pages, pdf_folder="./data/pdf_downloads", txt_folder="./data/txt"):
    for i in range(pages):
        tree = get_content(URL + str(i + 1))
        card_containers = tree.xpath("//div[contains(@class, 'card-container-11P0y')]")

        for container in card_containers:
            pdf_link = container.xpath(".//figure/a[.//span[contains(text(), 'Get PDF')]]/@href")
            if pdf_link:
                pdf_url = pdf_link[0]
                title = container.xpath(".//h3[@itemprop='name']/a/span/text()")
                abstract = container.xpath(".//div[@itemprop='abstract']/span/text()")
                if pdf_url.startswith('http'):
                    sanitized_title = re.sub(r'[\\/:"*?<>|]+', '', title[0])
                    try:
                        response = requests.get(pdf_url, headers=HEADERS, stream=True)
                        response.raise_for_status()
                        pdf_path = os.path.join(pdf_folder, sanitized_title + '.pdf')
                        with open(pdf_path, 'wb') as f:
                            f.write(response.content)
                        print(f"Downloaded: {pdf_path}")
                        try:
                            abstract_path = os.path.join(txt_folder, sanitized_title + ".txt")
                            with open(abstract_path, "w") as file:
                                if abstract:
                                    file.write(abstract[0])
                                    print(f"Abstract saved to: {abstract_path}")
                                else:
                                    file.write("*** Abstract not present ***")
                                    print(f"Abstract non present but file created to: {abstract_path}")
                        except IOError as e:
                            raise Exception(f"Error writing {abstract_path}: {e}")
                    except requests.HTTPError as e:
                        print(f"Error downloading {pdf_url}: {e}")

if __name__ == '__main__':
    pages_limit = 70
    fetch_data(pages_limit)