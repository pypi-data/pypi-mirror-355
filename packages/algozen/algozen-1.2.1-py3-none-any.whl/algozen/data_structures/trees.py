"""Tree data structure implementations including Binary, BST, and AVL trees."""

from typing import Any, Optional, List, Callable
from collections import deque

class TreeNode:
    """Base node class for tree structures."""
    def __init__(self, data: Any) -> None:
        self.data = data
        self.left: Optional[TreeNode] = None
        self.right: Optional[TreeNode] = None
        self.height = 1  # Used for AVL tree balancing

class BinaryTree:
    """Binary tree implementation with traversal and utility methods."""
    
    def __init__(self) -> None:
        """Initialize an empty binary tree."""
        self.root: Optional[TreeNode] = None
        self._size = 0
    
    def insert_level_order(self, data: Any) -> None:
        """Insert a node in level order traversal.
        
        Time Complexity: O(n)
        Space Complexity: O(n)
        
        Args:
            data: Data to insert
        """
        new_node = TreeNode(data)
        if not self.root:
            self.root = new_node
            self._size += 1
            return
        
        queue = deque([self.root])
        while queue:
            node = queue.popleft()
            if not node.left:
                node.left = new_node
                self._size += 1
                return
            if not node.right:
                node.right = new_node
                self._size += 1
                return
            queue.append(node.left)
            queue.append(node.right)
    
    def inorder(self) -> List[Any]:
        """Perform inorder traversal.
        
        Time Complexity: O(n)
        Space Complexity: O(h) where h is height
        
        Returns:
            List[Any]: List of values in inorder
        """
        result = []
        
        def inorder_helper(node: Optional[TreeNode]) -> None:
            if node:
                inorder_helper(node.left)
                result.append(node.data)
                inorder_helper(node.right)
        
        inorder_helper(self.root)
        return result
    
    def preorder(self) -> List[Any]:
        """Perform preorder traversal.
        
        Time Complexity: O(n)
        Space Complexity: O(h)
        
        Returns:
            List[Any]: List of values in preorder
        """
        result = []
        
        def preorder_helper(node: Optional[TreeNode]) -> None:
            if node:
                result.append(node.data)
                preorder_helper(node.left)
                preorder_helper(node.right)
        
        preorder_helper(self.root)
        return result
    
    def postorder(self) -> List[Any]:
        """Perform postorder traversal.
        
        Time Complexity: O(n)
        Space Complexity: O(h)
        
        Returns:
            List[Any]: List of values in postorder
        """
        result = []
        
        def postorder_helper(node: Optional[TreeNode]) -> None:
            if node:
                postorder_helper(node.left)
                postorder_helper(node.right)
                result.append(node.data)
        
        postorder_helper(self.root)
        return result
    
    def level_order(self) -> List[List[Any]]:
        """Perform level order traversal.
        
        Time Complexity: O(n)
        Space Complexity: O(w) where w is max width
        
        Returns:
            List[List[Any]]: List of levels, each containing node values
        """
        if not self.root:
            return []
        
        result = []
        queue = deque([(self.root, 0)])
        current_level = 0
        current_values = []
        
        while queue:
            node, level = queue.popleft()
            
            if level > current_level:
                result.append(current_values)
                current_values = [node.data]
                current_level = level
            else:
                current_values.append(node.data)
            
            if node.left:
                queue.append((node.left, level + 1))
            if node.right:
                queue.append((node.right, level + 1))
        
        result.append(current_values)
        return result

class BST(BinaryTree):
    """Binary Search Tree implementation with efficient search operations."""
    
    def insert(self, data: Any) -> None:
        """Insert a new node maintaining BST property.
        
        Time Complexity: O(h)
        Space Complexity: O(h)
        
        Args:
            data: Data to insert
        """
        def insert_helper(node: Optional[TreeNode], data: Any) -> TreeNode:
            if not node:
                self._size += 1
                return TreeNode(data)
            
            if data < node.data:
                node.left = insert_helper(node.left, data)
            else:
                node.right = insert_helper(node.right, data)
            
            return node
        
        self.root = insert_helper(self.root, data)
    
    def search(self, data: Any) -> Optional[TreeNode]:
        """Search for a node with given data.
        
        Time Complexity: O(h)
        Space Complexity: O(h)
        
        Args:
            data: Data to search for
            
        Returns:
            Optional[TreeNode]: Found node or None
        """
        current = self.root
        while current:
            if data == current.data:
                return current
            elif data < current.data:
                current = current.left
            else:
                current = current.right
        return None

class AVLTree(BST):
    """AVL Tree implementation with automatic balancing."""
    
    def _get_height(self, node: Optional[TreeNode]) -> int:
        """Get height of a node."""
        return node.height if node else 0
    
    def _get_balance(self, node: Optional[TreeNode]) -> int:
        """Get balance factor of a node."""
        return self._get_height(node.left) - self._get_height(node.right) if node else 0
    
    def _update_height(self, node: TreeNode) -> None:
        """Update height of a node."""
        node.height = max(self._get_height(node.left), self._get_height(node.right)) + 1
    
    def _right_rotate(self, y: TreeNode) -> TreeNode:
        """Perform right rotation."""
        x = y.left
        T2 = x.right
        
        x.right = y
        y.left = T2
        
        self._update_height(y)
        self._update_height(x)
        
        return x
    
    def _left_rotate(self, x: TreeNode) -> TreeNode:
        """Perform left rotation."""
        y = x.right
        T2 = y.left
        
        y.left = x
        x.right = T2
        
        self._update_height(x)
        self._update_height(y)
        
        return y
    
    def insert(self, data: Any) -> None:
        """Insert a new node maintaining AVL balance.
        
        Time Complexity: O(log n)
        Space Complexity: O(log n)
        
        Args:
            data: Data to insert
        """
        def insert_helper(node: Optional[TreeNode], data: Any) -> TreeNode:
            # Perform normal BST insertion
            if not node:
                self._size += 1
                return TreeNode(data)
            
            if data < node.data:
                node.left = insert_helper(node.left, data)
            else:
                node.right = insert_helper(node.right, data)
            
            # Update height
            self._update_height(node)
            
            # Get balance factor
            balance = self._get_balance(node)
            
            # Left Left Case
            if balance > 1 and data < node.left.data:
                return self._right_rotate(node)
            
            # Right Right Case
            if balance < -1 and data > node.right.data:
                return self._left_rotate(node)
            
            # Left Right Case
            if balance > 1 and data > node.left.data:
                node.left = self._left_rotate(node.left)
                return self._right_rotate(node)
            
            # Right Left Case
            if balance < -1 and data < node.right.data:
                node.right = self._right_rotate(node.right)
                return self._left_rotate(node)
            
            return node
        
        self.root = insert_helper(self.root, data)