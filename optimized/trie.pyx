cdef class Node:
    cdef dict hashMap
    cdef str ch
    cdef set _ids

    def __init__(Node self, str ch):
        self.ch = ch
        self.hashMap = dict()
        self._ids = set()

    cpdef set ids(Node self):
        return self._ids

    def __sizeof__(self):
        return self.hashMap.__sizeof__() + self.ch.__sizeof__() + self._ids.__sizeof__()

cdef class TrieDictionary:
    cdef Node root
    cdef bint revers

    def __init__(TrieDictionary self, bint revers = False):
        self.root = Node('\0')
        self.revers = revers

    cpdef add_word(TrieDictionary self, str word, int doc_id):
        if self.revers:
            word = word[::-1]
        cdef Node cur_node
        cur_node = self.root
        cdef:
            int i
            str ch
            bint last
        for i, ch in enumerate(word):
            last = i + 1 == len(word)
            cur_node = self.add_char(cur_node, ch, doc_id if last else -1)

    cdef Node add_char(TrieDictionary self, Node node, str ch, int doc_id):
        cdef Node needed_branch
        try:
            needed_branch = <Node>node.hashMap[ch]
        except KeyError:
            needed_branch = node.hashMap[ch] = Node(ch)
        if doc_id != -1:
            needed_branch.ids().add(doc_id)
        return needed_branch

    cpdef has_word(TrieDictionary self, str word):
        cdef Node node
        node = self.get(word)
        return node is None and len(node.ids()) > 0

    cpdef Node get(TrieDictionary self, str word):
        if self.revers:
            word = word[::-1]
        cdef Node node
        node = self.root
        cdef str ch
        for ch in word:
            if ch in node.hashMap:
                node = node.hashMap[ch]
            else:
                return None
        return node

    cpdef int count_words(TrieDictionary self):
        return self._count_words(self.root)

    cdef int _count_words(TrieDictionary self, Node node):
        if node is None:
            return 0
        cdef int cnt
        cnt = 0
        if len(node.ids()) > 0:
            cnt += 1
        cdef Node n
        for n in node.hashMap.values():
            cnt += self._count_words(n)
        return cnt

    cpdef dict query(TrieDictionary self, str query):
        return self.collect_words(query, self.get(query))

    cdef dict collect_words(TrieDictionary self, str start_string, Node node):
        cdef dict words
        words = {}
        if len(start_string) > 0:
            self.collect_words_part(node, words, start_string[:-1])
        return words

    cdef collect_words_part(TrieDictionary self, Node node, dict word_dict, str current_word):
        if node is None:
            return

        current_word += node.ch

        if len(node.ids()) > 0:
            word_dict[current_word] = set(node.ids())

        cdef Node n
        for n in node.hashMap.values():
            self.collect_words_part(n, word_dict, current_word)

    def __sizeof__(self):
        return self.root.__sizeof__()
