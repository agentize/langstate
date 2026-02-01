from __future__ import annotations

"""
Directed Acyclic Hypergraph (DAH) implementation.

A DAH generalizes a DAG by allowing a *hyperedge* to connect multiple
source (prerequisite) nodes to a single target (dependent) node.
"""

import json
from graphlib import CycleError, TopologicalSorter
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Iterable,
    Iterator,
    List,
    Optional,
    Set,
    Tuple,
    TypeVar,
)
from uuid import UUID, uuid4

from .schema import DirectedAcyclicHypergraphEdge, DirectedAcyclicHypergraphNode

V = TypeVar("V")  # Node value
E = TypeVar("E")  # Edge metadata


class DirectedAcyclicHypergraph(Generic[V, E]):
    """Manages nodes & hyperedges for a Directed Acyclic Hypergraph.

    A DAH (Directed Acyclic Hypergraph) allows hyperedges that connect
    multiple source nodes to a single target node.

    Key differences from DAG:
    - is_ready: True if ANY incoming hyperedge has ALL sources satisfied (OR-of-ANDs)
    - Hyperedges can have multiple sources

    Node identity:
    - id: UUID (auto-generated unique identifier)
    - path: str (field path like "registrant.event.id" for addressing)

    Responsibilities:
    - Node/hyperedge creation & removal (bidirectional consistency)
    - Cycle detection treating each source->target pair as an edge for ordering
    - Graph-wide queries, traversal utilities, and export helpers
    """

    __slots__ = ("_nodes", "_path_to_uuid", "_edge_counter")

    def __init__(
        self, nodes: Iterable[DirectedAcyclicHypergraphNode[V, E]] | None = None
    ) -> None:
        self._nodes: Dict[UUID, DirectedAcyclicHypergraphNode[V, E]] = {}
        self._path_to_uuid: Dict[str, UUID] = {}  # Secondary index: path -> UUID
        if nodes:
            for n in nodes:
                self._nodes[n.id] = n
                self._path_to_uuid[n.path] = n.id
        self._edge_counter: int = 0

    # ---- Properties ---------------------------------------------------------

    @property
    def nodes(self) -> Dict[UUID, DirectedAcyclicHypergraphNode[V, E]]:
        """All nodes in the hypergraph (keyed by UUID)."""
        return self._nodes

    @property
    def path_to_uuid(self) -> Dict[str, UUID]:
        """Path to UUID mapping for node lookup."""
        return self._path_to_uuid

    # ---- Node operations ----------------------------------------------------

    def add_node(
        self, path: str, value: Optional[V] = None
    ) -> DirectedAcyclicHypergraphNode[V, E]:
        """Add or update a node in the hypergraph.

        Args:
            path: Field path (e.g., "registrant.event.id")
            value: Optional node payload

        Returns:
            The created or updated node
        """
        # Check if node exists by path
        existing_uuid = self._path_to_uuid.get(path)
        if existing_uuid is not None:
            node = self._nodes[existing_uuid]
            if value is not None:
                node.value = value
            return node

        # Create new node with generated UUID
        node_id = uuid4()
        node = DirectedAcyclicHypergraphNode[V, E](id=node_id, path=path, value=value)
        self._nodes[node_id] = node
        self._path_to_uuid[path] = node_id
        return node

    def get_node(self, path: str) -> Optional[DirectedAcyclicHypergraphNode[V, E]]:
        """Retrieve a node by path."""
        node_uuid = self._path_to_uuid.get(path)
        if node_uuid is None:
            return None
        return self._nodes.get(node_uuid)

    def get_node_by_uuid(
        self, node_uuid: UUID
    ) -> Optional[DirectedAcyclicHypergraphNode[V, E]]:
        """Retrieve a node by UUID."""
        return self._nodes.get(node_uuid)

    def remove_node(self, path: str) -> None:
        """Remove a node and all its hyperedges."""
        node_uuid = self._path_to_uuid.pop(path, None)
        if node_uuid is None:
            return
        node = self._nodes.pop(node_uuid, None)
        if node is None:
            return
        # Unlink incoming hyperedges
        for eid in list(node.in_edges.keys()):
            self.remove_hyperedge(eid, path)
        # Unlink outgoing: for each dependent node, remove hyperedges that reference this node as source
        for dep in list(node.dependents()):
            for eid, hedge in list(dep.in_edges.items()):
                if node in hedge.sources:
                    self.remove_hyperedge(eid, dep.path)

    # ---- Hyperedge operations -----------------------------------------------

    def _next_edge_id(self) -> UUID:
        """Generate next edge UUID."""
        return uuid4()

    def add_hyperedge(
        self,
        sources: Iterable[str],
        target_path: str,
        *,
        metadata: Optional[E] = None,
        edge_id: Optional[UUID] = None,
        check_cycle: bool = True,
    ) -> UUID:
        """Create or replace a hyperedge from sources to target.

        Args:
            sources: Source node paths
            target_path: Target node path
            metadata: Optional edge metadata
            edge_id: Optional edge UUID (auto-generated if not provided)
            check_cycle: Whether to check for cycles

        Returns:
            The hyperedge UUID.
        """
        sources_set = set(sources)
        if target_path in sources_set:
            raise ValueError(
                "Self dependency detected in hyperedge: target also listed as source."
            )
        if not sources_set:
            raise ValueError("Hyperedge must have at least one source node.")

        target = self.add_node(target_path)
        source_nodes: Set[DirectedAcyclicHypergraphNode[V, E]] = {
            self.add_node(s) for s in sources_set
        }

        # Perform cycle detection BEFORE committing (treat as multiple edges)
        if check_cycle:
            for s in sources_set:
                if self._would_create_cycle(s, target_path):
                    raise ValueError(
                        f"Cycle detected when adding hyperedge {sources_set} -> {target_path} (source {s} causes cycle)."
                    )

        hid = edge_id or self._next_edge_id()
        hedge = target.in_edges.get(hid)
        if hedge is None:
            target.in_edges[hid] = DirectedAcyclicHypergraphEdge(
                id=hid, sources=source_nodes, metadata=metadata
            )
        else:
            hedge.sources = source_nodes
            if metadata is not None:
                hedge.metadata = metadata

        # Update reverse mirrors
        for src_node in source_nodes:
            src_node.add_dependent(target)
        return hid

    def remove_hyperedge(self, edge_id: UUID, target_path: str) -> None:
        """Remove a hyperedge."""
        target = self.get_node(target_path)
        if not target:
            return
        hedge = target.in_edges.pop(edge_id, None)
        if hedge is None:
            return
        for src in hedge.sources:
            try:
                src.remove_dependent(target)
            except Exception:
                pass

    # ---- Backward compatibility (single-source edge API) --------------------

    def add_edge(
        self,
        prereq_path: str,
        dep_path: str,
        *,
        metadata: Optional[E] = None,
        check_cycle: bool = True,
    ) -> UUID:
        """Backward compatible helper matching old DAG API.

        Creates a 1-source hyperedge. Returns the hyperedge UUID.
        """
        return self.add_hyperedge(
            [prereq_path], dep_path, metadata=metadata, check_cycle=check_cycle
        )

    # ---- Graph-wide queries -------------------------------------------------

    def prerequisite_ids(self, path: str) -> Set[UUID]:
        """Get prerequisite UUIDs of a node."""
        node = self.get_node(path)
        return node.prerequisite_ids() if node else set()

    def prerequisite_paths(self, path: str) -> Set[str]:
        """Get prerequisite paths of a node."""
        node = self.get_node(path)
        return node.prerequisite_paths() if node else set()

    def dependents(self, path: str) -> Set[str]:
        """Get dependent paths of a node."""
        node = self.get_node(path)
        return {n.path for n in node.dependents()} if node else set()

    def ancestors(self, path: str) -> Set[str]:
        """All transitive prerequisite paths of a node."""
        seen: Set[str] = set()
        stack = list(self.prerequisite_paths(path))
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            stack.extend(self.prerequisite_paths(cur) - seen)
        return seen

    def descendants(self, path: str) -> Set[str]:
        """All transitive dependent paths of a node."""
        seen: Set[str] = set()
        stack = list(self.dependents(path))
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            stack.extend(self.dependents(cur) - seen)
        return seen

    def ready_nodes(self, satisfied: Set[str]) -> Set[str]:
        """Node paths that are ready given satisfied prerequisite paths."""
        return {node.path for node in self._nodes.values() if node.is_ready(satisfied)}

    def topological_order(self) -> List[str]:
        """Return node paths in topological order.

        Hyperedges with multiple sources are expanded into individual edges for
        ordering purposes.
        """
        expanded: Dict[str, Set[str]] = {
            node.path: set() for node in self._nodes.values()
        }
        for node in self._nodes.values():
            for hedge in node.in_edges.values():
                for src in hedge.sources:
                    expanded[node.path].add(src.path)
        try:
            return list(TopologicalSorter(expanded).static_order())
        except CycleError as err:
            raise ValueError(f"Dependency cycle detected: {err}")

    def validate_acyclic(self) -> None:
        """Validate that the hypergraph is acyclic."""
        _ = self.topological_order()

    def iter_hyperedges(self) -> Iterator[Tuple[Set[str], str, Optional[E], UUID]]:
        """Yield (source_paths, target_path, metadata, edge_id) for all hyperedges."""
        for node in self._nodes.values():
            for hid, hedge in node.in_edges.items():
                yield (hedge.source_paths(), node.path, hedge.metadata, hid)

    # ---- Internal helpers ---------------------------------------------------

    def _would_create_cycle(self, source_path: str, target_path: str) -> bool:
        """True if adding conceptual edge source->target closes a cycle.

        Check whether source_path is already a descendant of target_path.
        """
        return source_path in self.descendants(target_path)

    # ---- Export methods -----------------------------------------------------

    def to_dot(self) -> str:
        """Graphviz DOT representing hyperedges.

        Note: DOT doesnt natively support hyperedges; we emit individual edges.
        Uses path for node labels.
        """
        lines = ["digraph DAH {"]
        for node in self._nodes.values():
            lines.append(f'  "{node.path}";')
        for sources, tgt, metadata, eid in self.iter_hyperedges():
            for src in sources:
                meta_txt = f' [label="{eid}"]' if metadata is not None else ""
                lines.append(f'  "{src}" -> "{tgt}"{meta_txt};')
        lines.append("}")
        return "\n".join(lines)

    def to_mermaid(
        self,
        node_label_fn: Optional[Callable[[Any], str]] = None,
        edge_label_fn: Optional[Callable[[Optional[E]], str]] = None,
        max_label_length: int = 30,
    ) -> str:
        """Export to Mermaid format. Hyperedges expanded to individual edges.
        Uses path for node labels.
        """

        def _safe(s: str) -> str:
            return (
                s.replace("-", "_")
                .replace(".", "_")
                .replace("[", "_")
                .replace("]", "_")
                .replace("*", "star")
            )

        def _fmt_label(txt: str) -> str:
            if len(txt) > max_label_length:
                txt = txt[: max_label_length - 3] + "..."
            txt = txt.replace('"', "'")
            for ch in "(){}[]|":
                txt = txt.replace(ch, "")
            txt = txt.replace("+", " plus ")
            txt = " ".join(txt.split())
            return txt

        lines = ["graph TD"]
        for node in self._nodes.values():
            label: str
            if node_label_fn and node.value is not None:
                label = node_label_fn(node.value)
            else:
                label = node.path
            lines.append(f'    {_safe(node.path)}["{_fmt_label(label)}"]')

        for sources, tgt, metadata, _ in self.iter_hyperedges():
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
                lines.append(f"    {_safe(src)} -->{edge_label} {_safe(tgt)}")
        return "\n".join(lines)

    def to_json_dict(self) -> Dict[str, Any]:
        """Export hypergraph structure to JSON-serializable dict.
        Includes both UUID (id) and path for each node.
        """
        nodes_data: List[Dict[str, Any]] = []
        for node in self._nodes.values():
            node_info: Dict[str, Any] = {
                "id": str(node.id),
                "path": node.path,
                "value": None,
            }
            if node.value is not None:
                model_dump_fn = getattr(node.value, "model_dump", None)
                if model_dump_fn is not None:
                    try:
                        node_info["value"] = model_dump_fn()
                    except Exception:
                        node_info["value"] = str(node.value)
                elif hasattr(node.value, "__dict__"):
                    try:
                        node_info["value"] = vars(node.value)
                    except Exception:
                        node_info["value"] = str(node.value)
                else:
                    node_info["value"] = str(node.value)
            nodes_data.append(node_info)

        edges_data: List[Dict[str, Any]] = []
        for sources, tgt, metadata, eid in self.iter_hyperedges():
            edge_info: Dict[str, Any] = {
                "id": str(eid),
                "sources": list(sources),
                "target": tgt,
                "metadata": None,
            }
            if metadata is not None:
                model_dump_fn = getattr(metadata, "model_dump", None)
                if model_dump_fn is not None:
                    try:
                        edge_info["metadata"] = model_dump_fn()
                    except Exception:
                        edge_info["metadata"] = str(metadata)
                elif hasattr(metadata, "__dict__"):
                    try:
                        edge_info["metadata"] = vars(metadata)
                    except Exception:
                        edge_info["metadata"] = str(metadata)
                else:
                    edge_info["metadata"] = str(metadata)
            edges_data.append(edge_info)

        return {
            "nodes": nodes_data,
            "hyperedges": edges_data,
            "node_count": len(nodes_data),
            "hyperedge_count": len(edges_data),
        }

    def to_json(self, pretty: bool = True, indent: int = 2) -> str:
        """Export hypergraph structure to a JSON string."""
        payload = self.to_json_dict()
        if pretty:
            return json.dumps(payload, indent=indent)
        return json.dumps(payload, separators=(",", ":"))

    def to_ascii_tree(
        self,
        root_nodes: Optional[List[str]] = None,
        node_label_fn: Optional[Callable[[Any], str]] = None,
        edge_label_fn: Optional[Callable[[Optional[E]], str]] = None,
        max_depth: int = 10,
    ) -> str:
        """Generate ASCII tree representation.

        Hyperedges are displayed under a HyperEdges section; multi-source
        hyperedges list all sources. Uses path for node labels.
        """
        if root_nodes is None:
            root_nodes = [
                node.path
                for node in self._nodes.values()
                if not node.prerequisite_paths()
            ]
        lines: List[str] = []

        def render_node(
            path: str, prefix: str = "", is_last: bool = True, depth: int = 0
        ) -> None:
            if depth > max_depth:
                return
            node = self.get_node(path)
            if not node:
                return
            label: str
            if node_label_fn and node.value is not None:
                try:
                    label = node_label_fn(node.value)
                except Exception:
                    label = path
            else:
                label = path
            if len(label) > 60:
                label = label[:57] + "..."
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{label}")
            child_prefix = prefix + ("    " if is_last else "│   ")
            dependents = list(node.dependents())
            for i, dep_node in enumerate(dependents):
                render_node(
                    dep_node.path, child_prefix, i == len(dependents) - 1, depth + 1
                )

        lines.append("Schema")
        root_entity = root_nodes[0].split(".")[0] if root_nodes else "RootNode"
        lines.append(f"├── {root_entity}")
        root_prefix = "│   "
        for i, rid in enumerate(root_nodes):
            render_node(rid, root_prefix, i == len(root_nodes) - 1, 0)

        lines.append("└── HyperEdges")
        edges_prefix = "    "
        hyperedges = list(self.iter_hyperedges())
        # Show those with metadata first
        hyperedges = [e for e in hyperedges if e[2] is not None] + [
            e for e in hyperedges if e[2] is None
        ]

        for i, (sources, tgt, metadata, _) in enumerate(hyperedges):
            is_last = i == len(hyperedges) - 1
            connector = "└── " if is_last else "├── "
            edge_label = ""
            if edge_label_fn and metadata is not None:
                try:
                    edge_label = edge_label_fn(metadata)
                except Exception:
                    edge_label = ""
            else:
                to_node = self.get_node(tgt)
                if to_node and to_node.value is not None:
                    try:
                        constraints = getattr(to_node.value, "constraints", [])
                        labels: List[str] = []
                        for c in constraints or []:
                            edge_name_fn = getattr(c, "to_dag_edge_name", None)
                            if edge_name_fn is not None:
                                labels.append(str(edge_name_fn()))
                        if labels:
                            edge_label = labels[0]
                            if len(labels) > 1:
                                edge_label += f" (+{len(labels) - 1} more)"
                    except Exception:
                        pass
            src_list = ",".join(sorted(sources))
            meta_prefix = "[constraint] " if metadata is not None else ""
            label_part = f": {edge_label}" if edge_label else ""
            lines.append(
                f"{edges_prefix}{connector}{meta_prefix}({src_list} -> {tgt}){label_part}"
            )
        return "\n".join(lines)


__all__ = ["DirectedAcyclicHypergraph"]
