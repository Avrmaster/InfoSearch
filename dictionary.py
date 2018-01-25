class Dictionary:
    def __init__(self):
        super().__init__()
        self._d = dict()
        self._size = 0
        self._documents = set()

    def add_word(self, w: str, ind: int):
        s = self._d[w] = self._d.get(w, set())
        s.add(ind)
        self._documents.add(ind)
        self._size = len(self._d)
        return self

    def all_documents(self):
        return sorted(self._documents)

    def __contains__(self, item):
        return item in self._d

    def __iter__(self):
        return iter(self._d.items())

    def __len__(self):
        return self._size

    def __sizeof__(self):
        return self._d.__sizeof__()

    def __str__(self):
        printables = []
        for i, item in enumerate(self._d.items()):
            word, indexes = item
            to_print = f'{word}: {sorted(indexes)}'
            length = len(to_print)
            printables.append(to_print + ' ' * (65 - length) + ('\n' if i % 3 == 2 else ''))
        return ''.join(printables)
