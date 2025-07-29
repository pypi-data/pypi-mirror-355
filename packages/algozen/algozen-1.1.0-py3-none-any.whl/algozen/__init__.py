"""AlgoZen - Efficient Data Structures and Algorithms Implementation

This module provides a collection of optimized data structures and algorithms
to help developers solve complex problems with minimal code.
"""

__version__ = '1.1.0'
__author__ = 'AlgoZen Team'
__email__ = 'info@algozen.dev'

from .data_structures import (
    LinkedList,
    DoublyLinkedList,
    BinaryTree,
    BST,
    AVLTree,
    HashTable,
    MinHeap,
    MaxHeap,
    Stack,
    Queue
)

from .data_structures.advanced import (
    SkipList,
    DisjointSet,
    Trie,
    FenwickTree,
    SegmentTree
)

from .sorting import (
    quick_sort,
    merge_sort,
    heap_sort
)

from .searching import (
    binary_search,
    linear_search,
    interpolation_search
)

from .dynamic_programming import (
    longest_common_subsequence,
    knapsack,
    edit_distance,
    matrix_chain_multiplication
)

from .interview_prep import (
    two_sum,
    longest_substring_without_repeating,
    merge_intervals,
    trap_rain_water
)

from .system_design import (
    RateLimiter,
    ConsistentHashing,
    BloomFilter
)

from .design_patterns import (
    Singleton,
    Observer,
    Strategy
)

from .design_patterns_advanced import (
    Flyweight,
    Specification
)

__all__ = [
    # Data Structures
    'LinkedList',
    'DoublyLinkedList',
    'BinaryTree',
    'BST',
    'AVLTree',
    'HashTable',
    'MinHeap',
    'MaxHeap',
    'Stack',
    'Queue',
    
    # Advanced Data Structures
    'SkipList',
    'DisjointSet',
    'Trie',
    'FenwickTree',
    'SegmentTree',
    
    # Sorting Algorithms
    'quick_sort',
    'merge_sort',
    'heap_sort',
    
    # Searching Algorithms
    'binary_search',
    'linear_search',
    'interpolation_search',
    
    # Dynamic Programming
    'longest_common_subsequence',
    'knapsack',
    'edit_distance',
    'matrix_chain_multiplication',
    
    # Interview Prep
    'two_sum',
    'longest_substring_without_repeating',
    'merge_intervals',
    'trap_rain_water',
    
    # System Design
    'RateLimiter',
    'ConsistentHashing',
    'BloomFilter',
    
    # Design Patterns
    'Singleton',
    'Observer',
    'Strategy',
    'Flyweight',
    'Specification'
]