from utils.regex import clear_query, get_query_terms
from typing import List
from optimized.spimi.dictionary import Dictionary
from math import log


class Search:
    def execute(self, query: str) -> set:
        raise NotImplementedError


class BooleanSearch(Search):
    def __init__(self, d: Dictionary):
        self._all = set(i for i in range(d.docs_cnt()))
        self._d = d

    def ranked_execute(self, query: str) -> set:
        N = self._d.docs_cnt()
        suitable_documents = self.execute(query)
        print(f"Suitable documents: {suitable_documents}")

        for term in get_query_terms(query):
            print(f"Analyzing {term}")
            terms_documents = tuple(t for t in self._d.get_postring_tuples(term) if t[0] in suitable_documents)
            print(f"Occurs is documents with frequencies: {terms_documents}")
            idfs = tuple(log(N / td[1]) for td in terms_documents)
            print(f"IDFs: {idfs}")
            tf_idfs = tuple(td[1] * idf for td, idf in zip(terms_documents, idfs))
            print(f"tf_idfs: {tf_idfs}")

        return suitable_documents

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
