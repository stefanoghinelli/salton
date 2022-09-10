import os
from whoosh.index import create_in
from whoosh.fields import *

# srcFolder = '/home/massimiliano/UNI/Gestione_dell_informazione/thematic-search-engine/doc_tokens/'
# srcFolder = '../doc_tokens/'


open_textbooks_src_folder = '/home/massimiliano/thematic-search-engine/doc_tokens/open-textbooks/'
open_textbooks_dst_folder = '/open-textbooks/'

open_textbooks_files = os.listdir(open_textbooks_src_folder)


springer_src_folder = '/home/massimiliano/thematic-search-engine/doc_tokens/springer/'
springer_dst_folder = '/springer/'

springer_files = os.listdir(springer_src_folder)


def create_index(files, srcFolder, dst_folder):
    if not files:
        sys.exit("\'doc_tokens\' dir is empty cannot works")

    """
    Leggendo la documentazione, il campo TEXT usa uno 
    StandardAnalyzer di defualt che tokenizza il campo content,
    useremo quelli creati nella fase di pre-processing
    """
    schema = Schema(title=TEXT(stored=True), path=ID(stored=True), content=TEXT(stored=True))

    if not os.path.exists("indexdir" + dst_folder):
        os.mkdir("indexdir" + dst_folder)

    ix = create_in("indexdir" + dst_folder, schema)

    writer = ix.writer()

    for f_name in files:

        try:
            with open(srcFolder + f_name, 'r') as f:
                tkns = f.read()
        except FileNotFoundError:
            print('File \'{0}\' does not exit.'.format(f_name))
            return 1

        f.close()
        writer.add_document(title=f_name[:-4], content=tkns)

    writer.commit()


print("OPB indexing started...")
create_index(open_textbooks_files, open_textbooks_src_folder, open_textbooks_dst_folder)
print("OPB finished")

print("SPR indexing started...")
create_index(springer_files, springer_src_folder, springer_dst_folder)
print("SPR finished")

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
