"""LinkedList implementations including both singly and doubly linked lists."""

from typing import Any, Optional, Iterator

class Node:
    """A node in a linked list."""
    def __init__(self, data: Any) -> None:
        self.data = data
        self.next: Optional[Node] = None

class LinkedList:
    """Singly linked list implementation with efficient operations."""
    
    def __init__(self) -> None:
        """Initialize an empty linked list."""
        self.head: Optional[Node] = None
        self._size = 0
    
    def append(self, data: Any) -> None:
        """Add a new node with given data at the end of the list.
        
        Time Complexity: O(n)
        Space Complexity: O(1)
        
        Args:
            data: The data to be stored in the new node
        """
        new_node = Node(data)
        if not self.head:
            self.head = new_node
        else:
            current = self.head
            while current.next:
                current = current.next
            current.next = new_node
        self._size += 1
    
    def prepend(self, data: Any) -> None:
        """Add a new node with given data at the start of the list.
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        
        Args:
            data: The data to be stored in the new node
        """
        new_node = Node(data)
        new_node.next = self.head
        self.head = new_node
        self._size += 1
    
    def delete(self, data: Any) -> bool:
        """Delete the first occurrence of a node with the given data.
        
        Time Complexity: O(n)
        Space Complexity: O(1)
        
        Args:
            data: The data to be deleted
            
        Returns:
            bool: True if node was found and deleted, False otherwise
        """
        if not self.head:
            return False
            
        if self.head.data == data:
            self.head = self.head.next
            self._size -= 1
            return True
            
        current = self.head
        while current.next:
            if current.next.data == data:
                current.next = current.next.next
                self._size -= 1
                return True
            current = current.next
            
        return False
    
    def find(self, data: Any) -> Optional[Node]:
        """Find the first node containing the given data.
        
        Time Complexity: O(n)
        Space Complexity: O(1)
        
        Args:
            data: The data to search for
            
        Returns:
            Optional[Node]: The found node or None if not found
        """
        current = self.head
        while current:
            if current.data == data:
                return current
            current = current.next
        return None
    
    def reverse(self) -> None:
        """Reverse the linked list in-place.
        
        Time Complexity: O(n)
        Space Complexity: O(1)
        """
        prev = None
        current = self.head
        while current:
            next_node = current.next
            current.next = prev
            prev = current
            current = next_node
        self.head = prev
    
    def __len__(self) -> int:
        """Return the number of nodes in the list.
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        
        Returns:
            int: Number of nodes
        """
        return self._size
    
    def __getitem__(self, index: int) -> Any:
        """Get the item at the given index.
        
        Time Complexity: O(n) where n is the index
        
        Args:
            index: The index of the item to retrieve
            
        Returns:
            The data at the given index
            
        Raises:
            IndexError: If index is out of range
        """
        if index < 0 or index >= self._size:
            raise IndexError("Index out of range")
            
        current = self.head
        for _ in range(index):
            if current is None:
                raise IndexError("Index out of range")
            current = current.next
            
        if current is None:
            raise IndexError("Index out of range")
            
        return current.data
    
    def __iter__(self) -> Iterator[Any]:
        """Make the linked list iterable.
        
        Time Complexity: O(1) for iterator creation
        Space Complexity: O(1)
        
        Returns:
            Iterator[Any]: Iterator over the list's data
        """
        current = self.head
        while current:
            yield current.data
            current = current.next
    
    def __str__(self) -> str:
        """Return a string representation of the list.
        
        Time Complexity: O(n)
        Space Complexity: O(n)
        
        Returns:
            str: String representation of the list
        """
        return ' -> '.join(str(data) for data in self)

class DoublyNode(Node):
    """A node in a doubly linked list."""
    def __init__(self, data: Any) -> None:
        super().__init__(data)
        self.prev: Optional[DoublyNode] = None
        self.next: Optional[DoublyNode] = None

class DoublyLinkedList(LinkedList):
    """Doubly linked list implementation extending the base LinkedList."""
    
    def __init__(self) -> None:
        """Initialize an empty doubly linked list."""
        super().__init__()
        self.tail: Optional[DoublyNode] = None
    
    def append(self, data: Any) -> None:
        """Add a new node with given data at the end of the list.
        
        Time Complexity: O(1) - improved from base class
        Space Complexity: O(1)
        
        Args:
            data: The data to be stored in the new node
        """
        new_node = DoublyNode(data)
        if not self.head:
            self.head = new_node
            self.tail = new_node
        else:
            new_node.prev = self.tail
            self.tail.next = new_node
            self.tail = new_node
        self._size += 1
    
    def prepend(self, data: Any) -> None:
        """Add a new node with given data at the start of the list.
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        
        Args:
            data: The data to be stored in the new node
        """
        new_node = DoublyNode(data)
        if not self.head:
            self.head = new_node
            self.tail = new_node
        else:
            new_node.next = self.head
            self.head.prev = new_node
            self.head = new_node
        self._size += 1
    
    def delete(self, data: Any) -> bool:
        """Delete the first occurrence of a node with the given data.
        
        Time Complexity: O(n)
        Space Complexity: O(1)
        
        Args:
            data: The data to be deleted
            
        Returns:
            bool: True if node was found and deleted, False otherwise
        """
        current = self.head
        while current:
            if current.data == data:
                if current.prev:
                    current.prev.next = current.next
                else:
                    self.head = current.next
                
                if current.next:
                    current.next.prev = current.prev
                else:
                    self.tail = current.prev
                
                self._size -= 1
                return True
            current = current.next
        return False