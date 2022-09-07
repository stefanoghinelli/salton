import os
import nltk
import string
import sys
import pdftotext
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from krovetzstemmer import Stemmer
from contextlib import redirect_stdout


srcFolder = '/home/massimiliano/UNI/Gestione_dell_informazione/thematic-search-engine/documents/'
dstFolder = '/home/massimiliano/UNI/Gestione_dell_informazione/thematic-search-engine/doc_tokens/'

files = os.listdir(srcFolder)

if not files:
    sys.exit("\'documents\' dir is empty cannot works")


# servirà anche nella query sulla gui
def tokenize(text):
    tkn = word_tokenize(text)
    return tkn


for f_name in files:
    raw_f_path = srcFolder + f_name

    if f_name[-3:] == "pdf":
        # Load your PDF
        try:
            with open(raw_f_path, "rb") as f:
                pdf = pdftotext.PDF(f)
        except FileNotFoundError:
            print('File \'{0}\' does not exit.'.format(f_name))

        # TOKENIZATION FOR PDF
        tokens = tokenize("\n\n".join(pdf))
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
    stemmer = Stemmer()
    stem_words = []
    for word in filt_words:
        stem_words.append(stemmer.stem(word))

    # REMOVE PUNCTUATION
    punc = set(string.punctuation + "“" + "”" + "©" + "’")

    for word in stem_words:
        if word in punc:
            print("Ho rimosso: ", word)
            stem_words.remove(word)

    file_tokens_path = dstFolder + f_name[:-4] + "_tokens.txt"

    if not os.path.exists(file_tokens_path):
        os.mknod(file_tokens_path)

    # stampa i tokens su file in "doc_tokens"
    tokens_file = open(file_tokens_path, 'w')
    with redirect_stdout(tokens_file):
        print(stem_words)
    tokens_file.close()
    