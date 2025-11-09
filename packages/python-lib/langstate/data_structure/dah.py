from __future__ import annotations
"""
Directed Acyclic Hypergraph (DAH) implementation.

A DAH generalizes a DAG by allowing a *hyperedge* to connect multiple
source (prerequisite) nodes to a single target (dependent) node.

Key entities
------------
• Node class:    DirectedAcyclicHypergraphNode[V, E]
• HyperEdge:     DirectedAcyclicHypergraphEdge[E] (stored on target side)
• Manager class: DirectedAcyclicHypergraph[V, E]

Design principles
-----------------
1. Hyperedges are owned by the target node via `in_edges: Dict[id, HyperEdge]`.
   Each hyperedge has a synthetic stable id and contains a set of source node
   references plus optional metadata.
2. Reverse mirrors: each source node maintains a WeakSet of nodes that depend
   on it (any hyperedge that lists it as a source). This avoids strong cycles.
3. Graph-wide operations (topological order, cycle checks, export, viz) live
   in the manager class; nodes stay minimal and testable.
4. Aciclicity validation considers that a hyperedge A,B -> C conceptually adds
   individual edges A->C and B->C for cycle detection / ordering purposes.

Example
-------
edge1: {A, B} -> C
edge2: {C}    -> D

Ordering must place A,B before C and C before D.
"""

from dataclasses import dataclass, field
from graphlib import TopologicalSorter, CycleError
from typing import Any, Dict, Generic, Iterable, Iterator, List, Optional, Set, Tuple, TypeVar
import weakref
import itertools
import json

V = TypeVar("V")  # Node value
E = TypeVar("E")  # Edge metadata

# ---------------------------------------------------------------------------
# HyperEdge & Node
# ---------------------------------------------------------------------------

@dataclass
class DirectedAcyclicHypergraphEdge(Generic[E]):
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
    in_edges: Dict[str, DirectedAcyclicHypergraphEdge[E]] = field(default_factory=dict)

    # Reverse mirror: who depends on me (any node whose hyperedge lists me as a source)
    _dependents: "weakref.WeakSet[DirectedAcyclicHypergraphNode[V, E]]" = field(
        default_factory=weakref.WeakSet, repr=False
    )

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

    def hyperedges(self) -> List[DirectedAcyclicHypergraphEdge[E]]:
        return list(self.in_edges.values())

    def dependents(self) -> Set["DirectedAcyclicHypergraphNode[V, E]"]:
        return {n for n in self._dependents if n is not None}

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

# ---------------------------------------------------------------------------
# Manager: DirectedAcyclicHypergraph
# ---------------------------------------------------------------------------

class DirectedAcyclicHypergraph(Generic[V, E]):
    """Manages nodes & hyperedges for a Directed Acyclic Hypergraph.

    Responsibilities
    ----------------
    • Node/hyperedge creation & removal (bidirectional consistency).
    • Cycle detection treating each source->target pair as an edge for ordering.
    • Graph-wide queries, traversal utilities, and export helpers.
    """

    __slots__ = ("nodes", "_edge_counter")

    def __init__(self, nodes: Iterable[DirectedAcyclicHypergraphNode[V, E]] | None = None) -> None:
        self.nodes: Dict[str, DirectedAcyclicHypergraphNode[V, E]] = {}
        if nodes:
            for n in nodes:
                self.nodes[n.id] = n
        self._edge_counter: int = 0  # for synthetic hyperedge ids

    # ---- Node factory -------------------------------------------------------
    def add_node(self, node_id: str, value: Optional[V] = None) -> DirectedAcyclicHypergraphNode[V, E]:
        node = self.nodes.get(node_id)
        if node is None:
            node = DirectedAcyclicHypergraphNode[V, E](id=node_id, value=value)
            self.nodes[node_id] = node
        else:
            if value is not None:
                node.value = value
        return node

    def get_node(self, node_id: str) -> Optional[DirectedAcyclicHypergraphNode[V, E]]:
        return self.nodes.get(node_id)

    # ---- Hyperedge operations ----------------------------------------------
    def _next_edge_id(self) -> str:
        self._edge_counter += 1
        return f"e{self._edge_counter}"

    def add_hyperedge(
        self,
        sources: Iterable[str],
        target_id: str,
        *,
        metadata: Optional[E] = None,
        edge_id: Optional[str] = None,
        check_cycle: bool = True,
    ) -> str:
        """Create or replace a hyperedge from `sources` to `target_id`.

        Returns the hyperedge id. Cycle detection treats each source individually
        (i.e., adds conceptual edges s->target for all s in sources).
        """
        sources_set = {s for s in sources}
        if target_id in sources_set:
            raise ValueError("Self dependency detected in hyperedge: target also listed as source.")
        if not sources_set:
            raise ValueError("Hyperedge must have at least one source node.")

        target = self.add_node(target_id)
        source_nodes: Set[DirectedAcyclicHypergraphNode[V, E]] = {self.add_node(s) for s in sources_set}

        # Perform cycle detection BEFORE committing (treat as multiple edges)
        if check_cycle:
            for s in sources_set:
                if self._would_create_cycle(s, target_id):
                    raise ValueError(f"Cycle detected when adding hyperedge {sources_set} -> {target_id} (source {s} causes cycle).")

        hid = edge_id or self._next_edge_id()
        hedge = target.in_edges.get(hid)
        if hedge is None:
            target.in_edges[hid] = DirectedAcyclicHypergraphEdge(id=hid, sources=source_nodes, metadata=metadata)
        else:
            hedge.sources = source_nodes
            if metadata is not None:
                hedge.metadata = metadata

        # Update reverse mirrors
        for src_node in source_nodes:
            src_node._dependents.add(target)
        return hid

    def remove_hyperedge(self, edge_id: str, target_id: str) -> None:
        target = self.nodes.get(target_id)
        if not target:
            return
        hedge = target.in_edges.pop(edge_id, None)
        if hedge is None:
            return
        for src in hedge.sources:
            try:
                src._dependents.discard(target)  # type: ignore[attr-defined]
            except Exception:
                pass

    def remove_node(self, node_id: str) -> None:
        node = self.nodes.pop(node_id, None)
        if node is None:
            return
        # Unlink incoming hyperedges
        for eid in list(node.in_edges.keys()):
            self.remove_hyperedge(eid, node_id)
        # Unlink outgoing: for each dependent node, remove hyperedges that reference this node as a source
        for dep in list(node.dependents()):
            for eid, hedge in list(dep.in_edges.items()):
                if node in hedge.sources:
                    self.remove_hyperedge(eid, dep.id)

    # ---- Graph-wide queries -------------------------------------------------
    def prerequisite_ids(self, node_id: str) -> Set[str]:
        node = self.nodes.get(node_id)
        return node.prerequisite_ids() if node else set()

    def dependents(self, node_id: str) -> Set[str]:
        node = self.nodes.get(node_id)
        return {n.id for n in node.dependents()} if node else set()

    def ancestors(self, node_id: str) -> Set[str]:
        seen: Set[str] = set()
        stack = list(self.prerequisite_ids(node_id))
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            stack.extend(self.prerequisite_ids(cur) - seen)
        return seen

    def descendants(self, node_id: str) -> Set[str]:
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
        """Return node IDs in topological order.

        Hyperedges with multiple sources are expanded into individual edges for
        ordering purposes.
        """
        expanded: Dict[str, Set[str]] = {nid: set() for nid in self.nodes}
        for tgt_id, tgt_node in self.nodes.items():
            for hedge in tgt_node.in_edges.values():
                for src in hedge.sources:
                    expanded[tgt_id].add(src.id)
        try:
            return list(TopologicalSorter(expanded).static_order())
        except CycleError as err:
            raise ValueError(f"Dependency cycle detected: {err}")

    def validate_acyclic(self) -> None:
        _ = self.topological_order()

    def iter_hyperedges(self) -> Iterator[Tuple[Set[str], str, Optional[E], str]]:
        """Yield (source_ids, target_id, metadata, edge_id) for all hyperedges."""
        for tgt_id, tgt_node in self.nodes.items():
            for hid, hedge in tgt_node.in_edges.items():
                yield (hedge.source_ids(), tgt_id, hedge.metadata, hid)

    # ---- Visualization / Export --------------------------------------------
    def to_dot(self) -> str:
        """Graphviz DOT (unstyled) representing hyperedges as multi-source comments.

        Note: DOT doesn't natively support hyperedges; we emit individual edges
        with identical metadata comments.
        """
        lines = ["digraph DAH {"]
        for nid in self.nodes:
            lines.append(f'  "{nid}";')
        for sources, tgt, metadata, eid in self.iter_hyperedges():
            for src in sources:
                meta_txt = f" [label={eid}]" if metadata is not None else ""
                lines.append(f'  "{src}" -> "{tgt}"{meta_txt};')
        lines.append("}")
        return "\n".join(lines)

    def to_mermaid(self, node_label_fn=None, edge_label_fn=None, max_label_length: int = 30) -> str:
        """Export to Mermaid format. Hyperedges expanded to individual edges."""
        def _safe(s: str) -> str:
            return s.replace("-", "_").replace(".", "_").replace("[", "_").replace("]", "_").replace("*", "star")
        def _fmt_label(txt: str) -> str:
            if len(txt) > max_label_length:
                txt = txt[: max_label_length - 3] + "..."
            txt = txt.replace('"', "'")
            forbidden = "(){}[]|"
            for ch in forbidden:
                txt = txt.replace(ch, "")
            txt = txt.replace("+", " plus ")
            txt = " ".join(txt.split())
            return txt

        lines = ["graph TD"]
        for node_id, node in self.nodes.items():
            label = node_label_fn(node.value) if (node_label_fn and node.value is not None) else node_id
            lines.append(f'    {_safe(node_id)}["{_fmt_label(label)}"]')
        for sources, tgt, metadata, eid in self.iter_hyperedges():
            edge_label = ""
            label_txt: Optional[str] = None
            if edge_label_fn and metadata is not None:
                try:
                    label_txt = edge_label_fn(metadata)
                except Exception:
                    label_txt = None
            if label_txt:
                safe_txt = _fmt_label(label_txt)
                if safe_txt:
                    edge_label = f"|{safe_txt}|"
            for src in sources:
                lines.append(f'    {_safe(src)} -->{edge_label} {_safe(tgt)}')
        return "\n".join(lines)

    def to_json_dict(self) -> Dict[str, Any]:
        nodes_data = []
        for node_id, node in self.nodes.items():
            node_info = {"id": node_id, "value": None}
            if node.value is not None:
                if hasattr(node.value, 'model_dump'):
                    try:
                        node_info["value"] = node.value.model_dump()
                    except Exception:
                        node_info["value"] = str(node.value)
                elif hasattr(node.value, '__dict__'):
                    try:
                        node_info["value"] = vars(node.value)
                    except Exception:
                        node_info["value"] = str(node.value)
                else:
                    node_info["value"] = str(node.value)
            nodes_data.append(node_info)
        edges_data = []
        for sources, tgt, metadata, eid in self.iter_hyperedges():
            edge_info = {"id": eid, "sources": list(sources), "target": tgt, "metadata": None}
            if metadata is not None:
                if hasattr(metadata, 'model_dump'):
                    try:
                        edge_info["metadata"] = metadata.model_dump()
                    except Exception:
                        edge_info["metadata"] = str(metadata)
                elif hasattr(metadata, '__dict__'):
                    try:
                        edge_info["metadata"] = vars(metadata)
                    except Exception:
                        edge_info["metadata"] = str(metadata)
                else:
                    edge_info["metadata"] = str(metadata)
            edges_data.append(edge_info)
        return {"nodes": nodes_data, "hyperedges": edges_data, "node_count": len(nodes_data), "hyperedge_count": len(edges_data)}

    def to_json(self, pretty: bool = True, indent: int = 2) -> str:
        payload = self.to_json_dict()
        if pretty:
            return json.dumps(payload, indent=indent)
        return json.dumps(payload, separators=(",", ":"))

    # ---- Internal helpers ---------------------------------------------------
    def _would_create_cycle(self, source_id: str, target_id: str) -> bool:
        """True if adding conceptual edge source->target closes a cycle.

        Check whether `source_id` is already a descendant of `target_id`.
        """
        return source_id in self.descendants(target_id)

__all__ = [
    "DirectedAcyclicHypergraphEdge",
    "DirectedAcyclicHypergraphNode",
    "DirectedAcyclicHypergraph",
]
