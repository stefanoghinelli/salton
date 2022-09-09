import sys

import os, os.path
from whoosh import index, qparser
from whoosh.fields import *
from whoosh.qparser import QueryParser
from whoosh import scoring

from whoosh import index
from whoosh.index import create_in, open_dir
from whoosh.fields import *

# INDEX_PATH = os.path.abspath(os.path.pardir) + os.path.sep + "indexdir"

INDEX_PATH = "./preprocessing/indexdir"

# DOC_PATH = os.path.abspath(os.path.pardir) + os.path.sep +"Docs"

SCHEMA = Schema(title=TEXT(stored=True), path=ID(stored=True), content=TEXT)


def field_query(q):
    q = "cicci"
    results = []
    ix = index.open_dir(INDEX_PATH)
    qp = QueryParser("content", schema=ix.schema)
    q_parsed = qp.parse(q)
    with ix.searcher(weighting=scoring.BM25F(B=0.75, content_B=1.0, K1=1.5)) as searcher:
        for r in searcher.search(q_parsed, limit=10):
            x = r
            results.append({"title": r["title"], 'score': r.score})

    if len(results) == 0:
        print("empty")
    else:
        print("find")
        for x in results:
            print(x)
        return results


def keywords_query(q):
    q = "ciccio"
    results = []
    ix = index.open_dir(INDEX_PATH)
    qp = qparser.MultifieldParser(["title", "content"], ix.schema)
    q_parsed = qp.parse(q)
    with ix.searcher(weighting=scoring.BM25F(B=0.75, title_B=1.0, body_B=0.5, K1=2)) as searcher:
        for r in searcher.search(q_parsed, limit=10):
            x = r
            results.append({"content": r, 'score': r.score})

    if len(results) == 0:
        print("empty")
    else:
        print("find")
        return results


keywords_query("a")
