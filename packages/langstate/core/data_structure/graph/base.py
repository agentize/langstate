from __future__ import annotations

"""
Abstract base classes for generic graph structures.

This module provides common interfaces for directed graph structures,
serving as a foundation for specialized implementations like DAG and DAH.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Generic, List, Optional, Set, TypeVar

V = TypeVar("V")  # Node value
E = TypeVar("E")  # Edge metadata


class BaseGraphEdge(ABC, Generic[V, E]):
    """Base interface for graph edge.
    
    An edge connects one or more source nodes to a target node.
    For simple graphs, sources contain a single node.
    For hypergraphs, sources can contain multiple nodes.
    """
    
    @property
    @abstractmethod
    def sources(self) -> Set["BaseGraphNode[V, E]"]:
        """Source/prerequisite node references."""
        pass
    
    @property
    @abstractmethod
    def metadata(self) -> Optional[E]:
        """Optional edge metadata (weight, label, constraint, etc.)."""
        pass
    
    @abstractmethod
    def source_ids(self) -> Set[str]:
        """Get IDs of all source nodes."""
        pass


class BaseGraphNode(ABC, Generic[V, E]):
    """Base interface for graph node."""
    
    @property
    @abstractmethod
    def id(self) -> str:
        """Unique identifier for the node."""
        pass
    
    @property
    @abstractmethod
    def value(self) -> Optional[V]:
        """Optional node value/payload."""
        pass
    
    @abstractmethod
    def prerequisite_ids(self) -> Set[str]:
        """IDs of nodes this node depends on (prerequisites)."""
        pass
    
    @abstractmethod
    def dependents(self) -> Set["BaseGraphNode[V, E]"]:
        """Nodes that depend on this node."""
        pass
    
    @abstractmethod
    def is_ready(self, satisfied: Set[str]) -> bool:
        """Check if node is ready to process given satisfied prerequisites.
        
        The exact semantics depend on the graph type:
        - Simple graphs: all prerequisites must be satisfied
        - Hypergraphs: at least one complete hyperedge must be satisfied
        """
        pass
    
    @abstractmethod
    def __hash__(self) -> int:
        """Hash by node id."""
        pass
    
    @abstractmethod
    def __eq__(self, other: object) -> bool:
        """Equality by node id."""
        pass


class BaseGraph(ABC, Generic[V, E]):
    """Base interface for directed graph manager.
    
    Provides common operations for managing nodes, edges, and analyzing
    graph structure (topology, dependencies, serialization).
    """
    
    @property
    @abstractmethod
    def nodes(self) -> Dict[str, "BaseGraphNode[V, E]"]:
        """All nodes in the graph."""
        pass
    
    @abstractmethod
    def add_node(self, node_id: str, value: Optional[V] = None) -> BaseGraphNode[V, E]:
        """Add or update a node in the graph.
        
        Args:
            node_id: Unique identifier for the node
            value: Optional node payload
            
        Returns:
            The created or updated node
        """
        pass
    
    @abstractmethod
    def get_node(self, node_id: str) -> Optional[BaseGraphNode[V, E]]:
        """Retrieve a node by ID.
        
        Args:
            node_id: The node identifier
            
        Returns:
            The node if found, None otherwise
        """
        pass
    
    @abstractmethod
    def remove_node(self, node_id: str) -> None:
        """Remove a node and all its edges.
        
        Args:
            node_id: The node to remove
        """
        pass
    
    @abstractmethod
    def prerequisite_ids(self, node_id: str) -> Set[str]:
        """Get prerequisite IDs of a node.
        
        Args:
            node_id: The node to query
            
        Returns:
            Set of prerequisite node IDs
        """
        pass
    
    @abstractmethod
    def dependents(self, node_id: str) -> Set[str]:
        """Get dependents of a node.
        
        Args:
            node_id: The node to query
            
        Returns:
            Set of dependent node IDs
        """
        pass
    
    @abstractmethod
    def ancestors(self, node_id: str) -> Set[str]:
        """Get all transitive prerequisites of a node.
        
        Args:
            node_id: The node to query
            
        Returns:
            Set of all ancestor node IDs
        """
        pass
    
    @abstractmethod
    def descendants(self, node_id: str) -> Set[str]:
        """Get all transitive dependents of a node.
        
        Args:
            node_id: The node to query
            
        Returns:
            Set of all descendant node IDs
        """
        pass
    
    @abstractmethod
    def ready_nodes(self, satisfied: Set[str]) -> Set[str]:
        """Find nodes that are ready given satisfied prerequisites.
        
        Args:
            satisfied: Set of node IDs that are already satisfied
            
        Returns:
            Set of node IDs that are ready to process
        """
        pass
    
    @abstractmethod
    def topological_order(self) -> List[str]:
        """Return node IDs in topological order.
        
        Returns:
            List of node IDs in dependency order
            
        Raises:
            Exception if graph contains cycles
        """
        pass
    
    @abstractmethod
    def validate_acyclic(self) -> None:
        """Validate that the graph is acyclic.
        
        Raises:
            Exception if cycles are detected
        """
        pass
    
    @abstractmethod
    def to_dot(self) -> str:
        """Export to Graphviz DOT format.
        
        Returns:
            DOT format string
        """
        pass
    
    @abstractmethod
    def to_mermaid(
        self,
        node_label_fn: Optional[Callable[[str], str]] = None,
        edge_label_fn: Optional[Callable[[Optional[E]], str]] = None,
        max_label_length: int = 30,
    ) -> str:
        """Export to Mermaid diagram format.
        
        Args:
            node_label_fn: Optional function to customize node labels
            edge_label_fn: Optional function to customize edge labels
            max_label_length: Maximum label length before truncation
            
        Returns:
            Mermaid format string
        """
        pass
    
    @abstractmethod
    def to_json_dict(self) -> Dict[str, Any]:
        """Export graph structure to JSON-serializable dict.
        
        Returns:
            Dictionary representation of the graph
        """
        pass
    
    @abstractmethod
    def to_json(self, pretty: bool = True, indent: int = 2) -> str:
        """Export graph structure to a JSON string.
        
        Args:
            pretty: Whether to format the output
            indent: Indentation level for pretty printing
            
        Returns:
            JSON string representation
        """
        pass
    
    @abstractmethod
    def to_ascii_tree(
        self,
        root_nodes: Optional[List[str]] = None,
        node_label_fn: Optional[Callable[[str], str]] = None,
        edge_label_fn: Optional[Callable[[Optional[E]], str]] = None,
        max_depth: int = 10,
    ) -> str:
        """Generate ASCII tree representation.
        
        Args:
            root_nodes: Optional list of root nodes to start from
            node_label_fn: Optional function to customize node labels
            edge_label_fn: Optional function to customize edge labels
            max_depth: Maximum tree depth to render
            
        Returns:
            ASCII tree string
        """
        pass


__all__ = [
    "BaseGraphEdge",
    "BaseGraphNode",
    "BaseGraph",
]
