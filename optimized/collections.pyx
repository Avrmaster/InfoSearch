from libc.stdlib cimport malloc

cdef struct Node:
    long el
    Node*next

cdef class LongLinkedSet:
    cdef Node*_root

    # def __cinit__(LongLinkedSet self):
    #     self._root = NULL  # just to explicitly define

    cpdef long add(LongLinkedSet self, long new_el):
        """
        :param new_el: new longeger to add
        :return: 1 if element was added and 0 if it already was there
        """
        cdef Node* new_n
        new_node = <Node*> malloc(sizeof(Node))
        new_node.el = new_el

        if self._root == NULL:
            self._root = new_node
            return 1

        cdef Node* node
        node = self._root

        if self._root.el >= new_el:
            if self._root.el == new_el:
                return 0
            new_node.next = self._root
            self._root = new_node
            return 1

        while node.next != NULL and node.next.el < new_el:
            node = node.next

        if node.next == NULL or node.next.el != new_el:
            new_node.next = node.next
            node.next = new_node
            return 1
        return 0

    cpdef LongLinkedSet union(LongLinkedSet self, LongLinkedSet another):
        cdef LongLinkedSet res
        res = LongLinkedSet()

        cdef long el
        cdef Node* cur
        cdef Node* left
        cdef Node* right
        cdef Node* new_n

        left = self._root
        right = another._root
        while left != NULL or right != NULL:
            if right == NULL or (left != NULL and left.el <= right.el):
                el = left.el
                left = left.next
            else:
                el = right.el
                right = right.next

            print(f"El: {el}")
            new_node = <Node*> malloc(sizeof(Node))
            new_node.el =el

            if cur == NULL:
                cur = res._root = new_n
            else:
                cur.next = new_n
                cur = new_n
        return res

    cpdef list get_all(LongLinkedSet self):
        cdef list a
        a = []
        cdef Node*node
        node = self._root
        while node != NULL:
            a.append(node.el)
            node = node.next
        return a

    def __str__(LongLinkedSet self):
        return self.get_all().__str__()
