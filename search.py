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
        except Exception as e:
            print(f"Exception was caught during query execution: {e}")
            return set()


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


class TrieJokerSearch(Search):
    def __init__(self, d: Dictionary):
        self._dictionary = d

    def execute(self, query: str) -> set:
        regex = re.compile(query.replace('*', '.*'))

        if '*' in query:
            start: str = query[:query.index('*')]
            end: str = query[query.rindex('*')+1:]

            if start and end:
                s_d: dict = self._dictionary.get_trie_dict(start)
                e_d: dict = self._dictionary.get_trie_dict(end, revers=True)
                common_keys = set(s_d.keys()).intersection(set(e_d.keys()))
                # print(f"Starts keys: {set(s_d.keys())}")
                # print(f"Ends keys: {set(e_d.keys())}")
                # print(f"Common keys: {set(common_keys)}")
                res_dict = {k: s_d[k].intersection(e_d[k]) for k in common_keys}
            else:
                res_dict = self._dictionary.get_trie_dict(start if start else end, len(start) == 0)

        else:
            res_dict = self._dictionary.get_trie_dict(query)

        res = set()
        for k, v in res_dict.items():
            if regex.match(k):
                print(f"Found word {k}")
                res = res.union(v)
        return res
