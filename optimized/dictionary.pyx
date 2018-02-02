from __future__ import print_function
from multiprocessing import cpu_count
from multiprocessing.pool import ThreadPool
import os
import re

cdef class Dictionary:
    cdef dict _d
    cdef int _docs_cnt

    def __init__(self):
        self._d = dict()
        self._docs_cnt = 0

    # cpdef list add_dir(self, str to_index_path):
    def add_dir(self, to_index_path):
        files_cnt = len(os.listdir(to_index_path))
        chunk_size = 15
        chunks = [(i*chunk_size, (i+1)*chunk_size) for i in range(files_cnt//chunk_size)]
        if chunks[-1][1] != files_cnt:
            chunks.append((chunks[-1][1], files_cnt-1))
        print(f"Splitting |{to_index_path}| into {len(chunks)} chunks")
        if len(chunks) > 0:
            res = []
            for pool_res in ThreadPool(cpu_count()).starmap(self._add_dir,
                                      [(to_index_path, ch[0], ch[1]) for ch in chunks]):
                res.extend(pool_res)
            return res
        else:
            return self._add_dir(to_index_path, 0, files_cnt)

    # cdef list _add_dir(self, str to_index_path, int start, int end):
    def _add_dir(self, to_index_path, start, end):
        """
        Read all files in directory (with utf-8 encoding) and add their all words.
        Each paragraph is indexed
        :param to_index_path: relative or absolute path to dir with documents
        :return: paragraph_map, a map from paragraph_id (index) to Tuple of it's (document_filepath, line_num)
        :rtype: List[Tuple]
        """
        # print(f"Indexing directory {to_index_path} [{start}:{end}]..")

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
        cdef long long line_num
        cdef str line
        cdef str word

        cdef list paragraphs_map
        paragraphs_map = []

        for doc_id, filename in enumerate(docs_list):
            filepath = to_index_path + '/' + filename
            with open(filepath) as file:
                for line_num, line in enumerate(file):
                    if len(line) < 2:
                        continue
                    for word in split_ex.split(line):
                        word = strip_ex.sub('', word)
                        if len(word) > 0:
                            self.add_word(word, len(paragraphs_map))
                            words_cnt += 1
                    paragraphs_map.append((filepath, line_num))
            read_size += os.path.getsize(filepath) // 1024
            print(f'\rReading{"."*(doc_id%3)}{" "*(3-doc_id%3)}{(read_size*100)/total_size}% '
                  f'{doc_id+1}/{len(docs_list)} - {filename}', end='')

        # print("\rReading 100%")
        # print(f"Total words read: {words_cnt}")
        return paragraphs_map

    cdef add_word(self, str w, int ind):
        w = w.capitalize()
        cdef set s
        s = self._d[w] = self._d.get(w, set())
        s.add(ind)
        self._docs_cnt = max(self._docs_cnt, ind + 1)
        pass

    cpdef set get_ids(self, str word):
        return self._d.get(word.capitalize(), set())

    cpdef docs_cnt(self):
        return self._docs_cnt

    def __contains__(self, item):
        return item in self._d

    def __iter__(self):
        return iter(self._d.items())

    def __len__(self):
        return len(self._d)

    def __sizeof__(self):
        return self._d.__sizeof__()

    def __str__(self):
        printables = []
        for i, item in enumerate(self._d.items()):
            word, indexes = item
            info = f'in {len(indexes)} pars.'
            printables.append('<| ' + word + ' ' * (30 - len(word)) + info + ' |>' + ' ' * (30 - len(info)) +
                              ('\n' if i % 3 == 2 else ''))
        return ''.join(printables)
