from dictionary import Dictionary
from matrices import IncidenceMatrix
from search import BooleanSearch
import os
import re
import sys
from time import sleep
from cachetools import cached, LFUCache


dictionary = Dictionary()
split_ex = re.compile(r"[^a-zа-я'-]+", flags=re.IGNORECASE)
strip_ex = re.compile(r"^['-]+", flags=re.IGNORECASE)

docs_list = os.listdir('documents/txt')
total_size = sum([os.path.getsize(f'documents/txt/{f}') for f in docs_list])
read_size = 0
words_cnt = 0


paragraphs_map = []
for doc_id, filename in enumerate(docs_list):
    filepath = f'documents/txt/{filename}'
    with open(filepath) as file:
        for line_num, line in enumerate(file):
            for word in split_ex.split(line):
                word = strip_ex.sub('', word)
                if len(word) > 1:
                    dictionary.add_word(word, len(paragraphs_map))
                    words_cnt += 1
            paragraphs_map.append((filepath, line_num))

    read_size += os.path.getsize(filepath)
    print(f'\rReading.. {(read_size*100)//total_size}% {doc_id+1}/{len(docs_list)}', end='')
print()

# it's just taking too long
# im = IncidenceMatrix(dictionary)
# print(im, end='\n\n')
print(dictionary, end='\n\n')
print(f"Total paragraph count")
print(f"Total words count: {words_cnt}")
print(f"Unique words count: {len(dictionary)}", end='\n\n')
# print(f"IncidenceMatrix sys size: {sys.getsizeof(im)}\n")
print(f"Dictionary sys size: {sys.getsizeof(dictionary)}\n")


@cached(cache=LFUCache(maxsize=300))
def get_paragraph(p_id: int):
    fpath, lnum = paragraphs_map[p_id]
    with open(fpath) as f:
        for j, l in enumerate(f):
            print(f"\ropening{'.'*(j%3)+' '*(3-j%3)}{(j+1)*100//(lnum+1)}%", end='')
            if j == lnum:
                print(end='\r')
                return l


bs = BooleanSearch(dictionary)
while True:
    query = input("Enter your query (empty to quit): ")
    if not query:
        break
    paragraphs = bs.execute(query)
    print(f"Found {len(paragraphs)} results")
    for i, p in enumerate(paragraphs):
        print(f"Res {(i+1)}: \n{get_paragraph(p)}")
        if input() != "":
            break
