import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

filename = 'test_book.txt'

try:
    with open(filename, 'rt', encoding="utf-8") as f_obj:
        content = f_obj.read()
except FileNotFoundError:
    print('File \'{0}\' does not exit.'.format(filename))

#TOKENIZATION
#Tokenizza il contenuto del file

tokens = word_tokenize(content)

#STOPWORDS REMOVAL & LEMMATIZATION
#Rimuove le parole ininfluenti, le porta nella sua forma base e le appende in una lista

wnl = nltk.WordNetLemmatizer()

#migliora la performance
stops = set(stopwords.words("english"))

filt_words = [wnl.lemmatize(t.lower()) for t in tokens if t.lower() not in stops]

print(filt_words[:50])

