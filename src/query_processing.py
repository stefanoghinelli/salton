from whoosh.qparser import MultifieldParser, OrGroup, AndGroup
from whoosh import scoring
from whoosh import index

INDEX_PATH = "../data/indexes"

def submit_query(user_query, idx_path):
    ix = index.open_dir(idx_path)
    qp = MultifieldParser(["title", 
                           "abstract",
                           "content"],  # all selected fields
                          schema=ix.schema,  # my schema
                          group=OrGroup  # OR instead AND
                          )
    if "AND" in user_query:
        qp = MultifieldParser(["title",
                               "abstract",
                               "content"],  # all selected fields
                              schema=ix.schema,  # my schema
                              group=AndGroup  # AND instead OR
                              )

    user_query = user_query.lower()
    # print("This is uin: " + user_query)
    q = qp.parse(user_query)

    # print("This is the parsed query: " + str(q))
    with ix.searcher(weighting=scoring.BM25F(B=0.75, content_B=1.0, K1=1.2)) as searcher:
        results = searcher.search(q, limit=5)
        ret = []
        # print(str(len(results)) + " results\n")
        for r in results:
            # print(r.rank, ".", r["title"], " (Score: ", r.score, ")", )
            ret.append({"title": r["title"], "abstract": r["abstract"], 'score': r.score, 'rank': r.rank})
        # print("\nRun time: " + "{:.5f}".format(results.runtime) + " s")
        return ret

def search_something(q_benchmark=""):
    if q_benchmark != "":
        uin = q_benchmark
    else:
        uin = input("Insert your query: ")

    # print("\nSubmitted query -------")
    ris = submit_query(uin, INDEX_PATH)

    total_ris = [j for i in [ris] for j in i]
    sorted_ris = sorted(total_ris, key=lambda x: x["score"], reverse=True)

    print("\n---------------------")
    print("---------------------")
    print("    R e s u l t s    ")
    print("---------------------")
    print("---------------------")

    for w in sorted_ris:
        print("Paper: ", w['title'])
        print("Abstract: ", w['abstract'])
        print("Score: ", w['score'])
        print("---------------------")

    ix = index.open_dir(INDEX_PATH)
    qp = MultifieldParser(["title",
                           "abstract",
                           "content"],
                          schema=ix.schema,
                          )
    user_query = uin.lower()
    q = qp.parse(user_query)
    with ix.searcher(weighting=scoring.BM25F(B=0.75, content_B=1.0, K1=1.2)) as searcher:
        corrected = searcher.correct_query(q, user_query)
        if corrected.query != q:
            print("\n ----> Maybe did you mean:", corrected.string + " ?")

    if q_benchmark != "":
        return sorted_ris


if __name__ == '__main__':
    search_something()