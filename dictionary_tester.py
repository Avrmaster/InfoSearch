from dictionary import Dictionary
from matrices import IncidenceMatrix
from search import BooleanSearch
import os
import re
import sys


dictionary = Dictionary()
split_ex = re.compile(r"[^a-zа-я'-]+", flags=re.IGNORECASE)
strip_ex = re.compile(r"^['-]+", flags=re.IGNORECASE)

docs_list = os.listdir('documents/txt')
total_size = sum([os.path.getsize(f'documents/txt/{f}') for f in docs_list])
read_size = 0
words_cnt = 0
par_cnt = 0
for doc_id, filename in enumerate(docs_list):
    filepath = f'documents/txt/{filename}'
    with open(filepath) as file:
        for line in file:
            for word in split_ex.split(line):
                word = strip_ex.sub('', word)
                if len(word) > 1:
                    dictionary.add_word(word.capitalize(), doc_id)
                    words_cnt += 1
    read_size += os.path.getsize(filepath)
    print(f'\rReading.. {(read_size*100)//total_size}% {doc_id+1}/{len(docs_list)}', end='')
print()
im = IncidenceMatrix(dictionary)
print(im, end='\n\n')
print(dictionary, end='\n\n')
print(f"Total paragraph count")
print(f"Total words count: {words_cnt}")
print(f"Unique words count: {len(dictionary)}", end='\n\n')
print(f"IncidenceMatrix sys size: {sys.getsizeof(im)}\n"
      f"Dictionary sys size: {sys.getsizeof(dictionary)}\n")

# print("Searching for Harry and ")
