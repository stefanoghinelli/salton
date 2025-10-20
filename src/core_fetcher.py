import requests
import os
import re
import logging
from typing import Optional, List
from dataclasses import dataclass
from lxml import html
from .config import DATA_DIR

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class PaperMetadata:
    """
    Data class to hold paper metadata
    """
    title: str
    abstract: str
    pdf_url: str

class CoreFetcher:
    """
    HTML scraper for core.ac.uk (fallback source)
    """
    def __init__(self):
        self.base_url = 'https://core.ac.uk/search?q=fieldsOfStudy%3A%22computer+science%22&page='
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        }
    
    def fetch_page(self, page_number: int) -> List[PaperMetadata]:
        """
        Scrape a single page from core.ac.uk.
        """
        url = f"{self.base_url}{page_number}"
        try:
            logger.info(f"Fetching page {page_number}: {url}")
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            logger.info(f"Page {page_number} received, parsing...")
            tree = html.fromstring(response.content)
            
            results = []
            for container in tree.xpath("//div[contains(@class, 'card-container-11P0y')]"):
                try:
                    pdf_link = None
                    for pattern in [
                        ".//figure/a[.//span[contains(text(), 'Get PDF')]]/@href",
                        ".//a[contains(@class, 'download-pdf')]/@href",
                        ".//a[contains(@href, '/download/')]/@href"
                    ]:
                        links = container.xpath(pattern)
                        if links:
                            pdf_link = links[0]
                            break
                    
                    if not pdf_link:
                        continue
                    
                    title = container.xpath(".//h3[@itemprop='name']/a/span/text()")
                    abstract = container.xpath(".//div[@itemprop='abstract']/span/text()")
                    
                    if title:
                        results.append(PaperMetadata(
                            title=title[0],
                            abstract=abstract[0] if abstract else "",
                            pdf_url=pdf_link
                        ))
                except Exception as e:
                    logger.error(f"Error extracting metadata: {str(e)}")
                    continue
            
            logger.info(f"Found {len(results)} papers on page {page_number}")
            return results
            
        except Exception as e:
            logger.error(f"Error fetching page {page_number}: {str(e)}")
            return []
    
    def download_document(self, metadata: PaperMetadata) -> Optional[bytes]:
        try:
            logger.info(f"Downloading PDF: {metadata.title[:50]}...")
            logger.info(f"PDF URL: {metadata.pdf_url}")
            response = requests.get(metadata.pdf_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            logger.info(f"PDF downloaded successfully: {len(response.content)} bytes")
            return response.content
        except Exception as e:
            logger.error(f"Error downloading {metadata.title}: {str(e)}")
            return None

def fetch_papers(limit: int = 100) -> None:
    """
    Scrape papers from core.ac.uk
    """
    try:
        fetcher = CoreFetcher()
        pdf_folder = os.path.join(DATA_DIR, "pdf_downloads")
        txt_folder = os.path.join(DATA_DIR, "txt")
        
        os.makedirs(pdf_folder, exist_ok=True)
        os.makedirs(txt_folder, exist_ok=True)
        
        collected_count = 0
        current_page = 1
        
        while collected_count < limit:
            logger.info(f"Trying page {current_page} (collected: {collected_count}/{limit})")
            papers = fetcher.fetch_page(current_page)
            if not papers:
                logger.warning(f"No papers found on page {current_page}, moving to next page")
                current_page += 1
                if current_page > 20:
                    logger.error("Reached maximum page limit (20), stopping")
                    break
                continue
                
            for paper in papers:
                if collected_count >= limit:
                    break
                    
                logger.info(f"Processing paper: {paper.title[:60]}...")
                sanitized_title = re.sub(r'[\\/:"*?<>|]+', '', paper.title)
                pdf_path = os.path.join(pdf_folder, f"{sanitized_title}.pdf")
                
                if os.path.exists(pdf_path):
                    logger.info(f"Skipping existing paper: {paper.title[:50]}...")
                    continue
                
                if content := fetcher.download_document(paper):
                    try:
                        sanitized_title = re.sub(r'[\\/:"*?<>|]+', '', paper.title)
                        pdf_path = os.path.join(pdf_folder, f"{sanitized_title}.pdf")
                        with open(pdf_path, 'wb') as f:
                            f.write(content)
                        
                        abstract_path = os.path.join(txt_folder, f"{sanitized_title}.txt")
                        with open(abstract_path, 'w', encoding='utf-8') as f:
                            f.write(paper.abstract or "*** Abstract not present ***")
                        
                        url_path = os.path.join(txt_folder, f"{sanitized_title}_url.txt")
                        with open(url_path, 'w', encoding='utf-8') as f:
                            f.write(paper.pdf_url)
                        
                        collected_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error saving {paper.title[:50]}: {str(e)}")
                        continue
                else:
                    logger.warning(f"Failed to download: {paper.title[:50]}...")

            current_page += 1
        
        logger.info(f"Successfully collected {collected_count} documents")
        
    except Exception as e:
        logger.error(f"Document collection failed: {str(e)}")
        raise

if __name__ == '__main__':
    fetch_papers(100)
