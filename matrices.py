from dictionary import Dictionary
from typing import List
import numpy as np
np.set_printoptions(threshold=np.nan, linewidth=200)


class IncidenceMatrix:
    def __init__(self, d: Dictionary):
        self._matrix = [[i for i in range(d.docs_cnt())] for w in range(len(d))]
        self._words: List[str] = []
        for i, item in enumerate(d):
            word, doc_ids = item
            self._words.append(word)
            for j in doc_ids:
                self._matrix[i][j] = 1

    def __str__(self):
        return str(self._matrix)

    def __len__(self):
        return len(self._matrix)

    def __sizeof__(self):
        return self._matrix.__sizeof__() + sum([s.__sizeof__() for s in self._words])
