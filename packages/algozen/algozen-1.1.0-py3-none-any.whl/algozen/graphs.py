"""Graph algorithms implementation with optimized traversal and path finding."""

from typing import Dict, List, Set, Optional, TypeVar, Generic, Tuple
from collections import defaultdict, deque
from heapq import heappush, heappop
from math import inf

T = TypeVar('T')

class Graph(Generic[T]):
    """Graph implementation supporting both directed and undirected graphs.
    
    Features:
    1. Adjacency list representation for space efficiency
    2. Support for weighted edges
    3. Optional direction for edges
    4. Efficient traversal algorithms
    """
    
    def __init__(self, directed: bool = False) -> None:
        """Initialize an empty graph.
        
        Args:
            directed: Whether the graph is directed (default: False)
        """
        self.graph: Dict[T, Dict[T, float]] = defaultdict(dict)
        self.directed = directed
    
    def add_vertex(self, vertex: T) -> None:
        """Add a vertex to the graph.
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        
        Args:
            vertex: Vertex to add
        """
        if vertex not in self.graph:
            self.graph[vertex] = {}
    
    def add_edge(self, source: T, dest: T, weight: float = 1.0) -> None:
        """Add an edge to the graph.
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        
        Args:
            source: Source vertex
            dest: Destination vertex
            weight: Edge weight (default: 1.0)
        """
        self.graph[source][dest] = weight
        if not self.directed:
            self.graph[dest][source] = weight
    
    def remove_edge(self, source: T, dest: T) -> None:
        """Remove an edge from the graph.
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        
        Args:
            source: Source vertex
            dest: Destination vertex
        """
        if dest in self.graph[source]:
            del self.graph[source][dest]
            if not self.directed and source in self.graph[dest]:
                del self.graph[dest][source]
    
    def get_vertices(self) -> Set[T]:
        """Get all vertices in the graph.
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        
        Returns:
            Set[T]: Set of all vertices
        """
        return set(self.graph.keys())
    
    def get_edges(self) -> List[Tuple[T, T, float]]:
        """Get all edges in the graph.
        
        Time Complexity: O(V + E)
        Space Complexity: O(E)
        
        Returns:
            List[Tuple[T, T, float]]: List of (source, dest, weight) tuples
        """
        edges = []
        seen = set()
        
        for source in self.graph:
            for dest, weight in self.graph[source].items():
                if not self.directed:
                    if (source, dest) not in seen and (dest, source) not in seen:
                        edges.append((source, dest, weight))
                        seen.add((source, dest))
                else:
                    edges.append((source, dest, weight))
        
        return edges
    
    def bfs(self, start: T) -> List[T]:
        """Perform breadth-first search traversal.
        
        Time Complexity: O(V + E)
        Space Complexity: O(V)
        
        Args:
            start: Starting vertex
            
        Returns:
            List[T]: List of vertices in BFS order
        """
        visited = set([start])
        queue = deque([start])
        result = []
        
        while queue:
            vertex = queue.popleft()
            result.append(vertex)
            
            for neighbor in self.graph[vertex]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        
        return result
    
    def dfs(self, start: T) -> List[T]:
        """Perform depth-first search traversal.
        
        Time Complexity: O(V + E)
        Space Complexity: O(V)
        
        Args:
            start: Starting vertex
            
        Returns:
            List[T]: List of vertices in DFS order
        """
        visited = set()
        result = []
        
        def dfs_helper(vertex: T) -> None:
            visited.add(vertex)
            result.append(vertex)
            
            for neighbor in self.graph[vertex]:
                if neighbor not in visited:
                    dfs_helper(neighbor)
        
        dfs_helper(start)
        return result
    
    def shortest_path(self, start: T, end: T) -> Tuple[List[T], float]:
        """Find shortest path between two vertices using Dijkstra's algorithm.
        
        Time Complexity: O((V + E) log V)
        Space Complexity: O(V)
        
        Args:
            start: Starting vertex
            end: Ending vertex
            
        Returns:
            Tuple[List[T], float]: (Path as list of vertices, total distance)
        """
        distances = {vertex: inf for vertex in self.graph}
        distances[start] = 0
        previous = {vertex: None for vertex in self.graph}
        pq = [(0, start)]
        visited = set()
        
        while pq:
            current_distance, current_vertex = heappop(pq)
            
            if current_vertex == end:
                path = []
                while current_vertex:
                    path.append(current_vertex)
                    current_vertex = previous[current_vertex]
                return path[::-1], current_distance
            
            if current_vertex in visited:
                continue
            
            visited.add(current_vertex)
            
            for neighbor, weight in self.graph[current_vertex].items():
                distance = current_distance + weight
                
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous[neighbor] = current_vertex
                    heappush(pq, (distance, neighbor))
        
        return [], inf
    
    def is_cyclic(self) -> bool:
        """Check if the graph contains a cycle.
        
        Time Complexity: O(V + E)
        Space Complexity: O(V)
        
        Returns:
            bool: True if graph contains a cycle, False otherwise
        """
        visited = set()
        rec_stack = set()
        
        def has_cycle(vertex: T) -> bool:
            visited.add(vertex)
            rec_stack.add(vertex)
            
            for neighbor in self.graph[vertex]:
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(vertex)
            return False
        
        for vertex in self.graph:
            if vertex not in visited:
                if has_cycle(vertex):
                    return True
        
        return False