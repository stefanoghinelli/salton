import re
from whoosh.qparser import MultifieldParser, OrGroup, AndGroup
from whoosh import scoring, index

INDEX_PATH = "./data/indexes"

def submit_query(user_query, searcher, qp):
    user_query = user_query.lower()
    # print("This is uin: " + user_query)

    if re.search(r'\bAND\b', user_query, re.IGNORECASE):
        qp = MultifieldParser(["title", "abstract", "content"], schema=searcher.schema, group=AndGroup)
    else:
        qp = MultifieldParser(["title", "abstract", "content"], schema=searcher.schema, group=OrGroup)

    q = qp.parse(user_query)

    results = searcher.search(q, limit=5)
    ret = []
    # print(str(len(results)) + " results\n")
    for r in results:
        ret.append({"title": r["title"], "abstract": r["abstract"], 'score': r.score, 'rank': r.rank})
    return ret

def search_something(q_benchmark=""):
    ix = index.open_dir(INDEX_PATH)
    searcher = ix.searcher(weighting=scoring.BM25F(B=0.75, content_B=1.0, K1=1.2))
    qp = MultifieldParser(["title", "abstract", "content"], schema=searcher.schema, group=OrGroup)

    uin = q_benchmark if q_benchmark != "" else input("Insert your query: ")
    ris = submit_query(uin, searcher, qp)

    sorted_ris = sorted(ris, key=lambda x: x["score"], reverse=True)

    print("\n---------------------")
    print("---------------------")
    print("    R e s u l t s    ")
    print("---------------------")
    print("---------------------")

    for w in sorted_ris:
        print(f"Paper: {w['title']}")
        print(f"Abstract: {w['abstract']}")
        print(f"Score: {w['score']}")
        print("---------------------")

    user_query = uin.lower()
    q = qp.parse(user_query)
    corrected = searcher.correct_query(q, user_query)
    if corrected.query != q and len(sorted_ris) == 0:
        print(f"\n ----> Maybe did you mean: {corrected.string} ?")

    searcher.close()
    return sorted_ris if q_benchmark != "" else None

if __name__ == '__main__':
    search_something()
