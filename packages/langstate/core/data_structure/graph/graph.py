from __future__ import annotations

"""
Base Graph implementation with common functionality.

This module provides the Graph base class that implements common operations
for directed graph structures, serving as a foundation for DAG and DAH.
"""

import json
from graphlib import CycleError, TopologicalSorter
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Iterator,
    List,
    Optional,
    Set,
    Tuple,
    TypeVar,
)

from .base import BaseGraph, BaseGraphNode

V = TypeVar("V")  # Node value
E = TypeVar("E")  # Edge metadata


class Graph(BaseGraph[V, E], Generic[V, E]):
    """Base implementation of directed graph manager.

    Provides common operations for managing nodes, edges, and analyzing
    graph structure. Subclasses (DAG, DAH) should override methods as needed.

    This class implements:
    - Node management (add, get, remove)
    - Graph traversal (ancestors, descendants)
    - Ready node detection
    - Topological ordering
    - Export to various formats (DOT, Mermaid, JSON, ASCII tree)
    """

    __slots__ = ("_nodes",)

    def __init__(self) -> None:
        self._nodes: Dict[str, BaseGraphNode[V, E]] = {}

    # ---- Property implementations -------------------------------------------

    @property
    def nodes(self) -> Dict[str, BaseGraphNode[V, E]]:
        """All nodes in the graph."""
        return self._nodes

    # ---- Abstract methods that subclasses must implement --------------------

    def add_node(self, node_id: str, value: Optional[V] = None) -> BaseGraphNode[V, E]:
        """Add or update a node in the graph.

        Subclasses must implement this method to create appropriate node types.
        """
        raise NotImplementedError("Subclasses must implement add_node")

    def get_node(self, node_id: str) -> Optional[BaseGraphNode[V, E]]:
        """Retrieve a node by ID."""
        return self._nodes.get(node_id)

    def remove_node(self, node_id: str) -> None:
        """Remove a node and all its edges.

        Subclasses must implement this method to handle edge cleanup.
        """
        raise NotImplementedError("Subclasses must implement remove_node")

    # ---- Graph-wide queries -------------------------------------------------

    def prerequisite_ids(self, node_id: str) -> Set[str]:
        """Get prerequisite IDs of a node."""
        node = self._nodes.get(node_id)
        return node.prerequisite_ids() if node else set()

    def dependents(self, node_id: str) -> Set[str]:
        """Get dependents of a node."""
        node = self._nodes.get(node_id)
        return {n.id for n in node.dependents()} if node else set()

    def ancestors(self, node_id: str) -> Set[str]:
        """Get all transitive prerequisites of a node."""
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
        """Get all transitive dependents of a node."""
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
        """Find nodes that are ready given satisfied prerequisites."""
        return {nid for nid, node in self._nodes.items() if node.is_ready(satisfied)}

    # ---- Topological ordering -----------------------------------------------

    def _build_dependency_graph(self) -> Dict[str, Set[str]]:
        """Build dependency graph for topological sorting.

        Subclasses may override this to handle different edge structures.
        """
        return {nid: node.prerequisite_ids() for nid, node in self._nodes.items()}

    def topological_order(self) -> List[str]:
        """Return node IDs in topological order (raises on cycles)."""
        edges = self._build_dependency_graph()
        try:
            return list(TopologicalSorter(edges).static_order())
        except CycleError as err:
            raise ValueError(f"Dependency cycle detected: {err}")

    def validate_acyclic(self) -> None:
        """Validate that the graph is acyclic."""
        _ = self.topological_order()

    # ---- Cycle detection helper ---------------------------------------------

    def _would_create_cycle(self, source_id: str, target_id: str) -> bool:
        """Check if adding source->target edge would create a cycle.

        True if source_id is already a descendant of target_id.
        """
        return source_id in self.descendants(target_id)

    # ---- Edge iteration (subclasses should implement) -----------------------

    def _iter_edges(self) -> Iterator[Tuple[str, str, Optional[E]]]:
        """Yield (source_id, target_id, metadata) for all edges.

        Subclasses must implement this for their specific edge structure.
        """
        raise NotImplementedError("Subclasses must implement _iter_edges")

    # ---- Export methods -----------------------------------------------------

    def to_dot(self) -> str:
        """Export to Graphviz DOT format."""
        lines = ["digraph G {"]
        for nid in self._nodes:
            lines.append(f'  "{nid}";')
        for src, dst, _ in self._iter_edges():
            lines.append(f'  "{src}" -> "{dst}";')
        lines.append("}")
        return "\n".join(lines)

    def to_mermaid(
        self,
        node_label_fn: Optional[Callable[[Any], str]] = None,
        edge_label_fn: Optional[Callable[[Optional[E]], str]] = None,
        max_label_length: int = 30,
    ) -> str:
        """Export to Mermaid diagram format."""

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

        # Add all nodes
        for node_id, node in self._nodes.items():
            safe_id = _safe(node_id)
            label: str
            if node_label_fn and node.value is not None:
                label = node_label_fn(node.value)
            else:
                label = node_id
            lines.append(f'    {safe_id}["{_fmt_label(label)}"]')

        # Add edges
        for src, dst, metadata in self._iter_edges():
            safe_src = _safe(src)
            safe_dst = _safe(dst)

            edge_label = ""
            if edge_label_fn and metadata is not None:
                try:
                    label_txt = edge_label_fn(metadata)
                    if label_txt:
                        edge_label = f"|{_fmt_label(label_txt)}|"
                except Exception:
                    pass

            lines.append(f"    {safe_src} -->{edge_label} {safe_dst}")

        return "\n".join(lines)

    def to_json_dict(self) -> Dict[str, Any]:
        """Export graph structure to JSON-serializable dict."""
        nodes_data: List[Dict[str, Any]] = []
        for node_id, node in self._nodes.items():
            node_info: Dict[str, Any] = {"id": node_id, "value": None}

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
        for src, dst, metadata in self._iter_edges():
            edge_info: Dict[str, Any] = {"from": src, "to": dst, "metadata": None}

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
            "edges": edges_data,
            "node_count": len(nodes_data),
            "edge_count": len(edges_data),
        }

    def to_json(self, pretty: bool = True, indent: int = 2) -> str:
        """Export graph structure to a JSON string."""
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
        """Generate ASCII tree representation."""
        if root_nodes is None:
            # Find nodes with no prerequisites
            root_nodes = [
                nid for nid, node in self._nodes.items() if not node.prerequisite_ids()
            ]

        lines: List[str] = []

        def render_node(
            node_id: str, prefix: str = "", is_last: bool = True, depth: int = 0
        ) -> None:
            if depth > max_depth:
                return

            node = self._nodes.get(node_id)
            if not node:
                return

            # Get label
            label: str
            if node_label_fn and node.value is not None:
                try:
                    label = node_label_fn(node.value)
                except Exception:
                    label = node_id
            else:
                label = node_id

            # Truncate if too long
            if len(label) > 60:
                label = label[:57] + "..."

            # Draw the current node
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{label}")

            # Prepare prefix for children
            child_prefix = prefix + ("    " if is_last else "│   ")

            # Get dependents (children)
            dependents = list(node.dependents())
            for i, dep_node in enumerate(dependents):
                render_node(
                    dep_node.id, child_prefix, i == len(dependents) - 1, depth + 1
                )

        # Top level: Schema
        lines.append("Schema")

        # Extract root entity name
        root_entity = root_nodes[0].split(".")[0] if root_nodes else "RootNode"
        lines.append(f"├── {root_entity}")
        root_prefix = "│   "

        # Render root nodes
        for i, rid in enumerate(root_nodes):
            render_node(rid, root_prefix, i == len(root_nodes) - 1, 0)

        # Edges section
        lines.append("└── Edges")
        edges_prefix = "    "

        edge_list = list(self._iter_edges())
        # Show edges with metadata first
        edge_list = [e for e in edge_list if e[2] is not None] + [
            e for e in edge_list if e[2] is None
        ]

        for i, (from_id, to_id, metadata) in enumerate(edge_list):
            is_last_edge = i == len(edge_list) - 1
            connector = "└── " if is_last_edge else "├── "

            edge_label = ""
            if edge_label_fn and metadata is not None:
                try:
                    edge_label = f": {edge_label_fn(metadata)}"
                except Exception:
                    pass

            prefix = "[constraint] " if metadata is not None else ""
            edge_display = f"{prefix}({from_id} -> {to_id}){edge_label}"
            lines.append(f"{edges_prefix}{connector}{edge_display}")

        return "\n".join(lines)


__all__ = ["Graph"]
