import os
from typing import NamedTuple


class MetaData(NamedTuple):
    filepath: str
    title: str
    author: str


def extract_metadata(filepath: str, encoding: str) -> MetaData:
    title = ""
    author = ""
    with open(filepath, "r", encoding=encoding) as f:
        for line in f:

            pass
    return MetaData(filepath=filepath, title=title, author=author)
