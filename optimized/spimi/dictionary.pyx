from __future__ import print_function

import operator

from cachetools import LFUCache, cached
from multiprocessing.pool import Pool
from multiprocessing import cpu_count

from utils.regex import super_strip
from utils.files import get_all_files
import win32file
import shutil
import json
import sys
import os

from utils.scoring import process_fb2

# _ENCODING = "iso-8859-1"
_ENCODING = "utf-8"
_tempPath = "D:/tempSpimiBlocks"
_indexTermsFilename = "spimiIndex_terms.txt"
_indexPostsFilename = "spimiIndex_posts.txt"

cpdef tuple get_largest_file_and_its_lines_count():
    cdef:
        str longest_file_path
        long lines_count
    longest_file_path = os.path.join(_tempPath, max([(os.path.getsize(os.path.join(_tempPath, path)), path)
                                                     for path in os.listdir(_tempPath)], key=operator.itemgetter(0))[1])
    lines_count = 0
    with open(longest_file_path, "r", encoding=_ENCODING) as f:
        for line in f:
            lines_count += 1
    return longest_file_path, lines_count


cdef _write_number_variable_length(long n, list output, list buffer):
    while n > 0:
        buffer.append(n & 0b01111111)
        n >>= 7
    if len(buffer) > 0:
        buffer[0] |= 0b10000000
    else:
        buffer.append(0b10000000)
    output.extend(reversed(buffer))
    buffer.clear()

cpdef bytearray _compress_posting_list(list posting_list):
    cdef:
        int last = 0
        int dif = 0
        list output = []
        list buffer = []

    for doc_i, freq_in_i in posting_list:
        dif = doc_i - last
        last = doc_i
        _write_number_variable_length(dif, output, buffer)
        _write_number_variable_length(freq_in_i, output, buffer)
    return bytearray(output)

cpdef tuple _decompress_posting_list(bytes compressed_list):
    cdef:
        int cur = 0
        int offset = 0
        list output = []
        bint freq_number = False
    for b in compressed_list:
        cur = cur << 7 | (b & 0b01111111)
        if b >= 0b10000000:  # last bit is 1
            if not freq_number:
                output.append(offset + cur)
                offset += cur
            else:
                output.append(cur)
            freq_number = not freq_number
            cur = 0
    return tuple(zip(output[::2], output[1::2])) # make document-freq pairs

cpdef str _write_block_to_file(dict block, int start_doc_id, int block_num):
    cdef:
        str block_filepath = os.path.join(_tempPath, "temp{}b{}.txt".format(start_doc_id, block_num))
    if not os.path.exists(_tempPath):
        os.makedirs(_tempPath)

    with open(block_filepath, "w+", encoding=_ENCODING) as f:
        for i, t in enumerate(sorted(block.keys())):
            f.write(f'{t}\n')
            f.write(json.dumps(block[t]))
            f.write('\n')
    return block_filepath

cpdef _generate_block_dictionaries(tuple filepaths, int start_doc_id, int max_block_size = 1024 * 1024 * 16):
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
    cdef long words_cnt
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
        try:
        #     TEXT FILES
        #     with open(filepath, encoding=_ENCODING) as file:
        #         print(f"Parsing {filepath}")
        #         for line in file:
        #             if len(line) == 0:
        #                 continue
        #             for word in line.split(" "):
        #                 word = super_strip(word)
        #                 if len(word) > 0:
        #                     try:
        #                         cur_postings = cur_dict[word]
        #                         if cur_postings[-1][0] != start_doc_id + doc_num:
        #                             # register a word in this document for the first time
        #                             cur_postings.append([start_doc_id + doc_num, 1])
        #                         else:
        #                             # add 1 more occurence in this document
        #                             cur_postings[-1][1] += 1
        #                     except KeyError:
        #                         # register new word and new occurence in the document at the same time
        #                         cur_dict[word] = [[start_doc_id + doc_num, 1]]
        #                     words_cnt += 1
        #                 if sys.getsizeof(cur_dict) > max_block_size:
        #                     dict_paths.append(_write_block_to_file(cur_dict, start_doc_id, len(dict_paths)))
        #                     cur_dict.clear()
            print(f"Parsing {filepath}")
            tags_texts, metadata = process_fb2(filepath)
            for line in tags_texts:
                if len(line) == 0:
                    continue
                for word in line.split(" "):
                    word = super_strip(word)
                    if len(word) > 0:
                        try:
                            cur_postings = cur_dict[word]
                            if cur_postings[-1][0] != start_doc_id + doc_num:
                                # register a word in this document for the first time
                                cur_postings.append([start_doc_id + doc_num, 1])
                            else:
                                # add 1 more occurence in this document
                                cur_postings[-1][1] += 1
                        except KeyError:
                            # register new word and new occurence in the document at the same time
                            cur_dict[word] = [[start_doc_id + doc_num, 1]]
                        words_cnt += 1
                    if sys.getsizeof(cur_dict) > max_block_size:
                        dict_paths.append(_write_block_to_file(cur_dict, start_doc_id, len(dict_paths)))
                        cur_dict.clear()
        except UnicodeDecodeError as e:
            print(f"{e} at file {filepath}")

    if len(cur_dict) > 0:
        dict_paths.append(_write_block_to_file(cur_dict, start_doc_id, len(dict_paths)))

    return dict_paths, words_cnt

cdef class Dictionary:
    cdef:
        tuple _documents_map
        list _terms_posts

    def __init__(self, str to_index_path, str extension = "txt"):
        win32file._setmaxstdio(1024 * 5)
        print(f"Max opened files count set to {win32file._getmaxstdio()}")

        print(f"Searching for *.{extension} files in {to_index_path}..")
        files = get_all_files(to_index_path, extension)
        # filepath of documents with ID index indicates
        self._documents_map = tuple(filepath for i, filepath in enumerate(files))

        files_cnt = len(self._documents_map)
        pools_cnt = max(1, cpu_count() - 1)
        # pools_cnt = 1

        chunk_size = max(1, files_cnt // (10 * pools_cnt))
        chunks = [(i * chunk_size, (i + 1) * chunk_size) for i in range(files_cnt // chunk_size)]
        # append the last chunk which was not included with previous generator because of smaller size than the others
        if len(chunks) == 0:
            chunks = [(0, files_cnt)]
        elif chunks[-1][1] != files_cnt:
            chunks.append((chunks[-1][1], files_cnt))

        print(f"\n\nSplitting {files_cnt} documents in |{to_index_path}| into {len(chunks)} chunk(s)")
        print(f"Processing in {pools_cnt} pools")
        if os.path.exists(_tempPath):
            for f in os.listdir(_tempPath):
                os.remove(os.path.join(_tempPath, f))
        res = Pool(pools_cnt).starmap(_generate_block_dictionaries,
                                      [(self._documents_map[ch[0]:ch[1]], ch[0]) for ch in chunks])
        print(f"\n{sum([len(r[0]) for r in res])} BLOCK(S) CREATED from {sum([r[1] for r in res])} WORD(S)")

        ## MERGING ##
        print("Preparing merge..")
        blocks = []
        print("Merging..")
        try:
            blocks = [open(os.path.join(_tempPath, bl), "r", encoding=_ENCODING) for bl in os.listdir(_tempPath)]

            cur_terms = [b.readline().rstrip('\n') for b in blocks]
            cur_posting_lists = [json.loads(b.readline().rstrip('\n')) for b in blocks]

            largest_file_path, largest_lines_count = get_largest_file_and_its_lines_count()
            cur_line_at_largest_block = 0

            last_term = ""
            last_posting_list = []
            with open(_indexTermsFilename, "wb+") as ft, \
                    open(_indexPostsFilename, "wb+") as fp:

                self._terms_posts = []
                cur_term_pos = cur_post_pos = 0

                while len(blocks) > 0:
                    min_index, min_term = min(enumerate(cur_terms), key=operator.itemgetter(1))  # type: int, str
                    if not min_term:
                        blocks[min_index].close()
                        blocks.pop(min_index)
                        cur_terms.pop(min_index)
                        cur_posting_lists.pop(min_index)
                    else:
                        if min_term == last_term:
                            last_posting_list.extend(cur_posting_lists[min_index])
                        else:
                            ####
                            if last_term:
                                last_posting_list = sorted(last_posting_list)
                                disk_term = bytearray(last_term, _ENCODING)
                                ft.write(disk_term)

                                disk_post = _compress_posting_list(last_posting_list)
                                fp.write(disk_post)

                                self._terms_posts.append((cur_term_pos, cur_post_pos))
                                cur_term_pos += len(disk_term)
                                cur_post_pos += len(disk_post)
                            ####
                            last_posting_list = cur_posting_lists[min_index]
                            last_term = min_term
                        cur_terms[min_index] = blocks[min_index].readline().rstrip('\n')
                        if blocks[min_index].name == largest_file_path:
                            cur_line_at_largest_block += 1
                            print(f"\rMERGING PROGRESS:"
                                  f"{(cur_line_at_largest_block*200)//largest_lines_count}%", end='')
                        if cur_terms[min_index]:
                            cur_posting_lists[min_index] = json.loads(blocks[min_index].readline().rstrip('\n'))
        except IOError as e:
            print(f"Error while merging blocks: {e}")

    cpdef int docs_cnt(self):
        return len(self._documents_map)

    def __len__(self):
        return len(self._terms_posts)

    def get_document_filepath(self, int d_id):
        return self._documents_map[d_id]

    @cached(cache=LFUCache(maxsize=10))
    def get_document(self, d_id):
        with open(self.get_document_filepath(d_id), "r", encoding=_ENCODING) as f:
            return ''.join(f.readlines())

    cpdef str get_encoding(self):
        return _ENCODING

    cpdef tuple get_postring_tuples(self, str word):
        cdef:
            int left = 0
            int right = len(self._terms_posts) - 1
            int middle
            bytes term_bytes
            bytes posts_bytes
            str cur_term
            tuple term_post
            tuple next_term_post

        word = super_strip(word)
        with open(_indexTermsFilename, "rb") as ft, \
                open(_indexPostsFilename, "rb") as fp:
            while True:
                if right < left:
                    return tuple()

                middle = (left + right) // 2

                term_post = self._terms_posts[middle]
                ft.seek(term_post[0], 0)
                fp.seek(term_post[1], 0)

                if middle + 1 < len(self._terms_posts):
                    next_term_post = self._terms_posts[middle + 1]

                    term_bytes = ft.read(next_term_post[0] - term_post[0])
                    posts_bytes = fp.read(next_term_post[1] - term_post[1])
                else:
                    # read to the end
                    term_bytes = ft.read(-1)
                    posts_bytes = fp.read(-1)

                cur_term = term_bytes.decode(_ENCODING)

                if word < cur_term:
                    right = middle - 1
                elif word > cur_term:
                    left = middle + 1
                else:
                    return _decompress_posting_list(posts_bytes)

    def __contains__(self, str item):
        return len(self.get_postring_tuples(item)) > 0

    def __sizeof__(self):
        return self._terms_posts.__sizeof__()

    def total_size(self):
        total_size = self.__sizeof__() \
                     + os.path.getsize(_indexTermsFilename) \
                     + os.path.getsize(_indexPostsFilename)
        print(f"TotalSize: {total_size}")
        print(f"IndexTerms: {os.path.getsize(_indexTermsFilename)}")
        print(f"IndexPosts: {os.path.getsize(_indexPostsFilename)}")
        return total_size

    def remove_temp_files(self):
        if os.path.exists(_tempPath):
            shutil.rmtree(_tempPath)
