import os
from whoosh.index import create_in
from whoosh.fields import *
import hashlib
from datetime import datetime

from whoosh.qparser import QueryParser

open_textbooks_src_folder = '../doc_tokens/open-textbooks/'
open_textbooks_dst_folder = '/open-textbooks/'
open_textbooks_files = os.listdir(open_textbooks_src_folder)

springer_src_folder = '../doc_tokens/springer/'
springer_dst_folder = '/springer/'
springer_files = os.listdir(springer_src_folder)

"""
Leggendo la documentazione, il campo TEXT usa uno 
StandardAnalyzer di defualt che tokenizza il campo content,
useremo quelli creati nella fase di pre-processing
"""
analyzer = analysis.StemmingAnalyzer()
schema = Schema(uuid=ID(unique=True), title=TEXT(stored=True, analyzer=analyzer, spelling=True),
                content=TEXT(stored=True, analyzer=analyzer, spelling=True), date=DATETIME(stored=True))


# questa funzione si occupa di:
# - ricevere in input l'identificativo (UUID) del documento della sorgente 2
# - cercare tale UUID eseguendo una query sul campo "uuid" dell'indice della sorgente 1
# - restituire True se tale documento non è ancora presente, false altrimenti

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

    if not os.path.exists("indexdir" + dst_folder):
        os.mkdir("indexdir" + dst_folder)

    writer = ix.writer()

    for f_name in files:

        try:
            with open(srcFolder + f_name, 'r') as f:
                tkns = f.read()
        except FileNotFoundError:
            print('File \'{0}\' does not exit.'.format(f_name))
            return 1

        f.close()
        # composizione del fileName originale in formato PDF
        f_name_in_pdf = f_name.replace("_tokens.txt", ".pdf")
        # calcolo dell'MD5 del fileName, il quale sarà utilizzato come UUID dell'entita' per renderla univoca
        hash_object = hashlib.md5(str(f_name_in_pdf).encode('utf-8'))
        uuid = hash_object.hexdigest()

        # eseguita la entity resolution solo quando viene elaborata la sorgente 2 "springer (SPR)"
        if "springer" in srcFolder:
            if exec_entity_resolution(uuid):
                writer.add_document(title=f_name_in_pdf, content=tkns, uuid=uuid, date=datetime.now())
            else:
                print(f_name_in_pdf + " was merged.")

        writer.add_document(title=f_name_in_pdf, content=tkns, uuid=uuid, date=datetime.now())

    writer.commit()


print("OPB indexing started...")
open_textbooks_ix = create_in("indexdir" + open_textbooks_dst_folder, schema)
create_index(open_textbooks_files, open_textbooks_src_folder, open_textbooks_dst_folder, open_textbooks_ix)
print("OPB finished")

print("SPR indexing started...")
springer_ix = create_in("indexdir" + springer_dst_folder, schema)
create_index(springer_files, springer_src_folder, springer_dst_folder, springer_ix)
print("SPR finished")
