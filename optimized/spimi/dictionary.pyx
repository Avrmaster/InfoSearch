from __future__ import print_function

from nltk.stem.porter import PorterStemmer
from cachetools import LFUCache, cached
from multiprocessing.pool import Pool
from multiprocessing import cpu_count
from itertools import chain
from glob import glob
import shutil
import json
import sys
import os
import re

_tempPath = "D:/tempSpimiBlocks"

cpdef bytearray _compress_posting_list(list posting_list):
    cdef:
        int last = 0
        int dif = 0
        list output = []
        list buffer = []
    for i in posting_list:
        dif = i - last
        last = i
        while dif > 0:
            buffer.append(dif & 0b01111111)
            dif >>= 7
        buffer[0] |= 0b10000000
        output.extend(reversed(buffer))
        buffer.clear()
    return bytearray(output)

cpdef list _decompress_posting_list(bytearray compressed_list):
    cdef:
        int cur = 0
        int offset = 0
        list output = []
    for b in list(compressed_list):
        cur = cur << 7 | (b & 0b01111111)
        if b >= 0b10000000: # last bit is 1
            output.append(offset+cur)
            offset += cur
            cur = 0
    return output

cpdef str _write_block_to_file(dict block, int start_doc_id, int block_num):
    """
    :param block: 
    :param start_doc_id: 
    :param block_num: 
    :return: path
    """
    cdef:
        list post_term_list = []
        int cur_term_pos = 0
        int cur_post_pos = 0
        str terms_filepath = os.path.join(_tempPath, "temp_t{}b{}.txt".format(start_doc_id, block_num))
        str posts_filepath = os.path.join(_tempPath, "temp_p{}b{}.txt".format(start_doc_id, block_num))
        str index_filepath = os.path.join(_tempPath, "temp_i{}b{}.txt".format(start_doc_id, block_num))
    if not os.path.exists(_tempPath):
        os.makedirs(_tempPath)

    with open(terms_filepath, "wb+") as ft, \
            open(posts_filepath, "wb+") as fp, \
            open(index_filepath, "w+") as fi:
        for t in sorted(block.keys()):
            disk_term = (bytearray(t, "utf-8"))
            ft.write(bytes([len(disk_term)]))  # assuming that term's length will not exceed 255 symbols
            ft.write(disk_term)

            disk_post = _compress_posting_list(block[t])
            fp.write(disk_post)

            post_term_list.append((cur_term_pos, cur_post_pos))
            cur_term_pos += 1 + len(disk_term)  # 1 for term size byte
            cur_post_pos += len(disk_post)

        json.dump(post_term_list, fp=fi)
    return terms_filepath

# cpdef _generate_block_dictionaries(tuple filepaths, int start_doc_id, int max_block_size = 1073741824):
cpdef _generate_block_dictionaries(tuple filepaths, int start_doc_id, int max_block_size = 1024 * 512):
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
    stemmer = PorterStemmer()

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
            # print(f"Parsing {filepath}")
            for line in file:
                if len(line) < 2:
                    continue
                # for word in line.split(" "):
                for word in split_ex.split(line):
                    word = strip_ex.sub('', word.lower())
                    if len(word) > 0:
                        # word = stemmer.stem(strip_ex.sub('', word))
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

    if len(cur_dict) > 0:
        dict_paths.append(_write_block_to_file(cur_dict, start_doc_id, len(dict_paths)))

    return dict_paths, words_cnt

cdef class Dictionary:
    cdef:
        int _terms_cnt
        int _docs_cnt
        tuple _documents_map

    def __init__(self, str to_index_path, bint recursively = True):
        files = (chain.from_iterable(glob(os.path.join(x[0], '*.txt')) for x in os.walk(to_index_path)))
        # filepath of documents with ID index indicates
        documents_map = tuple(filepath for i, filepath in enumerate(iter(files)))
        files_cnt = len(documents_map)
        # pools_cnt = max(1, cpu_count() - 1)
        pools_cnt = 1

        chunk_size = max(1, files_cnt // (3 * pools_cnt))
        chunks = [(i * chunk_size, (i + 1) * chunk_size) for i in range(files_cnt // chunk_size)]
        # append the last chunk which was not included with previous generator because of smaller size than the others
        if len(chunks) == 0:
            chunks = [(0, files_cnt)]
        elif chunks[-1][1] != files_cnt:
            chunks.append((chunks[-1][1], files_cnt))

        print(f"\n\nSplitting {files_cnt} documents in |{to_index_path}| into {len(chunks)} chunk(s)")
        print(f"Processing in {pools_cnt} pools")
        for f in os.listdir(_tempPath):
            os.remove(os.path.join(_tempPath, f))
        res = Pool(pools_cnt).starmap(_generate_block_dictionaries,
                                      [(documents_map[ch[0]:ch[1]], ch[0]) for ch in chunks])
        print(f"\n{sum([len(r[0]) for r in res])} BLOCK(S) CREATED from {sum([r[1] for r in res])} WORD(S)")
        self._docs_cnt = files_cnt
        self._documents_map = documents_map
        # TODO merge blocks

        # if os.path.exists(_tempPath):
        #     shutil.rmtree(_tempPath)
        self._terms_cnt = 0

    cpdef docs_cnt(self):
        return self._docs_cnt

    def __len__(self):
        return self._terms_cnt

    def get_document_filepath(self, int d_id):
        if d_id < 0 or d_id >= len(self.documents_map):
            raise IndexError(f"Dictionary does not contain document {d_id}")
        return self.documents_map[d_id]

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
