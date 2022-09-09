from whoosh import qparser
from whoosh.qparser import QueryParser
from whoosh import scoring
from whoosh import index
from whoosh.fields import *

# INDEX_PATH = os.path.abspath(os.path.pardir) + os.path.sep + "indexdir"
OPENB_INDEX_PATH = "./preprocessing/indexdir/open-textbooks"
SPR_INDEX_PATH = "./preprocessing/indexdir/springer"

# DOC_PATH = os.path.abspath(os.path.pardir) + os.path.sep +"Docs"
SCHEMA = Schema(title=TEXT(stored=True), path=ID(stored=True), content=TEXT)


def keywords_query(q, idx_path):
    # q = "Engineering"
    results = []
    ix = index.open_dir(idx_path)
    qp = qparser.MultifieldParser(["title", "content"], ix.schema)
    q_parsed = qp.parse(q)
    with ix.searcher(weighting=scoring.BM25F(B=0.75, title_B=1.0, body_B=0.5, K1=2)) as searcher:
        for r in searcher.search(q_parsed, limit=10):
            results.append({"content": r["title"], 'score': r.score})

    if len(results) == 0:
        print("empty")
    else:
        print("find")
        return results


queryfatta = "ferrari"
ris_opb = keywords_query(queryfatta, OPENB_INDEX_PATH)
ris_spr = keywords_query(queryfatta, SPR_INDEX_PATH)

total_ris = [j for i in [ris_opb, ris_spr] for j in i]
sorted_ris = sorted(total_ris, key = lambda x: x["score"], reverse=True)

for x in sorted_ris:
    print(x)

#
# def field_query(q):
#     q = "cicci"
#     results = []
#     ix = index.open_dir(INDEX_PATH)
#     qp = QueryParser("content", schema=ix.schema)
#     q_parsed = qp.parse(q)
#     with ix.searcher(weighting=scoring.BM25F(B=0.75, content_B=1.0, K1=1.5)) as searcher:
#         for r in searcher.search(q_parsed, limit=10):
#             x = r
#             results.append({"title": r["title"], 'score': r.score})
#
#     if len(results) == 0:
#         print("empty")
#     else:
#         print("find")
#         for x in results:
#             print(x)
#         return results
