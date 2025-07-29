"""Common System Design problems and solutions frequently asked in tech interviews."""

from typing import List, Dict, Optional, Set
from collections import defaultdict, OrderedDict, deque
from datetime import datetime, timedelta
import threading
import time

class RateLimiter:
    """Sliding Window Rate Limiter implementation.
    
    Common at: Meta, Google, Uber
    Features:
    - Sliding window algorithm
    - Thread-safe implementation
    - Configurable capacity and window size
    
    Time Complexity: O(1) for allow_request
    Space Complexity: O(capacity) for storing timestamps
    """
    
    def __init__(self, capacity: int, window_size: int):
        """Initialize rate limiter.
        
        Args:
            capacity: Maximum number of requests allowed in the window
            window_size: Time window in seconds
        """
        self.capacity = capacity
        self.window_size = window_size
        self.requests = deque()
        self.lock = threading.Lock()
    
    def allow_request(self) -> bool:
        """Check if a new request should be allowed.
        
        Returns:
            bool: True if request is allowed, False otherwise
        """
        with self.lock:
            now = time.time()
            
            # Remove expired timestamps
            while self.requests and self.requests[0] <= now - self.window_size:
                self.requests.popleft()
            
            # Check if we can allow a new request
            if len(self.requests) < self.capacity:
                self.requests.append(now)
                return True
            
            return False

class ConsistentHashing:
    """Consistent Hashing implementation for distributed systems.
    
    Common at: Amazon, Meta, Microsoft
    Features:
    - Virtual nodes for better distribution
    - O(log n) lookup time
    - Minimal redistribution on node changes
    """
    
    def __init__(self, nodes: List[str] = None, replicas: int = 100):
        self.replicas = replicas
        self.ring = OrderedDict()
        self.nodes = set()
        
        if nodes:
            for node in nodes:
                self.add_node(node)
    
    def _hash(self, key: str) -> int:
        return hash(key) & 0xffffffff
    
    def add_node(self, node: str) -> None:
        if node in self.nodes:
            return
        
        self.nodes.add(node)
        for i in range(self.replicas):
            hash_key = self._hash(f"{node}:{i}")
            self.ring[hash_key] = node
        
        self.ring = OrderedDict(sorted(self.ring.items()))
    
    def remove_node(self, node: str) -> None:
        if node not in self.nodes:
            return
        
        self.nodes.remove(node)
        for i in range(self.replicas):
            hash_key = self._hash(f"{node}:{i}")
            del self.ring[hash_key]
    
    def get_node(self, key: str) -> Optional[str]:
        if not self.ring:
            return None
        
        hash_key = self._hash(key)
        for ring_key in self.ring:
            if ring_key >= hash_key:
                return self.ring[ring_key]
        return self.ring[next(iter(self.ring))]

class BloomFilter:
    """Bloom Filter implementation for efficient set membership testing.
    
    Common at: Google, LinkedIn, Twitter
    Features:
    - Space-efficient probabilistic data structure
    - No false negatives
    - Configurable false positive rate
    """
    
    def __init__(self, size: int, hash_count: int):
        """Initialize Bloom Filter.
        
        Args:
            size: Size of bit array
            hash_count: Number of hash functions to use
        """
        self.size = size
        self.hash_count = hash_count
        self.bit_array = [False] * size
    
    def _get_hash_values(self, item: str) -> List[int]:
        """Generate hash values for an item.
        
        Args:
            item: Item to hash
            
        Returns:
            List[int]: List of hash values
        """
        hash_values = []
        for seed in range(self.hash_count):
            hash_val = hash(f"{item}:{seed}") % self.size
            hash_values.append(hash_val)
        return hash_values
    
    def add(self, item: str) -> None:
        """Add an item to the Bloom Filter.
        
        Args:
            item: Item to add
        """
        for bit_index in self._get_hash_values(item):
            self.bit_array[bit_index] = True
    
    def might_contain(self, item: str) -> bool:
        """Check if an item might be in the set.
        
        Args:
            item: Item to check
            
        Returns:
            bool: True if item might be in set, False if definitely not in set
        """
        return all(self.bit_array[i] for i in self._get_hash_values(item))