import os
from whoosh.index import create_in
from whoosh.fields import *
from datetime import datetime
from whoosh.qparser import QueryParser
from query_processing import *

"""
Reading the documentation, the TEXT field uses a 
StandardAnalyzer of default that tokenizes the content field,
we will use those created in the pre-processing phase 
"""
ANALYZER = analysis.StemmingAnalyzer()
SCHEMA = Schema(title=TEXT(stored=True, analyzer=ANALYZER, spelling=True), abstract=TEXT(stored=True, analyzer=ANALYZER, spelling=True),
                content=TEXT(stored=True, analyzer=ANALYZER, spelling=True), date=DATETIME(stored=True))
SRC_FOLDER = './data/txt/'
DST_FOLDER = './data/indexes/'

def create_index(files, scr_folder, dst_folder, ix):
    if not files:
        sys.exit("\'data/txt\' directory is empty, cannot work")

    writer = ix.writer()

    for f_name in files:
        if f_name.endswith('_tokens.txt'):
            try:
                with open(scr_folder + f_name, 'r') as f:
                    tkns = f.read()
                abstract_file_name = f_name.replace("_tokens.txt", ".txt")
                with open(scr_folder + abstract_file_name, 'r') as f:
                    abstract = f.read().replace('\n', ' ')
                title = f_name.replace("_tokens.txt", "")
                writer.add_document(title=title, content=tkns, abstract=abstract, date=datetime.now())
            except FileNotFoundError:
                print(f"File '{f_name}' or '{abstract_file_name}' does not exist")
                continue
        else:
            continue
    writer.commit()

if __name__ == '__main__':
    print("Indexing started")
    ix = create_in(DST_FOLDER, SCHEMA)
    create_index(os.listdir(SRC_FOLDER), SRC_FOLDER, DST_FOLDER, ix)
    print("Indexing finished")
