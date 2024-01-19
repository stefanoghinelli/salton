import os
import sys
import pdftotext
from nltk import word_tokenize, pos_tag
from nltk.corpus import stopwords, wordnet as wn, wordnet
from nltk.stem import WordNetLemmatizer

SRC_FOLDER = './data/pdf_downloads/'
DST_FOLDER = './data/txt/'
FILES = os.listdir(SRC_FOLDER)

def preprocessor(files, src_folder, dst_folder):
    if not files:
        sys.exit("\'data/pdf_downloads\' directory is empty, cannot work")

    stops = set(stopwords.words("english"))
    lemmatizer = WordNetLemmatizer()

    for f_name in files:
        raw_f_path = os.path.join(src_folder, f_name)
        print("Starting pre-processing file: " + f_name)
        try:
            with open(raw_f_path, "rb") as f:
                pdf = pdftotext.PDF(f)
        except FileNotFoundError:
            print('File \'{0}\' does not exit.'.format(f_name))
            continue
        except IOError:
            print('File \'{0}\' has input/output exception.'.format(f_name))
            continue

        txt = "\n\n".join(pdf)
        tokens = word_tokenize(txt)
        filt_words = [lemmatizer.lemmatize(token.lower()) for token in tokens if token.isalpha() and token.lower() not in stops]

        #print("Disambiguation started")
        #disambiguate_terms(filt_words)
        #print("Disambiguation ended")

        output_file_path = os.path.join(dst_folder, f_name[:-4] + "_tokens.txt")
        with open(output_file_path, 'w') as output_file:
            output_file.write(" ".join(filt_words))
        print(f"Writed tokens of : {f_name}")

def disambiguate_terms(terms):
    tagged_terms = pos_tag(terms)
    for term, tag in tagged_terms:
        best = None
        max_score = 0.0
        wnet_pos = get_wordnet_pos(tag)
        for sense in wn.synsets(term, pos=wnet_pos):
            ctx_similarity = 0.0
            for context_term, _ in tagged_terms:
                if term != context_term:
                    best_cxt_score = 0.0
                    for context_sense in wn.synsets(context_term, pos=wnet_pos):
                        similarity = sense.path_similarity(context_sense)
                        if similarity and similarity > best_cxt_score:
                            best_cxt_score = similarity
                    ctx_similarity += best_cxt_score
            if ctx_similarity > max_score:
                best = sense
                max_score = ctx_similarity
        # if best:
        #     print(f"{term}: {best} - {best.definition()}")
        # else:
        #     print(f"{term}: no meaning found")

def get_wordnet_pos(treebank_tag):
    if treebank_tag.startswith('J'):
        return wordnet.ADJ
    elif treebank_tag.startswith('V'):
        return wordnet.VERB
    elif treebank_tag.startswith('N'):
        return wordnet.NOUN
    elif treebank_tag.startswith('R'):
        return wordnet.ADV
    else:
        return wordnet.NOUN 

if __name__ == '__main__':
    preprocessor(FILES, SRC_FOLDER, DST_FOLDER)

