"""Advanced data structures for high-performance systems and specialized use cases."""

from typing import TypeVar, Generic, Optional, List, Dict, Set, Tuple
from collections import defaultdict
from abc import ABC, abstractmethod
import random

T = TypeVar('T')

class SkipList(Generic[T]):
    """Skip List implementation for efficient search and insertion.
    
    Time Complexity:
    - Search: O(log n)
    - Insert: O(log n)
    - Delete: O(log n)
    Space Complexity: O(n)
    """
    
    class Node:
        def __init__(self, level: int, value: T):
            self.value = value
            self.next = [None] * (level + 1)
    
    def __init__(self, max_level: int = 16, p: float = 0.5):
        self.max_level = max_level
        self.p = p
        self.level = 0
        self.head = self.Node(max_level, None)
    
    def _random_level(self) -> int:
        level = 0
        while random.random() < self.p and level < self.max_level:
            level += 1
        return level
    
    def search(self, value: T) -> bool:
        """Search for a value in the skip list.
        
        Args:
            value: Value to search for
            
        Returns:
            bool: True if value exists, False otherwise
        """
        current = self.head
        
        for i in range(self.level, -1, -1):
            while current.next[i] and current.next[i].value < value:
                current = current.next[i]
        
        current = current.next[0]
        return current is not None and current.value == value
    
    def insert(self, value: T) -> None:
        update = [None] * (self.max_level + 1)
        current = self.head
        
        for i in range(self.level, -1, -1):
            while current.next[i] and current.next[i].value < value:
                current = current.next[i]
            update[i] = current
        
        level = self._random_level()
        if level > self.level:
            for i in range(self.level + 1, level + 1):
                update[i] = self.head
            self.level = level
        
        new_node = self.Node(level, value)
        for i in range(level + 1):
            new_node.next[i] = update[i].next[i]
            update[i].next[i] = new_node

class DisjointSet:
    """Disjoint Set (Union-Find) with path compression and union by rank.
    
    Time Complexity:
    - Find: O(α(n)) ≈ O(1)
    - Union: O(α(n)) ≈ O(1)
    Space Complexity: O(n)
    """
    
    def __init__(self, size: int):
        self.parent = list(range(size))
        self.rank = [0] * size
    
    def find(self, x: int) -> int:
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]
    
    def union(self, x: int, y: int) -> None:
        px, py = self.find(x), self.find(y)
        if px == py:
            return
        
        if self.rank[px] < self.rank[py]:
            self.parent[px] = py
        elif self.rank[px] > self.rank[py]:
            self.parent[py] = px
        else:
            self.parent[py] = px
            self.rank[px] += 1
    
    def connected(self, x: int, y: int) -> bool:
        """Check if two elements are in the same set.
        
        Args:
            x: First element
            y: Second element
            
        Returns:
            bool: True if elements are connected, False otherwise
        """
        return self.find(x) == self.find(y)

class Trie:
    """Trie (Prefix Tree) implementation for efficient string operations.
    
    Time Complexity:
    - Insert: O(m)
    - Search: O(m)
    - StartsWith: O(m)
    Space Complexity: O(ALPHABET_SIZE * m * n)
    where m is key length, n is number of keys
    """
    
    def __init__(self):
        self.children: Dict[str, 'Trie'] = {}
        self.is_end = False
    
    def insert(self, word: str) -> None:
        """Insert a word into the trie.
        
        Args:
            word: Word to insert
        """
        node = self
        for char in word:
            if char not in node.children:
                node.children[char] = Trie()
            node = node.children[char]
        node.is_end = True
    
    def search(self, word: str) -> bool:
        """Search for a word in the trie.
        
        Args:
            word: Word to search for
            
        Returns:
            bool: True if word exists, False otherwise
        """
        node = self
        for char in word:
            if char not in node.children:
                return False
            node = node.children[char]
        return node.is_end
    
    def starts_with(self, prefix: str) -> bool:
        """Check if any word in the trie starts with the given prefix.
        
        Args:
            prefix: Prefix to check for
            
        Returns:
            bool: True if prefix exists, False otherwise
        """
        node = self
        for char in prefix:
            if char not in node.children:
                return False
            node = node.children[char]
        return True

class FenwickTree:
    """Fenwick Tree (Binary Indexed Tree) for efficient range queries.
    
    Time Complexity:
    - Update: O(log n)
    - Query: O(log n)
    Space Complexity: O(n)
    """
    
    def __init__(self, n: int):
        self.size = n
        self.tree = [0] * (n + 1)
    
    def update(self, index: int, value: int) -> None:
        """Add value to element at index.
        
        Args:
            index: 0-based index to update
            value: Value to add
        """
        index += 1
        while index <= self.size:
            self.tree[index] += value
            index += index & (-index)
    
    def prefix_sum(self, index: int) -> int:
        """Get sum of elements from index 0 to index.
        
        Args:
            index: Right boundary of range (inclusive)
            
        Returns:
            int: Sum of elements in range [0, index]
        """
        index += 1
        total = 0
        while index > 0:
            total += self.tree[index]
            index -= index & (-index)
        return total
    
    def range_sum(self, left: int, right: int) -> int:
        """Get sum of elements in range [left, right].
        
        Args:
            left: Left boundary of range
            right: Right boundary of range
            
        Returns:
            int: Sum of elements in range [left, right]
        """
        return self.prefix_sum(right) - (self.prefix_sum(left - 1) if left > 0 else 0)

class SegmentTree:
    """Segment Tree for range queries and updates.
    
    Time Complexity:
    - Build: O(n)
    - Update: O(log n)
    - Query: O(log n)
    Space Complexity: O(n)
    """
    
    def __init__(self, arr: List[int]):
        self.n = len(arr)
        self.tree = [0] * (4 * self.n)
        if self.n > 0:
            self._build(arr, 0, 0, self.n - 1)
    
    def _build(self, arr: List[int], node: int, start: int, end: int) -> None:
        if start == end:
            self.tree[node] = arr[start]
            return
        
        mid = (start + end) // 2
        self._build(arr, 2 * node + 1, start, mid)
        self._build(arr, 2 * node + 2, mid + 1, end)
        self.tree[node] = self.tree[2 * node + 1] + self.tree[2 * node + 2]
    
    def update(self, index: int, value: int) -> None:
        """Update element at index to value.
        
        Args:
            index: Index to update
            value: New value
        """
        self._update(0, 0, self.n - 1, index, value)
    
    def _update(self, node: int, start: int, end: int, index: int, value: int) -> None:
        if start == end:
            self.tree[node] = value
            return
        
        mid = (start + end) // 2
        if start <= index <= mid:
            self._update(2 * node + 1, start, mid, index, value)
        else:
            self._update(2 * node + 2, mid + 1, end, index, value)
        self.tree[node] = self.tree[2 * node + 1] + self.tree[2 * node + 2]
    
    def query(self, left: int, right: int) -> int:
        """Get sum of elements in range [left, right].
        
        Args:
            left: Left boundary of range
            right: Right boundary of range
            
        Returns:
            int: Sum of elements in range [left, right]
        """
        return self._query(0, 0, self.n - 1, left, right)
    
    def _query(self, node: int, start: int, end: int, left: int, right: int) -> int:
        if right < start or left > end:
            return 0
        if left <= start and end <= right:
            return self.tree[node]
        
        mid = (start + end) // 2
        return (
            self._query(2 * node + 1, start, mid, left, right) +
            self._query(2 * node + 2, mid + 1, end, left, right)
        )