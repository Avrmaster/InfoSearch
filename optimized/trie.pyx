cdef class Node:
    cdef dict hashMap
    cdef str ch
    cdef bint is_complete
    cdef list ids

    def __init__(Node self, str ch):
        self.ch = ch
        self.hashMap = dict()
        self.is_complete = False

    def is_completed(Node self):
        return self.is_complete

    def set_completed(Node self, bint is_complete):
        self.is_complete = is_complete

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
        cdef int i
        cdef str ch
        for i, ch in enumerate(word):
            cur_node = self.add_char(cur_node, ch, i + 1 == len(word))

    cdef Node add_char(TrieDictionary self, Node node, str ch, bint is_final):
        cdef Node needed_branch
        try:
            needed_branch = <Node>node.hashMap[ch]
        except KeyError:
            needed_branch = node.hashMap[ch] = Node(ch)
        needed_branch.set_completed(needed_branch.is_completed() or is_final)
        return needed_branch

    cpdef has_word(TrieDictionary self, str word):
        cdef Node node
        node = self.get(word)
        return node is None and node.is_completed()

    cpdef Node get(TrieDictionary self, str word):
        if self.revers:
            word = word[::-1]
        cdef Node node
        node = self.root
        cdef str ch
        for ch in word:
            node = node.hashMap.get(ch, None)
            if node is None:
                return None
        return node

    cpdef str query(TrieDictionary self, str query, int max_cnt):
        return self.collect_words(query, self.get(query), max_cnt)

    cpdef int count_words(TrieDictionary self):
        return self._count_words(self.root)

    cpdef int _count_words(TrieDictionary self, Node node):
        if node is None:
            return 0
        cdef int cnt
        cnt = 0
        if node.is_complete:
            cnt += 1
        cdef Node n
        for n in node.hashMap.values():
            cnt += self._count_words(n)
        return cnt

    cdef list collect_words(TrieDictionary self, str start_string, Node node, int max_cnt):
        cdef list words
        words = []
        if len(start_string) > 0:
            self.collect_words_part(node, words, start_string[:-1], max_cnt)
        return words

    cpdef collect_words_part(TrieDictionary self, Node node, list word_list, str current_word, int max_cnt):
        if len(word_list) >= max_cnt or node is None:
            return

        current_word += node.ch

        if node.is_complete:
            word_list.append(current_word)

        cdef Node n
        for n in node.hashMap.values():
            if len(word_list) < max_cnt:
                self.collect_words_part(n, word_list, current_word, max_cnt)


                # static public class SearchResult {
                #         public final bint wordExists;
                #         public final List<String> suggestions;
                #
                #         private SearchResult(bint isWord) {
                #             this.wordExists = isWord;
                #             this.suggestions = new LinkedList<>();
                #         }
                #
                #         private SearchResult(bint isWord, List<String> suggestions) {
                #             this.wordExists = isWord;
                #             this.suggestions = suggestions;
                #         }
                #     }
                #
                #     public SearchResult queryWord(String word) {
                #         List<String> suggestions = new LinkedList<>();
                #         bint exists = hasWord(word);
                #         for (String s : query(word, MAX_SUGGESTIONS_COUNT)) {
                #             suggestions.add(s);
                #         }
                #         return new SearchResult(exists, suggestions);
                #     }
                #
                # }
