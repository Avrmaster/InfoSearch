from typing import NamedTuple


class MetaData(NamedTuple):
    filepath: str
    title: str
    author: str


_title_str = "Title:"
_author_str = "Author:"
_max_read_lines = 30


def extract_metadata(filepath: str, encoding: str) -> MetaData:
    title = ""
    author = ""
    with open(filepath, "r", encoding=encoding) as f:
        for i, line in enumerate(f):
            if i == 0 or _title_str in line:
                try:
                    title = line[line.index(_title_str)+len(_title_str):]
                except ValueError:
                    title = line
            elif _author_str in line:
                author = line[line.index(_author_str)+len(_author_str):]
            if (title and author) or i > _max_read_lines:
                break
    return MetaData(filepath=filepath, title=title.strip(), author=author.strip())
