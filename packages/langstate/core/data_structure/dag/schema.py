from __future__ import annotations

"""
Schema definitions (dataclasses) for Directed Acyclic Graph structures.

These are concrete data classes that implement the interfaces from base.py
through duck typing (structural subtyping).
"""

from dataclasses import dataclass, field
from typing import Dict, Generic, Optional, Set, TypeVar
import weakref

V = TypeVar("V")  # Node value
E = TypeVar("E")  # Edge metadata


@dataclass
class DirectedAcyclicGraphEdge(Generic[V, E]):
    """Edge stored on the dependent side: dependent  ←edge—  prerequisite.

    Attributes
    ----------
    target: DirectedAcyclicGraphNode[V, E]
        The prerequisite node (this is the node we depend on).
    metadata: Optional[E]
        Optional edge metadata (weight, label, constraint, etc.).
    """

    target: "DirectedAcyclicGraphNode[V, E]"
    metadata: Optional[E] = None

    @property
    def sources(self) -> Set["DirectedAcyclicGraphNode[V, E]"]:
        """Source nodes (returns single-element set with target for compatibility)."""
        return {self.target}

    def source_ids(self) -> Set[str]:
        """Get IDs of all source nodes (returns single-element set for DAG)."""
        return {self.target.id}


@dataclass
class DirectedAcyclicGraphNode(Generic[V, E]):
    """Represents a vertex in a Directed Acyclic Graph.

    Only local concerns live here; graph-wide logic is in the manager.
    The node is hashable by its stable `id` to support sets and weak refs.
    """

    id: str
    value: Optional[V] = None

    # Truth source: dependencies (this node depends on -> edge with node ref + metadata)
    depends_on: Dict[str, "DirectedAcyclicGraphEdge[V, E]"] = field(default_factory=dict)  # type: ignore[misc]

    # Reverse mirror: who depends on me (weak, to avoid strong cycles)
    _dependents: "weakref.WeakSet[DirectedAcyclicGraphNode[V, E]]" = field(  # type: ignore[misc]
        default_factory=weakref.WeakSet, repr=False
    )

    # ---- Reverse mirror management (for use by DAG manager) ----------------
    def add_dependent(self, node: "DirectedAcyclicGraphNode[V, E]") -> None:
        """Register a node as depending on this node."""
        self._dependents.add(node)

    def remove_dependent(self, node: "DirectedAcyclicGraphNode[V, E]") -> None:
        """Unregister a node as depending on this node."""
        self._dependents.discard(node)

    # Identity & hashing by id (stable across process lifetime)
    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, DirectedAcyclicGraphNode) and self.id == other.id

    # ---- Local queries ------------------------------------------------------
    def prerequisites(self) -> Set[str]:
        """IDs of nodes this node depends on."""
        return set(self.depends_on.keys())

    def prerequisite_ids(self) -> Set[str]:
        """IDs of nodes this node depends on (alias for prerequisites)."""
        return self.prerequisites()

    def prerequisite_nodes(self) -> Set["DirectedAcyclicGraphNode[V, E]"]:
        """Direct node references of prerequisites (fast traversal)."""
        return {edge.target for edge in self.depends_on.values()}

    def dependents(self) -> Set["DirectedAcyclicGraphNode[V, E]"]:
        """Materialize current dependents (strong refs) from the WeakSet mirror."""
        return set(self._dependents)

    def is_ready(self, satisfied: Set[str]) -> bool:
        """True if all prerequisites are in `satisfied`."""
        return self.prerequisites().issubset(satisfied)


__all__ = [
    "DirectedAcyclicGraphEdge",
    "DirectedAcyclicGraphNode",
]
