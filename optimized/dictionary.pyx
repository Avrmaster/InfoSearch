from __future__ import print_function
from multiprocessing import cpu_count
from multiprocessing.pool import ThreadPool
from optimized.trie import TrieDictionary
import os
import re

from cachetools import LFUCache, cached

_use_multi_thread: bool = False

cdef class Dictionary:
    cdef dict _d
    cdef dict _double_d
    cdef dict _pos_d
    cdef object _trie_d
    cdef object _trie_rev_d

    cdef int _docs_cnt
    cdef list _paragraphs_map

    def __init__(self):
        self._d = dict()
        self._double_d = dict()
        self._pos_d = dict()
        self._trie_d = TrieDictionary()
        self._trie_rev_d = TrieDictionary(revers=True)

        self._docs_cnt = 0
        self._paragraphs_map = []

    cpdef add_dir(self, str to_index_path):
        files_cnt = len(os.listdir(to_index_path))
        chunk_size = 15
        chunks = [(i*chunk_size, (i+1)*chunk_size) for i in range(files_cnt//chunk_size)]
        if _use_multi_thread and chunks[-1][1] != files_cnt:
            chunks.append((chunks[-1][1], files_cnt))
        if len(chunks) > 0 and _use_multi_thread:
            print(f"Splitting {files_cnt} documents into |{to_index_path}| into {len(chunks)} chunks")
            ThreadPool(cpu_count()).starmap(Dictionary._add_dir,
                                                      [(self, to_index_path, ch[0], ch[1]) for ch in chunks])
        else:
            self._add_dir(to_index_path, 0, files_cnt)

    # cdef _add_dir(Dictionary self, str to_index_path, int start, int end):
    def _add_dir(self, to_index_path, int start, int end):
        """
        Read all files in directory (with utf-8 encoding) and add their all words.
        Each paragraph is indexed
        :param to_index_path: relative or absolute path to dir with documents
        :return: paragraph_map, a map from paragraph_id (index) to Tuple of it's (document_filepath, line_num)
        :rtype: List[Tuple]
        """
        if not _use_multi_thread:
            print(f"Indexing directory {to_index_path} [{start}:{end}]..")

        split_ex = re.compile(r"[^\w'-]+", flags=re.IGNORECASE)
        strip_ex = re.compile(r"^['-]+|['-]+$", flags=re.IGNORECASE)

        cdef list docs_list
        cdef long total_size
        cdef long read_size
        cdef long words_cnt
        docs_list = os.listdir(to_index_path)[start:end]
        total_size = sum([os.path.getsize(f'{to_index_path}/{f}') for f in docs_list]) // 1024
        read_size = 0
        words_cnt = 0

        cdef long doc_id
        cdef str filename
        cdef str filepath
        cdef long line_num
        cdef str line
        cdef str word
        cdef int p_id

        for doc_id, filename in enumerate(docs_list):
            filepath = to_index_path + '/' + filename
            with open(filepath) as file:
                for line_num, line in enumerate(file):
                    if len(line) < 2:
                        continue
                    for word_pos, word in enumerate(split_ex.split(line)):
                        # word = strip_ex.sub('', word)
                        if len(word) > 0:
                            p_id = len(self._paragraphs_map)
                            # self._add_word(word, p_id)
                            # self._add_pos_word(word, p_id, word_pos)
                            self._add_trie_word(word, p_id)
                            words_cnt += 1
                    self._paragraphs_map.append((filepath, line_num))
            read_size += os.path.getsize(filepath) // 1024
            print(f'\rReading{"."*(doc_id%3)}{" "*(3-doc_id%3)}{(read_size*100)/total_size}% '
                  f'{doc_id+1}/{len(docs_list)} - {filename}', end='')

        if not _use_multi_thread:
            print("\rReading 100%")
            print(f"Total words read: {words_cnt}")

    cdef _add_word(self, str w, int ind):
        w = w.capitalize()
        cdef set s
        if w in self._d:
            s = self._d[w]
        else:
            s = self._d[w] = set()
        s.add(ind)
        self._docs_cnt = max(self._docs_cnt, ind + 1)

    cdef _add_sequence(self, str w1, str w2, int ind):
        w1 = w1.capitalize()
        w2 = w2.capitalize()
        cdef str seq
        seq = w1+'\t'+w2
        cdef set s
        s = self._double_d[seq] = self._double_d.get(seq, set())
        s.add(ind)

    cdef _add_pos_word(self, str w, int ind, int pos):
        w = w.capitalize()
        cdef dict dd
        dd = self._pos_d[w] = self._pos_d.get(w, dict())
        cdef set positions
        positions = dd[ind] = dd.get(ind, set())
        positions.add(pos)

    cdef _add_trie_word(self, str w, int ind):
        self._trie_d.add_word(w, ind)
        self._trie_rev_d.add_word(w, ind)

    cpdef set get_ids(self, str word):
        return self._d.get(word.capitalize(), set())

    cpdef set get_sequence_ids(self, str word1, str word2):
        return self._double_d.get(word1.capitalize()+'\t'+word2.capitalize(), set())

    cpdef dict get_positions(self, str word):
        return dict(self._pos_d.get(word.capitalize(), dict()))  # creating a copy

    cpdef dict get_postions

    cpdef docs_cnt(self):
        return self._docs_cnt

    cpdef get_paragraph_info(self, p_num):
        if p_num < 0 or p_num >= len(self._paragraphs_map):
            raise IndexError(f"Dictionary does not contain paragraph {p_num}")
        return self._paragraphs_map[p_num]

    @cached(cache=LFUCache(maxsize=300))
    def get_paragraph(self, p_num):
        if p_num < 0 or p_num >= len(self._paragraphs_map):
            raise IndexError(f"Dictionary does not contain paragraph {p_num}")
        fpath, lnum = self.get_paragraph_info(p_num)
        with open(fpath) as f:
            for j, l in enumerate(f):
                print(f"\ropening{'.'*(j%3)+' '*(3-j%3)}{(j+1)*100//(lnum+1)}%", end='')
                if j == lnum:
                    print(end='\r')
                    return l

    def __contains__(self, item):
        return item in self._d

    def __iter__(self):
        return iter(self._d.items())

    def __len__(self):
        return len(self._d)

    def __sizeof__(self):
        return self._d.__sizeof__() + self._double_d.__sizeof__() + self._pos_d.__sizeof__()\
                                    + self._trie_d.__sizeof__() + self._trie_rev_d.__sizeof__()

    def __str__(self):
        printables = []
        for i, item in enumerate(self._d.items()):
            word, indexes = item
            info = f'in {len(indexes)} pars.'
            printables.append('<| ' + word + ' ' * (30 - len(word)) + info + ' |>' + ' ' * (30 - len(info)) +
                              ('\n' if i % 3 == 2 else ''))
        return ''.join(printables)
