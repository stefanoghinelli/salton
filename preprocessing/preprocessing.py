import os
import nltk
import string
import sys
import pdftotext
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem.lancaster import LancasterStemmer
from nltk.corpus import wordnet as wn

"""
Open-textbooks Files
"""

open_textbooks_src_folder = '../documents/open-textbooks/'
open_textbooks_dst_folder = '../doc_tokens/open-textbooks/'
open_textbooks_files = os.listdir(open_textbooks_src_folder)

"""
Springer Files
"""

springer_src_folder = '../documents/springer/'
springer_dst_folder = '../doc_tokens/springer/'
springer_files = os.listdir(springer_src_folder)


def preprocessor(files, scr_folder, dst_folder):
    if not files:
        sys.exit("\'documents\' dir is empty cannot works")

    for f_name in files:

        raw_f_path = scr_folder + f_name
        print("Starting pre-processing file: " + f_name)

        # check file dimension
        file_stats = os.stat(raw_f_path)
        size = file_stats.st_size / (1024 * 1024)

        if size:
            if f_name[-3:] == "pdf":
                # Load your PDF
                try:
                    with open(raw_f_path, "rb") as f:
                        txt = pdftotext.PDF(f)
                except FileNotFoundError:
                    print('File \'{0}\' does not exit.'.format(f_name))
                    return 1

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
                tokens = word_tokenize(content)

            print("Ended tokenization of : " + f_name)

            # migliora la performance; assume che i libri siano scritti in inglese
            stops = set(stopwords.words("english"))

            wnl = nltk.WordNetLemmatizer()

            # STOPWORDS REMOVAL & LEMMATIZATION
            filt_words = [wnl.lemmatize(tkn.lower()) for tkn in tokens if tkn.lower() not in stops]

            lancaster = LancasterStemmer()
            for word in filt_words:
                word = lancaster.stem(word)

            print("Ended lemming/stemming of : " + f_name)

            # REMOVE PUNCTUATION
            punc = set(string.punctuation + "“" + "”" + "©" + "’" + "∞")

            print("Starting removing punctuation of  : " + f_name)

            for word in filt_words:
                if word in punc:
                    filt_words.remove(word)

            file_tokens_path = dst_folder + f_name[:-4] + "_tokens.txt"

            f = open(file_tokens_path, "w")
            f.write(" ".join(filt_words))
            f.close()

            print("Writed tokens of : " + f_name)

            # print("Disambiguation started")
            # disambiguateTerms(filt_words)
            # print("Disambiguation ended")
        else:
            print("Corrupted file  : " + f_name)


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


preprocessor(open_textbooks_files, open_textbooks_src_folder, open_textbooks_dst_folder)
preprocessor(springer_files, springer_src_folder, springer_dst_folder)
