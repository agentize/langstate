from __future__ import annotations

"""
Abstract base classes and interfaces for Directed Acyclic Hypergraph structures.
"""

from abc import abstractmethod
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    Set,
    Tuple,
    TypeVar,
)

from ..graph.base import BaseGraph, BaseGraphEdge, BaseGraphNode

V = TypeVar("V")  # Node value
E = TypeVar("E")  # Edge metadata


class BaseDirectedAcyclicHypergraphEdge(BaseGraphEdge[V, E]):
    """Interface for DAH hyperedge.

    A hyperedge can connect multiple source nodes to a target node.
    """

    @property
    @abstractmethod
    def id(self) -> str:
        """Stable identifier of this hyperedge."""
        pass

    @property
    @abstractmethod
    def metadata(self) -> Optional[E]:
        """Optional metadata."""
        pass

    @abstractmethod
    def source_ids(self) -> Set[str]:
        """Get IDs of all source nodes."""
        pass


class BaseDirectedAcyclicHypergraphNode(BaseGraphNode[V, E]):
    """Interface for DAH node."""

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
    def in_edges(self) -> Dict[str, "BaseDirectedAcyclicHypergraphEdge[V, E]"]:
        """Incoming hyperedges."""
        pass

    @abstractmethod
    def prerequisite_ids(self) -> Set[str]:
        """All distinct source node IDs feeding into this node via hyperedges."""
        pass

    @abstractmethod
    def hyperedges(self) -> List["BaseDirectedAcyclicHypergraphEdge[V, E]"]:
        """Get all incoming hyperedges."""
        pass

    @abstractmethod
    def is_ready(self, satisfied: Set[str]) -> bool:
        """True if there exists at least one hyperedge whose sources are all satisfied."""
        pass

    @abstractmethod
    def __hash__(self) -> int:
        """Hash by node id."""
        pass

    @abstractmethod
    def __eq__(self, other: object) -> bool:
        """Equality by node id."""
        pass


class BaseDirectedAcyclicHypergraph(BaseGraph[V, E]):
    """Interface for Directed Acyclic Hypergraph manager."""

    @abstractmethod
    def add_node(
        self, node_id: str, value: Optional[V] = None
    ) -> BaseDirectedAcyclicHypergraphNode[V, E]:
        """Add or update a node in the hypergraph."""
        pass

    @abstractmethod
    def get_node(
        self, node_id: str
    ) -> Optional[BaseDirectedAcyclicHypergraphNode[V, E]]:
        """Retrieve a node by ID."""
        pass

    @abstractmethod
    def add_hyperedge(
        self,
        sources: Iterable[str],
        target_id: str,
        *,
        metadata: Optional[E] = None,
        edge_id: Optional[str] = None,
        check_cycle: bool = True,
    ) -> str:
        """Create or replace a hyperedge from `sources` to `target_id`."""
        pass

    @abstractmethod
    def remove_hyperedge(self, edge_id: str, target_id: str) -> None:
        """Remove a hyperedge."""
        pass

    @abstractmethod
    def remove_node(self, node_id: str) -> None:
        """Remove a node and all its hyperedges."""
        pass

    @abstractmethod
    def prerequisite_ids(self, node_id: str) -> Set[str]:
        """Get prerequisite IDs of a node."""
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
        """Validate that the hypergraph is acyclic."""
        pass

    @abstractmethod
    def iter_hyperedges(self) -> Iterator[Tuple[Set[str], str, Optional[E], str]]:
        """Yield (source_ids, target_id, metadata, edge_id) for all hyperedges."""
        pass

    @abstractmethod
    def add_edge(
        self,
        prereq_id: str,
        dep_id: str,
        *,
        metadata: Optional[E] = None,
        check_cycle: bool = True,
    ) -> str:
        """Backward compatible helper matching old DAG API (creates 1-source hyperedge)."""
        pass

    @abstractmethod
    def to_dot(self) -> str:
        """Export to Graphviz DOT format."""
        pass

    @abstractmethod
    def to_mermaid(
        self,
        node_label_fn: Optional[Callable[[str], str]] = None,
        edge_label_fn: Optional[Callable[[Optional[E]], str]] = None,
        max_label_length: int = 30,
    ) -> str:
        """Export to Mermaid format."""
        pass

    @abstractmethod
    def to_json_dict(self) -> Dict[str, Any]:
        """Export hypergraph structure to JSON-serializable dict."""
        pass

    @abstractmethod
    def to_json(self, pretty: bool = True, indent: int = 2) -> str:
        """Export hypergraph structure to a JSON string."""
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


__all__ = [
    "BaseDirectedAcyclicHypergraphEdge",
    "BaseDirectedAcyclicHypergraphNode",
    "BaseDirectedAcyclicHypergraph",
]
