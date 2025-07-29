"""Hash table implementation with efficient collision resolution."""

from typing import Any, Optional, List, Tuple, Iterator
from collections.abc import Hashable

class HashNode:
    """Node for hash table entries."""
    def __init__(self, key: Hashable, value: Any) -> None:
        self.key = key
        self.value = value
        self.next: Optional[HashNode] = None

class HashTable:
    """Hash table implementation using separate chaining.
    
    Features:
    1. Dynamic resizing for load balancing
    2. Separate chaining for collision resolution
    3. Efficient key distribution
    4. Iterator support
    """
    
    def __init__(self, initial_capacity: int = 16, load_factor: float = 0.75) -> None:
        """Initialize an empty hash table.
        
        Args:
            initial_capacity: Initial size of hash table (default: 16)
            load_factor: Threshold for resizing (default: 0.75)
        """
        if initial_capacity < 1:
            raise ValueError("Capacity must be positive")
        if not 0 < load_factor <= 1:
            raise ValueError("Load factor must be between 0 and 1")
        
        self._capacity = initial_capacity
        self._load_factor = load_factor
        self._size = 0
        self._buckets: List[Optional[HashNode]] = [None] * initial_capacity
    
    def _hash(self, key: Hashable) -> int:
        """Generate hash code for a key.
        
        Uses Python's built-in hash function and ensures even distribution.
        
        Args:
            key: Key to hash
            
        Returns:
            int: Bucket index
        """
        return hash(key) & (self._capacity - 1)
    
    def put(self, key: Hashable, value: Any) -> None:
        """Add or update a key-value pair.
        
        Time Complexity: O(1) average, O(n) worst
        Space Complexity: O(1)
        
        Args:
            key: Key to store
            value: Value to store
        """
        index = self._hash(key)
        
        # Update existing key
        current = self._buckets[index]
        while current:
            if current.key == key:
                current.value = value
                return
            current = current.next
        
        # Add new key
        node = HashNode(key, value)
        node.next = self._buckets[index]
        self._buckets[index] = node
        self._size += 1
        
        # Resize if load factor exceeded
        if self._size / self._capacity > self._load_factor:
            self._resize(2 * self._capacity)
    
    def get(self, key: Hashable) -> Any:
        """Get value for a key.
        
        Time Complexity: O(1) average, O(n) worst
        Space Complexity: O(1)
        
        Args:
            key: Key to look up
            
        Returns:
            Any: Associated value
            
        Raises:
            KeyError: If key not found
        """
        index = self._hash(key)
        current = self._buckets[index]
        
        while current:
            if current.key == key:
                return current.value
            current = current.next
        
        raise KeyError(key)
    
    def remove(self, key: Hashable) -> None:
        """Remove a key-value pair.
        
        Time Complexity: O(1) average, O(n) worst
        Space Complexity: O(1)
        
        Args:
            key: Key to remove
            
        Raises:
            KeyError: If key not found
        """
        index = self._hash(key)
        current = self._buckets[index]
        prev = None
        
        while current:
            if current.key == key:
                if prev:
                    prev.next = current.next
                else:
                    self._buckets[index] = current.next
                self._size -= 1
                
                # Resize if load factor too low
                if self._size > 0 and self._size / self._capacity < self._load_factor / 4:
                    self._resize(self._capacity // 2)
                return
            
            prev = current
            current = current.next
        
        raise KeyError(key)
    
    def _resize(self, new_capacity: int) -> None:
        """Resize the hash table.
        
        Time Complexity: O(n)
        Space Complexity: O(n)
        
        Args:
            new_capacity: New table size
        """
        old_buckets = self._buckets
        self._capacity = new_capacity
        self._buckets = [None] * new_capacity
        self._size = 0
        
        # Rehash all entries
        for bucket in old_buckets:
            current = bucket
            while current:
                self.put(current.key, current.value)
                current = current.next
    
    def contains(self, key: Hashable) -> bool:
        """Check if key exists.
        
        Time Complexity: O(1) average, O(n) worst
        Space Complexity: O(1)
        
        Args:
            key: Key to check
            
        Returns:
            bool: True if key exists, False otherwise
        """
        try:
            self.get(key)
            return True
        except KeyError:
            return False
    
    def clear(self) -> None:
        """Remove all entries.
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        self._buckets = [None] * self._capacity
        self._size = 0
    
    def items(self) -> List[Tuple[Hashable, Any]]:
        """Get all key-value pairs.
        
        Time Complexity: O(n)
        Space Complexity: O(n)
        
        Returns:
            List[Tuple[Hashable, Any]]: List of key-value pairs
        """
        result = []
        for bucket in self._buckets:
            current = bucket
            while current:
                result.append((current.key, current.value))
                current = current.next
        return result
    
    def __len__(self) -> int:
        """Get number of entries.
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        
        Returns:
            int: Number of entries
        """
        return self._size
    
    def __iter__(self) -> Iterator[Tuple[Hashable, Any]]:
        """Make hash table iterable.
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        
        Returns:
            Iterator[Tuple[Hashable, Any]]: Iterator over key-value pairs
        """
        return iter(self.items())
    
    def __str__(self) -> str:
        """Get string representation.
        
        Time Complexity: O(n)
        Space Complexity: O(n)
        
        Returns:
            str: String representation
        """
        return str(dict(self.items()))