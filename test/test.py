import nltk
import string

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.corpus import wordnet as wn

from whoosh import scoring
from whoosh.index import create_in, open_dir
from whoosh.fields import *
from whoosh.qparser import MultifieldParser, OrGroup


ana = analysis.StemmingAnalyzer()

schema = Schema(path=ID(stored=True, unique=True), content=TEXT(stored=True, analyzer=ana, spelling=True),
                doc=TEXT(stored=True, analyzer=ana, spelling=True))

ix = create_in("indexdir", schema)

writer = ix.writer()
writer.add_document(path=str(1), content="algebra math theorem", doc="Basic algebra with applications")
writer.add_document(path=str(2), content="Science numerical calculation math", doc="Art of Polynomial Interpolation")
writer.add_document(path=str(3), content="programming language numerical calculation", doc="A guide to MATLAB")
writer.add_document(path=str(4), content="Anatomy brain nerve", doc="Human Anatomy")
writer.add_document(path=str(5), content="literature america united state ", doc="American literature")

writer.add_document(path=str(6), content="agriculture india farmer plant",
                    doc="Agricultural value chains in India")
writer.add_document(path=str(7), content="climate change catastrophe green", doc="Climate of the middle")
writer.add_document(path=str(8), content="finance digital economy money bank",
                    doc="The Future of Financial Systems in the Digital Age")
writer.add_document(path=str(9), content="travel digital places photo",
                    doc="The psychosocial reality of Digital Travel")
writer.add_document(path=str(10), content="biocultural diversity medicine landscape",
                    doc="Case studies in Biocultural Diversity")
writer.add_document(path=str(11), content="health law regulation theory",
                    doc="The fundamentals of healthcare administration")
writer.add_document(path=str(12), content="platform digital internet regulation",
                    doc="Digital platform regulation")
writer.add_document(path=str(13), content="business ethics education philosophy ",
                    doc="Times of insight")


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


def disambiguateTerms(terms):
    for t_i in terms:  # t_i is target term
        selSense = None
        selScore = 0.0
        for s_ti in wn.synsets(t_i, wn.NOUN):
            score_i = 0.0
            for t_j in terms:  # t_j term in t_i's context window
                if t_i == t_j:
                    continue
                bestScore = 0.0
                for s_tj in wn.synsets(t_j, wn.NOUN):
                    tempScore = s_ti.wup_similarity(s_tj)
                    if tempScore > bestScore:
                        bestScore = tempScore
                score_i = score_i + bestScore
            if score_i > selScore:
                selScore = score_i
                selSense = s_ti
        if selSense is not None:
            print(t_i, ": ", selSense, ", ", selSense.definition())
            print("Score: ", selScore)
        else:
            print(t_i, ": --")


user_query = input("Inserisci la tua ricerca : ")

# user_query = "i need the main theorems for math's test"

token = word_tokenize(user_query.lower())

stops = set(stopwords.words("english"))
punc = set(string.punctuation + "“" + "”" + "©" + "’" + "∞")
wnl = nltk.WordNetLemmatizer()

# disambiguateTerms(token)

# print(token)
user_query = ' '.join([wnl.lemmatize(word) for word in user_query.split() if word not in stops and punc])
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
