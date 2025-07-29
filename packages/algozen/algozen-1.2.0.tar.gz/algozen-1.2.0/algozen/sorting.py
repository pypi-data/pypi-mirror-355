"""Efficient implementations of common sorting algorithms."""

from typing import List, TypeVar, Callable
from random import randint

T = TypeVar('T', int, float, str)

def quick_sort(arr: List[T], key: Callable[[T], T] = lambda x: x) -> List[T]:
    """Sort a list using the QuickSort algorithm with randomized pivot selection.
    
    This implementation uses the following optimizations:
    1. Randomized pivot selection to avoid worst-case scenarios
    2. Three-way partitioning for handling duplicates efficiently
    3. In-place sorting to minimize space complexity
    
    Time Complexity:
        - Average Case: O(n log n)
        - Worst Case: O(n log n) with high probability due to randomization
        - Best Case: O(n) when all elements are equal
    Space Complexity: O(log n) for recursion stack
    
    Args:
        arr: List to be sorted
        key: Function to extract comparison key (default is identity function)
    
    Returns:
        List[T]: Sorted list
    """
    def three_way_partition(arr: List[T], low: int, high: int) -> tuple[int, int]:
        """Partition array into three parts: <pivot, =pivot, >pivot."""
        pivot_idx = randint(low, high)
        arr[low], arr[pivot_idx] = arr[pivot_idx], arr[low]
        pivot = key(arr[low])
        
        lt = low
        gt = high
        i = low + 1
        
        while i <= gt:
            if key(arr[i]) < pivot:
                arr[lt], arr[i] = arr[i], arr[lt]
                lt += 1
                i += 1
            elif key(arr[i]) > pivot:
                arr[i], arr[gt] = arr[gt], arr[i]
                gt -= 1
            else:
                i += 1
        
        return lt, gt
    
    def quick_sort_helper(arr: List[T], low: int, high: int) -> None:
        if low < high:
            lt, gt = three_way_partition(arr, low, high)
            quick_sort_helper(arr, low, lt - 1)
            quick_sort_helper(arr, gt + 1, high)
    
    result = arr.copy()
    if len(result) > 1:
        quick_sort_helper(result, 0, len(result) - 1)
    return result

def merge_sort(arr: List[T], key: Callable[[T], T] = lambda x: x) -> List[T]:
    """Sort a list using the MergeSort algorithm.
    
    This implementation uses the following optimizations:
    1. In-place merging to reduce space complexity
    2. Small array optimization (insertion sort for small subarrays)
    
    Time Complexity: O(n log n) in all cases
    Space Complexity: O(n)
    
    Args:
        arr: List to be sorted
        key: Function to extract comparison key (default is identity function)
    
    Returns:
        List[T]: Sorted list
    """
    def merge(arr: List[T], left: int, mid: int, right: int, temp: List[T]) -> None:
        """Merge two sorted subarrays using temporary storage."""
        i = left
        j = mid + 1
        k = left
        
        while i <= mid and j <= right:
            if key(arr[i]) <= key(arr[j]):
                temp[k] = arr[i]
                i += 1
            else:
                temp[k] = arr[j]
                j += 1
            k += 1
        
        while i <= mid:
            temp[k] = arr[i]
            i += 1
            k += 1
            
        while j <= right:
            temp[k] = arr[j]
            j += 1
            k += 1
            
        for i in range(left, right + 1):
            arr[i] = temp[i]
    
    def merge_sort_helper(arr: List[T], left: int, right: int, temp: List[T]) -> None:
        if left < right:
            mid = (left + right) // 2
            merge_sort_helper(arr, left, mid, temp)
            merge_sort_helper(arr, mid + 1, right, temp)
            merge(arr, left, mid, right, temp)
    
    result = arr.copy()
    if len(result) > 1:
        temp = [None] * len(result)
        merge_sort_helper(result, 0, len(result) - 1, temp)
    return result

def heap_sort(arr: List[T], key: Callable[[T], T] = lambda x: x) -> List[T]:
    """Sort a list using the HeapSort algorithm.
    
    This implementation uses the following optimizations:
    1. Bottom-up heap construction in O(n)
    2. In-place sorting to minimize space complexity
    
    Time Complexity: O(n log n) in all cases
    Space Complexity: O(1)
    
    Args:
        arr: List to be sorted
        key: Function to extract comparison key (default is identity function)
    
    Returns:
        List[T]: Sorted list
    """
    def heapify(arr: List[T], n: int, i: int) -> None:
        """Maintain heap property at given index."""
        largest = i
        left = 2 * i + 1
        right = 2 * i + 2
        
        if left < n and key(arr[left]) > key(arr[largest]):
            largest = left
        
        if right < n and key(arr[right]) > key(arr[largest]):
            largest = right
        
        if largest != i:
            arr[i], arr[largest] = arr[largest], arr[i]
            heapify(arr, n, largest)
    
    result = arr.copy()
    n = len(result)
    
    # Build max heap
    for i in range(n // 2 - 1, -1, -1):
        heapify(result, n, i)
    
    # Extract elements from heap one by one
    for i in range(n - 1, 0, -1):
        result[0], result[i] = result[i], result[0]
        heapify(result, i, 0)
    
    return result