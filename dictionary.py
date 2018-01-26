class Dictionary:
    def __init__(self):
        super().__init__()
        self._d = dict()
        self._docs_cnt = 0

    def add_word(self, w: str, ind: int):
        w = w.capitalize()
        s = self._d[w] = self._d.get(w, set())
        s.add(ind)
        self._docs_cnt = max(self._docs_cnt, ind+1)
        return self

    def get_ids(self, word: str) -> set:
        return self._d.get(word.capitalize(), set())

    def docs_cnt(self):
        return self._docs_cnt

    def __contains__(self, item):
        return item in self._d

    def __iter__(self):
        return iter(self._d.items())

    def __len__(self):
        return len(self._d)

    def __sizeof__(self):
        return self._d.__sizeof__()

    def __str__(self):
        printables = []
        for i, item in enumerate(self._d.items()):
            word, indexes = item
            info = f'in {len(indexes)} pars.'
            printables.append('<| ' + word + ' ' * (30 - len(word)) + info + ' |>' + ' ' * (30 - len(info)) +
                              ('\n' if i % 3 == 2 else ''))
        return ''.join(printables)
