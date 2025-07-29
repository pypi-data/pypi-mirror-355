"""Unit tests for AlgoZen package."""

import unittest
from algozen.data_structures import LinkedList, DoublyLinkedList, Stack, Queue, BST, AVLTree, HashTable, MinHeap, MaxHeap
from algozen.data_structures.advanced import SkipList, DisjointSet, Trie, FenwickTree, SegmentTree
from algozen.sorting import quick_sort, merge_sort, heap_sort
from algozen.searching import binary_search, linear_search, interpolation_search
from algozen.dynamic_programming import longest_common_subsequence, knapsack, edit_distance, matrix_chain_multiplication
from algozen.interview_prep import two_sum, longest_substring_without_repeating, merge_intervals, trap_rain_water
from algozen.system_design import RateLimiter, ConsistentHashing, BloomFilter
from algozen.design_patterns import Singleton, Observer, Strategy
from algozen.design_patterns_advanced import Flyweight, PriceSpecification

class TestDataStructures(unittest.TestCase):
    """Test cases for basic data structures."""
    
    def test_linked_list(self):
        ll = LinkedList()
        ll.append(1)
        ll.append(2)
        self.assertEqual(str(ll), '1 -> 2')
        self.assertEqual(len(ll), 2)
        
    def test_stack(self):
        stack = Stack()
        stack.push(1)
        stack.push(2)
        self.assertEqual(stack.pop(), 2)
        self.assertEqual(len(stack), 1)
        
    def test_queue(self):
        queue = Queue()
        queue.enqueue(1)
        queue.enqueue(2)
        self.assertEqual(queue.dequeue(), 1)
        self.assertEqual(len(queue), 1)
        
    def test_bst(self):
        bst = BST()
        bst.insert(5)
        bst.insert(3)
        bst.insert(7)
        self.assertTrue(bst.search(3))
        self.assertFalse(bst.search(4))

class TestAdvancedDataStructures(unittest.TestCase):
    """Test cases for advanced data structures."""

    def test_skip_list(self):
        skip_list = SkipList()
        skip_list.insert(5)
        skip_list.insert(10)
        self.assertTrue(skip_list.search(5))
        self.assertTrue(skip_list.search(10))
        self.assertFalse(skip_list.search(7))

    def test_trie(self):
        trie = Trie()
        trie.insert("hello")
        trie.insert("world")
        self.assertTrue(trie.search("hello"))
        self.assertTrue(trie.starts_with("hel"))
        self.assertFalse(trie.search("hell"))

    def test_disjoint_set(self):
        ds = DisjointSet(5)
        ds.union(0, 2)
        ds.union(4, 2)
        self.assertTrue(ds.connected(4, 0))
        self.assertFalse(ds.connected(1, 0))

class TestAlgorithms(unittest.TestCase):
    """Test cases for algorithms."""
    
    def test_sorting(self):
        arr = [64, 34, 25, 12, 22, 11, 90]
        sorted_arr = [11, 12, 22, 25, 34, 64, 90]
        self.assertEqual(quick_sort(arr.copy()), sorted_arr)
        self.assertEqual(merge_sort(arr.copy()), sorted_arr)
        self.assertEqual(heap_sort(arr.copy()), sorted_arr)
        
    def test_searching(self):
        arr = [11, 12, 22, 25, 34, 64, 90]
        self.assertEqual(binary_search(arr, 25), 3)
        self.assertEqual(linear_search(arr, 25), 3)
        self.assertIsNone(binary_search(arr, 13))
        
    def test_dynamic_programming(self):
        self.assertEqual(longest_common_subsequence("ABCDGH", "AEDFHR"), "ADH")
        self.assertEqual(edit_distance("kitten", "sitting"), 3)

class TestDesignPatterns(unittest.TestCase):
    """Test cases for design patterns."""

    def test_singleton(self):
        instance1 = Singleton()
        instance2 = Singleton()
        self.assertEqual(instance1, instance2)

    def test_observer(self):
        subject = Observer.Subject()
        observer = Observer.ConcreteObserver()
        subject.attach(observer)
        subject.state = 123
        self.assertEqual(observer.state, 123)

    def test_specification(self):
        price_spec = PriceSpecification(0, 100)
        self.assertTrue(price_spec.is_satisfied_by(50))
        self.assertFalse(price_spec.is_satisfied_by(150))

class TestSystemDesign(unittest.TestCase):
    """Test cases for system design components."""

    def test_rate_limiter(self):
        limiter = RateLimiter(capacity=2, window_size=1)
        self.assertTrue(limiter.allow_request())
        self.assertTrue(limiter.allow_request())
        self.assertFalse(limiter.allow_request())

    def test_bloom_filter(self):
        bf = BloomFilter(size=1000, hash_count=3)
        bf.add("test1")
        bf.add("test2")
        self.assertTrue(bf.might_contain("test1"))
        self.assertTrue(bf.might_contain("test2"))
        self.assertFalse(bf.might_contain("test3"))

class TestInterviewPrep(unittest.TestCase):
    """Test cases for interview preparation problems."""

    def test_two_sum(self):
        nums = [2, 7, 11, 15]
        target = 9
        self.assertEqual(two_sum(nums, target), [0, 1])

    def test_longest_substring(self):
        s = "abcabcbb"
        self.assertEqual(longest_substring_without_repeating(s), 3)

    def test_merge_intervals(self):
        intervals = [[1,3],[2,6],[8,10],[15,18]]
        expected = [[1,6],[8,10],[15,18]]
        self.assertEqual(merge_intervals(intervals), expected)

if __name__ == '__main__':
    unittest.main()