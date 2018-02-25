from __future__ import print_function

from cachetools import LFUCache, cached
from multiprocessing.pool import Pool
from multiprocessing import cpu_count
from itertools import chain
from glob import glob
import sys
import os
import re


cpdef str _write_block_to_file(dict block, int start_doc_id, int block_num):
    """
    :param block: 
    :param start_doc_id: 
    :param block_num: 
    :return: path
    """
    cdef:
        str path = "tempSpimiBlocks"

    if not os.path.exists(path):
        os.makedirs(path)
    with open(os.path.join(path, "temp{}b{}.txt".format(start_doc_id, block_num)), "w+") as f:
        for term in sorted(block.keys()):
            f.write(f"{term} - {block[term]}\n")
    return path

# cpdef _generate_block_dictionaries(tuple filepaths, int start_doc_id, int max_block_size = 1073741824):
cpdef _generate_block_dictionaries(tuple filepaths, int start_doc_id, int max_block_size = 1024*512):
    """
    Generate dictionaries {TERM: POSTING LIST} of limited size
    and store them to temp directory. Files are to be merged and deleted later.

    :param filepaths: list of file's paths to be divided into limited size dictionaries
    :type filepaths: tuple
    :param start_doc_id: document_id the first element in filepaths
    :type start_doc_id: int
    :param max_block_size: size in bytes which dictionary will not exceed
    :type max_block_size: int
    :return: tuple of dictionaries' paths and total read words count
    :rtype: Tuple[List[str], int]
    """

    split_ex = re.compile(r"[^\w'-]+", flags=re.IGNORECASE)
    strip_ex = re.compile(r"^['-]+|['-]+$", flags=re.IGNORECASE)

    cdef long total_size
    cdef long parsed_size
    cdef long words_cnt
    total_size = max(sum([os.path.getsize(f) for f in filepaths]) // 1024, 1)
    parsed_size = 0
    words_cnt = 0

    cdef long doc_num
    cdef str filepath
    cdef str line
    cdef str word

    cdef list dict_paths
    cdef dict cur_dict
    dict_paths = []
    cur_dict = {}

    for doc_num, filepath in enumerate(filepaths):
        with open(filepath) as file:
            for line in file:
                if len(line) < 2:
                    continue
                for word in split_ex.split(line):
                    word = strip_ex.sub('', word)
                    if len(word) > 0:
                        word = word.lower()
                        try:
                            if cur_dict[word][-1] != start_doc_id + doc_num:
                                cur_dict[word].append(start_doc_id + doc_num)
                        except KeyError:
                            cur_dict[word] = [start_doc_id + doc_num]
                        words_cnt += 1
                    if sys.getsizeof(cur_dict) > max_block_size:
                        dict_paths.append(_write_block_to_file(cur_dict, start_doc_id, len(dict_paths)))
                        cur_dict.clear()
        parsed_size += os.path.getsize(filepath) // 1024
        print(f"Parsing {filepath}")

    if len(cur_dict) > 0:
        dict_paths.append(_write_block_to_file(cur_dict, start_doc_id, len(dict_paths)))

    return dict_paths, words_cnt

cdef class Dictionary:
    cdef:
        int _terms_cnt
        int _docs_cnt

    def __init__(self, str to_index_path, bint recursively = True):
        files = (chain.from_iterable(glob(os.path.join(x[0], '*.txt')) for x in os.walk(to_index_path)))
        # filepath of documents with ID index indicates
        documents_map = tuple(filepath for i, filepath in enumerate(iter(files)))
        files_cnt = len(documents_map)
        pools_cnt = max(1, cpu_count() - 1)

        chunk_size = max(1, files_cnt // (3 * pools_cnt))
        chunks = [(i * chunk_size, (i + 1) * chunk_size) for i in range(files_cnt // chunk_size)]
        # append the last chunk which was not included with previous generator because of smaller size than the others
        if len(chunks) == 0:
            chunks = [(0, files_cnt)]
        elif chunks[-1][1] != files_cnt:
            chunks.append((chunks[-1][1], files_cnt))

        print(f"\n\nSplitting {files_cnt} documents in |{to_index_path}| into {len(chunks)} chunk(s)")
        print(f"Processing in {pools_cnt} pools")
        res = Pool(pools_cnt).starmap(_generate_block_dictionaries,
                                                    [(documents_map[ch[0]:ch[1]], ch[0]) for ch in chunks])
        print(f"\n{sum([len(r[0]) for r in res])} BLOCK(S) CREATED from {sum([r[1] for r in res])} WORD(S)")

        self._terms_cnt = 0
        self._docs_cnt = files_cnt

    def __len__(self):
        return self._terms_cnt

    cpdef docs_cnt(self):
        return self._docs_cnt

        # cpdef get_paragraph_info(self, p_num):
        #     if p_num < 0 or p_num >= len(self._paragraphs_map):
        #         raise IndexError(f"Dictionary does not contain paragraph {p_num}")
        #     return self._paragraphs_map[p_num]
        #
        # @cached(cache=LFUCache(maxsize=300))
        # def get_paragraph(self, p_num):
        #     if p_num < 0 or p_num >= len(self._paragraphs_map):
        #         raise IndexError(f"Dictionary does not contain paragraph {p_num}")
        #     fpath, lnum = self.get_paragraph_info(p_num)
        #     with open(fpath) as f:
        #         for j, l in enumerate(f):
        #             print(f"\ropening{'.'*(j%3)+' '*(3-j%3)}{(j+1)*100//(lnum+1)}%", end='')
        #             if j == lnum:
        #                 print(end='\r')
        #                 return l
        #
        # def __contains__(self, item):
        #     return item in self._d
        #
        # def __iter__(self):
        #     return iter(self._d.items())


        # def __sizeof__(self):
        #     return self._d.__sizeof__() + self._double_d.__sizeof__() + self._pos_d.__sizeof__()\
        #                                 + self._trie_d.__sizeof__() + self._trie_rev_d.__sizeof__()
        #
        # def __str__(self):
        #     printables = []
        #     for i, item in enumerate(self._d.items()):
        #         word, indexes = item
        #         info = f'in {len(indexes)} pars.'
        #         printables.append('<| ' + word + ' ' * (30 - len(word)) + info + ' |>' + ' ' * (30 - len(info)) +
        #                           ('\n' if i % 3 == 2 else ''))
        #     return ''.join(printables)
