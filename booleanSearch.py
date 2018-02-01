import re
from typing import List

from optimized.dictionary import Dictionary


class BooleanSearch:
    def __init__(self, d: Dictionary):
        self._all = set(i for i in range(d.docs_cnt()))
        self._d = d
        self._sub_ex = re.compile('[\w~]( +)[\w~]')

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

        for m in self._sub_ex.finditer(query):
            query = query[:m.span(1)[0]]+'&'+query[m.span(1)[1]:]

        query = f'(|{query})'

        # print(f"executing {query}")

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
                operands.append(self._d.get_ids(w))
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
