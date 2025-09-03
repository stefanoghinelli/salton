import time
import click
from pathlib import Path
from typing import Callable
import nltk
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
from collections import Counter
import string

from .config import DATA_DIR, BENCHMARK_DIR, INDEX_DIR

class OrderedGroup(click.Group):
    def __init__(self, name=None, commands=None, **attrs):
        super(OrderedGroup, self).__init__(name, commands, **attrs)
        self.commands = commands or {}
        self.command_order = [
            'fetch',
            'preprocess',
            'index',
            'search',
            'stats',
            'benchmark'
        ]

    def list_commands(self, ctx):
        return self.command_order


def summarize_text(text: str, max_sentences: int = 2) -> str:
    if not text or len(text) < 100:
        return text
    
    sentences = sent_tokenize(text)
    if len(sentences) <= max_sentences:
        return text
    
    try:
        stop_words = set(stopwords.words('english'))
    except LookupError:
        nltk.download('stopwords')
        stop_words = set(stopwords.words('english'))
    
    word_freq = Counter()
    for sentence in sentences:
        words = sentence.lower().translate(str.maketrans('', '', string.punctuation)).split()
        for word in words:
            if word not in stop_words and len(word) > 2:
                word_freq[word] += 1
    
    sentence_scores = {}
    for sentence in sentences:
        words = sentence.lower().translate(str.maketrans('', '', string.punctuation)).split()
        score = sum(word_freq[word] for word in words if word in word_freq)
        sentence_scores[sentence] = score
    
    top_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)[:max_sentences]
    top_sentences.sort(key=lambda x: sentences.index(x[0]))
    
    return ' '.join([sentence for sentence, score in top_sentences])

def print_header(text: str):
    click.echo("\n" + "=" * 50)
    click.echo(f"  {text}")
    click.echo("=" * 50 + "\n")

@click.group(cls=OrderedGroup)
def cli():
    """
    Salton: your tool for retrieving papers faster
    """
    pass

@cli.command()
@click.option('--limit', '-l', default=100, help='Number of papers to fetch')
def fetch(limit: int):
    """
    Fetch papers from CORE repository
    """
    try:
        from .scraping import scrape_papers
        
        print_header("Fetching Papers")
        
        scrape_papers(limit)
            
    except ImportError as e:
        click.echo(f"\nError: Missing dependencies for fetching papers. {str(e)}")
        click.echo("Please install the required dependencies: pip install requests lxml")
    except Exception as e:
        click.echo(f"\nError fetching papers: {str(e)}")

@cli.command()
@click.option('--wsd', is_flag=True, help='Enable Word Sense Disambiguation')
def preprocess(wsd):
    """
    Tokenize, lemmatize, remove stopwords
    """
    try:
        from .preprocessing import preprocess_papers
        
        print_header("Preprocessing Papers")
        
        preprocess_papers(use_disambiguation=wsd)
            
    except Exception as e:
        click.echo(f"\nError preprocessing papers: {str(e)}")

@cli.command()
def index():
    """
    Build the index
    """
    try:
        from .indexing import build_index
        import shutil
        import os
        
        print_header("Indexing Papers")
        
        # Remove the existing one to avoid duplications
        if os.path.exists(INDEX_DIR):
            click.echo("Removing existing index...")
            shutil.rmtree(INDEX_DIR)
            click.echo("Index removed.")
        
        with click.progressbar(length=100, label='Indexing papers') as bar:
            def progress_callback(percent):
                bar.update(percent - bar.pos)
            
            build_index(progress_callback)
            
    except Exception as e:
        click.echo(f"\nError indexing papers: {str(e)}")

@cli.command()
@click.option('--query', '-q', prompt='Enter your search query', help='Search query')
@click.option('--limit', '-l', default=10, help='Number of results to show')
def search(query: str, limit: int):
    """
    Query papers by keyword
    """
    try:
        from .query_processing import process_query
        
        print_header(f"Results for: {query}")
        
        results = process_query(query, limit)
        
        if not results:
            click.echo("No results found.")
            return
            
        for i, result in enumerate(results, 1):
            click.echo(f"{i}. Title: {result['title']}")
            click.echo(f"   Score: {result['score']:.4f}")
            if 'abstract' in result and result['abstract']:
                summary = summarize_text(result['abstract'])
                import textwrap
                wrapped = textwrap.fill(summary, width=70)
                formatted_abstract = wrapped.replace('\n', '\n             ')
                click.echo(f"   Abstract: {formatted_abstract}")
            if 'portal_url' in result and result['portal_url']:
                click.echo(f"   URL: {result['portal_url']}")
            click.echo("")
            
    except Exception as e:
        click.echo(f"\nError searching: {str(e)}")

@cli.command()
def stats():
    """
    Show statistics
    """
    try:
        from .indexing import get_index_stats
        
        print_header("Statistics")
        
        try:
            index_stats = get_index_stats()
            
            click.echo("Index statistics:")
            click.echo(f"-Documents indexed: {index_stats['doc_count']}")
            click.echo(f"-Unique terms: {index_stats['unique_terms']}")
            click.echo(f"-Index size: {index_stats['index_size_mb']:.2f} MB")
        except Exception as e:
            click.echo("Index statistics:")
            click.echo(f"-Error retrieving index statistics: {str(e)}")
        
        data_dir = Path(DATA_DIR)
        pdf_dir = data_dir / "pdf_downloads"
        txt_dir = data_dir / "txt"
        
        raw_count = len(list(pdf_dir.glob("*.pdf"))) if pdf_dir.exists() else 0
        processed_count = len(list(txt_dir.glob("*_tokens.txt"))) if txt_dir.exists() else 0
        
        click.echo("\nData statistics:")
        click.echo(f"-Raw papers: {raw_count}")
        click.echo(f"-Processed papers: {processed_count}")
        
        benchmark_dir = Path(BENCHMARK_DIR)
        query_sets = len(list(benchmark_dir.glob("query_*.txt"))) if benchmark_dir.exists() else 0
        
        click.echo("\nBenchmark statistics:")
        click.echo(f"-Available query sets: {query_sets}")
        
    except Exception as e:
        click.echo(f"\nError getting stats: {str(e)}")

@cli.command()
@click.option('--save/--no-save', default=True, help='Save benchmark results to file')
@click.option('--detailed/--simple', default=False, help='Show detailed results')
def benchmark(save: bool, detailed: bool):
    """
    Run benchmarks
    """
    try:
        print_header("Running benchmarks")
        
        try:
            from .benchmarking import run_benchmark
        except ImportError as e:
            click.echo(f"\nError: Missing dependencies for benchmarking. {str(e)}")
            return
        
        def progress_callback(percent):
            if hasattr(progress_callback, 'bar'):
                progress_callback.bar.update(percent - progress_callback.bar.pos)
        
        with click.progressbar(length=100, label='Running benchmarks') as bar:
            progress_callback.bar = bar
            
            try:
                results = run_benchmark(save_results=save, progress_callback=progress_callback)
            except ValueError as e:
                click.echo(f"\nError: {str(e)}")
                return
            except Exception as e:
                click.echo(f"\nError during benchmark: {str(e)}")
                return
            
        click.echo("\nBenchmark completed!")
        
        if not results:
            click.echo("No results to display.")
            return
            
        if detailed:
            click.echo("\nDetailed Results:\n")
            for query, metrics in results.items():
                click.echo(f"Query: {query}")
                click.echo(f"  Precision: {metrics['precision']:.4f}")
                click.echo(f"  Recall: {metrics['recall']:.4f}")
                click.echo(f"  NDCG: {metrics['ndcg']:.4f}")
                click.echo(f"  MAP: {metrics['map']:.4f}")
                click.echo(f"  Execution Time: {metrics['execution_time']:.4f}s")
                click.echo(f"  Result Count: {metrics['result_count']}")
                click.echo("")
        else:
            click.echo("\nSummary Results:\n")
            avg_precision = sum(m['precision'] for m in results.values()) / len(results) if results else 0
            avg_recall = sum(m['recall'] for m in results.values()) / len(results) if results else 0
            avg_ndcg = sum(m['ndcg'] for m in results.values()) / len(results) if results else 0
            avg_map = sum(m['map'] for m in results.values()) / len(results) if results else 0
            
            click.echo(f"Average Precision: {avg_precision:.4f}")
            click.echo(f"Average Recall: {avg_recall:.4f}")
            click.echo(f"Average NDCG: {avg_ndcg:.4f}")
            click.echo(f"Average MAP: {avg_map:.4f}")
            
    except Exception as e:
        click.echo(f"\nError running benchmark: {str(e)}")

def main():
    cli()

if __name__ == '__main__':
    main() 