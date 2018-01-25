from dictionary import Dictionary
from typing import List


class BooleanSearch:
    def __init__(self, d: Dictionary):
        self._d = d
        pass

    def execute(self, query: str) -> List[int]:
        print(f"Q: {query}")
        return []
