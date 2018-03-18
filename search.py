import operator

from utils.regex import clear_query, get_query_terms
from optimized.spimi.dictionary import Dictionary
from utils.scoring import extract_metadata
from itertools import chain
from typing import List
from math import log


class Search:
    def execute(self, query: str) -> set:
        raise NotImplementedError


class BooleanSearch(Search):
    def __init__(self, d: Dictionary):
        self._all = set(i for i in range(d.docs_cnt()))
        self._d = d

    def ranked_execute(self, query: str) -> tuple:
        N = self._d.docs_cnt()
        suitable_documents = self.execute(query)
        # metadata = tuple(chain.from_iterable(tuple((mtd.title, mtd.author) for mtd in
        #                                            (extract_metadata(self._d.get_document_filepath(d_id),
        #                                                              self._d.get_encoding())
        #                                             for d_id in suitable_documents))))
        metadata = tuple(
            (t[0], t[1].title, t[1].author) for t in (((d_id, extract_metadata(
                self._d.get_document_filepath(d_id),
                self._d.get_encoding())) for d_id in suitable_documents)))

        print(f"Suitable documents: {suitable_documents}")
        print(f"Their metadata: {metadata}")

        scores = {d: 0 for d in suitable_documents}
        for term in get_query_terms(query):
            print(f"Analyzing {term}")
            term_documents = tuple(t for t in self._d.get_postring_tuples(term) if t[0] in suitable_documents)
            print(f"Occurs is documents' with frequencies: {term_documents}")
            try:
                idf = log(N / len(self._d.get_postring_tuples(term)))
            except ZeroDivisionError:
                # word is not present in any of the documents.
                # It could happen since query engine supports negotion operator
                continue
            print(f"IDF: {idf}")
            tf_idfs = tuple((term_doc[0], term_doc[1] * idf) for term_doc in term_documents)
            print(f"tf_idfs: {tf_idfs}")
            for doc_id, tf_score in tf_idfs:
                scores[doc_id] += tf_score

            term_metadatas = tuple(t for t in metadata if term in list(chain(t[1])))
            print(f"Occurs in metadatas' {term_metadatas}")
            try:
                metadata_idf = log(len(metadata) / len(term_metadatas))
                metadata_tf_idfs = tuple((t[0], metadata_idf) for t in term_metadatas)
                print(f"Metadata idf: {metadata_idf}")
                print(f"Metadata tf-idf: {metadata_tf_idfs}")
                for doc_id, met_score in metadata_tf_idfs:
                    scores[doc_id] += met_score
            except ZeroDivisionError:
                # term is not in metadata. That's okay too
                continue
        print(f"Scores: {scores}")
        sorted_docs = tuple(d[0] for d in sorted(scores.items(), key=operator.itemgetter(1), reverse=True))
        print(f"Sorted doc_ids: {sorted_docs}")
        return sorted_docs

    def execute(self, query: str) -> set:
        """
        Find paragraphs that satisfy given query.
        Query can consist of words and symbols
        '|' for logical operator OR
        '&' for logical operator AND
        '~' for logical operator NOT (not supported yet)
        '(' with ')' for grouping elements
        A space between words is treated as AND
        :return: set of paragraphs' ids
        """
        try:
            query = clear_query(query)
            query = f'(|{query})'

            print(f"executing {query}")

            operators = []
            operands: List[set] = [set()]
            w = ''
            inverse_last = False
            for e in query:
                if e == ' ':
                    continue
                if e == '~':
                    inverse_last = not inverse_last
                if e in ('&', '|', '(', ')') and len(w) > 0:
                    operands.append(set((t[0] for t in self._d.get_postring_tuples(w))))
                    if inverse_last:
                        operands.append(self._all.difference(operands.pop()))
                        inverse_last = False
                    w = ''
                if e in ('&', '|', '(', '~'):
                    operators.append(e)
                elif e == ')':
                    for o in reversed(operators):
                        if o == '(':
                            break
                        if o == '&':
                            operands.append(operands.pop().intersection(operands.pop()))
                        elif o == '|':
                            operands.append(operands.pop().union(operands.pop()))
                else:
                    w += e

            return operands.pop()
        except Exception as e:
            print(f"Exception was caught during query execution: {e}")
            return set()
