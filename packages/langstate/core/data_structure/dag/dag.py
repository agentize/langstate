from __future__ import annotations

"""
Directed Acyclic Graph (DAG) implementation.

This module provides the DirectedAcyclicGraph class that implements
a standard DAG where each edge connects a single source to a target.
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

from .schema import DirectedAcyclicGraphEdge, DirectedAcyclicGraphNode

V = TypeVar("V")  # Node value
E = TypeVar("E")  # Edge metadata


class DirectedAcyclicGraph(Generic[V, E]):
    """Manages a set of DAG nodes and provides graph-level operations.

    A DAG (Directed Acyclic Graph) where each edge connects exactly one
    source node (prerequisite) to one target node (dependent).

    Node identity:
    - id: UUID (auto-generated unique identifier)
    - path: str (field path like "registrant.event.id" for addressing)

    Responsibilities:
    - Node/edge creation and removal (with bidirectional consistency)
    - Optional incremental cycle check on edge add
    - Fast, clear graph-wide queries and export helpers
    """

    __slots__ = ("_nodes", "_path_to_uuid")

    def __init__(
        self, nodes: Iterable[DirectedAcyclicGraphNode[V, E]] | None = None
    ) -> None:
        self._nodes: Dict[UUID, DirectedAcyclicGraphNode[V, E]] = {}
        self._path_to_uuid: Dict[str, UUID] = {}  # Secondary index: path -> UUID
        if nodes:
            for n in nodes:
                self._nodes[n.id] = n
                self._path_to_uuid[n.path] = n.id

    # ---- Properties ---------------------------------------------------------

    @property
    def nodes(self) -> Dict[UUID, DirectedAcyclicGraphNode[V, E]]:
        """All nodes in the graph (keyed by UUID)."""
        return self._nodes

    @property
    def path_to_uuid(self) -> Dict[str, UUID]:
        """Path to UUID mapping for node lookup."""
        return self._path_to_uuid

    # ---- Node operations ----------------------------------------------------

    def add_node(
        self, path: str, value: Optional[V] = None
    ) -> DirectedAcyclicGraphNode[V, E]:
        """Add or update a node in the graph.

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
        node = DirectedAcyclicGraphNode[V, E](id=node_id, path=path, value=value)
        self._nodes[node_id] = node
        self._path_to_uuid[path] = node_id
        return node

    def get_node(self, path: str) -> Optional[DirectedAcyclicGraphNode[V, E]]:
        """Retrieve a node by path."""
        node_uuid = self._path_to_uuid.get(path)
        if node_uuid is None:
            return None
        return self._nodes.get(node_uuid)

    def get_node_by_uuid(
        self, node_uuid: UUID
    ) -> Optional[DirectedAcyclicGraphNode[V, E]]:
        """Retrieve a node by UUID."""
        return self._nodes.get(node_uuid)

    def remove_node(self, path: str) -> None:
        """Remove a node and all its edges."""
        node_uuid = self._path_to_uuid.pop(path, None)
        if node_uuid is None:
            return
        node = self._nodes.pop(node_uuid, None)
        if node is None:
            return
        # Unlink inbound edges (node as dependent)
        for prereq_path in list(node.depends_on.keys()):
            self.remove_edge(prereq_path, path)
        # Unlink outbound edges (node as prerequisite)
        for dep in list(node.dependents()):
            self.remove_edge(path, dep.path)

    # ---- Edge operations ----------------------------------------------------

    def add_edge(
        self,
        prereq_path: str,
        dep_path: str,
        *,
        metadata: Optional[E] = None,
        check_cycle: bool = True,
    ) -> None:
        """Create/refresh an edge prereq_path -> dep_path (idempotent).

        Maintains both the truth side (dependent.depends_on) and the reverse
        WeakSet (prereq._dependents). If check_cycle=True, raises ValueError
        if adding the edge would introduce a cycle.
        """
        if prereq_path == dep_path:
            raise ValueError("Self dependency detected.")

        prereq = self.add_node(prereq_path)
        dep = self.add_node(dep_path)

        # Idempotent update on truth side (key is prereq's path)
        edge = dep.depends_on.get(prereq_path)
        if edge is None:
            dep.depends_on[prereq_path] = DirectedAcyclicGraphEdge(
                target=prereq, metadata=metadata
            )
        else:
            if metadata is not None:
                edge.metadata = metadata
            edge.target = prereq  # ensure pointer is correct

        # Maintain reverse mirror
        prereq.add_dependent(dep)

        if check_cycle and self._would_create_cycle(prereq_path, dep_path):
            # Roll back and raise
            self.remove_edge(prereq_path, dep_path)
            raise ValueError(
                f"Dependency cycle detected when adding {prereq_path} -> {dep_path}."
            )

    def remove_edge(self, prereq_path: str, dep_path: str) -> None:
        """Remove an edge between two nodes."""
        dep = self.get_node(dep_path)
        if not dep:
            return
        # Remove from dependent truth side
        removed = dep.depends_on.pop(prereq_path, None)
        if removed is not None:
            # Remove from reverse mirror
            prereq = self.get_node(prereq_path)
            if prereq is not None:
                try:
                    prereq.remove_dependent(dep)
                except Exception:
                    pass

    # ---- Graph-wide queries -------------------------------------------------

    def prerequisites(self, path: str) -> Set[str]:
        """Get prerequisite paths of a node."""
        node = self.get_node(path)
        return node.prerequisites() if node else set()

    def prerequisite_ids(self, path: str) -> Set[UUID]:
        """Get prerequisite UUIDs of a node."""
        node = self.get_node(path)
        return node.prerequisite_ids() if node else set()

    def prerequisite_paths(self, path: str) -> Set[str]:
        """Get prerequisite paths of a node (alias for prerequisites)."""
        return self.prerequisites(path)

    def dependents(self, path: str) -> Set[str]:
        """Get dependent paths of a node."""
        node = self.get_node(path)
        return {n.path for n in node.dependents()} if node else set()

    def ancestors(self, path: str) -> Set[str]:
        """All transitive prerequisite paths of a node."""
        seen: Set[str] = set()
        stack = list(self.prerequisites(path))
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            stack.extend(self.prerequisites(cur) - seen)
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
        """Return node paths in topological order (raises on cycles)."""
        edges = {node.path: node.prerequisites() for node in self._nodes.values()}
        try:
            return list(TopologicalSorter(edges).static_order())
        except CycleError as err:
            raise ValueError(f"Dependency cycle detected: {err}")

    def validate_acyclic(self) -> None:
        """Validate that the graph is acyclic."""
        _ = self.topological_order()

    def iter_edges(self) -> Iterator[Tuple[str, str, Optional[E]]]:
        """Yield (prereq_path, dep_path, metadata) for all edges."""
        for node in self._nodes.values():
            for prereq_path, edge in node.depends_on.items():
                yield (prereq_path, node.path, edge.metadata)

    # ---- Internal helpers ---------------------------------------------------

    def _would_create_cycle(self, prereq_path: str, dep_path: str) -> bool:
        """True if adding prereq_path -> dep_path closes a cycle.

        We check whether prereq_path is already a descendant of dep_path.
        If yes, then adding the edge would create a cycle.
        """
        return prereq_path in self.descendants(dep_path)

    # ---- Export methods -----------------------------------------------------

    def to_dot(self) -> str:
        """Graphviz DOT (unstyled). Uses path for node labels."""
        lines = ["digraph DAG {"]
        for node in self._nodes.values():
            lines.append(f'  "{node.path}";')
        for src, dst, _ in self.iter_edges():
            lines.append(f'  "{src}" -> "{dst}";')
        lines.append("}")
        return "\n".join(lines)

    def to_mermaid(
        self,
        node_label_fn: Optional[Callable[[Any], str]] = None,
        edge_label_fn: Optional[Callable[[Optional[E]], str]] = None,
        max_label_length: int = 30,
        root_nodes: Optional[List[str]] = None,
    ) -> str:
        """Export graph to Mermaid diagram format.

        Structure:
        - Adds a synthesized root entity node and connects it to all
          graph roots (nodes with no prerequisites).
        - Renders edges directly between related nodes.
        - Uses path for node labels.
        """
        if root_nodes is None:
            root_nodes = [
                node.path for node in self._nodes.values() if not node.prerequisites()
            ]

        # Determine a root entity name
        root_entity = root_nodes[0].split(".")[0] if root_nodes else "Root"

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

        # Add the synthesized root entity node
        safe_root_entity = _safe(root_entity)
        lines.append(f'    {safe_root_entity}["{_fmt_label(root_entity)}"]')

        # Add all nodes with labels
        for node in self._nodes.values():
            safe_id = _safe(node.path)
            if node_label_fn and node.value is not None:
                label = node_label_fn(node.value)
            else:
                label = node.path
            lines.append(f'    {safe_id}["{_fmt_label(label)}"]')

        # Connect root entity to graph roots
        for path in root_nodes:
            lines.append(f"    {safe_root_entity} --> {_safe(path)}")

        # Add edges between nodes with labels
        for prereq_path, dep_path, metadata in self.iter_edges():
            safe_prereq = _safe(prereq_path)
            safe_dep = _safe(dep_path)

            edge_label = ""
            label_txt: Optional[str] = None
            if edge_label_fn and metadata is not None:
                try:
                    label_txt = edge_label_fn(metadata)
                except Exception:
                    label_txt = None
            if not label_txt:
                # Fallback: synthesize from target node constraints
                to_node = self.get_node(dep_path)
                if to_node and to_node.value is not None:
                    try:
                        constraints = getattr(to_node.value, "constraints", [])
                        constraint_labels: List[str] = []
                        for c in constraints or []:
                            if hasattr(c, "to_dag_edge_name"):
                                constraint_labels.append(c.to_dag_edge_name())
                        if constraint_labels:
                            label_txt = constraint_labels[0]
                            if len(constraint_labels) > 1:
                                label_txt += f" (+{len(constraint_labels) - 1} more)"
                    except Exception:
                        label_txt = None

            if label_txt:
                safe_txt = _fmt_label(label_txt)
                if safe_txt:
                    edge_label = f"|{safe_txt}|"

            lines.append(f"    {safe_prereq} -->{edge_label} {safe_dep}")

        return "\n".join(lines)

    def to_ascii_tree(
        self,
        root_nodes: Optional[List[str]] = None,
        node_label_fn: Optional[Callable[[Any], str]] = None,
        edge_label_fn: Optional[Callable[[Optional[E]], str]] = None,
        max_depth: int = 10,
    ) -> str:
        """Generate ASCII tree representation of the DAG.

        Args:
            root_nodes: List of root node paths to start from (nodes with no prerequisites)
            node_label_fn: Optional function to extract label from node value
            edge_label_fn: Optional function to extract label from edge metadata
            max_depth: Maximum depth to traverse

        Returns:
            ASCII tree string showing Schema -> [RootNode, Edges] structure.
            Uses path for node labels.
        """
        if root_nodes is None:
            root_nodes = [
                node.path for node in self._nodes.values() if not node.prerequisites()
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

            # Get label
            if node_label_fn and node.value is not None:
                try:
                    label = node_label_fn(node.value)
                except Exception:
                    label = path
            else:
                label = path

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
                    dep_node.path, child_prefix, i == len(dependents) - 1, depth + 1
                )

        # Top level: Schema
        lines.append("Schema")

        # Extract root entity name
        root_entity = root_nodes[0].split(".")[0] if root_nodes else "RootNode"
        lines.append(f"├── {root_entity}")
        root_prefix = "│   "

        # Render root nodes under RootNode
        for i, root_path in enumerate(root_nodes):
            render_node(root_path, root_prefix, i == len(root_nodes) - 1, 0)

        # Edges section
        lines.append("└── Edges")
        edges_prefix = "    "

        edge_list = list(self.iter_edges())
        # Show constraint edges first for visibility, then structural edges
        edge_list = [e for e in edge_list if e[2] is not None] + [
            e for e in edge_list if e[2] is None
        ]

        for i, (from_path, to_path, metadata) in enumerate(edge_list):
            is_last_edge = i == len(edge_list) - 1
            connector = "└── " if is_last_edge else "├── "

            # Get edge label using edge_label_fn if provided
            edge_label = ""
            if edge_label_fn and metadata is not None:
                try:
                    edge_label = edge_label_fn(metadata)
                except Exception:
                    edge_label = ""
            else:
                # Default: show constraint info from target property
                to_node = self.get_node(to_path)
                if to_node and to_node.value is not None:
                    try:
                        constraints = getattr(to_node.value, "constraints", [])
                        if constraints:
                            constraint_labels: List[str] = []
                            for constraint in constraints or []:
                                edge_name_fn = getattr(
                                    constraint, "to_dag_edge_name", None
                                )
                                if edge_name_fn is not None:
                                    constraint_labels.append(str(edge_name_fn()))
                            if constraint_labels:
                                edge_label = constraint_labels[0]
                                if len(constraint_labels) > 1:
                                    edge_label += f" (+{len(constraint_labels)-1} more)"
                    except Exception:
                        pass

            prefix_str = "[constraint] " if metadata is not None else ""
            label_part = f": {edge_label}" if edge_label else ""
            edge_display = f"{prefix_str}({from_path} -> {to_path}){label_part}"
            lines.append(f"{edges_prefix}{connector}{edge_display}")

        return "\n".join(lines)

    def to_json_dict(self) -> Dict[str, Any]:
        """Export graph structure to JSON-serializable dict.
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
        for prereq_path, dep_path, metadata in self.iter_edges():
            edge_info: Dict[str, Any] = {
                "from": prereq_path,
                "to": dep_path,
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


__all__ = ["DirectedAcyclicGraph"]
