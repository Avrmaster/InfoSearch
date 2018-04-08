from itertools import chain
from glob import glob
import os
from cachetools import cached, LFUCache


@cached(cache=LFUCache(maxsize=2))
def get_all_files(directory: str, extension: str = "txt"):
    return iter(chain.from_iterable(glob(os.path.join(x[0], f'*.{extension}')) for x in os.walk(directory)))


@cached(cache=LFUCache(maxsize=2))
def get_total_files_size_in_directory(directory: str, extension: str = "txt"):
    return sum((os.path.getsize(f) for f in get_all_files(directory=directory, extension=extension)))
