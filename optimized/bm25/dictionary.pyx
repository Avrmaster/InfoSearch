from __future__ import print_function
from gensim.summarization import bm25
import re
from heapq import nlargest
from utils.files import get_all_files

_ENCODING = "utf-8"
word_regex = r"[/w'-]+"

cdef class Dictionary:
    cdef:
        tuple document_paths
        object bm25_obj
        int avg_idf

    def __init__(self, str to_index_path, str extension = "txt"):
        corpus = []
        self.document_paths = tuple(get_all_files(to_index_path, extension))
        for i, filepath in enumerate(self.document_paths):
            print(f"\rIndexing {i+1}/{len(self.document_paths)}", end="")
            doc = []
            with open(filepath) as file:
                for line in file:
                    for word in re.findall(word_regex, line):
                        doc.append(word.lower())
            corpus.append(doc)
        self.bm25_obj = bm25.BM25(corpus=corpus)
        self.avg_idf = sum(map(lambda k: float(self.bm25_obj.idf[k]), self.bm25_obj.idf.keys())) / len(
            self.bm25_obj.idf.keys())

    def best(self, n: int, query_str: str):
        query_doc = [word.lower() for word in re.findall(word_regex, query_str)]
        scores = self.bm25_obj.get_scores(query_doc, self.avg_idf)
        doc_ids = [i for i in range(len(self.document_paths))]
        best_ids = nlargest(n, doc_ids, key=lambda i: scores[i])
        return [self.document_paths[doc_id] for doc_id in best_ids]

