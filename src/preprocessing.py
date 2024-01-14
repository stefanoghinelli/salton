import os
import nltk
import string
import sys
import pdftotext
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem.lancaster import LancasterStemmer
from nltk.corpus import wordnet as wn

SRC_FOLDER = '../data/pdf_downloads/'
DST_FOLDER = '../data/txt/'
FILES = os.listdir(SRC_FOLDER)

def preprocessor(files, scr_folder, dst_folder):
    if not files:
        sys.exit("\'documents\' dir is empty cannot works")

    for f_name in files:
        raw_f_path = scr_folder + f_name
        print("Starting pre-processing file: " + f_name)
        if f_name[-3:] == "pdf":
            try:
                with open(raw_f_path, "rb") as f:
                    txt = pdftotext.PDF(f)
            except FileNotFoundError:
                print('File \'{0}\' does not exit.'.format(f_name))
                continue
            except IOError:
                print('File \'{0}\' has input/output exception.'.format(f_name))
                continue

            # TOKENIZATION FOR PDF
            tokens = word_tokenize("\n\n".join(txt))
            
        print("Ended tokenization of : " + f_name)
        stops = set(stopwords.words("english"))
        wnl = nltk.WordNetLemmatizer()
        # STOPWORDS REMOVAL & LEMMATIZATION
        filt_words = [wnl.lemmatize(tkn.lower()) for tkn in tokens if tkn.lower() not in stops]
        lancaster = LancasterStemmer()
        for word in filt_words:
            word = lancaster.stem(word)
        print("Ended lemming/stemming of : " + f_name)
        
        # REMOVE PUNCTUATION
        # punc = set(string.punctuation + "“" + "”" + "©" + "’" + "∞")
        # print("Starting removing punctuation of  : " + f_name)

        # for word in filt_words:
        #     if word in punc:
        #         filt_words.remove(word)

        file_tokens_path = dst_folder + f_name[:-4] + "_tokens.txt"
        f = open(file_tokens_path, "w")
        f.write(" ".join(filt_words))
        f.close()

        print("Writed tokens of : " + f_name)

        # print("Disambiguation started")
        # disambiguateTerms(filt_words)
        # print("Disambiguation ended")


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

if __name__ == '__main__':
    preprocessor(FILES, SRC_FOLDER, DST_FOLDER)

