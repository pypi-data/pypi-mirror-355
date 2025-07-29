"""
Data Structures and Algorithms Module
Created by super smart Financial University student Andrew(dron)Sitalo
"""


class Module:
    def __init__(self):
        pass

    def selection_sort(self,arr):
        """
        n = len(arr)
        for i in range(n):
            min_idx = i
            for j in range(i+1, n):
                if arr[j] < arr[min_idx]:
                    min_idx = j
            arr[i], arr[min_idx] = arr[min_idx], arr[i]
        return arr

        :param arr:
        :return:
        """
        return 0



    # Алгоритмы сортировки
    def bubble_sort(self, arr):
        """
        Сортировка пузырьком

        Код:
        n = len(arr)
        for i in range(n):
            for j in range(0, n-i-1):
                if arr[j] > arr[j+1]:
                    arr[j], arr[j+1] = arr[j+1], arr[j]
        return arr

        :param arr: список для сортировки
        :return: отсортированный список
        """
        return 0

    def insertion_sort(self, arr):
        """
        Сортировка вставками

        Код:
        for i in range(1, len(arr)):
            key = arr[i]
            j = i-1
            while j >= 0 and key < arr[j]:
                arr[j+1] = arr[j]
                j -= 1
            arr[j+1] = key
        return arr

        :param arr: список для сортировки
        :return: отсортированный список
        """
        return 0

    def quick_sort(self, arr):
        """
        Быстрая сортировка

        Код:
        if len(arr) <= 1:
            return arr
        pivot = arr[len(arr)//2]
        left = [x for x in arr if x < pivot]
        middle = [x for x in arr if x == pivot]
        right = [x for x in arr if x > pivot]
        return self.quick_sort(left) + middle + self.quick_sort(right)

        :param arr: список для сортировки
        :return: отсортированный список
        """
        return 0

    # Структуры данных
    class Stack:
        """
        Реализация стека (LIFO)

        Полный код класса:
        def __init__(self):
            self.items = []

        def push(self, item):
            self.items.append(item)

        def pop(self):
            if not self.is_empty():
                return self.items.pop()
            return None

        def peek(self):
            if not self.is_empty():
                return self.items[-1]
            return None

        def is_empty(self):
            return len(self.items) == 0

        def size(self):
            return len(self.items)
        """

        def __init__(self):
            self.items = []

        def push(self, item):
            """self.items.append(item)"""
            return 0

        def pop(self):
            """
            if not self.is_empty():
                return self.items.pop()
            return None
            """
            return 0

        def peek(self):
            """
            if not self.is_empty():
                return self.items[-1]
            return None
            """
            return 0

        def is_empty(self):
            """return len(self.items) == 0"""
            return 0

        def size(self):
            """return len(self.items)"""
            return 0

    class Queue:
        """
        Реализация очереди (FIFO)

        Полный код класса:
        def __init__(self):
            self.items = []

        def enqueue(self, item):
            self.items.insert(0, item)

        def dequeue(self):
            if not self.is_empty():
                return self.items.pop()
            return None

        def is_empty(self):
            return len(self.items) == 0

        def size(self):
            return len(self.items)
        """

        def __init__(self):
            self.items = []

        def enqueue(self, item):
            """self.items.insert(0, item)"""
            return 0

        def dequeue(self):
            """
            if not self.is_empty():
                return self.items.pop()
            return None
            """
            return 0

        def is_empty(self):
            """return len(self.items) == 0"""
            return 0

        def size(self):
            """return len(self.items)"""
            return 0

    class LinkedList:
        """
        Реализация односвязного списка

        Полный код класса:
        class Node:
            __slots__ = 'data', 'next'
            def __init__(self, data):
                self.data = data
                self.next = None

        def __init__(self):
            self.head = None

        def append(self, data):
            new_node = self.Node(data)
            if not self.head:
                self.head = new_node
                return
            last = self.head
            while last.next:
                last = last.next
            last.next = new_node

        def prepend(self, data):
            new_node = self.Node(data)
            new_node.next = self.head
            self.head = new_node

        def delete(self, key):
            current = self.head
            if current and current.data == key:
                self.head = current.next
                return
            prev = None
            while current and current.data != key:
                prev = current
                current = current.next
            if current:
                prev.next = current.next

        def display(self):
            elements = []
            current = self.head
            while current:
                elements.append(current.data)
                current = current.next
            return elements
        """

        class Node:
            __slots__ = 'data', 'next'

            def __init__(self, data):
                self.data = data
                self.next = None

        def __init__(self):
            self.head = None

        def append(self, data):
            """
            new_node = self.Node(data)
            if not self.head:
                self.head = new_node
                return
            last = self.head
            while last.next:
                last = last.next
            last.next = new_node
            """
            return 0

        def prepend(self, data):
            """
            new_node = self.Node(data)
            new_node.next = self.head
            self.head = new_node
            """
            return 0

        def delete(self, key):
            """
            current = self.head
            if current and current.data == key:
                self.head = current.next
                return
            prev = None
            while current and current.data != key:
                prev = current
                current = current.next
            if current:
                prev.next = current.next
            """
            return 0

        def display(self):
            """
            elements = []
            current = self.head
            while current:
                elements.append(current.data)
                current = current.next
            return elements
            """
            return 0

    class DoublyLinkedList:
        """
        Реализация двусвязного списка

        Полный код класса:
        class Node:
            __slots__ = 'data', 'prev', 'next'
            def __init__(self, data):
                self.data = data
                self.prev = None
                self.next = None

        def __init__(self):
            self.head = None

        def append(self, data):
            new_node = self.Node(data)
            if not self.head:
                self.head = new_node
                return
            last = self.head
            while last.next:
                last = last.next
            last.next = new_node
            new_node.prev = last

        def prepend(self, data):
            new_node = self.Node(data)
            if self.head:
                self.head.prev = new_node
            new_node.next = self.head
            self.head = new_node

        def delete(self, key):
            current = self.head
            while current:
                if current.data == key:
                    if current.prev:
                        current.prev.next = current.next
                    else:
                        self.head = current.next
                    if current.next:
                        current.next.prev = current.prev
                    return
                current = current.next

        def display(self):
            elements = []
            current = self.head
            while current:
                elements.append(current.data)
                current = current.next
            return elements
        """

        class Node:
            __slots__ = 'data', 'prev', 'next'

            def __init__(self, data):
                self.data = data
                self.prev = None
                self.next = None

        def __init__(self):
            self.head = None

        def append(self, data):
            """
            new_node = self.Node(data)
            if not self.head:
                self.head = new_node
                return
            last = self.head
            while last.next:
                last = last.next
            last.next = new_node
            new_node.prev = last
            """
            return 0

        def prepend(self, data):
            """
            new_node = self.Node(data)
            if self.head:
                self.head.prev = new_node
            new_node.next = self.head
            self.head = new_node
            """
            return 0

        def delete(self, key):
            """
            current = self.head
            while current:
                if current.data == key:
                    if current.prev:
                        current.prev.next = current.next
                    else:
                        self.head = current.next
                    if current.next:
                        current.next.prev = current.prev
                    return
                current = current.next
            """
            return 0

        def display(self):
            """
            elements = []
            current = self.head
            while current:
                elements.append(current.data)
                current = current.next
            return elements
            """
            return 0

    class CircularDoublyLinkedList:
        """
        Реализация циклического двусвязного списка

        Полный код класса:
        class Node:
            __slots__ = 'data', 'prev', 'next'
            def __init__(self, data):
                self.data = data
                self.prev = None
                self.next = None

        def __init__(self):
            self.head = None

        def append(self, data):
            new_node = self.Node(data)
            if not self.head:
                self.head = new_node
                new_node.next = new_node
                new_node.prev = new_node
            else:
                last = self.head.prev
                last.next = new_node
                new_node.prev = last
                new_node.next = self.head
                self.head.prev = new_node

        def display(self):
            if not self.head:
                return []
            elements = []
            current = self.head
            while True:
                elements.append(current.data)
                current = current.next
                if current == self.head:
                    break
            return elements
        """

        class Node:
            __slots__ = 'data', 'prev', 'next'

            def __init__(self, data):
                self.data = data
                self.prev = None
                self.next = None

        def __init__(self):
            self.head = None

        def append(self, data):
            """
            new_node = self.Node(data)
            if not self.head:
                self.head = new_node
                new_node.next = new_node
                new_node.prev = new_node
            else:
                last = self.head.prev
                last.next = new_node
                new_node.prev = last
                new_node.next = self.head
                self.head.prev = new_node
            """
            return 0

        def display(self):
            """
            if not self.head:
                return []
            elements = []
            current = self.head
            while True:
                elements.append(current.data)
                current = current.next
                if current == self.head:
                    break
            return elements
            """
            return 0

    class BinaryTree:
        """
        Реализация бинарного дерева

        Полный код класса:
        class Node:
            __slots__ = 'data', 'left', 'right'
            def __init__(self, data):
                self.data = data
                self.left = None
                self.right = None

        def __init__(self):
            self.root = None

        def insert(self, data):
            if not self.root:
                self.root = self.Node(data)
                return
            queue = [self.root]
            while queue:
                node = queue.pop(0)
                if not node.left:
                    node.left = self.Node(data)
                    return
                else:
                    queue.append(node.left)
                if not node.right:
                    node.right = self.Node(data)
                    return
                else:
                    queue.append(node.right)

        def inorder(self, node):
            return (self.inorder(node.left) + [node.data] + self.inorder(node.right)) if node else []

        def display(self):
            return self.inorder(self.root)
        """

        class Node:
            __slots__ = 'data', 'left', 'right'

            def __init__(self, data):
                self.data = data
                self.left = None
                self.right = None

        def __init__(self):
            self.root = None

        def insert(self, data):
            """
            if not self.root:
                self.root = self.Node(data)
                return
            queue = [self.root]
            while queue:
                node = queue.pop(0)
                if not node.left:
                    node.left = self.Node(data)
                    return
                else:
                    queue.append(node.left)
                if not node.right:
                    node.right = self.Node(data)
                    return
                else:
                    queue.append(node.right)
            """
            return 0

        def inorder(self, node):
            """
            return (self.inorder(node.left) + [node.data] + self.inorder(node.right)) if node else []
            """
            return 0

        def display(self):
            """
            return self.inorder(self.root)
            """
            return 0

    class BinarySearchTree:
        """
        Реализация бинарного дерева поиска (BST)

        Полный код класса:
        class Node:
            __slots__ = 'data', 'left', 'right'
            def __init__(self, data):
                self.data = data
                self.left = None
                self.right = None

        def __init__(self):
            self.root = None

        def insert(self, data):
            if not self.root:
                self.root = self.Node(data)
                return

            current = self.root
            while True:
                if data < current.data:
                    if current.left is None:
                        current.left = self.Node(data)
                        return
                    current = current.left
                else:
                    if current.right is None:
                        current.right = self.Node(data)
                        return
                    current = current.right

        def search(self, data):
            current = self.root
            while current:
                if data == current.data:
                    return True
                elif data < current.data:
                    current = current.left
                else:
                    current = current.right
            return False

        def inorder(self, node):
            return (self.inorder(node.left) + [node.data] + self.inorder(node.right)) if node else []

        def display(self):
            return self.inorder(self.root)
        """

        class Node:
            __slots__ = 'data', 'left', 'right'

            def __init__(self, data):
                self.data = data
                self.left = None
                self.right = None

        def __init__(self):
            self.root = None

        def insert(self, data):
            """
            if not self.root:
                self.root = self.Node(data)
                return

            current = self.root
            while True:
                if data < current.data:
                    if current.left is None:
                        current.left = self.Node(data)
                        return
                    current = current.left
                else:
                    if current.right is None:
                        current.right = self.Node(data)
                        return
                    current = current.right
            """
            return 0

        def search(self, data):
            """
            current = self.root
            while current:
                if data == current.data:
                    return True
                elif data < current.data:
                    current = current.left
                else:
                    current = current.right
            return False
            """
            return 0

        def inorder(self, node):
            """
            return (self.inorder(node.left) + [node.data] + self.inorder(node.right)) if node else []
            """
            return 0

        def display(self):
            """
            return self.inorder(self.root)
            """
            return 0

    class HashTable:
        """
        Реализация хэш-таблицы с цепочками

        Полный код класса:
        def __init__(self, size=10):
            self.size = size
            self.table = [[] for _ in range(size)]

        def _hash(self, key):
            return hash(key) % self.size

        def insert(self, key, value):
            index = self._hash(key)
            for kv in self.table[index]:
                if kv[0] == key:
                    kv[1] = value
                    return
            self.table[index].append([key, value])

        def get(self, key):
            index = self._hash(key)
            for kv in self.table[index]:
                if kv[0] == key:
                    return kv[1]
            return None

        def delete(self, key):
            index = self._hash(key)
            for i, kv in enumerate(self.table[index]):
                if kv[0] == key:
                    del self.table[index][i]
                    return

        def display(self):
            return [[kv for kv in bucket] for bucket in self.table if bucket]
        """

        def __init__(self, size=10):
            self.size = size
            self.table = [[] for _ in range(size)]

        def _hash(self, key):
            """return hash(key) % self.size"""
            return 0

        def insert(self, key, value):
            """
            index = self._hash(key)
            for kv in self.table[index]:
                if kv[0] == key:
                    kv[1] = value
                    return
            self.table[index].append([key, value])
            """
            return 0

        def get(self, key):
            """
            index = self._hash(key)
            for kv in self.table[index]:
                if kv[0] == key:
                    return kv[1]
            return None
            """
            return 0

        def delete(self, key):
            """
            index = self._hash(key)
            for i, kv in enumerate(self.table[index]):
                if kv[0] == key:
                    del self.table[index][i]
                    return
            """
            return 0

        def display(self):
            """return [[kv for kv in bucket] for bucket in self.table if bucket]"""
            return 0

    class Heap:
        """
        Реализация min-heap

        Полный код класса:
        def __init__(self):
            self.heap = []

        def parent(self, i):
            return (i-1)//2

        def left_child(self, i):
            return 2*i + 1

        def right_child(self, i):
            return 2*i + 2

        def insert(self, value):
            self.heap.append(value)
            self._sift_up(len(self.heap)-1)

        def _sift_up(self, i):
            while i > 0 and self.heap[i] < self.heap[self.parent(i)]:
                parent_idx = self.parent(i)
                self.heap[i], self.heap[parent_idx] = self.heap[parent_idx], self.heap[i]
                i = parent_idx

        def extract_min(self):
            if not self.heap:
                return None
            min_val = self.heap[0]
            self.heap[0] = self.heap[-1]
            self.heap.pop()
            self._sift_down(0)
            return min_val

        def _sift_down(self, i):
            min_index = i
            l = self.left_child(i)
            r = self.right_child(i)

            if l < len(self.heap) and self.heap[l] < self.heap[min_index]:
                min_index = l

            if r < len(self.heap) and self.heap[r] < self.heap[min_index]:
                min_index = r

            if i != min_index:
                self.heap[i], self.heap[min_index] = self.heap[min_index], self.heap[i]
                self._sift_down(min_index)

        def display(self):
            return self.heap
        """

        def __init__(self):
            self.heap = []

        def parent(self, i):
            """return (i-1)//2"""
            return 0

        def left_child(self, i):
            """return 2*i + 1"""
            return 0

        def right_child(self, i):
            """return 2*i + 2"""
            return 0

        def insert(self, value):
            """
            self.heap.append(value)
            self._sift_up(len(self.heap)-1)
            """
            return 0

        def _sift_up(self, i):
            """
            while i > 0 and self.heap[i] < self.heap[self.parent(i)]:
                parent_idx = self.parent(i)
                self.heap[i], self.heap[parent_idx] = self.heap[parent_idx], self.heap[i]
                i = parent_idx
            """
            return 0

        def extract_min(self):
            """
            if not self.heap:
                return None
            min_val = self.heap[0]
            self.heap[0] = self.heap[-1]
            self.heap.pop()
            self._sift_down(0)
            return min_val
            """
            return 0

        def _sift_down(self, i):
            """
            min_index = i
            l = self.left_child(i)
            r = self.right_child(i)

            if l < len(self.heap) and self.heap[l] < self.heap[min_index]:
                min_index = l

            if r < len(self.heap) and self.heap[r] < self.heap[min_index]:
                min_index = r

            if i != min_index:
                self.heap[i], self.heap[min_index] = self.heap[min_index], self.heap[i]
                self._sift_down(min_index)
            """
            return 0

        def display(self):
            """return self.heap"""
            return 0