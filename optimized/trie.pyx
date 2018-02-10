cdef class Node:
    cdef char ch
    cdef char is_complete
    cdef dict hashMap

    def __init__(Node self, char ch):
        self.ch = ch
        self.hashMap = dict()

    def __str__(Node self):
        return "[" + self.ch + "] (" + self.is_complete + ")"

cdef class SearchDictionary:
    cdef Node root

    def __init__(SearchDictionary self, char ch):
        self.root = Node('\0')

    cpdef add_word(SearchDictionary self, str word):
        cdef Node cur_node
        cur_node = self.root
        cdef int i
        cdef str ch
        for i, ch in enumerate(word):
            cur_node = self.add_char(cur_node, ch, i + 1 == len(word))

    cdef Node add_char(SearchDictionary self, Node node, char ch, char is_final):
        cdef Node needed_branch
        needed_branch = node.hashMap.get(ch, None)
        if needed_branch is None:
            needed_branch = Node(ch)
            node.hashMap[ch] = Node
        needed_branch.is_complete |= is_final
        return needed_branch

    cpdef has_word(SearchDictionary self, str word):
        cdef Node node
        node = self.get(word)
        return node is None and node.is_complete

    cpdef Node get(SearchDictionary self, str word):
        cdef Node node
        node = self.root
        cdef str ch
        for ch in word:
            node = node.hashMap.get(ch, None)
            if node is None:
                return None
        return node

    cpdef str query(SearchDictionary self, str query, int max_cnt):
        return self.collect_words(query, self.get(query), max_cnt)

    cpdef int count_words(SearchDictionary self):
        return self._count_words(self.root)

    cpdef int _count_words(SearchDictionary self, Node node):
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

    cdef list collect_words(SearchDictionary self, str start_string, Node node, int max_cnt):
        cdef list words
        words = []
        if len(start_string) > 0:
            self.collect_words_part(node, words, start_string[:-1], max_cnt)
        return words

    cpdef collect_words_part(SearchDictionary self, Node node, list word_list, str current_word, int max_cnt):
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
                #         public final boolean wordExists;
                #         public final List<String> suggestions;
                #
                #         private SearchResult(boolean isWord) {
                #             this.wordExists = isWord;
                #             this.suggestions = new LinkedList<>();
                #         }
                #
                #         private SearchResult(boolean isWord, List<String> suggestions) {
                #             this.wordExists = isWord;
                #             this.suggestions = suggestions;
                #         }
                #     }
                #
                #     public SearchResult queryWord(String word) {
                #         List<String> suggestions = new LinkedList<>();
                #         boolean exists = hasWord(word);
                #         for (String s : query(word, MAX_SUGGESTIONS_COUNT)) {
                #             suggestions.add(s);
                #         }
                #         return new SearchResult(exists, suggestions);
                #     }
                #
                # }
