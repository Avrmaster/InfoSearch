import re
from utils.regex import clear_query
from typing import List
from optimized.spimi.dictionary import Dictionary


class Search:
    def execute(self, query: str) -> set:
        raise NotImplementedError


class BooleanSearch(Search):
    def __init__(self, d: Dictionary):
        self._all = set(i for i in range(d.docs_cnt()))
        self._d = d

    def ranked_execute(self, query: str) -> set:
        suitable_documents = self.execute(query)

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
