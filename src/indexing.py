import os
import logging
from datetime import datetime
from typing import Optional, Dict
from whoosh.index import create_in, exists_in, open_dir
from whoosh.fields import Schema, TEXT, DATETIME
from .config import DATA_DIR, INDEX_DIR
from .lemmatizer import LemmatizingAnalyzer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Indexer:
    """
    Whoosh indexer using lemmatization
    """
    def __init__(self):
        """
        Initialize indexer with lemmatization-based analysis
        """
        self.txt_folder = os.path.join(DATA_DIR, "txt")
        self.index_dir = INDEX_DIR

        analyzer = LemmatizingAnalyzer(use_pos=False, apply_stemming=True)

        self.schema = Schema(
            title=TEXT(stored=True, analyzer=analyzer, spelling=True),
            abstract=TEXT(stored=True, analyzer=analyzer, spelling=True),
            content=TEXT(stored=True, analyzer=analyzer, spelling=True),
            portal_url=TEXT(stored=True),
            date=DATETIME(stored=True)
        )
        
        self.index = self._create_or_open_index()
    
    def _create_or_open_index(self):
        if not os.path.exists(self.index_dir):
            os.makedirs(self.index_dir)
            return create_in(self.index_dir, self.schema)
        elif exists_in(self.index_dir):
            return open_dir(self.index_dir)
        else:
            return create_in(self.index_dir, self.schema)

    def load_document(self, filename: str) -> Optional[Dict]:
        """
        Load document from text files
        """
        if filename.endswith('_tokens.txt') or filename.endswith('_url.txt'):
            return None

        title = filename[:-4] if filename.endswith('.txt') else filename
        abstract_path = os.path.join(self.txt_folder, filename)
        url_path = os.path.join(self.txt_folder, f"{title}_url.txt")

        if not os.path.exists(abstract_path):
            return None

        try:
            with open(abstract_path, 'r', encoding='utf-8') as f:
                abstract = f.read()

            portal_url = ""
            if os.path.exists(url_path):
                with open(url_path, 'r', encoding='utf-8') as f:
                    portal_url = f.read().strip()

            return {
                'title': title.replace('_', ' '),
                'content': abstract,
                'abstract': abstract,
                'portal_url': portal_url,
                'date': datetime.now()
            }

        except Exception as e:
            logger.error(f"Error loading document {filename}: {str(e)}")
            return None

    def index_documents(self) -> int:
        """
        Index all documents using lemmatization
        """
        files = [f for f in os.listdir(self.txt_folder) if f.endswith('.txt')]
        if not files:
            logger.error("No text files found")
            return 0

        writer = self.index.writer()
        indexed_count = 0
        
        try:
            for i, filename in enumerate(files):
                doc = self.load_document(filename)
                if doc:
                    writer.add_document(**doc)
                    indexed_count += 1
                    logger.debug(f"Indexed: {doc['title']}")
                
            
            writer.commit()
            logger.info(f"Successfully indexed {indexed_count} documents")
            return indexed_count
            
        except Exception as e:
            logger.error(f"Error during indexing: {str(e)}")
            writer.cancel()
            raise


def build_index() -> None:
    """
    Build search index using lemmatization
    """
    try:
        logger.info("Building index with lemmatization")
        indexer = Indexer()
        num_indexed = indexer.index_documents()
        logger.info(f"Indexing completed: {num_indexed} documents")
    except Exception as e:
        logger.error(f"Indexing failed: {str(e)}")
        raise

if __name__ == '__main__':
    build_index()
