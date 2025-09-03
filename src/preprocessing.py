import os
import logging
import PyPDF2
from nltk import word_tokenize, pos_tag
from nltk.corpus import wordnet, stopwords
from nltk.stem import WordNetLemmatizer
from typing import List, Optional, Callable, Tuple
from .config import DATA_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class TextProcessor:
    def __init__(self):
        self.stops = set(stopwords.words("english"))
        self.lemmatizer = WordNetLemmatizer()
    
    def process_text(self, text: str) -> List[str]:
        tokens = word_tokenize(text)
        return [
            self.lemmatizer.lemmatize(token.lower()) 
            for token in tokens 
            if token.isalpha() and token.lower() not in self.stops
        ]

class WordSenseDisambiguator:
    def __init__(self):
        self._pos_map = {
            "J": wordnet.ADJ,
            "V": wordnet.VERB, 
            "N": wordnet.NOUN,
            "R": wordnet.ADV
        }
    
    def disambiguate(self, terms: List[str]) -> List[Tuple[str, Optional[str]]]:
        tagged_terms = pos_tag(terms)
        results = []
        
        for idx, (term, tag) in enumerate(tagged_terms):
            best_sense = self._find_best_sense(term, tag, tagged_terms, idx)
            results.append((term, best_sense.name() if best_sense else None))
        
        return results
    
    def _find_best_sense(self, term: str, tag: str, tagged_terms: List[Tuple[str, str]], idx: int):
        best_sense = None
        max_score = 0.0
        wordnet_pos = self._pos_map.get(tag[0], wordnet.NOUN)
        
        start = max(0, idx - 5)
        end = min(len(tagged_terms), idx + 6)
        context_terms = [t for t, _ in tagged_terms[start:end] if t != term]
        
        for sense in wordnet.synsets(term, pos=wordnet_pos):
            context_score = self._compute_context_score(sense, context_terms)
            if context_score > max_score:
                best_sense = sense
                max_score = context_score
        
        return best_sense
    
    def _compute_context_score(self, sense, context_terms: List[str]) -> float:
        return sum(
            max(
                (similarity for context_sense in wordnet.synsets(context_term)
                 if (similarity := self._safe_similarity(sense, context_sense)) is not None),
                default=0.0
            )
            for context_term in context_terms
        )
    
    def _safe_similarity(self, sense1, sense2) -> Optional[float]:
        try:
            similarity = sense1.path_similarity(sense2)
            return similarity if similarity is not None else 0.0
        except Exception:
            return None

class PDFProcessor:
    def __init__(self, use_disambiguation: bool = False):
        self.pdf_folder = os.path.join(DATA_DIR, "pdf_downloads")
        self.txt_folder = os.path.join(DATA_DIR, "txt")
        self.text_processor = TextProcessor()
        self.disambiguator = WordSenseDisambiguator() if use_disambiguation else None
        
        os.makedirs(self.txt_folder, exist_ok=True)
    
    def process_all(self, progress_callback: Optional[Callable[[int], None]] = None) -> None:
        files = [f for f in os.listdir(self.pdf_folder) if f.endswith('.pdf')]
        if not files:
            logger.error("No PDF files found")
            return
        
        processed_count = 0
        
        for i, filename in enumerate(files):
            if self._process_single_pdf(filename):
                processed_count += 1
                logger.info(f"Processed {processed_count}/{len(files)}: {filename}")
            
            if progress_callback:
                progress = int((i + 1) / len(files) * 100)
                progress_callback(progress)
        
        logger.info(f"Completed: {processed_count} files processed")
    
    def _process_single_pdf(self, filename: str) -> bool:
        title = os.path.splitext(filename)[0]
        tokens_file = os.path.join(self.txt_folder, f"{title}_tokens.txt")
        
        if os.path.exists(tokens_file):
            logger.info(f"Skipping existing: {filename}")
            return True
        
        try:
            pdf_path = os.path.join(self.pdf_folder, filename)
            text = self._extract_pdf_text(pdf_path)
            tokens = self.text_processor.process_text(text)
            
            if self.disambiguator:
                disambiguated_terms = self.disambiguator.disambiguate(tokens)
                tokens = [term for term, sense in disambiguated_terms]
            
            with open(tokens_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(tokens))
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing {filename}: {e}")
            return False
    
    def _extract_pdf_text(self, filepath: str) -> str:
        try:
            with open(filepath, "rb") as f:
                pdf_reader = PyPDF2.PdfReader(f)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n\n"
                return text
        except (PyPDF2.errors.PdfReadError, EOFError) as e:
            logger.warning(f"Corrupted PDF {filepath}: {str(e)}")
            raise ValueError(f"Corrupted PDF file: {str(e)}")

def preprocess_papers(progress_callback: Optional[Callable[[int], None]] = None, use_disambiguation: bool = False) -> None:
    try:
        processor = PDFProcessor(use_disambiguation=use_disambiguation)
        processor.process_all(progress_callback=progress_callback)
    except Exception as e:
        logger.error(f"Preprocessing failed: {str(e)}")
        raise

if __name__ == "__main__":
    preprocess_papers()