from __future__ import annotations

"""
Schema definitions (dataclasses) for Directed Acyclic Hypergraph structures.
"""

from dataclasses import dataclass, field
from typing import Dict, Generic, List, Optional, Set, TypeVar
import weakref

V = TypeVar("V")  # Node value
E = TypeVar("E")  # Edge metadata


@dataclass
class DirectedAcyclicHypergraphEdge(Generic[V, E]):
    """Hyperedge stored on the target node: {sources...} -hyperedge-> target.

    Attributes
    ----------
    id: str
        Stable identifier of this hyperedge (unique within the graph).
    sources: Set[DirectedAcyclicHypergraphNode[V, E]]
        Source/prerequisite node references.
    metadata: Optional[E]
        Optional metadata (weight, label, constraint, etc.).
    """

    id: str
    sources: Set["DirectedAcyclicHypergraphNode[V, E]"]
    metadata: Optional[E] = None

    def source_ids(self) -> Set[str]:
        return {n.id for n in self.sources}


@dataclass
class DirectedAcyclicHypergraphNode(Generic[V, E]):
    """Represents a vertex in a Directed Acyclic Hypergraph.

    Local concerns only; global logic in manager. Hashable by id.
    """

    id: str
    value: Optional[V] = None

    # Incoming hyperedges: each provides multiple sources leading to this node
    in_edges: Dict[str, "DirectedAcyclicHypergraphEdge[V, E]"] = field(default_factory=dict)  # type: ignore[misc]

    # Reverse mirror: who depends on me (any node whose hyperedge lists me as a source)
    _dependents: "weakref.WeakSet[DirectedAcyclicHypergraphNode[V, E]]" = field(  # type: ignore[misc]
        default_factory=weakref.WeakSet, repr=False
    )

    # ---- Reverse mirror management (for use by DAH manager) ----------------
    def add_dependent(self, node: "DirectedAcyclicHypergraphNode[V, E]") -> None:
        """Register a node as depending on this node."""
        self._dependents.add(node)

    def remove_dependent(self, node: "DirectedAcyclicHypergraphNode[V, E]") -> None:
        """Unregister a node as depending on this node."""
        self._dependents.discard(node)

    def __hash__(self) -> int:  # Stable hashing
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, DirectedAcyclicHypergraphNode) and self.id == other.id

    # ---- Local queries ------------------------------------------------------
    def prerequisite_ids(self) -> Set[str]:
        """All distinct source node IDs feeding into this node via hyperedges."""
        ids: Set[str] = set()
        for hedge in self.in_edges.values():
            ids.update(hedge.source_ids())
        return ids

    def hyperedges(self) -> List["DirectedAcyclicHypergraphEdge[V, E]"]:
        return list(self.in_edges.values())

    def dependents(self) -> Set["DirectedAcyclicHypergraphNode[V, E]"]:
        return set(self._dependents)

    def is_ready(self, satisfied: Set[str]) -> bool:
        """True if there exists at least one hyperedge whose sources are all satisfied.

        Interpretation: node becomes available when ANY of its incoming hyperedges
        has all prerequisites satisfied (OR-of-ANDs). If a node has no incoming
        hyperedges it is trivially ready.
        """
        if not self.in_edges:
            return True
        for hedge in self.in_edges.values():
            if hedge.source_ids().issubset(satisfied):
                return True
        return False


__all__ = [
    "DirectedAcyclicHypergraphEdge",
    "DirectedAcyclicHypergraphNode",
]
