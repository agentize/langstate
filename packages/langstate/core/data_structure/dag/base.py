from __future__ import annotations

"""
Abstract base classes and interfaces for Directed Acyclic Graph structures.
"""

from abc import abstractmethod
from typing import Any, Callable, Dict, Iterator, List, Optional, Set, Tuple, TypeVar

from ..graph.base import BaseGraph, BaseGraphEdge, BaseGraphNode

V = TypeVar("V")  # Node value
E = TypeVar("E")  # Edge metadata


class BaseDirectedAcyclicGraphEdge(BaseGraphEdge[V, E]):
    """Interface for DAG edge.

    A DAG edge connects a single source (prerequisite) to a target node.
    """

    @property
    @abstractmethod
    def target(self) -> "BaseDirectedAcyclicGraphNode[V, E]":
        """The prerequisite node (the node we depend on)."""
        pass

    @property
    @abstractmethod
    def sources(self) -> Set["BaseGraphNode[V, E]"]:
        """Source nodes (returns single-element set with target for DAG compatibility)."""
        pass

    @property
    @abstractmethod
    def metadata(self) -> Optional[E]:
        """Optional edge metadata."""
        pass

    @abstractmethod
    def source_ids(self) -> Set[str]:
        """Get IDs of all source nodes (returns single-element set for DAG)."""
        pass


class BaseDirectedAcyclicGraphNode(BaseGraphNode[V, E]):
    """Interface for DAG node."""

    @property
    @abstractmethod
    def id(self) -> str:
        """Unique identifier for the node."""
        pass

    @property
    @abstractmethod
    def value(self) -> Optional[V]:
        """Optional node value."""
        pass

    @property
    @abstractmethod
    def depends_on(self) -> Dict[str, "BaseDirectedAcyclicGraphEdge[V, E]"]:
        """Dependencies (this node depends on -> edge with node ref + metadata)."""
        pass

    @abstractmethod
    def prerequisites(self) -> Set[str]:
        """IDs of nodes this node depends on."""
        pass

    @abstractmethod
    def prerequisite_ids(self) -> Set[str]:
        """IDs of nodes this node depends on (alias for prerequisites)."""
        pass

    @abstractmethod
    def prerequisite_nodes(self) -> Set["BaseDirectedAcyclicGraphNode[V, E]"]:
        """Direct node references of prerequisites (fast traversal)."""
        pass

    @abstractmethod
    def is_ready(self, satisfied: Set[str]) -> bool:
        """True if all prerequisites are in `satisfied`."""
        pass

    @abstractmethod
    def __hash__(self) -> int:
        """Hash by node id."""
        pass

    @abstractmethod
    def __eq__(self, other: object) -> bool:
        """Equality by node id."""
        pass


class BaseDirectedAcyclicGraph(BaseGraph[V, E]):
    """Interface for Directed Acyclic Graph manager."""

    @abstractmethod
    def add_node(
        self, node_id: str, value: Optional[V] = None
    ) -> BaseDirectedAcyclicGraphNode[V, E]:
        """Add or update a node in the graph."""
        pass

    @abstractmethod
    def get_node(self, node_id: str) -> Optional[BaseDirectedAcyclicGraphNode[V, E]]:
        """Retrieve a node by ID."""
        pass

    @abstractmethod
    def add_edge(
        self,
        prereq_id: str,
        dep_id: str,
        *,
        metadata: Optional[E] = None,
        check_cycle: bool = True,
    ) -> None:
        """Create/refresh an edge `prereq_id -> dep_id`."""
        pass

    @abstractmethod
    def remove_edge(self, prereq_id: str, dep_id: str) -> None:
        """Remove an edge between two nodes."""
        pass

    @abstractmethod
    def remove_node(self, node_id: str) -> None:
        """Remove a node and all its edges."""
        pass

    @abstractmethod
    def prerequisites(self, node_id: str) -> Set[str]:
        """Get prerequisites of a node."""
        pass

    @abstractmethod
    def prerequisite_ids(self, node_id: str) -> Set[str]:
        """Get prerequisites of a node (alias for prerequisites)."""
        pass

    @abstractmethod
    def dependents(self, node_id: str) -> Set[str]:
        """Get dependents of a node."""
        pass

    @abstractmethod
    def ancestors(self, node_id: str) -> Set[str]:
        """All transitive prerequisites of `node_id`."""
        pass

    @abstractmethod
    def descendants(self, node_id: str) -> Set[str]:
        """All transitive dependents of `node_id`."""
        pass

    @abstractmethod
    def ready_nodes(self, satisfied: Set[str]) -> Set[str]:
        """Nodes that are ready given satisfied prerequisites."""
        pass

    @abstractmethod
    def topological_order(self) -> List[str]:
        """Return node IDs in topological order."""
        pass

    @abstractmethod
    def validate_acyclic(self) -> None:
        """Validate that the graph is acyclic."""
        pass

    @abstractmethod
    def iter_edges(self) -> Iterator[Tuple[str, str, Optional[E]]]:
        """Yield (prereq_id, dep_id, metadata) for all edges."""
        pass

    @abstractmethod
    def to_dot(self) -> str:
        """Export to Graphviz DOT format."""
        pass

    @abstractmethod
    def to_ascii_tree(
        self,
        root_nodes: Optional[List[str]] = None,
        node_label_fn: Optional[Callable[[str], str]] = None,
        edge_label_fn: Optional[Callable[[Optional[E]], str]] = None,
        max_depth: int = 10,
    ) -> str:
        """Generate ASCII tree representation."""
        pass

    @abstractmethod
    def to_mermaid(
        self,
        node_label_fn: Optional[Callable[[str], str]] = None,
        edge_label_fn: Optional[Callable[[Optional[E]], str]] = None,
        max_label_length: int = 30,
        root_nodes: Optional[List[str]] = None,
    ) -> str:
        """Export graph to Mermaid diagram format."""
        pass

    @abstractmethod
    def to_json_dict(self) -> Dict[str, Any]:
        """Export graph structure to JSON-serializable dict."""
        pass

    @abstractmethod
    def to_json(self, pretty: bool = True, indent: int = 2) -> str:
        """Export graph structure to a JSON string."""
        pass


__all__ = [
    "BaseDirectedAcyclicGraphEdge",
    "BaseDirectedAcyclicGraphNode",
    "BaseDirectedAcyclicGraph",
]
