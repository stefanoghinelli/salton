import requests
import sys
from lxml import html

OPEN_TEXTBOOK_BASE_URL = 'https://open.umn.edu'
SPRINGER_BASE_URL = 'https://link.springer.com'


def download(url, filename):
    # Opening connection
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/102.0.0.0 Safari/537.36'}
    print("Opening connection ...")
    with requests.get(url, headers=headers, stream=True) as r:
        if r.status_code != 200:
            print("Impossible to download file '{}'\nError Code : {}\nReason : {}\n\n".format(
                url, r.status_code, r.reason), file=sys.stderr)
        else:
            # Storing the file as a pdf
            print("Saving the pdf file  :\n\"{}\" ...".format(filename))
            with open(filename, 'wb') as f:
                try:
                    total_size = int(r.headers['Content-length'])
                    saved_size_pers = 0
                    movers_by = 8192 * 100 / total_size
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            saved_size_pers += movers_by
                            print("\r=>> %.2f%%" % (
                                saved_size_pers if saved_size_pers <= 100 else 100.0), end='')
                    print(end='\n\n')
                except Exception:
                    print("==> Save impossible : {}\\".format(filename))
                    f.flush()
                    r.close()
            r.close()


def get_content(url):
    page = requests.get(url)
    content = html.fromstring(page.content)
    return content


def get_sourceOPB(pages):
    for i in range(0, pages):
        content = get_content(OPEN_TEXTBOOK_BASE_URL + "/opentextbooks/textbooks/new?&page=" + str(i + 1))
        divs = content.xpath('//div[@id="textbook-list"]/div')
        for div in divs:
            div_intern = div.xpath("./div")[1]
            filename = "../documents/open-textbooks/" + div_intern.xpath('./h2/a/text()')[0] + ".pdf"
            url = div_intern.xpath('./h2/a')[0].get('href')
            print("Calling the URL:" + OPEN_TEXTBOOK_BASE_URL + url)
            content = get_content(OPEN_TEXTBOOK_BASE_URL + url)
            anchors = content.xpath('//ul[@id="BookTypes"]/li/a')
            for anchor in anchors:
                extension = anchor.xpath('./text()')[0]
                if extension == "PDF":
                    uri = anchor.get('href')
                    final_pdf_url = OPEN_TEXTBOOK_BASE_URL + uri
                    print("Downloading from URL" + final_pdf_url)
                    download(final_pdf_url, filename)


def get_sourceSPR(pages):
    for i in range(0, pages):
        content = get_content(
            SPRINGER_BASE_URL + "/search/page/" + str(i + 1) + "?facet-content-type=%22Book%22&package=openaccess")
        lis = content.xpath('//ol[@id="results-list"]/li')
        for li in lis:
            div = li.xpath("./div")[1]
            url = div.xpath('./h2/a')[0].get('href')
            name = div.xpath('./h2/a')[0]
            filename = "../documents/springer/" + name.xpath('./text()')[0] + ".pdf"
            print("Calling the URL:" + SPRINGER_BASE_URL + url)
            content = get_content(SPRINGER_BASE_URL + url)
            div = content.xpath('//div[@id="sidebar"]/div')[0]
            # se l'elemento div recuperato in pagina è uguale a 0
            # significa che non è presente il bottone del download PDF
            if len(div) > 0:
                url = div.xpath('./div')[0].xpath('./div')[0].xpath('./a')[0].get('href')
                if url.endswith('.pdf'):
                    print("Downloading from URL" + url)
                    download(url, filename)


get_sourceOPB(1)
get_sourceSPR(1)
