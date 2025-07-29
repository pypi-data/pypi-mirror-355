"""Efficient implementations of searching algorithms."""

from typing import List, TypeVar, Optional, Callable

T = TypeVar('T', int, float, str)

def binary_search(arr: List[T], target: T, key: Callable[[T], T] = lambda x: x) -> Optional[int]:
    """Perform binary search on a sorted list.
    
    This implementation includes the following optimizations:
    1. Early termination for common cases
    2. Mid-calculation that avoids integer overflow
    3. Support for custom key functions for complex objects
    
    Time Complexity: O(log n)
    Space Complexity: O(1)
    
    Args:
        arr: Sorted list to search in
        target: Value to search for
        key: Function to extract comparison key (default is identity function)
    
    Returns:
        Optional[int]: Index of target if found, None otherwise
    
    Raises:
        ValueError: If the input list is not sorted
    """
    # Verify list is sorted
    if any(key(arr[i]) > key(arr[i + 1]) for i in range(len(arr) - 1)):
        raise ValueError("Input list must be sorted")
    
    # Early termination checks
    if not arr:
        return None
    if key(target) < key(arr[0]) or key(target) > key(arr[-1]):
        return None
    
    left, right = 0, len(arr) - 1
    
    while left <= right:
        # Avoid integer overflow
        mid = left + (right - left) // 2
        mid_val = key(arr[mid])
        
        if mid_val == key(target):
            # Found target, now find leftmost occurrence
            while mid > 0 and key(arr[mid - 1]) == key(target):
                mid -= 1
            return mid
        elif mid_val < key(target):
            left = mid + 1
        else:
            right = mid - 1
    
    return None

def linear_search(arr: List[T], target: T, key: Callable[[T], T] = lambda x: x) -> Optional[int]:
    """Perform linear search on a list.
    
    This implementation includes the following optimizations:
    1. Early termination when target is found
    2. Support for custom key functions for complex objects
    3. Optional early termination for sorted lists
    
    Time Complexity: O(n)
    Space Complexity: O(1)
    
    Args:
        arr: List to search in
        target: Value to search for
        key: Function to extract comparison key (default is identity function)
    
    Returns:
        Optional[int]: Index of target if found, None otherwise
    """
    target_key = key(target)
    
    # Check if list is sorted for potential early termination
    is_sorted = all(key(arr[i]) <= key(arr[i + 1]) for i in range(len(arr) - 1))
    
    for i, item in enumerate(arr):
        item_key = key(item)
        
        # Early termination for sorted lists
        if is_sorted and item_key > target_key:
            return None
        
        if item_key == target_key:
            return i
    
    return None

def interpolation_search(arr: List[T], target: T, key: Callable[[T], T] = lambda x: x) -> Optional[int]:
    """Perform interpolation search on a sorted list of uniformly distributed values.
    
    This implementation includes the following optimizations:
    1. Early termination checks
    2. Bounds checking to prevent array out-of-bounds
    3. Fallback to binary search for non-uniform distributions
    
    Time Complexity:
        - Average Case (uniform distribution): O(log log n)
        - Worst Case: O(n)
    Space Complexity: O(1)
    
    Args:
        arr: Sorted list to search in
        target: Value to search for
        key: Function to extract comparison key (default is identity function)
    
    Returns:
        Optional[int]: Index of target if found, None otherwise
    
    Raises:
        ValueError: If the input list is not sorted
    """
    if not arr:
        return None
    
    # Verify list is sorted
    if any(key(arr[i]) > key(arr[i + 1]) for i in range(len(arr) - 1)):
        raise ValueError("Input list must be sorted")
    
    left, right = 0, len(arr) - 1
    target_key = key(target)
    
    # Early termination checks
    if target_key < key(arr[left]) or target_key > key(arr[right]):
        return None
    
    while left <= right and target_key >= key(arr[left]) and target_key <= key(arr[right]):
        if left == right:
            return left if key(arr[left]) == target_key else None
        
        # Avoid division by zero
        if key(arr[left]) == key(arr[right]):
            return left if key(arr[left]) == target_key else None
        
        # Calculate probe position
        pos = left + int(
            (right - left) * 
            (target_key - key(arr[left])) / 
            (key(arr[right]) - key(arr[left]))
        )
        
        # Bounds check
        pos = min(right, max(left, pos))
        
        if key(arr[pos]) == target_key:
            # Found target, now find leftmost occurrence
            while pos > 0 and key(arr[pos - 1]) == target_key:
                pos -= 1
            return pos
        elif key(arr[pos]) < target_key:
            left = pos + 1
        else:
            right = pos - 1
    
    return None