import os

from nltk.corpus import stopwords
from whoosh import scoring
from whoosh.index import create_in, open_dir
from whoosh.fields import *
from whoosh.qparser import MultifieldParser, OrGroup

ana = analysis.StemmingAnalyzer()

schema = Schema(path=ID(stored=True, unique=True), content=TEXT(stored=True, analyzer=ana, spelling=True),
                doc=TEXT(stored=True, analyzer=ana, spelling=True))

ix = create_in("indexdir", schema)

writer = ix.writer()
writer.add_document(path=str(1), content="advanced", doc="calcio")
writer.add_document(path=str(2), content="advanced algebra advanced algebra advanced algebra ",
                    doc="advanced algebra advanced algebra advanced algebra ")
writer.add_document(path=str(3), content="cosange algebrone advanced algebra  ", doc="cosange algebrone advanced algebra ")
writer.add_document(path=str(4), content="advanced algebr advanced algebra ", doc="advanced algebr advanced algebra ")
writer.commit()

# ix = open_dir('indexdir')
# with ix.searcher(weighting=scoring.BM25F(B=0.75, doc_B=0.85, K1=2)) as searcher:
#     query = QueryParser("doc", ix.schema).parse("advanced")
#     results = searcher.search(query, terms=True, limit=20)
#     for r in results:
#         print(r["doc"], " / ", " (Score: ", r.score, ")", r.rank, r.docnum)

ix = open_dir('indexdir')
qp = MultifieldParser(["content",
                       "doc"],  # all selected fields
                      schema=ix.schema,  # with my schema
                      group=OrGroup)  # OR instead AND

user_query = 'doc:calcio'
user_query = user_query.lower()
stops = set(stopwords.words("english"))
user_query = ' '.join([word for word in user_query.split() if word not in stops])
q = qp.parse(user_query)
print("This is UNI: " + user_query)
q = qp.parse(user_query)
print("This is the parsed query: " + str(q))
with ix.searcher(weighting=scoring.BM25F(B=0.75, doc_B=1.0, K1=1.2)) as searcher:
    corrected = searcher.correct_query(q, user_query)
    if corrected.query != q:
        print("Did you mean:", corrected.string + " ?")
        exit(1)
    results = searcher.search(q)
    print(str(len(results)) + " results\n")
    for r in results:
        print(r.rank, ".", r["doc"], " (Score: ", r.score, ")", )

    print("\nRun time: " + "{:.5f}".format(results.runtime) + " s")
