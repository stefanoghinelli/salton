from whoosh.qparser import QueryParser, MultifieldParser, OrGroup
from whoosh import scoring
from whoosh import index

# INDEX_PATH = os.path.abspath(os.path.pardir) + os.path.sep + "indexdir"

OPENB_INDEX_PATH = "./preprocessing/indexdir/open-textbooks"
SPR_INDEX_PATH = "./preprocessing/indexdir/springer"

# DOC_PATH = os.path.abspath(os.path.pardir) + os.path.sep +"Docs"


def submit_query(user_query, idx_path):
    ix = index.open_dir(idx_path)
    qp = MultifieldParser(["title",
                           "content"],  # all selected fields
                          schema=ix.schema,  # with my schema
                          group=OrGroup)  # OR instead AND
    user_query = user_query.lower()
    print("This is UNI: " + user_query)
    q = qp.parse(user_query)
    print("This is the parsed query: " + str(q))
    with ix.searcher(weighting=scoring.BM25F(B=0.75, content_B=1.0, K1=1.2)) as searcher:
        corrected = searcher.correct_query(q, user_query)
        if corrected.query != q:
            print("Did you mean:", corrected.string + " ?")
            exit(1)
        results = searcher.search(q)
        ret = []
        print(str(len(results)) + " results\n")
        for r in results:
            print(r.rank, ".", r["title"], " (Score: ", r.score, ")", )
            ret.append({"title": r["title"], 'score': r.score})

        print("\nRun time: " + "{:.5f}".format(results.runtime) + " s")
        return ret

UNI = "diagnosis"
print("\nSubmitted OPB query -------")
ris_opb = submit_query(UNI, OPENB_INDEX_PATH)
print("\nSubmitted SPR query -------")
ris_spr = submit_query(UNI, SPR_INDEX_PATH)

total_ris = [j for i in [ris_opb, ris_spr] for j in i]
sorted_ris = sorted(total_ris, key=lambda x: x["score"], reverse=True)

print("\nFinal results -------")

for w in sorted_ris:
    print(w)


#
# def submit_query(q, idx_path):
#     results = []
#     ix = index.open_dir(idx_path)
#     query = QueryParser("content", ix.schema).parse(q)
#     with ix.searcher(weighting=scoring.BM25F(B=0.75, title_B=1.0, content_B=0.1, K1=2)) as searcher:
#         for r in searcher.search(query, limit=30):
#             results.append({'rank': r.rank, 'book': r["title"], 'score': r.score})
#     return results