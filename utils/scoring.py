from typing import NamedTuple, Tuple, List
import xml.etree.cElementTree as ET


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
                    title = line[line.index(_title_str) + len(_title_str):]
                except ValueError:
                    title = line
            elif _author_str in line:
                author = line[line.index(_author_str) + len(_author_str):]
            if (title and author) or i > _max_read_lines:
                break
    return MetaData(filepath=filepath, title=title.strip(), author=author.strip())


def process_fb2(filepath: str) -> Tuple[List[str], MetaData]:
    """
    :param filepath: an absolute path to fb2 file
    :return: body and doc Metadata
    """
    try:
        tree = ET.ElementTree(file=filepath)
        root_tag = tree.getroot().tag
        xmlns = root_tag[root_tag.find('{'):root_tag.find('}') + 1]

        title = None
        title_tag = f"{xmlns}book-title"

        author = None
        author_tag = f"{xmlns}author"
        first_name_tag = f"{xmlns}first-name"
        last_name_tag = f"{xmlns}last-name"

        tag_bodies = []
        body_tag = f"{xmlns}p"

        for elem in tree.iter():
            if elem.tag == body_tag and elem.text is not None:
                tag_bodies.append(elem.text)
            elif elem.tag == title_tag and title is None:
                title = elem.text if elem.text is not None else "Not specified"
            elif elem.tag == author_tag and author is None:

                first_name_el = elem.find(first_name_tag)
                last_name_el = elem.find(last_name_tag)
                if first_name_el is None and last_name_el is None:
                    continue

                first_name, last_name = (first_name_el.text, last_name_el.text)

                if first_name is None and last_name is None:
                    author = "Not specified"
                elif first_name is None:
                    author = last_name
                elif last_name is None:
                    author = first_name
                else:
                    author = "{} {}".format(first_name, last_name)

        return tag_bodies, MetaData(filepath=filepath, title=title, author=author)
    except Exception:
        return [], MetaData(filepath=filepath, title="Broken file", author="Broken file")
