import os; os.system("python optimized_build.py build_ext --inplace")
from dictionary import Dictionary
from booleanSearch import BooleanSearch
import os
import re
import sys
from cachetools import cached, LFUCache

while True:
    pass

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
    print(f'\rReading{"."*(doc_id%3)}{" "*(3-doc_id%3)}{(read_size*100)//total_size}% {doc_id+1}/{len(docs_list)} - '
          f'{filename}', end='')
print()

print(dictionary, end='\n\n')
print(f"Total paragraph count: {len(paragraphs_map)}")
print(f"Total words count: {words_cnt}")
print(f"Unique words count: {len(dictionary)}", end='\n\n')
print(f"Dictionary system size: ~{sys.getsizeof(dictionary)//1024}kB\n")


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
