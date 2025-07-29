"""Stack and Queue implementations with efficient operations."""

from typing import Any, List, Optional, Iterator
from collections import deque

class Stack:
    """Stack implementation with dynamic array.
    
    Features:
    1. Dynamic resizing for efficient space usage
    2. O(1) push and pop operations
    3. Iterator support
    4. Bounds checking
    """
    
    def __init__(self, capacity: int = 10) -> None:
        """Initialize an empty stack.
        
        Args:
            capacity: Initial capacity (default: 10)
        """
        self._items: List[Any] = [None] * capacity
        self._size = 0
        self._capacity = capacity
    
    def push(self, item: Any) -> None:
        """Push an item onto the stack.
        
        Time Complexity: O(1) amortized
        Space Complexity: O(1)
        
        Args:
            item: Item to push
        """
        if self._size == self._capacity:
            self._resize(2 * self._capacity)
        
        self._items[self._size] = item
        self._size += 1
    
    def pop(self) -> Any:
        """Pop an item from the stack.
        
        Time Complexity: O(1) amortized
        Space Complexity: O(1)
        
        Returns:
            Any: Popped item
            
        Raises:
            IndexError: If stack is empty
        """
        if self.is_empty():
            raise IndexError("Pop from empty stack")
        
        self._size -= 1
        item = self._items[self._size]
        self._items[self._size] = None
        
        if self._size > 0 and self._size == self._capacity // 4:
            self._resize(self._capacity // 2)
        
        return item
    
    def peek(self) -> Any:
        """Look at the top item without removing it.
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        
        Returns:
            Any: Top item
            
        Raises:
            IndexError: If stack is empty
        """
        if self.is_empty():
            raise IndexError("Peek at empty stack")
        return self._items[self._size - 1]
    
    def is_empty(self) -> bool:
        """Check if stack is empty.
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        
        Returns:
            bool: True if empty, False otherwise
        """
        return self._size == 0
    
    def _resize(self, new_capacity: int) -> None:
        """Resize the internal array.
        
        Time Complexity: O(n)
        Space Complexity: O(n)
        
        Args:
            new_capacity: New array size
        """
        temp = [None] * new_capacity
        for i in range(self._size):
            temp[i] = self._items[i]
        self._items = temp
        self._capacity = new_capacity
    
    def __len__(self) -> int:
        """Get number of items in stack.
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        
        Returns:
            int: Number of items
        """
        return self._size
    
    def __iter__(self) -> Iterator[Any]:
        """Make stack iterable.
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        
        Returns:
            Iterator[Any]: Iterator over items
        """
        for i in range(self._size - 1, -1, -1):
            yield self._items[i]

class Queue:
    """Queue implementation using doubly-linked list.
    
    Features:
    1. O(1) enqueue and dequeue operations
    2. Iterator support
    3. Efficient memory usage
    4. Optional maximum size limit
    """
    
    def __init__(self, max_size: Optional[int] = None) -> None:
        """Initialize an empty queue.
        
        Args:
            max_size: Maximum queue size (default: None for unlimited)
        """
        self._items = deque()
        self._max_size = max_size
    
    def enqueue(self, item: Any) -> None:
        """Add an item to the queue.
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        
        Args:
            item: Item to add
            
        Raises:
            ValueError: If queue is at max size
        """
        if self._max_size and len(self._items) >= self._max_size:
            raise ValueError("Queue is full")
        self._items.append(item)
    
    def dequeue(self) -> Any:
        """Remove and return the first item.
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        
        Returns:
            Any: First item
            
        Raises:
            IndexError: If queue is empty
        """
        if self.is_empty():
            raise IndexError("Dequeue from empty queue")
        return self._items.popleft()
    
    def peek(self) -> Any:
        """Look at the first item without removing it.
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        
        Returns:
            Any: First item
            
        Raises:
            IndexError: If queue is empty
        """
        if self.is_empty():
            raise IndexError("Peek at empty queue")
        return self._items[0]
    
    def is_empty(self) -> bool:
        """Check if queue is empty.
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        
        Returns:
            bool: True if empty, False otherwise
        """
        return len(self._items) == 0
    
    def is_full(self) -> bool:
        """Check if queue is at max size.
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        
        Returns:
            bool: True if full, False otherwise
        """
        return self._max_size is not None and len(self._items) >= self._max_size
    
    def __len__(self) -> int:
        """Get number of items in queue.
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        
        Returns:
            int: Number of items
        """
        return len(self._items)
    
    def __iter__(self) -> Iterator[Any]:
        """Make queue iterable.
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        
        Returns:
            Iterator[Any]: Iterator over items
        """
        return iter(self._items)