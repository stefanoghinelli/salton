import os
import logging
from datetime import datetime
from typing import List, Optional, Dict, Callable
from whoosh.index import create_in, exists_in, open_dir
from whoosh.fields import Schema, TEXT, DATETIME, analysis
from whoosh.qparser import QueryParser
from .config import DATA_DIR, INDEX_DIR

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DocumentLoader:
    def __init__(self, txt_folder: str):
        self.txt_folder = txt_folder
    
    def load_document(self, filename: str) -> Optional[Dict]:
        if filename.endswith('_tokens.txt') or filename.endswith('_url.txt'):
            return None
            
        title = filename[:-4] if filename.endswith('.txt') else filename
        
        abstract_path = os.path.join(self.txt_folder, filename)
        tokens_path = os.path.join(self.txt_folder, f"{title}_tokens.txt")
        url_path = os.path.join(self.txt_folder, f"{title}_url.txt")
        
        if not os.path.exists(tokens_path):
            return None
        
        try:
            abstract = ""
            if os.path.exists(abstract_path):
                with open(abstract_path, 'r', encoding='utf-8') as f:
                    abstract = f.read()
            
            portal_url = ""
            if os.path.exists(url_path):
                with open(url_path, 'r', encoding='utf-8') as f:
                    portal_url = f.read().strip()
            
            with open(tokens_path, 'r', encoding='utf-8') as f:
                content = f.read()
            content = ' '.join(content.split('\n'))
            
            return {
                'title': title,
                'content': content,
                'abstract': abstract,
                'portal_url': portal_url,
                'date': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error loading document {filename}: {str(e)}")
            return None

class WhooshIndexer:
    def __init__(self):
        self.txt_folder = os.path.join(DATA_DIR, "txt")
        self.index_dir = INDEX_DIR
        self.loader = DocumentLoader(self.txt_folder)
        
        self.schema = Schema(
            title=TEXT(stored=True, analyzer=analysis.StemmingAnalyzer(), spelling=True),
            abstract=TEXT(stored=True, analyzer=analysis.StemmingAnalyzer(), spelling=True),
            content=TEXT(stored=True, analyzer=analysis.StemmingAnalyzer(), spelling=True),
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
    
    def index_documents(self, progress_callback: Optional[Callable[[int], None]] = None) -> int:
        files = [f for f in os.listdir(self.txt_folder) if f.endswith('.txt')]
        if not files:
            logger.error("No text files found")
            return 0

        writer = self.index.writer()
        indexed_count = 0
        
        try:
            for i, filename in enumerate(files):
                doc = self.loader.load_document(filename)
                if doc:
                    writer.add_document(**doc)
                    indexed_count += 1
                    logger.debug(f"Indexed: {doc['title']}")
                
                if progress_callback:
                    progress = int((i + 1) / len(files) * 100)
                    progress_callback(progress)
            
            writer.commit()
            logger.info(f"Successfully indexed {indexed_count} documents")
            return indexed_count
            
        except Exception as e:
            logger.error(f"Error during indexing: {str(e)}")
            writer.cancel()
            raise
    
    def search(self, query_string: str, field: str = "content") -> List[Dict]:
        with self.index.searcher() as searcher:
            query = QueryParser(field, self.schema).parse(query_string)
            results = searcher.search(query)
            return [dict(result) for result in results]

def get_index_stats() -> Dict[str, float]:
    try:
        indexer = WhooshIndexer()
        index = indexer.index
        
        doc_count = index.doc_count()
        
        unique_terms = 0
        with index.reader() as reader:
            for field in ['title', 'content', 'abstract']:
                if field in reader.schema:
                    field_terms = set(reader.lexicon(field))
                    unique_terms += len(field_terms)
        
        index_size = sum(
            os.path.getsize(os.path.join(dirpath, f))
            for dirpath, _, filenames in os.walk(indexer.index_dir)
            for f in filenames
        )
        
        return {
            "doc_count": doc_count,
            "unique_terms": unique_terms,
            "index_size_mb": index_size / (1024 * 1024)
        }
        
    except Exception as e:
        logger.error(f"Error getting index statistics: {str(e)}")
        return {"doc_count": 0, "unique_terms": 0, "index_size_mb": 0.0}

def build_index(progress_callback: Optional[Callable[[int], None]] = None) -> None:
    try:
        indexer = WhooshIndexer()
        num_indexed = indexer.index_documents(progress_callback=progress_callback)
        logger.info(f"Indexing completed: {num_indexed} documents")
    except Exception as e:
        logger.error(f"Indexing failed: {str(e)}")
        raise

if __name__ == '__main__':
    build_index()