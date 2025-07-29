"""Common Design Patterns implementations frequently used in software engineering."""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from threading import Lock

# Creational Patterns

class Singleton(type):
    """Singleton Pattern implementation as a metaclass.
    
    Ensures a class has only one instance and provides global access point.
    Common at: Microsoft, Amazon, Google
    """
    _instances = {}
    _lock = Lock()
    
    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                cls._instances[cls] = super().__call__(*args, **kwargs)
            return cls._instances[cls]

class Builder:
    """Builder Pattern implementation.
    
    Separates complex object construction from its representation.
    Common at: Google, Meta, Amazon
    """
    def __init__(self):
        self.reset()
    
    def reset(self) -> None:
        self._product = Product()
    
    def set_part_a(self, value: str) -> None:
        self._product.add(f"PartA: {value}")
    
    def set_part_b(self, value: str) -> None:
        self._product.add(f"PartB: {value}")
    
    def get_result(self) -> 'Product':
        product = self._product
        self.reset()
        return product

class Product:
    def __init__(self):
        self.parts = []
    
    def add(self, part: str) -> None:
        self.parts.append(part)

# Structural Patterns

class Adapter:
    """Adapter Pattern implementation.
    
    Allows incompatible interfaces to work together.
    Common at: Microsoft, Amazon, Meta
    """
    def __init__(self, adaptee):
        self.adaptee = adaptee
    
    def specific_request(self) -> str:
        return f"Adapter: {self.adaptee.different_request()}"

class Decorator(ABC):
    """Decorator Pattern implementation.
    
    Attaches additional responsibilities to objects dynamically.
    Common at: Netflix, Amazon, Google
    """
    def __init__(self, component):
        self._component = component
    
    @abstractmethod
    def operation(self) -> str:
        pass

class ConcreteDecorator(Decorator):
    def operation(self) -> str:
        return f"Decorator({self._component.operation()})"

# Behavioral Patterns

class Observer:
    """Observer Pattern implementation.
    
    Defines one-to-many dependency between objects.
    Common at: Meta, Google, Twitter
    """
    
    class Subject:
        def __init__(self):
            self._observers: List['Observer.ConcreteObserver'] = []
            self._state = None
        
        @property
        def state(self) -> Any:
            return self._state
        
        @state.setter
        def state(self, value: Any) -> None:
            self._state = value
            self._notify()
        
        def attach(self, observer: 'Observer.ConcreteObserver') -> None:
            self._observers.append(observer)
        
        def detach(self, observer: 'Observer.ConcreteObserver') -> None:
            self._observers.remove(observer)
        
        def _notify(self) -> None:
            for observer in self._observers:
                observer.update(self._state)
    
    class ConcreteObserver:
        def __init__(self):
            self.state = None
        
        def update(self, state: Any) -> None:
            self.state = state

class Strategy:
    """Strategy Pattern implementation.
    
    Defines a family of algorithms and makes them interchangeable.
    Common at: Amazon, Google, Trading Companies
    """
    
    def __init__(self, strategy=None):
        self._strategy = strategy
    
    def set_strategy(self, strategy) -> None:
        self._strategy = strategy
    
    def execute(self, *args, **kwargs) -> Any:
        if self._strategy:
            return self._strategy.execute(*args, **kwargs)
        return None

class Command(ABC):
    """Command Pattern implementation.
    
    Encapsulates a request as an object.
    Common at: Microsoft, Gaming Companies
    """
    
    @abstractmethod
    def execute(self) -> None:
        pass
    
    @abstractmethod
    def undo(self) -> None:
        pass

class State(ABC):
    """State Pattern implementation.
    
    Allows an object to alter its behavior when its internal state changes.
    Common at: Gaming Companies, UI Framework Companies
    """
    
    @abstractmethod
    def handle(self) -> str:
        pass
    
    @abstractmethod
    def switch(self, context) -> None:
        pass