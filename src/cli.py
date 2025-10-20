import time
import click
from pathlib import Path
import nltk
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
from collections import Counter
import string

from .config import INDEX_DIR, BENCHMARK_DIR

class OrderedGroup(click.Group):
    def __init__(self, name=None, commands=None, **attrs):
        super(OrderedGroup, self).__init__(name, commands, **attrs)
        self.commands = commands or {}
        self.command_order = [
            'fetch',
            'index',
            'search',
            'benchmark',
            'mark-relevance'
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
@click.option('--source', '-s', default='arxiv', type=click.Choice(['arxiv', 'core']))
@click.option(
    '--category',
    '-c',
    default='cs.DC'
)
def fetch(limit: int, source: str, category: str):
    """
    Fetch papers from arXiv or CORE
    """
    try:
        print_header(f"Fetching Cloud/Distributed Papers from {source.upper()}")

        if source == 'arxiv':
            from .arxiv_fetcher import fetch_papers as fetch_papers_arxiv
            click.echo(f"Category: {category}")
            click.echo(f"Fetching {limit} papers...\n")
            if category.lower() == 'cs.ai':
                click.echo("Tip: Try cs.DC, cs.NI, or cs.PF for distributed/cloud systems.\n")
            fetch_papers_arxiv(limit, category=category)
        else:
            from .core_fetcher import fetch_papers as fetch_papers_core
            fetch_papers_core(limit)

    except ImportError as e:
        click.echo(f"\nError: Missing dependencies for fetching papers. {str(e)}")
        click.echo("Please install the required dependencies: pip install requests lxml")
    except Exception as e:
        click.echo(f"\nError fetching papers: {str(e)}")

@cli.command()
def index():
    """
    Build the search index using lemmatization
    """
    try:
        import shutil
        import os

        print_header("Indexing Papers with Lemmatization")

        if os.path.exists(INDEX_DIR):
            click.echo("Removing existing index...")
            shutil.rmtree(INDEX_DIR)
            click.echo("Index removed")

        from .indexing import build_index

        build_index()

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
        from .querier import process_query
        
        print_header(f"Results for: {query}")
        
        results = process_query(query, limit)
        
        if not results:
            try:
                from .querier import WhooshSearchEngine
                engine = WhooshSearchEngine()
                suggestion = engine.suggest_correction(query)
                if suggestion and suggestion.lower() != query.lower():
                    click.echo(f"No results found. Did you mean: '{suggestion}'?")
                else:
                    click.echo("No results found")
            except Exception:
                click.echo("No results found")
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
def benchmark():
    """
    Run evaluation benchmarks
    """
    try:
        print_header("Running Benchmarks")

        from .benchmarking import run_benchmark

        results = run_benchmark(save_results=True, query_set="default")

        if not results:
            click.echo("No results to display. Check that query files exist in evaluation/queries/")
            return

        for query, metrics in results.items():
            click.echo(f"Query: {query}")
            click.echo(f"  Precision: {metrics['precision']:.4f}")
            click.echo(f"  Recall: {metrics['recall']:.4f}")
            click.echo(f"  NDCG: {metrics['ndcg']:.4f}")
            click.echo(f"  MAP: {metrics['map']:.4f}")
            click.echo(f"  Execution Time: {metrics['execution_time']:.4f}s")
            click.echo(f"  Result Count: {metrics['result_count']}")
            click.echo("")

    except Exception as e:
        click.echo(f"\nError running benchmark: {str(e)}")
        import traceback
        traceback.print_exc()

@cli.command(name='mark-relevance')
def mark_relevance():
    """
    Manually mark relevant papers for benchmark judgments
    """
    try:
        print_header("Mark relevance judgments")

        from .querier import process_query

        queries_file = Path(BENCHMARK_DIR) / "query_natural_lang.txt"
        if not queries_file.exists():
            click.echo("Error: query_natural_lang.txt not found")
            return

        with open(queries_file) as f:
            queries = [line.strip() for line in f if line.strip() and not line.startswith('#')]

        click.echo(f"Found {len(queries)} queries to evaluate\n")
        click.echo("For each query, you'll see the top 20 results")
        click.echo("Mark relevant papers by entering their numbers (e.g., '1 3 5' or '1-5')\n")

        relevance_data = []

        for i, query in enumerate(queries, 1):
            click.echo(f"\n{'='*70}")
            click.echo(f"Query {i}/{len(queries)}: {query}")
            click.echo('='*70)

            results = process_query(query, limit=20)

            if not results:
                click.echo("No results found for this query")
                relevance_data.append([])
                continue

            for j, result in enumerate(results, 1):
                click.echo(f"\n{j}. {result['title']}")
                click.echo(f"   Score: {result['score']:.2f}")
                if result.get('abstract'):
                    abstract_preview = result['abstract'][:150] + "..." if len(result['abstract']) > 150 else result['abstract']
                    click.echo(f"   {abstract_preview}")

            click.echo(f"\n{'='*70}")
            relevant_input = click.prompt(
                "Enter relevant paper numbers (e.g., '1 3 5' or '1-5'), or press Enter to skip",
                default="",
                show_default=False
            )

            relevant_titles = []
            if relevant_input.strip():
                try:
                    numbers = set()
                    for part in relevant_input.split():
                        if '-' in part:
                            start, end = part.split('-')
                            numbers.update(range(int(start), int(end) + 1))
                        else:
                            numbers.add(int(part))

                    for num in sorted(numbers):
                        if 1 <= num <= len(results):
                            relevant_titles.append(results[num-1]['title'])
                        else:
                            click.echo(f"Warning: {num} is out of range, ignoring")

                    click.echo(f"Marked {len(relevant_titles)} papers as relevant")
                except Exception as e:
                    click.echo(f"Error parsing input: {e}")
            else:
                click.echo("No papers marked as relevant")

            relevance_data.append(relevant_titles)

        output_file = Path(BENCHMARK_DIR) / "query_relevance.txt"
        with open(output_file, 'w') as f:
            f.write("# Relevance judgments for benchmark queries\n")
            f.write("# Format: query_index|relevant_paper_title_1|relevant_paper_title_2|...\n")

            for i, (query, titles) in enumerate(zip(queries, relevance_data), 1):
                if titles:
                    titles_str = "|".join(titles)
                    f.write(f"{i}|{titles_str}\n")
                else:
                    f.write(f"{i}|\n")

        click.echo(f"\n{'='*70}")
        click.echo(f"  Saved relevance judgments to {output_file}")
        click.echo(f"  Total queries: {len(queries)}")
        click.echo(f"  Queries with relevance judgments: {sum(1 for r in relevance_data if r)}")
        click.echo(f"\nYou can now run benchmark cmd")

    except Exception as e:
        click.echo(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    cli()

if __name__ == '__main__':
    main() 
