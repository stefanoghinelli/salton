import os
from whoosh.index import create_in
from whoosh.fields import *
import hashlib
from datetime import datetime
from whoosh.qparser import QueryParser
from queryprocessing import *

open_textbooks_src_folder = '../doc_tokens/open-textbooks/'
open_textbooks_dst_folder = '/open-textbooks/'
open_textbooks_files = os.listdir(open_textbooks_src_folder)

springer_src_folder = '../doc_tokens/springer/'
springer_dst_folder = '/springer/'
springer_files = os.listdir(springer_src_folder)

"""
Reading the documentation, the TEXT field uses a 
StandardAnalyzer of default that tokenizes the content field,
we will use those created in the pre-processing phase 
"""
analyzer = analysis.StemmingAnalyzer()
schema = Schema(uuid=ID(unique=True), title=TEXT(stored=True, analyzer=analyzer, spelling=True),
                content=TEXT(stored=True, analyzer=analyzer, spelling=True), date=DATETIME(stored=True))

"""
This function is responsible for:
 1. receiving as input the identifier (UUID) of the source 2 document
 2 .search for such UUID by running a query on the "uuid" field of the index of source 1
 3. return True if such document is not yet present, false otherwise
"""


def exec_entity_resolution(uuid):
    qp = QueryParser("uuid", schema=open_textbooks_ix.schema)
    q = qp.parse(uuid)
    not_yet_present = True
    with open_textbooks_ix.searcher() as s:
        results = s.search(q)
        if len(results) > 0:
            not_yet_present = False

    return not_yet_present


def create_index(files, srcFolder, dst_folder, ix):
    if not files:
        sys.exit("\'doc_tokens\' dir is empty cannot works")

    if not os.path.exists("../indexdir" + dst_folder):
        os.mkdir("../indexdir" + dst_folder)

    writer = ix.writer()

    for f_name in files:

        try:
            with open(srcFolder + f_name, 'r') as f:
                tkns = f.read()
        except FileNotFoundError:
            print('File \'{0}\' does not exit.'.format(f_name))
            return 1

        f.close()
        # composition of the original fileName in PDF format
        f_name_in_pdf = f_name.replace("_tokens.txt", ".pdf")
        # compute MD5 of the fileName, which will be used as the UUID of the entity to make it unique
        hash_object = hashlib.md5(str(f_name_in_pdf).encode('utf-8'))
        uuid = hash_object.hexdigest()
        # performs entity resolution only if is the source 2 "springer"
        if "springer" in srcFolder:
            if exec_entity_resolution(uuid):
                writer.add_document(title=f_name_in_pdf, content=tkns, uuid=uuid, date=datetime.now())
            else:
                print(f_name_in_pdf + " already present.")
        else:
            writer.add_document(title=f_name_in_pdf, content=tkns, uuid=uuid, date=datetime.now())

    writer.commit()


if __name__ == '__main__':
    print("Opentextbook indexing started...")
    open_textbooks_ix = create_in("../indexdir" + open_textbooks_dst_folder, schema)
    create_index(open_textbooks_files, open_textbooks_src_folder, open_textbooks_dst_folder, open_textbooks_ix)
    print("Opentextbook finished")

    print("Springer indexing started...")
    springer_ix = create_in("../indexdir" + springer_dst_folder, schema)
    create_index(springer_files, springer_src_folder, springer_dst_folder, springer_ix)
    print("Springer finished")
