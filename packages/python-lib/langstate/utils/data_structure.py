from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Generic, List, Optional, Set, Tuple, TypeVar
from graphlib import TopologicalSorter, CycleError

T = TypeVar("T")

# --- Tree structure ---

@dataclass(slots=True)
class TreeNode(Generic[T]):
    """Pure data-structure representation of a tree node."""
    value: Optional[T] = None
    children: List["TreeNode[T]"] = field(default_factory=list)

    def add_child(self, child: "TreeNode[T]") -> None:
        """Attach a child node."""
        self.children.append(child)

    def walk(self) -> List["TreeNode[T]"]:
        """Return a flat list of all nodes in depth-first order."""
        result = [self]
        for c in self.children:
            result.extend(c.walk())
        return result


# --- Directed Acyclic Graph structure ---

@dataclass(slots=True)
class DAGEdge(Generic[T]):
    """Edge in a Directed Acyclic Graph, representing a dependency relationship."""
    target: "DAGNode"  # The node this edge points to (the prerequisite)
    metadata: Optional[T] = None  # Optional metadata for the edge
    
    def reverse(self, source: "DAGNode") -> "DAGEdge[T]":
        """Return a reversed edge pointing back to the source."""
        return DAGEdge(target=source, metadata=self.metadata)


@dataclass(slots=True)
class DAGNode(Generic[T]):
    """Node in a Directed Acyclic Graph."""
    id: str
    value: Optional[T] = None
    prerequisites: List["DAGEdge[T]"] = field(default_factory=list)  # Edges to prerequisite nodes
    
    def add_prerequisite(self, node: "DAGNode[T]", metadata: Optional[T] = None) -> "DAGEdge[T]":
        """Add a prerequisite (dependency) to this node."""
        if node.id == self.id:
            raise ValueError("Self dependency detected.")
        edge = DAGEdge(target=node, metadata=metadata)
        self.prerequisites.append(edge)
        return edge
    
    def remove_prerequisite(self, node: "DAGNode[T]") -> None:
        """Remove a prerequisite from this node."""
        self.prerequisites = [edge for edge in self.prerequisites if edge.target.id != node.id]
    
    def has_prerequisite(self, node_id: str) -> bool:
        """Check if a node is a prerequisite of this node."""
        return any(edge.target.id == node_id for edge in self.prerequisites)
    
    def get_prerequisite_ids(self) -> Set[str]:
        """Get IDs of all prerequisite nodes."""
        return {edge.target.id for edge in self.prerequisites}
    
    def is_ready(self, satisfied: Set[str]) -> bool:
        """Check if all prerequisites are satisfied."""
        return self.get_prerequisite_ids().issubset(satisfied)



@dataclass(slots=True)
class DAGGraph(Generic[T]):
    """Pure data-structure representation of a Directed Acyclic Graph (DAG)."""
    nodes: Dict[str, DAGNode[T]] = field(default_factory=dict)
    
    def add_node(self, node_id: str, value: Optional[T] = None) -> DAGNode[T]:
        """Add a node to the DAG."""
        if node_id not in self.nodes:
            self.nodes[node_id] = DAGNode(id=node_id, value=value)
        return self.nodes[node_id]

    def add_edge(self, prereq_id: str, dependent_id: str, metadata: Optional[T] = None) -> DAGEdge[T]:
        """Add a directed edge from prereq to dependent."""
        if prereq_id == dependent_id:
            raise ValueError("Self dependency detected.")
        
        # Ensure both nodes exist
        prereq_node = self.add_node(prereq_id)
        dependent_node = self.add_node(dependent_id)
        
        # Add prerequisite relationship
        return dependent_node.add_prerequisite(prereq_node, metadata)

    def topological_sort(self) -> List[str]:
        """Return a list of node ids in topological order."""
        edges_dict = {node_id: node.get_prerequisite_ids() for node_id, node in self.nodes.items()}
        sorter = TopologicalSorter(edges_dict)
        try:
            return list(sorter.static_order())
        except CycleError as e:
            raise ValueError(f"Dependency cycle detected: {e}")

    def dependents(self, node_id: str) -> Set[str]:
        """Return nodes that directly depend on a given node."""
        return {nid for nid, node in self.nodes.items() if node.has_prerequisite(node_id)}

    def prerequisites(self, node_id: str) -> Set[str]:
        """Return nodes that the given node depends on."""
        if node_id not in self.nodes:
            return set()
        return self.nodes[node_id].get_prerequisite_ids()

    def ready_nodes(self, satisfied: Set[str]) -> Set[str]:
        """Return nodes whose dependencies are all satisfied."""
        return {nid for nid, node in self.nodes.items() if node.is_ready(satisfied)}

    def validate_acyclic(self) -> None:
        """Raise if a cycle is detected."""
        _ = self.topological_sort()
    
    def get_all_edges(self) -> List[Tuple[str, str, Optional[T]]]:
        """Return all edges in the graph as (prereq_id, dependent_id, metadata) tuples."""
        edges = []
        for node_id, node in self.nodes.items():
            for edge in node.prerequisites:
                edges.append((edge.target.id, node_id, edge.metadata))
        return edges
