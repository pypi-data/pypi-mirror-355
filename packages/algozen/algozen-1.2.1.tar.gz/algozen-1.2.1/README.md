# AlgoZen: Your Complete DSA and Interview Preparation Library

AlgoZen is a comprehensive Python library that provides efficient implementations of data structures, algorithms, and common interview problems. It's designed to help developers practice and prepare for technical interviews at top tech companies.

## Features

### Core Data Structures
- Linked Lists (Singly and Doubly linked)
- Stack and Queue implementations
- Trees (Binary Tree, BST, AVL Tree)
- Hash Table with dynamic resizing
- Heap (MinHeap and MaxHeap variants)

### Advanced Data Structures
- Skip List (probabilistic data structure)
- Disjoint Set (Union-Find)
- Trie (Prefix Tree)
- Fenwick Tree (Binary Indexed Tree)
- Segment Tree (for range queries)

### Algorithms
- Sorting (Quick Sort, Merge Sort, Heap Sort)
- Searching (Binary Search, Linear Search, Interpolation Search)
- Graph algorithms with BFS, DFS, and Dijkstra's
- Dynamic Programming solutions

### Design Patterns
#### Basic Patterns
- Creational: Singleton, Builder
- Structural: Adapter, Decorator
- Behavioral: Observer, Strategy, Command
- Chain of Responsibility
- State and Memento

#### Advanced Patterns
- Flyweight (memory optimization)
- Composite (tree structures)
- Prototype (object cloning)
- Bridge (platform independence)
- Proxy (access control)
- Interpreter (DSL parsing)
- Visitor (extending functionality)
- Mediator (object interactions)
- Specification (business rules)

### System Design Components
- Rate Limiter
- Consistent Hashing
- Bloom Filter
- Leader Election
- Event Bus
- Circuit Breaker

### Interview Preparation
- Common DSA problems from top tech companies
- System Design implementations
- Time and space complexity analysis
- Best practices and optimization techniques

## Installation

```bash
pip install algozen
```

## Quick Start

```python
from algozen.data_structures import LinkedList, BST, MinHeap
from algozen.data_structures.advanced import SkipList, Trie
from algozen.sorting import quick_sort, merge_sort
from algozen.interview_prep import two_sum, lru_cache
from algozen.system_design import RateLimiter, ConsistentHashing
from algozen.design_patterns import Singleton, Observer
from algozen.design_patterns_advanced import Flyweight, Specification

# Use advanced data structures
skip_list = SkipList()
skip_list.insert(5)
skip_list.insert(10)

trie = Trie()
trie.insert("hello")
print(trie.search("hello"))  # True

# Apply advanced design patterns
flyweight_factory = FlyweightFactory()
flyweight = flyweight_factory.get_flyweight("shared_state")

# Create business rules
class PriceSpecification(Specification):
    def __init__(self, min_price: float, max_price: float):
        self.min_price = min_price
        self.max_price = max_price
    
    def is_satisfied_by(self, price: float) -> bool:
        return self.min_price <= price <= self.max_price

# Combine specifications
low_price = PriceSpecification(0, 50)
high_price = PriceSpecification(100, float('inf'))
medium_or_high = low_price.or_(high_price)
```

## Documentation

For detailed documentation and examples, visit our [documentation page](https://algozen.readthedocs.io/).

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes and version history.

## Support

If you have any questions or need help, please:
1. Check our [documentation](https://algozen.readthedocs.io/)
2. Open an issue on GitHub
3. Join our community discussions

## Acknowledgments

Special thanks to all contributors who have helped make AlgoZen a comprehensive resource for DSA and interview preparation.