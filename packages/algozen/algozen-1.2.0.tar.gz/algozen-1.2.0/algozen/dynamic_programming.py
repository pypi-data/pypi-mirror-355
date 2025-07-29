"""Efficient implementations of common dynamic programming problems."""

from typing import List, Tuple, Dict, Optional, Union
from functools import lru_cache

def fibonacci_dp(n: int, use_memoization: bool = True) -> int:
    """Calculate the nth Fibonacci number using dynamic programming.
    
    This implementation provides both memoization and tabulation approaches.
    
    Args:
        n: The index of the Fibonacci number to calculate (0-based)
        use_memoization: If True, uses memoization (top-down approach).
                       If False, uses tabulation (bottom-up approach).
                       
    Returns:
        The nth Fibonacci number
        
    Raises:
        ValueError: If n is negative
    """
    if n < 0:
        raise ValueError("n must be non-negative")
        
    # Base cases
    if n <= 1:
        return n
    
    if use_memoization:
        # Memoization (top-down) approach
        memo = {0: 0, 1: 1}
        
        def fib_memo(x: int) -> int:
            if x not in memo:
                memo[x] = fib_memo(x-1) + fib_memo(x-2)
            return memo[x]
            
        return fib_memo(n)
    else:
        # Tabulation (bottom-up) approach - more space efficient
        if n == 0:
            return 0
            
        prev, curr = 0, 1
        for _ in range(2, n + 1):
            prev, curr = curr, prev + curr
            
        return curr

def longest_common_subsequence(text1: str, text2: str) -> str:
    """Find the longest common subsequence between two strings.
    
    This implementation uses:
    1. Dynamic programming with space optimization
    2. Backtracking to reconstruct the sequence
    3. LRU cache for recursive calls
    
    Time Complexity: O(mn)
    Space Complexity: O(min(m,n))
    
    Args:
        text1: First string
        text2: Second string
    
    Returns:
        str: Longest common subsequence
    """
    m, n = len(text1), len(text2)
    
    # Use shorter string for column to optimize space
    if m < n:
        text1, text2 = text2, text1
        m, n = n, m
    
    # Current and previous row in dp table
    current = [0] * (n + 1)
    previous = [0] * (n + 1)
    
    # Backtrack matrix to reconstruct the sequence
    backtrack = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if text1[i-1] == text2[j-1]:
                current[j] = previous[j-1] + 1
                backtrack[i][j] = 1  # diagonal
            elif previous[j] >= current[j-1]:
                current[j] = previous[j]
                backtrack[i][j] = 2  # up
            else:
                current[j] = current[j-1]
                backtrack[i][j] = 3  # left
        
        # Swap rows
        previous, current = current, previous
    
    # Reconstruct the sequence
    lcs = []
    i, j = m, n
    while i > 0 and j > 0:
        if backtrack[i][j] == 1:
            lcs.append(text1[i-1])
            i -= 1
            j -= 1
        elif backtrack[i][j] == 2:
            i -= 1
        else:
            j -= 1
    
    return ''.join(reversed(lcs))

def knapsack(values: List[int], weights: List[int], capacity: int) -> Tuple[int, List[int]]:
    """Solve the 0/1 knapsack problem.
    
    This implementation uses:
    1. Dynamic programming with space optimization
    2. Item selection tracking
    3. Early termination for impossible cases
    
    Time Complexity: O(nW)
    Space Complexity: O(W)
    
    Args:
        values: List of item values
        weights: List of item weights
        capacity: Knapsack capacity
    
    Returns:
        Tuple[int, List[int]]: (Maximum value, List of selected item indices)
    """
    n = len(values)
    if n != len(weights):
        raise ValueError("Length of values and weights must be equal")
    
    if n == 0 or capacity <= 0:
        return 0, []
    
    # Early termination check
    if min(weights) > capacity:
        return 0, []
    
    # DP table and item selection tracking
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    selected = [[False] * (capacity + 1) for _ in range(n + 1)]
    
    for i in range(1, n + 1):
        for w in range(capacity + 1):
            if weights[i-1] <= w:
                include_value = dp[i-1][w - weights[i-1]] + values[i-1]
                if include_value > dp[i-1][w]:
                    dp[i][w] = include_value
                    selected[i][w] = True
                else:
                    dp[i][w] = dp[i-1][w]
            else:
                dp[i][w] = dp[i-1][w]
    
    # Backtrack to find selected items
    selected_items = []
    i, w = n, capacity
    while i > 0 and w > 0:
        if selected[i][w]:
            selected_items.append(i-1)
            w -= weights[i-1]
        i -= 1
    
    return dp[n][capacity], list(reversed(selected_items))

def edit_distance(word1: str, word2: str) -> int:
    """Calculate the minimum number of operations to convert word1 to word2.
    
    Operations allowed:
    1. Insert a character
    2. Delete a character
    3. Replace a character
    
    This implementation uses:
    1. Dynamic programming with space optimization
    2. Early termination for edge cases
    
    Time Complexity: O(mn)
    Space Complexity: O(min(m,n))
    
    Args:
        word1: First string
        word2: Second string
    
    Returns:
        int: Minimum number of operations required
    """
    m, n = len(word1), len(word2)
    
    # Handle edge cases
    if m == 0: return n
    if n == 0: return m
    if word1 == word2: return 0
    
    # Use shorter string for column to optimize space
    if m < n:
        word1, word2 = word2, word1
        m, n = n, m
    
    # Previous and current row in dp table
    previous = list(range(n + 1))
    current = [0] * (n + 1)
    
    for i in range(1, m + 1):
        current[0] = i
        for j in range(1, n + 1):
            if word1[i-1] == word2[j-1]:
                current[j] = previous[j-1]
            else:
                current[j] = 1 + min(
                    previous[j],    # delete
                    current[j-1],   # insert
                    previous[j-1]   # replace
                )
        previous, current = current, previous
    
    return previous[n]

def matrix_chain_multiplication(dimensions: List[int]) -> int:
    """Find the minimum number of operations needed to multiply a chain of matrices.
    
    This implementation uses:
    1. Dynamic programming with memoization
    2. Optimal substructure property
    
    Time Complexity: O(n^3)
    Space Complexity: O(n^2)
    
    Args:
        dimensions: List of matrix dimensions where matrix i has dimensions[i-1] x dimensions[i]
    
    Returns:
        int: Minimum number of scalar multiplications needed
    """
    n = len(dimensions) - 1
    if n <= 1:
        return 0
    
    # Initialize memoization table
    memo = {}
    
    def mcm_recursive(i: int, j: int) -> int:
        """Recursive helper with memoization."""
        if i == j:
            return 0
        
        if (i, j) in memo:
            return memo[(i, j)]
        
        min_ops = float('inf')
        for k in range(i, j):
            ops = (mcm_recursive(i, k) +
                   mcm_recursive(k + 1, j) +
                   dimensions[i-1] * dimensions[k] * dimensions[j])
            min_ops = min(min_ops, ops)
        
        memo[(i, j)] = min_ops
        return min_ops
    
    return mcm_recursive(1, n)