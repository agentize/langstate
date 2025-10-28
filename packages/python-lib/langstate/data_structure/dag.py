from __future__ import annotations

"""
Directed Acyclic Graph implementation with explicit, descriptive names and a
lightweight manager class.

- Node class:    DirectedAcyclicGraphNode[V, E]
- Edge class:    DirectedAcyclicGraphEdge[E] (stored on dependent side, holds node ref)
- Manager class: DirectedAcyclicGraph[V, E]

Design notes
------------
• Edges are owned by the *dependent* node via `depends_on: Dict[id, Edge]`.
  The edge holds a direct reference to the prerequisite node (fast traversal).
• Reverse links (who depends on me) are maintained as WeakSet on each node to
  avoid strong reference cycles. The manager updates both sides idempotently.
• Graph-level operations (topological order, cycle checks, export) live in the
  manager class to keep nodes focused and testable in isolation.
"""

from dataclasses import dataclass, field
from graphlib import TopologicalSorter, CycleError
from typing import Dict, Generic, Iterable, Iterator, List, Optional, Set, Tuple, TypeVar
import weakref

V = TypeVar("V")  # Node value
E = TypeVar("E")  # Edge metadata


# ---------------------------------------------------------------------------
# Edge & Node
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class DirectedAcyclicGraphEdge(Generic[E]):
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


@dataclass
class DirectedAcyclicGraphNode(Generic[V, E]):
    """Represents a vertex in a Directed Acyclic Graph.

    Only local concerns live here; graph-wide logic is in the manager.
    The node is hashable by its stable `id` to support sets and weak refs.
    """

    id: str
    value: Optional[V] = None

    # Truth source: dependencies (this node depends on -> edge with node ref + metadata)
    depends_on: Dict[str, DirectedAcyclicGraphEdge[E]] = field(default_factory=dict)

    # Reverse mirror: who depends on me (weak, to avoid strong cycles)
    _dependents: "weakref.WeakSet[DirectedAcyclicGraphNode[V, E]]" = field(
        default_factory=weakref.WeakSet, repr=False
    )

    # Identity & hashing by id (stable across process lifetime)
    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, DirectedAcyclicGraphNode) and self.id == other.id

    # ---- Local queries ------------------------------------------------------
    def prerequisites(self) -> Set[str]:
        """IDs of nodes this node depends on."""
        return set(self.depends_on.keys())

    def prerequisite_nodes(self) -> Set["DirectedAcyclicGraphNode[V, E]"]:
        """Direct node references of prerequisites (fast traversal)."""
        return {edge.target for edge in self.depends_on.values()}

    def dependents(self) -> Set["DirectedAcyclicGraphNode[V, E]"]:
        """Materialize current dependents (strong refs) from the WeakSet mirror."""
        return {n for n in self._dependents if n is not None}

    def is_ready(self, satisfied: Set[str]) -> bool:
        """True if all prerequisites are in `satisfied`."""
        return self.prerequisites().issubset(satisfied)


# ---------------------------------------------------------------------------
# Manager: DirectedAcyclicGraph
# ---------------------------------------------------------------------------

class DirectedAcyclicGraph(Generic[V, E]):
    """Manages a set of DAG nodes and provides graph-level operations.

    Responsibilities
    ----------------
    • Node/edge creation and removal (with bidirectional consistency).
    • Optional incremental cycle check on edge add.
    • Fast, clear graph-wide queries and export helpers.
    """

    __slots__ = ("nodes",)

    def __init__(self, nodes: Iterable[DirectedAcyclicGraphNode[V, E]] | None = None) -> None:
        self.nodes: Dict[str, DirectedAcyclicGraphNode[V, E]] = {}
        if nodes:
            for n in nodes:
                self.nodes[n.id] = n

    # ---- Node factory -------------------------------------------------------
    def add_node(self, node_id: str, value: Optional[V] = None) -> DirectedAcyclicGraphNode[V, E]:
        node = self.nodes.get(node_id)
        if node is None:
            node = DirectedAcyclicGraphNode[V, E](id=node_id, value=value)
            self.nodes[node_id] = node
        else:
            if value is not None:
                node.value = value
        return node

    def get_node(self, node_id: str) -> Optional[DirectedAcyclicGraphNode[V, E]]:
        return self.nodes.get(node_id)

    # ---- Edge operations ----------------------------------------------------
    def add_edge(
        self,
        prereq_id: str,
        dep_id: str,
        *,
        metadata: Optional[E] = None,
        check_cycle: bool = True,
    ) -> None:
        """Create/refresh an edge `prereq_id -> dep_id` (idempotent).

        Maintains both the truth side (dependent.depends_on) and the reverse
        WeakSet (prereq._dependents). If `check_cycle=True`, raises ValueError
        if adding the edge would introduce a cycle.
        """
        if prereq_id == dep_id:
            raise ValueError("Self dependency detected.")

        prereq = self.add_node(prereq_id)
        dep = self.add_node(dep_id)

        # Idempotent update on truth side
        edge = dep.depends_on.get(prereq_id)
        if edge is None:
            dep.depends_on[prereq_id] = DirectedAcyclicGraphEdge(target=prereq, metadata=metadata)
        else:
            if metadata is not None:
                edge.metadata = metadata
            edge.target = prereq  # ensure pointer is correct

        # Maintain reverse mirror
        prereq._dependents.add(dep)

        if check_cycle and self._would_create_cycle(prereq_id, dep_id):
            # Roll back and raise
            self.remove_edge(prereq_id, dep_id)
            raise ValueError(f"Dependency cycle detected when adding {prereq_id} -> {dep_id}.")

    def remove_edge(self, prereq_id: str, dep_id: str) -> None:
        dep = self.nodes.get(dep_id)
        if not dep:
            return
        # Remove from dependent truth side
        removed = dep.depends_on.pop(prereq_id, None)
        if removed is not None:
            # Remove from reverse mirror
            prereq = self.nodes.get(prereq_id)
            if prereq is not None:
                try:
                    prereq._dependents.discard(dep)  # type: ignore[attr-defined]
                except Exception:
                    pass

    def remove_node(self, node_id: str) -> None:
        node = self.nodes.pop(node_id, None)
        if node is None:
            return
        # Unlink inbound edges (node as dependent)
        for pid in list(node.depends_on.keys()):
            self.remove_edge(pid, node_id)
        # Unlink outbound edges (node as prerequisite)
        for dep in list(node.dependents()):
            self.remove_edge(node_id, dep.id)

    # ---- Graph-wide queries -------------------------------------------------
    def prerequisites(self, node_id: str) -> Set[str]:
        node = self.nodes.get(node_id)
        return node.prerequisites() if node else set()

    def dependents(self, node_id: str) -> Set[str]:
        node = self.nodes.get(node_id)
        return {n.id for n in node.dependents()} if node else set()

    def ancestors(self, node_id: str) -> Set[str]:
        """All transitive prerequisites of `node_id`."""
        seen: Set[str] = set()
        stack = list(self.prerequisites(node_id))
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            stack.extend(self.prerequisites(cur) - seen)
        return seen

    def descendants(self, node_id: str) -> Set[str]:
        """All transitive dependents of `node_id`."""
        seen: Set[str] = set()
        stack = list(self.dependents(node_id))
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            stack.extend(self.dependents(cur) - seen)
        return seen

    def ready_nodes(self, satisfied: Set[str]) -> Set[str]:
        return {nid for nid, node in self.nodes.items() if node.is_ready(satisfied)}

    def topological_order(self) -> List[str]:
        """Return node IDs in topological order (raises on cycles)."""
        edges = {nid: node.prerequisites() for nid, node in self.nodes.items()}
        try:
            return list(TopologicalSorter(edges).static_order())
        except CycleError as err:
            raise ValueError(f"Dependency cycle detected: {err}")

    def validate_acyclic(self) -> None:
        _ = self.topological_order()

    def iter_edges(self) -> Iterator[Tuple[str, str, Optional[E]]]:
        """Yield (prereq_id, dep_id, metadata) for all edges."""
        for dep_id, dep_node in self.nodes.items():
            for prereq_id, edge in dep_node.depends_on.items():
                yield (prereq_id, dep_id, edge.metadata)

    def to_dot(self) -> str:
        """Graphviz DOT (unstyled)."""
        lines = ["digraph DAG {"]
        for nid in self.nodes:
            lines.append(f'  "{nid}";')
        for src, dst, _ in self.iter_edges():
            lines.append(f'  "{src}" -> "{dst}";')
        lines.append("}")
        return "".join(lines)

    # ---- Internal helpers ---------------------------------------------------
    def _would_create_cycle(self, prereq_id: str, dep_id: str) -> bool:
        """True if adding `prereq_id -> dep_id` closes a cycle.

        We check whether `prereq_id` is already a descendant of `dep_id`.
        If yes, then adding the edge would create a cycle.
        """
        return prereq_id in self.descendants(dep_id)
