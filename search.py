import re
from typing import List

from optimized.dictionary import Dictionary


class Search:
    def execute(self, query: str) -> set:
        raise NotImplementedError


class BooleanSearch(Search):
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


class PhraseSearch(Search):
    def __init__(self, d: Dictionary):
        self._dictionary = d
        self._sub_ex = re.compile("[^\w']+")

    def execute(self, query: str) -> set:
        if ' ' in query:
            query = query.lower()
            parts = query.split(' ')
            print(f"Parts: {parts}")
            res = self._dictionary.get_ids(parts[0])
            for i in range(1, len(parts)):
                res.intersection_update(self._dictionary.get_sequence_ids(parts[i-1], parts[i]))

            final_res = set()
            paragraphs = [(pid, self._sub_ex.sub(self._dictionary.get_paragraph(pid), ' ').lower()) for pid in res]
            for pid, text in paragraphs:
                if query in text:
                    final_res.add(pid)
            return final_res
        else:
            return self._dictionary.get_ids(query)
