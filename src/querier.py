import re
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from whoosh.qparser import MultifieldParser, OrGroup, AndGroup
from whoosh import scoring, index
from .config import INDEX_DIR

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    title: str
    abstract: str
    score: float
    rank: int
    portal_url: str = ""

class WhooshSearchEngine:
    def __init__(self):
        self.index = index.open_dir(INDEX_DIR)
        self._searcher = None

    @property
    def searcher(self):
        if self._searcher is None:
            self._searcher = self.index.searcher(
                weighting=scoring.BM25F(K1=1.5, B=0.75)
            )
        return self._searcher
    
    def __del__(self):
        if hasattr(self, '_searcher') and self._searcher is not None:
            self._searcher.close()
    
    def search(self, query: str, limit: int = 5) -> List[SearchResult]:
        query = query.lower()

        try:
            query_group = AndGroup if re.search(r'\bAND\b', query, re.IGNORECASE) else OrGroup
            parser = MultifieldParser(
                ["title", "abstract", "content"],
                schema=self.searcher.schema,
                fieldboosts={'title': 3.0, 'abstract': 1.5, 'content': 1.0},
                group=query_group
            )
            whoosh_query = parser.parse(query)

            results = self.searcher.search(whoosh_query, limit=limit * 2)

            return [
                SearchResult(
                    title=r["title"],
                    abstract=r["abstract"],
                    score=r.score,
                    rank=r.rank,
                    portal_url=r.get("portal_url", "")
                )
                for r in results[:limit]
            ]
            
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return []
    
    def suggest_correction(self, query: str) -> Optional[str]:
        try:
            query_group = AndGroup if re.search(r'\bAND\b', query, re.IGNORECASE) else OrGroup
            parser = MultifieldParser(
                ["title", "abstract", "content"],
                schema=self.searcher.schema,
                fieldboosts={'title': 3.0, 'abstract': 1.5, 'content': 1.0},
                group=query_group
            )
            whoosh_query = parser.parse(query.lower())
            corrected = self.searcher.correct_query(whoosh_query, query.lower())

            if corrected.query != whoosh_query:
                logger.info(f"Suggested correction: '{query}' -> '{corrected.string}'")
                return corrected.string

        except Exception as e:
            logger.error(f"Correction suggestion error: {str(e)}")

        return None

def process_query(query: str, limit: int = 10) -> List[Dict]:
    try:
        engine = WhooshSearchEngine()
        results = engine.search(query, limit=limit)
        
        return [
            {
                "title": result.title,
                "abstract": result.abstract,
                "score": result.score,
                "portal_url": result.portal_url
            }
            for result in results
        ]
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return []

if __name__ == '__main__':
    pass