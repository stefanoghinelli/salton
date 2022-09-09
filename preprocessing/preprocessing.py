import os
import nltk
import string
import sys
import pdftotext
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem.lancaster import LancasterStemmer
from nltk.corpus import wordnet as wn
# from krovetzstemmer import Stemmer
from contextlib import redirect_stdout


"""
fare un ciclo in piu: il primo pesca da scrFolder + "open-textbooks" il secodo pesca da scrFolder + "springer"
ovviamente andrà cambiata dstFolder nelle altre due nuove cartelle cambiati.
Modificare indexdir in modo da aggiunger un altro indice.
indexdir/open-textbook/....
        /springer/.... 
"""

srcFolder = '/home/massimiliano/UNI/Gestione_dell_informazione/thematic-search-engine/documents/open-textbooks/'

dstFolder = '/home/massimiliano/UNI/Gestione_dell_informazione/thematic-search-engine/doc_tokens/'

files = os.listdir(srcFolder)

if not files:
    sys.exit("\'documents\' dir is empty cannot works")


for f_name in files:
    raw_f_path = srcFolder + f_name
    if f_name[-3:] == "pdf":
        # Load your PDF
        try:
            with open(raw_f_path, "rb") as f:
                txt = pdftotext.PDF(f)
        except FileNotFoundError:
            print('File \'{0}\' does not exit.'.format(f_name))

        # TOKENIZATION FOR PDF
        tokens = word_tokenize("\n\n".join(txt))
        # print(tokens)
    else:
        try:
            with open(raw_f_path, 'r') as f:
                content = f.read()
        except FileNotFoundError:
            print('File \'{0}\' does not exit.'.format(f_name))

        # TOKENIZATION FOR TXT
        tokens = tokenize(content)

    # migliora la performance; assume che i libri siano scritti in inglese
    stops = set(stopwords.words("english"))

    wnl = nltk.WordNetLemmatizer()

    # STOPWORDS REMOVAL & LEMMATIZATION
    filt_words = [wnl.lemmatize(tkn.lower()) for tkn in tokens if tkn.lower() not in stops]


    # STEMMING
    # krovetzstemmer meno aggressivo di Porter

    """
    stemmer = Stemmer()
    stem_words = []
    for word in filt_words:
        stem_words.append(stemmer.stem(word))"""

    lancaster = LancasterStemmer()
    for word in filt_words:
        word = lancaster.stem(word)

    # REMOVE PUNCTUATION
    punc = set(string.punctuation + "“" + "”" + "©" + "’" + "∞")

    for word in filt_words:
        if word in punc:
            filt_words.remove(word)

    file_tokens_path = dstFolder + f_name[:-4] + "_tokens.txt"

    if not os.path.exists(file_tokens_path):
        os.mknod(file_tokens_path)

    # stampa i tokens su file in "doc_tokens"
    tokens_file = open(file_tokens_path, 'w')
    with redirect_stdout(tokens_file):
        print(filt_words)
    tokens_file.close()

def disambiguateTerms(terms):
    for t_i in terms: # t_i is target term
        selSense = None
        selScore = 0.0
        for s_ti in wn.synsets(t_i, wn.NOUN):
            score_i = 0.0
            for t_j in terms: # t_j term in t_i's context window
                if (t_i==t_j):
                    continue
                bestScore = 0.0
                for s_tj in wn.synsets(t_j, wn.NOUN):
                    tempScore = s_ti.wup_similarity(s_tj)
                    if (tempScore>bestScore):
                        bestScore=tempScore
                score_i = score_i + bestScore
            if (score_i>selScore):
                selScore = score_i
                selSense = s_ti
        if (selSense is not None):
            print(t_i,": ",selSense,", ",selSense.definition())
            print("Score: ",selScore)
        else:
            print(t_i,": --")

disambiguateTerms(filt_words)