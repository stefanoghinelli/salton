from whoosh.analysis import Tokenizer, Token, LowercaseFilter, StopFilter, Filter
from whoosh.lang.porter import stem
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords, wordnet
from nltk import pos_tag
import re


class NLTKTokenizer(Tokenizer):
    """
    Tokenizer using NLTK's word tokenization
    """
    def __call__(self, text, positions=False, chars=False, keeporiginal=False,
                 removestops=True, start_pos=0, start_char=0, mode='', **kwargs):
        assert isinstance(text, str), f"Expected str, got {type(text)}"

        tokens = re.findall(r'\b[a-z0-9]+(?:-[a-z0-9]+)*\b', text.lower())

        pos = start_pos
        for t in tokens:
            token = Token(positions, chars, removestops=removestops, mode=mode)
            token.text = t
            token.pos = pos
            token.startchar = start_char
            token.endchar = start_char + len(t)

            yield token

            pos += 1
            start_char += len(t) + 1


class LemmaFilter(Filter):
    """
    Token filter using NLTK WordNetLemmatizer
    """
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self._pos_map = {
            'N': wordnet.NOUN,
            'V': wordnet.VERB,
            'J': wordnet.ADJ,
            'R': wordnet.ADV
        }

    def __call__(self, tokens):
        for token in tokens:
            lemma = self.lemmatizer.lemmatize(token.text, pos=wordnet.NOUN)

            if lemma == token.text:
                lemma = self.lemmatizer.lemmatize(token.text, pos=wordnet.VERB)

            token.text = lemma
            yield token


class LemmaFilterWithPOS(Filter):
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self._pos_map = {
            'N': wordnet.NOUN,
            'V': wordnet.VERB,
            'J': wordnet.ADJ,
            'R': wordnet.ADV
        }

    def __call__(self, tokens):
        token_list = list(tokens)
        words = [t.text for t in token_list]

        tagged = pos_tag(words)

        for token, (word, pos) in zip(token_list, tagged):
            wordnet_pos = self._pos_map.get(pos[0], wordnet.NOUN)
            token.text = self.lemmatizer.lemmatize(word, pos=wordnet_pos)
            yield token


class StemFilter(Filter):
    def __call__(self, tokens):
        for token in tokens:
            token.text = stem(token.text)
            yield token


def LemmatizingAnalyzer(stoplist=None, minsize=2, maxsize=None, use_pos=False, apply_stemming=False):
    if stoplist is None:
        stoplist = set(stopwords.words('english'))

    tokenizer = NLTKTokenizer()

    filters = [
        LowercaseFilter(),
        StopFilter(stoplist=stoplist, minsize=minsize, maxsize=maxsize),
        LemmaFilterWithPOS() if use_pos else LemmaFilter()
    ]

    if apply_stemming:
        filters.append(StemFilter())

    analyzer = tokenizer
    for f in filters:
        analyzer = analyzer | f

    return analyzer
