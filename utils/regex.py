from typing import Tuple
import re

_strip_ex = re.compile(r"[^\w'\-]|^['\-]+", flags=re.IGNORECASE)


def super_strip(word: str) -> str:
    return _strip_ex.sub("", word.lower())


_remove_non_words_ex = re.compile("[^\w'\-|~ ]", re.IGNORECASE)
_and_sub_ex = re.compile("[\w'\-]( +)[\w'\-]", re.IGNORECASE)
_remove_spaces = re.compile(" +", re.IGNORECASE)


def clear_query(query: str) -> str:
    query = _remove_non_words_ex.sub("", query)
    for m in _and_sub_ex.finditer(query):
        query = query[:m.span(1)[0]] + '&' + query[m.span(1)[1]:]
    return _remove_spaces.sub("", query)


_outline_terms_ex = re.compile("[\w'\-]+")


def get_query_terms(query: str) -> Tuple[str, ...]:
    return tuple(query[t.start():t.end()] for t in _outline_terms_ex.finditer(query))
