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
from typing import Any, Dict, Generic, Iterable, Iterator, List, Optional, Set, Tuple, TypeVar
import weakref

V = TypeVar("V")  # Node value
E = TypeVar("E")  # Edge metadata


# ---------------------------------------------------------------------------
# Edge & Node
# ---------------------------------------------------------------------------

@dataclass
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
        return "\n".join(lines)
    
    def to_ascii_tree(self, root_nodes=None, node_label_fn=None, max_depth: int = 10) -> str:
        """Generate ASCII tree representation of the DAG.
        
        Args:
            root_nodes: List of root node IDs to start from (nodes with no prerequisites)
            node_label_fn: Optional function to extract label from node value
            max_depth: Maximum depth to traverse
        
        Returns:
            ASCII tree string
        """
        if root_nodes is None:
            # Find nodes with no prerequisites
            root_nodes = [nid for nid, node in self.nodes.items() if not node.prerequisites()]
        
        lines = []
        visited = set()
        
        def render_node(node_id: str, prefix: str = "", is_last: bool = True, depth: int = 0):
            if depth > max_depth or node_id in visited:
                return
            visited.add(node_id)
            
            node = self.nodes.get(node_id)
            if not node:
                return
            
            # Get label
            if node_label_fn and node.value is not None:
                label = node_label_fn(node.value)
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
                is_last_child = (i == len(dependents) - 1)
                render_node(dep_node.id, child_prefix, is_last_child, depth + 1)
        
        # Render each root
        for i, root_id in enumerate(root_nodes):
            is_last_root = (i == len(root_nodes) - 1)
            render_node(root_id, "", is_last_root, 0)
        
        return "\n".join(lines)
    
    def to_mermaid(self, node_label_fn=None, edge_label_fn=None, max_label_length: int = 30) -> str:
        """Export graph to Mermaid diagram format.
        
        Args:
            node_label_fn: Optional function to extract label from node value
            edge_label_fn: Optional function to extract label from edge metadata
            max_label_length: Maximum length for labels (truncated with ...)
        
        Returns:
            Mermaid diagram string that can be embedded in Markdown
        """
        lines = ["graph TD"]
        
        # Add nodes with labels
        for node_id, node in self.nodes.items():
            # Sanitize node ID for Mermaid (alphanumeric + underscore)
            safe_id = node_id.replace("-", "_").replace(".", "_").replace("[", "_").replace("]", "_").replace("*", "star")
            
            # Get label
            if node_label_fn and node.value is not None:
                label = node_label_fn(node.value)
            else:
                label = node_id
            
            # Truncate if too long
            if len(label) > max_label_length:
                label = label[:max_label_length-3] + "..."
            
            # Escape special characters in label
            label = label.replace('"', "'")
            
            lines.append(f'    {safe_id}["{label}"]')
        
        # Add edges
        for prereq_id, dep_id, metadata in self.iter_edges():
            safe_prereq = prereq_id.replace("-", "_").replace(".", "_").replace("[", "_").replace("]", "_").replace("*", "star")
            safe_dep = dep_id.replace("-", "_").replace(".", "_").replace("[", "_").replace("]", "_").replace("*", "star")
            
            # Get edge label
            edge_label = ""
            if edge_label_fn and metadata is not None:
                label = edge_label_fn(metadata)
                if label and len(label) > max_label_length:
                    label = label[:max_label_length-3] + "..."
                if label:
                    label = label.replace('"', "'")
                    edge_label = f"|{label}|"
            
            lines.append(f'    {safe_prereq} -->{edge_label} {safe_dep}')
        
        return "\n".join(lines)

    def to_json_dict(self) -> Dict[str, Any]:
        """Export graph structure to JSON-serializable dict with node and edge info.
        
        Returns:
            Dict with 'nodes' and 'edges' keys containing full graph structure
        """
        nodes_data = []
        for node_id, node in self.nodes.items():
            node_info = {
                "id": node_id,
                "value": None,  # Will be set if serializable
            }
            
            # Try to serialize the value if it has useful attributes
            if node.value is not None:
                if hasattr(node.value, 'model_dump'):
                    # Pydantic model
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
        for prereq_id, dep_id, metadata in self.iter_edges():
            edge_info = {
                "from": prereq_id,
                "to": dep_id,
                "metadata": None,
            }
            
            # Try to serialize metadata
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
        
        return {
            "nodes": nodes_data,
            "edges": edges_data,
            "node_count": len(nodes_data),
            "edge_count": len(edges_data),
        }

    # ---- Internal helpers ---------------------------------------------------
    def _would_create_cycle(self, prereq_id: str, dep_id: str) -> bool:
        """True if adding `prereq_id -> dep_id` closes a cycle.

        We check whether `prereq_id` is already a descendant of `dep_id`.
        If yes, then adding the edge would create a cycle.
        """
        return prereq_id in self.descendants(dep_id)
