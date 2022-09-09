import os
import sys
from whoosh.index import create_in, open_dir
from whoosh.qparser import QueryParser
from whoosh.fields import *


#srcFolder = '/home/massimiliano/UNI/Gestione_dell_informazione/thematic-search-engine/doc_tokens/'
srcFolder = '../doc_tokens/'

files = os.listdir(srcFolder)
print(files)

if not files:
    sys.exit("\'doc_tokens\' dir is empty cannot works")


"""
Leggendo la documentazione, il campo TEXT usa uno 
StandardAnalyzer di defualt che tokenizza il campo content,
useremo quelli creati nella fase di pre-processing
"""
schema = Schema(title=TEXT(stored=True), path=ID(stored=True), content=TEXT)

if not os.path.exists("indexdir"):
    os.mkdir("indexdir")

ix = create_in("indexdir", schema)

writer = ix.writer()

for f_name in files:
    try:
        with open(srcFolder + f_name, 'r') as f:
            tkns = f.read()
    except FileNotFoundError:
        print('File \'{0}\' does not exit.'.format(f_name))
    f.close()
    writer.add_document(title=f_name[:-4], content=tkns)

writer.commit()
"""
ix = open_dir("indexdir")
searcher = ix.searcher()
# print(list(searcher.lexicon("content")))
parser = QueryParser("content", schema=ix.schema)
query = parser.parse(u"engineering")
results = searcher.search(query)
if len(results) == 0:
    print("Empty result!!")
else:
    for x in results:
        print(x)
"""




