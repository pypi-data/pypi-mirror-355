"""Heap implementations including both MinHeap and MaxHeap."""

from typing import List, Any, Optional, Callable, TypeVar, Generic

T = TypeVar('T')

class Heap(Generic[T]):
    """Base heap implementation with common functionality.
    
    Features:
    1. Dynamic resizing
    2. Custom comparison function support
    3. Efficient heapify operation
    4. Iterator support
    """
    
    def __init__(self, key: Callable[[T], Any] = lambda x: x, is_min: bool = True) -> None:
        """Initialize an empty heap.
        
        Args:
            key: Function to extract comparison key (default: identity)
            is_min: True for min heap, False for max heap (default: True)
        """
        self._items: List[T] = []
        self._key = key
        self._is_min = is_min
    
    def _compare(self, i: int, j: int) -> bool:
        """Compare two items in the heap.
        
        Args:
            i: First item index
            j: Second item index
            
        Returns:
            bool: True if items are in correct order, False otherwise
        """
        if self._is_min:
            return self._key(self._items[i]) <= self._key(self._items[j])
        return self._key(self._items[i]) >= self._key(self._items[j])
    
    def _sift_up(self, index: int) -> None:
        """Move an item up to its correct position.
        
        Time Complexity: O(log n)
        Space Complexity: O(1)
        
        Args:
            index: Index of item to move
        """
        parent = (index - 1) // 2
        
        while index > 0 and not self._compare(parent, index):
            self._items[parent], self._items[index] = self._items[index], self._items[parent]
            index = parent
            parent = (index - 1) // 2
    
    def _sift_down(self, index: int) -> None:
        """Move an item down to its correct position.
        
        Time Complexity: O(log n)
        Space Complexity: O(1)
        
        Args:
            index: Index of item to move
        """
        size = len(self._items)
        while True:
            min_index = index
            left = 2 * index + 1
            right = 2 * index + 2
            
            if left < size and not self._compare(min_index, left):
                min_index = left
            if right < size and not self._compare(min_index, right):
                min_index = right
            
            if min_index == index:
                break
            
            self._items[index], self._items[min_index] = self._items[min_index], self._items[index]
            index = min_index
    
    def push(self, item: T) -> None:
        """Add an item to the heap.
        
        Time Complexity: O(log n)
        Space Complexity: O(1)
        
        Args:
            item: Item to add
        """
        self._items.append(item)
        self._sift_up(len(self._items) - 1)
    
    def pop(self) -> T:
        """Remove and return the top item.
        
        Time Complexity: O(log n)
        Space Complexity: O(1)
        
        Returns:
            T: Top item
            
        Raises:
            IndexError: If heap is empty
        """
        if not self._items:
            raise IndexError("Pop from empty heap")
        
        if len(self._items) == 1:
            return self._items.pop()
        
        result = self._items[0]
        self._items[0] = self._items.pop()
        self._sift_down(0)
        
        return result
    
    def peek(self) -> T:
        """Look at the top item without removing it.
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        
        Returns:
            T: Top item
            
        Raises:
            IndexError: If heap is empty
        """
        if not self._items:
            raise IndexError("Peek at empty heap")
        return self._items[0]
    
    def heapify(self, items: List[T]) -> None:
        """Build heap from a list of items.
        
        Time Complexity: O(n)
        Space Complexity: O(1)
        
        Args:
            items: List of items to heapify
        """
        self._items = items.copy()
        for i in range(len(self._items) // 2 - 1, -1, -1):
            self._sift_down(i)
    
    def merge(self, other: 'Heap[T]') -> None:
        """Merge another heap into this one.
        
        Time Complexity: O(n)
        Space Complexity: O(1)
        
        Args:
            other: Heap to merge
        """
        if self._is_min != other._is_min:
            raise ValueError("Cannot merge min and max heaps")
        
        self._items.extend(other._items)
        for i in range(len(self._items) // 2 - 1, -1, -1):
            self._sift_down(i)
    
    def __len__(self) -> int:
        """Get number of items in heap.
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        
        Returns:
            int: Number of items
        """
        return len(self._items)
    
    def __bool__(self) -> bool:
        """Check if heap is not empty.
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        
        Returns:
            bool: True if not empty, False otherwise
        """
        return bool(self._items)

class MinHeap(Heap[T]):
    """Min heap implementation."""
    
    def __init__(self, key: Callable[[T], Any] = lambda x: x) -> None:
        """Initialize an empty min heap.
        
        Args:
            key: Function to extract comparison key (default: identity)
        """
        super().__init__(key=key, is_min=True)

class MaxHeap(Heap[T]):
    """Max heap implementation."""
    
    def __init__(self, key: Callable[[T], Any] = lambda x: x) -> None:
        """Initialize an empty max heap.
        
        Args:
            key: Function to extract comparison key (default: identity)
        """
        super().__init__(key=key, is_min=False)