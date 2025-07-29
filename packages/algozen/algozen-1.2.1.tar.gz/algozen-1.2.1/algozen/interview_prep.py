"""Common Data Structures and Algorithms problems frequently asked in tech interviews."""

from typing import List, Optional, Dict, Set, Tuple
from collections import defaultdict, deque
from heapq import heappush, heappop

def two_sum(nums: List[int], target: int) -> List[int]:
    """Find indices of two numbers that add up to target.
    
    Time: O(n), Space: O(n)
    Common at: Google, Meta, Amazon
    """
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []

def longest_substring_without_repeating(s: str) -> int:
    """Find length of longest substring without repeating characters.
    
    Time: O(n), Space: O(min(m,n)) where m is charset size
    Common at: Meta, Google, Amazon
    """
    char_index = {}
    max_length = start = 0
    
    for i, char in enumerate(s):
        if char in char_index and char_index[char] >= start:
            start = char_index[char] + 1
        else:
            max_length = max(max_length, i - start + 1)
        char_index[char] = i
        
    return max_length

def merge_intervals(intervals: List[List[int]]) -> List[List[int]]:
    """Merge overlapping intervals.
    
    Time: O(n log n), Space: O(n)
    Common at: Google, Meta, Microsoft
    """
    if not intervals:
        return []
        
    intervals.sort(key=lambda x: x[0])
    merged = [intervals[0]]
    
    for interval in intervals[1:]:
        if interval[0] <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], interval[1])
        else:
            merged.append(interval)
            
    return merged

def trap_rain_water(height: List[int]) -> int:
    """Calculate how much rain water can be trapped.
    
    Time: O(n), Space: O(1)
    Common at: Meta, Google, Amazon
    """
    if not height:
        return 0
        
    left, right = 0, len(height) - 1
    left_max = right_max = water = 0
    
    while left < right:
        if height[left] < height[right]:
            if height[left] >= left_max:
                left_max = height[left]
            else:
                water += left_max - height[left]
            left += 1
        else:
            if height[right] >= right_max:
                right_max = height[right]
            else:
                water += right_max - height[right]
            right -= 1
            
    return water

def word_break(s: str, wordDict: List[str]) -> bool:
    """Determine if string can be segmented into dictionary words.
    
    Time: O(n^2), Space: O(n)
    Common at: Meta, Google, Amazon
    """
    word_set = set(wordDict)
    dp = [False] * (len(s) + 1)
    dp[0] = True
    
    for i in range(1, len(s) + 1):
        for j in range(i):
            if dp[j] and s[j:i] in word_set:
                dp[i] = True
                break
                
    return dp[len(s)]

def lru_cache(capacity: int):
    """Implement Least Recently Used (LRU) cache.
    
    Common at: Meta, Google, Amazon
    """
    class Node:
        def __init__(self, key=None, value=None):
            self.key = key
            self.value = value
            self.prev = None
            self.next = None
    
    class LRUCache:
        def __init__(self, capacity: int):
            self.capacity = capacity
            self.cache = {}
            self.head = Node()
            self.tail = Node()
            self.head.next = self.tail
            self.tail.prev = self.head
        
        def _remove(self, node: Node) -> None:
            node.prev.next = node.next
            node.next.prev = node.prev
        
        def _add(self, node: Node) -> None:
            node.prev = self.head
            node.next = self.head.next
            self.head.next.prev = node
            self.head.next = node
        
        def get(self, key: int) -> int:
            if key in self.cache:
                node = self.cache[key]
                self._remove(node)
                self._add(node)
                return node.value
            return -1
        
        def put(self, key: int, value: int) -> None:
            if key in self.cache:
                self._remove(self.cache[key])
            node = Node(key, value)
            self._add(node)
            self.cache[key] = node
            if len(self.cache) > self.capacity:
                lru = self.tail.prev
                self._remove(lru)
                del self.cache[lru.key]
    
    return LRUCache

def course_schedule(numCourses: int, prerequisites: List[List[int]]) -> bool:
    """Determine if it's possible to finish all courses.
    
    Time: O(V + E), Space: O(V + E)
    Common at: Google, Meta, Amazon
    """
    graph = defaultdict(list)
    for course, prereq in prerequisites:
        graph[course].append(prereq)
    
    visited = set()
    path = set()
    
    def has_cycle(course: int) -> bool:
        if course in path:
            return True
        if course in visited:
            return False
            
        path.add(course)
        for prereq in graph[course]:
            if has_cycle(prereq):
                return True
        path.remove(course)
        visited.add(course)
        return False
    
    for course in range(numCourses):
        if has_cycle(course):
            return False
    return True

def median_finder():
    """Design a data structure that supports adding numbers and finding median.
    
    Common at: Google, Meta, Amazon
    """
    class MedianFinder:
        def __init__(self):
            self.small = []  # max heap
            self.large = []  # min heap
        
        def addNum(self, num: int) -> None:
            if len(self.small) == len(self.large):
                heappush(self.large, -heappushpop(self.small, -num))
            else:
                heappush(self.small, -heappushpop(self.large, num))
        
        def findMedian(self) -> float:
            if len(self.small) == len(self.large):
                return (-self.small[0] + self.large[0]) / 2
            return self.large[0]
    
    return MedianFinder

def serialize_deserialize_binary_tree():
    """Implement serialization and deserialization of binary tree.
    
    Common at: Meta, Google, Amazon
    """
    class TreeNode:
        def __init__(self, x):
            self.val = x
            self.left = None
            self.right = None
    
    class Codec:
        def serialize(self, root: Optional[TreeNode]) -> str:
            if not root:
                return 'null'
            return f'{root.val},{self.serialize(root.left)},{self.serialize(root.right)}'
        
        def deserialize(self, data: str) -> Optional[TreeNode]:
            def dfs():
                val = next(values)
                if val == 'null':
                    return None
                node = TreeNode(int(val))
                node.left = dfs()
                node.right = dfs()
                return node
            
            values = iter(data.split(','))
            return dfs()
    
    return Codec