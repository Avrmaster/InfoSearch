import re
from typing import List
from itertools import chain
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
        """
        Find paragraphs that satisfy given query.
        Query must consist only of words separated by spaces.
        Only those paragraphs will be returned that contain the whole phrase
        :return: set of paragraphs' ids
        """
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


class PositionalSearch(Search):
    def __init__(self, d: Dictionary):
        self._dictionary = d
        self._sub_ex = re.compile(" +")

    def execute(self, query: str) -> set:
        """
        Find paragraphs that satisfy given query.
        Query must consist only of words separated with spaces
        Words (except first) may be replaced with asterisk *
        :return: set of paragraphs' ids
        """
        query = self._sub_ex.sub(' ', query).strip()

        if ' ' in query:
            parts = query.split(' ')

            # query_re_raw = query.replace('*', r"[\w'-]+").replace(' ', r"[^\w'-]+")
            # query_re = re.compile(query_re_raw, flags=re.IGNORECASE)
            # phrase_index = dict()
            # for part in parts:
            #     if part == '*':
            #         for key, value in phrase_index.items():
            #             phrase_index[key] = phrase_index[key].union(set(map(lambda l: l+1, value)))
            #     else:
            #         for key, value in self._dictionary.get_positions(part).items():
            #             if key not in phrase_index:
            #                 phrase_index[key] = value
            #             else:
            #                 phrase_index[key] = phrase_index[key].union(value)
            # res = set()
            # for key, value in phrase_index.items():
            #     locations = sorted(value)
            #     maximum = 1
            #     for i in range(1, len(locations)):
            #         if locations[i-1] + 1 == locations[i]:
            #             maximum += 1
            #             if maximum >= len(parts):
            #                 p: str = self._dictionary.get_paragraph(key)
            #                 if query_re.findall(p):
            #                     res.add(key)
            #                 break
            #         else:
            #             maximum = 1
            # return res

            # def get_locations(positions: dict) -> set:
            #     locations = set()
            #     for val in positions.values():
            #         for v in val:
            #             locations.add(v)
            #     return locations

            def filter_positions(last_part_positions: dict, new_part_positions: dict) -> dict:
                r = dict()
                for docId, locs in new_part_positions.items():
                    last_locations = last_part_positions.get(docId, None)
                    if last_locations is not None:
                        for l in locs:
                            if l-1 in last_locations:
                                s = r[docId] = r.get(docId, set())
                                s.add(l)
                return r

            last_positions: dict = None
            for part in parts:
                if part != '*':
                    if last_positions is None:
                        last_positions = self._dictionary.get_positions(part)
                    else:
                        last_positions = filter_positions(last_positions, self._dictionary.get_positions(part))
                else:
                    for doc_id, locations in last_positions.items():
                        last_positions[doc_id] = set(map(lambda l: l+1, locations))
            return set(last_positions.keys())
        else:
            return self._dictionary.get_ids(query)














