from whoosh.qparser import MultifieldParser, OrGroup
from whoosh import scoring
from whoosh import index

OPENB_INDEX_PATH = "../indexdir/open-textbooks"
SPR_INDEX_PATH = "../indexdir/springer"

QUERY_NATURAL_PATH = "../evaluation/query_natual_lang.txt"
QUERY_BENCH_PATH = "../evaluation/query_benchmark.txt"


def submit_query(user_query, idx_path):
    ix = index.open_dir(idx_path)
    qp = MultifieldParser(["title",
                           "content"],  # all selected fields
                          schema=ix.schema,  # with my schema
                          group=OrGroup)  # OR instead AND
    user_query = user_query.lower()

    # print("This is uin: " + user_query)
    q = qp.parse(user_query)

    # print("This is the parsed query: " + str(q))
    with ix.searcher(weighting=scoring.BM25F(B=0.75, content_B=1.0, K1=1.2)) as searcher:
        results = searcher.search(q, limit=10)
        ret = []

        # print(str(len(results)) + " results\n")
        for r in results:
            # print(r.rank, ".", r["title"], " (Score: ", r.score, ")", )
            ret.append({"title": r["title"], 'score': r.score, 'rank': r.rank})

        # print("\nRun time: " + "{:.5f}".format(results.runtime) + " s")
        return ret


def search_something(q_benchmark=""):
    if q_benchmark != "":
        uin=q_benchmark
    else:
        uin = input("Insert your query: ")  # "An Exhical Foundation for Environmentalism"

    # print("\nSubmitted OPB query -------")
    ris_opb = submit_query(uin, OPENB_INDEX_PATH)

    # print("\nSubmitted SPR query -------")
    ris_spr = submit_query(uin, SPR_INDEX_PATH)

    total_ris = [j for i in [ris_opb, ris_spr] for j in i]
    sorted_ris = sorted(total_ris, key=lambda x: x["score"], reverse=True)

    print("\n---------------------")
    print("---------------------")
    print("    R e s u l t s")
    print("---------------------")
    print("---------------------")

    for w in sorted_ris:
        print("Book: ", w['title'], " - Score: ", w['score'])
        print("---------------------")

    ix = index.open_dir(OPENB_INDEX_PATH)
    qp = MultifieldParser(["title",
                           "content"],  # all selected fields
                          schema=ix.schema,  # with my schema
                          group=OrGroup)  # OR instead AND
    user_query = uin.lower()
    q = qp.parse(user_query)
    with ix.searcher(weighting=scoring.BM25F(B=0.75, content_B=1.0, K1=1.2)) as searcher:
        corrected = searcher.correct_query(q, user_query)
        if corrected.query != q:
            print("\n ----> Maybe did you mean:", corrected.string + " ?")

if __name__ == '__main__':
    search_something()
