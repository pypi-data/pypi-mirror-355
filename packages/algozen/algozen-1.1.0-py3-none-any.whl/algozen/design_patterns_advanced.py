"""Advanced Design Patterns for complex system architectures."""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable
from threading import Lock
from datetime import datetime
import json

class Specification(ABC):
    """Specification Pattern for business rules encapsulation.
    
    Common at: Enterprise Software Companies, E-commerce Companies
    Use Case: Complex business rules and validations
    """
    
    @abstractmethod
    def is_satisfied_by(self, candidate: Any) -> bool:
        pass
    
    def __and__(self, other: 'Specification') -> 'AndSpecification':
        return AndSpecification(self, other)
    
    def __or__(self, other: 'Specification') -> 'OrSpecification':
        return OrSpecification(self, other)
    
    def __not__(self) -> 'NotSpecification':
        return NotSpecification(self)

class AndSpecification(Specification):
    def __init__(self, *specifications: Specification):
        self.specifications = specifications
    
    def is_satisfied_by(self, candidate: Any) -> bool:
        return all(spec.is_satisfied_by(candidate) for spec in self.specifications)

class OrSpecification(Specification):
    def __init__(self, *specifications: Specification):
        self.specifications = specifications
    
    def is_satisfied_by(self, candidate: Any) -> bool:
        return any(spec.is_satisfied_by(candidate) for spec in self.specifications)

class NotSpecification(Specification):
    def __init__(self, specification: Specification):
        self.specification = specification
    
    def is_satisfied_by(self, candidate: Any) -> bool:
        return not self.specification.is_satisfied_by(candidate)

class PriceSpecification(Specification):
    def __init__(self, min_price: float, max_price: float):
        self.min_price = min_price
        self.max_price = max_price
    
    def is_satisfied_by(self, price: float) -> bool:
        return self.min_price <= price <= self.max_price

class Flyweight:
    """Flyweight Pattern for efficient memory usage with shared state.
    
    Common at: Google, Amazon, Gaming Companies
    Use Case: Managing large numbers of similar objects
    """
    
    def __init__(self):
        self._shared_state: Dict[str, Any] = {}
    
    def get_shared_state(self, key: str) -> Any:
        return self._shared_state.get(key)
    
    def add_shared_state(self, key: str, value: Any) -> None:
        self._shared_state[key] = value

class FlyweightFactory:
    _flyweights: Dict[str, Flyweight] = {}
    _lock = Lock()
    
    @classmethod
    def get_flyweight(cls, key: str) -> Flyweight:
        with cls._lock:
            if key not in cls._flyweights:
                cls._flyweights[key] = Flyweight()
            return cls._flyweights[key]

class Composite:
    """Composite Pattern for tree-like object structures.
    
    Common at: Meta, Microsoft, UI Framework Companies
    Use Case: Building complex hierarchical structures
    """
    
    def __init__(self, name: str):
        self.name = name
        self.children: List['Composite'] = []
        self.parent: Optional['Composite'] = None
    
    def add(self, component: 'Composite') -> None:
        component.parent = self
        self.children.append(component)
    
    def remove(self, component: 'Composite') -> None:
        component.parent = None
        self.children.remove(component)
    
    def is_composite(self) -> bool:
        return bool(self.children)
    
    def operation(self) -> str:
        results = [child.operation() for child in self.children]
        return f"{self.name}({', '.join(results)})"

class Prototype(ABC):
    """Prototype Pattern for object cloning.
    
    Common at: Gaming Companies, CAD Software Companies
    Use Case: Creating complex objects from templates
    """
    
    @abstractmethod
    def clone(self) -> 'Prototype':
        pass
    
    @abstractmethod
    def deep_clone(self) -> 'Prototype':
        pass

class Bridge(ABC):
    """Bridge Pattern for platform independence.
    
    Common at: Microsoft, Oracle, Cross-platform Companies
    Use Case: Separating abstraction from implementation
    """
    
    def __init__(self, implementation):
        self.implementation = implementation
    
    @abstractmethod
    def operation(self) -> str:
        pass

class Proxy:
    """Proxy Pattern with various proxy types.
    
    Common at: AWS, Google Cloud, Security Companies
    Use Case: Controlling access to objects
    """
    
    def __init__(self, subject):
        self._subject = subject
        self._access_log = []
    
    def request(self, *args, **kwargs) -> Any:
        self._log_access()
        return self._subject.request(*args, **kwargs)
    
    def _log_access(self) -> None:
        self._access_log.append({
            'time': datetime.now().isoformat(),
            'method': 'request'
        })
    
    def get_access_log(self) -> str:
        return json.dumps(self._access_log, indent=2)