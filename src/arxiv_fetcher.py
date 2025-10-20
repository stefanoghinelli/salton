import requests
import os
import re
import logging
import time
from typing import Optional, List
from dataclasses import dataclass
from .config import DATA_DIR

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class PaperMetadata:
    """
    Data class to hold paper metadata from arXiv
    """
    title: str
    abstract: str
    pdf_url: str
    authors: str = ""

class ArXivFetcher:
    """
    Client for the arXiv API
    """

    def __init__(self, category: str = 'cs.DC'):
        self.base_url = 'http://export.arxiv.org/api/query'
        self.category = category
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        }

    def fetch_papers(self, max_results: int = 100, start: int = 0) -> List[PaperMetadata]:
        """
        Fetch papers from arXiv API
        """
        papers = []

        params = {
            'search_query': f'cat:{self.category}',
            'start': start,
            'max_results': max_results,
            'sortBy': 'submittedDate',
            'sortOrder': 'descending'
        }

        try:
            logger.info(f"Fetching {max_results} papers from arXiv category: {self.category}")
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()

            from xml.etree import ElementTree as ET
            root = ET.fromstring(response.content)

            ns = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }

            entries = root.findall('atom:entry', ns)
            logger.info(f"Found {len(entries)} papers")

            for entry in entries:
                try:
                    title_elem = entry.find('atom:title', ns)
                    if title_elem is not None:
                        title = ' '.join(title_elem.text.strip().split())
                    else:
                        title = "Unknown"

                    abstract_elem = entry.find('atom:summary', ns)
                    if abstract_elem is not None:
                        abstract = ' '.join(abstract_elem.text.strip().split())
                    else:
                        abstract = ""

                    pdf_link = None
                    for link in entry.findall('atom:link', ns):
                        if link.get('title') == 'pdf':
                            pdf_link = link.get('href')
                            break

                    if not pdf_link:
                        continue

                    authors = []
                    for author in entry.findall('atom:author', ns):
                        name_elem = author.find('atom:name', ns)
                        if name_elem is not None:
                            authors.append(name_elem.text)
                    authors_str = ', '.join(authors)

                    papers.append(PaperMetadata(
                        title=title,
                        abstract=abstract,
                        pdf_url=pdf_link,
                        authors=authors_str
                    ))

                except Exception as e:
                    logger.error(f"Error parsing entry: {str(e)}")
                    continue

            logger.info(f"Successfully parsed {len(papers)} papers")
            return papers

        except Exception as e:
            logger.error(f"Error fetching from arXiv: {str(e)}")
            return []

    def download_pdf(self, metadata: PaperMetadata) -> Optional[bytes]:
        """
        Download PDF from arXiv
        """
        try:
            logger.info(f"Downloading: {metadata.title[:60]}...")
            response = requests.get(metadata.pdf_url, headers=self.headers, timeout=60)
            response.raise_for_status()
            logger.info(f"Downloaded successfully: {len(response.content)} bytes")
            return response.content
        except Exception as e:
            logger.error(f"Error downloading {metadata.title[:50]}: {str(e)}")
            return None

def fetch_papers(limit: int = 100, category: str = 'cs.DC') -> None:
    """
    Retrieve papers from the arXiv API
    """
    try:
        fetcher = ArXivFetcher(category=category)
        pdf_folder = os.path.join(DATA_DIR, "pdf_downloads")
        txt_folder = os.path.join(DATA_DIR, "txt")

        os.makedirs(pdf_folder, exist_ok=True)
        os.makedirs(txt_folder, exist_ok=True)

        batch_size = 100
        collected_count = 0
        start = 0

        while collected_count < limit:
            batch_limit = min(batch_size, limit - collected_count)
            logger.info(f"Fetching batch: {start} to {start + batch_limit}")

            papers = fetcher.fetch_papers(max_results=batch_limit, start=start)

            if not papers:
                logger.warning("No more papers available")
                break

            for paper in papers:
                if collected_count >= limit:
                    break

                logger.info(f"Processing: {paper.title[:60]}...")
                sanitized_title = re.sub(r'[\\/:*?"<>|]+', '', paper.title)[:100]
                pdf_path = os.path.join(pdf_folder, f"{sanitized_title}.pdf")

                if os.path.exists(pdf_path):
                    logger.info(f"Skipping existing: {paper.title[:50]}...")
                    continue

                content = fetcher.download_pdf(paper)
                if content:
                    try:
                        with open(pdf_path, 'wb') as f:
                            f.write(content)

                        abstract_path = os.path.join(txt_folder, f"{sanitized_title}.txt")
                        with open(abstract_path, 'w', encoding='utf-8') as f:
                            f.write(paper.abstract or "*** Abstract not available ***")

                        url_path = os.path.join(txt_folder, f"{sanitized_title}_url.txt")
                        with open(url_path, 'w', encoding='utf-8') as f:
                            f.write(paper.pdf_url)

                        collected_count += 1
                        logger.info(f"Collected: {collected_count}/{limit}")

                        time.sleep(3)

                    except Exception as e:
                        logger.error(f"Error saving {paper.title[:50]}: {str(e)}")
                        continue
                else:
                    logger.warning(f"Failed to download: {paper.title[:50]}")

            start += batch_limit

            time.sleep(5)

        logger.info(f"Successfully got {collected_count} papers from arXiv")

    except Exception as e:
        logger.error(f"arXiv fetch failed: {str(e)}")
        raise

if __name__ == '__main__':
    fetch_papers(100, category='cs.IR')
