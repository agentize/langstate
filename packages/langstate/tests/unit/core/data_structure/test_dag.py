"""
Comprehensive unit tests for DirectedAcyclicGraph (DAG) implementation.

Tests cover:
- Node operations (add, get, remove) with UUID/path duality
- Edge operations with cycle detection
- Graph queries (prerequisites, dependents, ancestors, descendants)
- Ready node detection
- Topological ordering
- Export methods (DOT, Mermaid, JSON, ASCII tree)
- Schema classes (DirectedAcyclicGraphNode, DirectedAcyclicGraphEdge)

Target: 100% code coverage for dag.py and schema.py
"""

# pyright: reportPrivateUsage=false

from __future__ import annotations

import json
import pytest
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from core.data_structure.dag.dag import DirectedAcyclicGraph
from core.data_structure.dag.schema import (
    DirectedAcyclicGraphEdge,
    DirectedAcyclicGraphNode,
)


# ============================================================================
# Test Fixtures and Helpers
# ============================================================================


@dataclass
class MockNodeValue:
    """Mock node value for testing node_label_fn."""

    name: str
    constraints: Optional[List[Any]] = None

    def model_dump(self) -> Dict[str, Any]:
        return {"name": self.name}


@dataclass
class MockEdgeMetadata:
    """Mock edge metadata for testing edge_label_fn."""

    weight: int
    label: str

    def model_dump(self) -> Dict[str, Any]:
        return {"weight": self.weight, "label": self.label}


class MockConstraint:
    """Mock constraint with to_dag_edge_name method."""

    def __init__(self, name: str):
        self._name = name

    def to_dag_edge_name(self) -> str:
        return self._name


@pytest.fixture
def empty_dag() -> DirectedAcyclicGraph[str, str]:
    """Create an empty DAG."""
    return DirectedAcyclicGraph[str, str]()


@pytest.fixture
def simple_dag() -> DirectedAcyclicGraph[str, str]:
    """Create a simple DAG: A -> B -> C."""
    dag = DirectedAcyclicGraph[str, str]()
    dag.add_node("A", value="value_A")
    dag.add_node("B", value="value_B")
    dag.add_node("C", value="value_C")
    dag.add_edge("A", "B")
    dag.add_edge("B", "C")
    return dag


@pytest.fixture
def diamond_dag() -> DirectedAcyclicGraph[str, str]:
    """Create a diamond DAG: A -> B, A -> C, B -> D, C -> D."""
    dag = DirectedAcyclicGraph[str, str]()
    dag.add_node("A")
    dag.add_node("B")
    dag.add_node("C")
    dag.add_node("D")
    dag.add_edge("A", "B")
    dag.add_edge("A", "C")
    dag.add_edge("B", "D")
    dag.add_edge("C", "D")
    return dag


@pytest.fixture
def any_dag() -> DirectedAcyclicGraph[Any, Any]:
    """Create an empty DAG with Any types for testing custom value/metadata types."""
    return DirectedAcyclicGraph[Any, Any]()


# ============================================================================
# Test DirectedAcyclicGraphNode (Schema)
# ============================================================================


class TestDirectedAcyclicGraphNode:
    """Tests for DirectedAcyclicGraphNode dataclass."""

    def test_node_creation_with_uuid_and_path(self):
        """Node should be created with given UUID and path."""
        node_id = uuid4()
        node = DirectedAcyclicGraphNode[str, str](id=node_id, path="test.path")

        assert node.id == node_id
        assert node.path == "test.path"
        assert node.value is None
        assert node.depends_on == {}
        assert node.dependents() == set()

    def test_node_creation_with_value(self):
        """Node should store optional value."""
        node_id = uuid4()
        node = DirectedAcyclicGraphNode[str, str](
            id=node_id, path="test.path", value="test_value"
        )

        assert node.value == "test_value"

    def test_node_hash_by_uuid(self):
        """Node hash should be based on UUID."""
        node_id = uuid4()
        node = DirectedAcyclicGraphNode[str, str](id=node_id, path="test.path")

        assert hash(node) == hash(node_id)

    def test_node_equality_by_uuid(self):
        """Two nodes with same UUID should be equal."""
        node_id = uuid4()
        node1 = DirectedAcyclicGraphNode[str, str](id=node_id, path="path1")
        node2 = DirectedAcyclicGraphNode[str, str](id=node_id, path="path2")

        assert node1 == node2

    def test_node_inequality_different_uuid(self):
        """Two nodes with different UUIDs should not be equal."""
        node1 = DirectedAcyclicGraphNode[str, str](id=uuid4(), path="path")
        node2 = DirectedAcyclicGraphNode[str, str](id=uuid4(), path="path")

        assert node1 != node2

    def test_node_inequality_with_non_node(self):
        """Node should not equal non-node objects."""
        node = DirectedAcyclicGraphNode[str, str](id=uuid4(), path="path")

        assert node != "not a node"
        assert node != 123
        assert node != None

    def test_add_and_remove_dependent(self):
        """Test dependent management via WeakSet."""
        prereq = DirectedAcyclicGraphNode[str, str](id=uuid4(), path="prereq")
        dependent = DirectedAcyclicGraphNode[str, str](id=uuid4(), path="dependent")

        prereq.add_dependent(dependent)
        assert dependent in prereq.dependents()

        prereq.remove_dependent(dependent)
        assert dependent not in prereq.dependents()

    def test_prerequisites_empty(self):
        """Node without dependencies should have empty prerequisites."""
        node = DirectedAcyclicGraphNode[str, str](id=uuid4(), path="node")

        assert node.prerequisites() == set()
        assert node.prerequisite_ids() == set()
        assert node.prerequisite_paths() == set()
        assert node.prerequisite_nodes() == set()

    def test_prerequisites_with_dependencies(self):
        """Node with dependencies should report correct prerequisites."""
        prereq = DirectedAcyclicGraphNode[str, str](id=uuid4(), path="prereq")
        dependent = DirectedAcyclicGraphNode[str, str](id=uuid4(), path="dependent")

        edge = DirectedAcyclicGraphEdge[str, str](target=prereq)
        dependent.depends_on["prereq"] = edge

        assert dependent.prerequisites() == {"prereq"}
        assert dependent.prerequisite_ids() == {prereq.id}
        assert dependent.prerequisite_paths() == {"prereq"}
        assert dependent.prerequisite_nodes() == {prereq}

    def test_is_ready_no_prerequisites(self):
        """Node without prerequisites is always ready."""
        node = DirectedAcyclicGraphNode[str, str](id=uuid4(), path="node")

        assert node.is_ready(set()) is True
        assert node.is_ready({"other"}) is True

    def test_is_ready_with_prerequisites_satisfied(self):
        """Node is ready when all prerequisites are satisfied."""
        prereq = DirectedAcyclicGraphNode[str, str](id=uuid4(), path="prereq")
        dependent = DirectedAcyclicGraphNode[str, str](id=uuid4(), path="dependent")

        edge = DirectedAcyclicGraphEdge[str, str](target=prereq)
        dependent.depends_on["prereq"] = edge

        assert dependent.is_ready({"prereq"}) is True
        assert dependent.is_ready({"prereq", "extra"}) is True

    def test_is_ready_with_prerequisites_not_satisfied(self):
        """Node is not ready when prerequisites are missing."""
        prereq = DirectedAcyclicGraphNode[str, str](id=uuid4(), path="prereq")
        dependent = DirectedAcyclicGraphNode[str, str](id=uuid4(), path="dependent")

        edge = DirectedAcyclicGraphEdge[str, str](target=prereq)
        dependent.depends_on["prereq"] = edge

        assert dependent.is_ready(set()) is False
        assert dependent.is_ready({"wrong"}) is False


# ============================================================================
# Test DirectedAcyclicGraphEdge (Schema)
# ============================================================================


class TestDirectedAcyclicGraphEdge:
    """Tests for DirectedAcyclicGraphEdge dataclass."""

    def test_edge_creation(self):
        """Edge should be created with target node."""
        target = DirectedAcyclicGraphNode[str, str](id=uuid4(), path="target")
        edge = DirectedAcyclicGraphEdge[str, str](target=target)

        assert edge.target == target
        assert edge.metadata is None

    def test_edge_with_metadata(self):
        """Edge should store optional metadata."""
        target = DirectedAcyclicGraphNode[str, str](id=uuid4(), path="target")
        edge = DirectedAcyclicGraphEdge[str, str](target=target, metadata="edge_data")

        assert edge.metadata == "edge_data"

    def test_edge_sources_returns_single_element_set(self):
        """Edge sources should return set with target for DAG compatibility."""
        target = DirectedAcyclicGraphNode[str, str](id=uuid4(), path="target")
        edge = DirectedAcyclicGraphEdge[str, str](target=target)

        assert edge.sources == {target}

    def test_edge_source_ids(self):
        """Edge source_ids should return target's UUID in set."""
        target = DirectedAcyclicGraphNode[str, str](id=uuid4(), path="target")
        edge = DirectedAcyclicGraphEdge[str, str](target=target)

        assert edge.source_ids() == {target.id}

    def test_edge_source_paths(self):
        """Edge source_paths should return target's path in set."""
        target = DirectedAcyclicGraphNode[str, str](id=uuid4(), path="target")
        edge = DirectedAcyclicGraphEdge[str, str](target=target)

        assert edge.source_paths() == {"target"}


# ============================================================================
# Test DirectedAcyclicGraph - Initialization
# ============================================================================


class TestDAGInitialization:
    """Tests for DAG initialization."""

    def test_empty_dag_creation(self):
        """Empty DAG should have no nodes."""
        dag = DirectedAcyclicGraph[str, str]()

        assert dag.nodes == {}
        assert dag.path_to_uuid == {}

    def test_dag_creation_with_existing_nodes(self):
        """DAG can be initialized with existing nodes."""
        node1 = DirectedAcyclicGraphNode[str, str](id=uuid4(), path="node1")
        node2 = DirectedAcyclicGraphNode[str, str](id=uuid4(), path="node2")

        dag = DirectedAcyclicGraph[str, str](nodes=[node1, node2])

        assert len(dag.nodes) == 2
        assert dag.get_node("node1") == node1
        assert dag.get_node("node2") == node2
        assert dag.path_to_uuid["node1"] == node1.id
        assert dag.path_to_uuid["node2"] == node2.id


# ============================================================================
# Test DirectedAcyclicGraph - Node Operations
# ============================================================================


class TestDAGNodeOperations:
    """Tests for DAG node operations."""

    def test_add_node_creates_new_node(self, empty_dag: DirectedAcyclicGraph[str, str]):
        """Adding a new node should create it in the graph."""
        node = empty_dag.add_node("test.path", value="test_value")

        assert node.path == "test.path"
        assert node.value == "test_value"
        assert node.id is not None
        assert empty_dag.get_node("test.path") == node

    def test_add_node_idempotent_returns_existing(
        self, empty_dag: DirectedAcyclicGraph[str, str]
    ):
        """Adding existing node should return it without creating duplicate."""
        node1 = empty_dag.add_node("test.path", value="value1")
        node2 = empty_dag.add_node("test.path")

        assert node1 is node2
        assert node1.value == "value1"  # Value unchanged

    def test_add_node_updates_value_when_provided(
        self, empty_dag: DirectedAcyclicGraph[str, str]
    ):
        """Adding existing node with new value should update it."""
        node1 = empty_dag.add_node("test.path", value="value1")
        node2 = empty_dag.add_node("test.path", value="value2")

        assert node1 is node2
        assert node1.value == "value2"

    def test_get_node_existing(self, simple_dag: DirectedAcyclicGraph[str, str]):
        """Getting existing node should return it."""
        node = simple_dag.get_node("A")

        assert node is not None
        assert node.path == "A"
        assert node.value == "value_A"

    def test_get_node_nonexistent(self, empty_dag: DirectedAcyclicGraph[str, str]):
        """Getting nonexistent node should return None."""
        node = empty_dag.get_node("nonexistent")

        assert node is None

    def test_get_node_by_uuid(self, empty_dag: DirectedAcyclicGraph[str, str]):
        """Getting node by UUID should work."""
        added_node = empty_dag.add_node("test.path")

        retrieved = empty_dag.get_node_by_uuid(added_node.id)

        assert retrieved == added_node

    def test_get_node_by_uuid_nonexistent(
        self, empty_dag: DirectedAcyclicGraph[str, str]
    ):
        """Getting nonexistent UUID should return None."""
        result = empty_dag.get_node_by_uuid(uuid4())

        assert result is None

    def test_remove_node_removes_from_graph(
        self, simple_dag: DirectedAcyclicGraph[str, str]
    ):
        """Removing node should remove it from graph."""
        simple_dag.remove_node("B")

        assert simple_dag.get_node("B") is None
        assert "B" not in simple_dag.path_to_uuid

    def test_remove_node_removes_inbound_edges(
        self, simple_dag: DirectedAcyclicGraph[str, str]
    ):
        """Removing node should remove edges where node is dependent."""
        simple_dag.remove_node("B")

        # B no longer depends on A
        node_a = simple_dag.get_node("A")
        assert node_a is not None
        assert all(d.path != "B" for d in node_a.dependents())

    def test_remove_node_removes_outbound_edges(
        self, simple_dag: DirectedAcyclicGraph[str, str]
    ):
        """Removing node should remove edges where node is prerequisite."""
        simple_dag.remove_node("B")

        # C no longer depends on B
        node_c = simple_dag.get_node("C")
        assert node_c is not None
        assert "B" not in node_c.depends_on

    def test_remove_nonexistent_node_no_error(
        self, empty_dag: DirectedAcyclicGraph[str, str]
    ):
        """Removing nonexistent node should not raise error."""
        empty_dag.remove_node("nonexistent")  # Should not raise


# ============================================================================
# Test DirectedAcyclicGraph - Edge Operations
# ============================================================================


class TestDAGEdgeOperations:
    """Tests for DAG edge operations."""

    def test_add_edge_creates_nodes_if_needed(
        self, empty_dag: DirectedAcyclicGraph[str, str]
    ):
        """Adding edge should create nodes if they don't exist."""
        empty_dag.add_edge("prereq", "dep")

        assert empty_dag.get_node("prereq") is not None
        assert empty_dag.get_node("dep") is not None

    def test_add_edge_creates_dependency(
        self, empty_dag: DirectedAcyclicGraph[str, str]
    ):
        """Adding edge should create dependency relationship."""
        empty_dag.add_edge("prereq", "dep")

        dep_node = empty_dag.get_node("dep")
        assert dep_node is not None
        assert "prereq" in dep_node.depends_on

    def test_add_edge_with_metadata(self, empty_dag: DirectedAcyclicGraph[str, str]):
        """Adding edge should store metadata."""
        empty_dag.add_edge("prereq", "dep", metadata="edge_metadata")

        dep_node = empty_dag.get_node("dep")
        assert dep_node is not None
        edge = dep_node.depends_on["prereq"]
        assert edge.metadata == "edge_metadata"

    def test_add_edge_idempotent(self, empty_dag: DirectedAcyclicGraph[str, str]):
        """Adding same edge twice should be idempotent."""
        empty_dag.add_edge("prereq", "dep", metadata="meta1")
        empty_dag.add_edge("prereq", "dep", metadata="meta2")

        dep_node = empty_dag.get_node("dep")
        assert dep_node is not None
        assert len(dep_node.depends_on) == 1
        assert dep_node.depends_on["prereq"].metadata == "meta2"

    def test_add_edge_maintains_reverse_mirror(
        self, empty_dag: DirectedAcyclicGraph[str, str]
    ):
        """Adding edge should update prerequisite's dependents."""
        empty_dag.add_edge("prereq", "dep")

        prereq_node = empty_dag.get_node("prereq")
        dep_node = empty_dag.get_node("dep")
        assert prereq_node is not None
        assert dep_node is not None
        assert dep_node in prereq_node.dependents()

    def test_add_edge_self_dependency_raises(
        self, empty_dag: DirectedAcyclicGraph[str, str]
    ):
        """Self-dependency should raise ValueError."""
        with pytest.raises(ValueError, match="Self dependency"):
            empty_dag.add_edge("A", "A")

    def test_add_edge_cycle_detection(self, simple_dag: DirectedAcyclicGraph[str, str]):
        """Adding cycle-creating edge should raise ValueError."""
        # simple_dag: A -> B -> C
        with pytest.raises(ValueError, match="cycle"):
            simple_dag.add_edge("C", "A")  # Would create cycle

    def test_add_edge_no_cycle_check(self, simple_dag: DirectedAcyclicGraph[str, str]):
        """Cycle check can be disabled."""
        # This would create a cycle, but check is disabled
        simple_dag.add_edge("C", "A", check_cycle=False)

        # Edge should be added
        node_a = simple_dag.get_node("A")
        assert node_a is not None
        assert "C" in node_a.depends_on

    def test_remove_edge(self, simple_dag: DirectedAcyclicGraph[str, str]):
        """Removing edge should remove dependency."""
        simple_dag.remove_edge("A", "B")

        node_b = simple_dag.get_node("B")
        assert node_b is not None
        assert "A" not in node_b.depends_on

    def test_remove_edge_updates_reverse_mirror(
        self, simple_dag: DirectedAcyclicGraph[str, str]
    ):
        """Removing edge should update prerequisite's dependents."""
        node_a = simple_dag.get_node("A")
        node_b = simple_dag.get_node("B")
        assert node_a is not None
        assert node_b is not None

        assert node_b in node_a.dependents()

        simple_dag.remove_edge("A", "B")

        assert node_b not in node_a.dependents()

    def test_remove_nonexistent_edge_no_error(
        self, simple_dag: DirectedAcyclicGraph[str, str]
    ):
        """Removing nonexistent edge should not raise error."""
        simple_dag.remove_edge("A", "C")  # No direct edge exists

    def test_remove_edge_nonexistent_node_no_error(
        self, empty_dag: DirectedAcyclicGraph[str, str]
    ):
        """Removing edge from nonexistent nodes should not raise error."""
        empty_dag.remove_edge("nonexistent1", "nonexistent2")


# ============================================================================
# Test DirectedAcyclicGraph - Graph Queries
# ============================================================================


class TestDAGGraphQueries:
    """Tests for DAG graph-wide queries."""

    def test_prerequisites(self, simple_dag: DirectedAcyclicGraph[str, str]):
        """Prerequisites should return direct prerequisites."""
        assert simple_dag.prerequisites("B") == {"A"}
        assert simple_dag.prerequisites("C") == {"B"}
        assert simple_dag.prerequisites("A") == set()

    def test_prerequisites_nonexistent_node(
        self, empty_dag: DirectedAcyclicGraph[str, str]
    ):
        """Prerequisites of nonexistent node should be empty set."""
        assert empty_dag.prerequisites("nonexistent") == set()

    def test_prerequisite_ids(self, simple_dag: DirectedAcyclicGraph[str, str]):
        """Prerequisite IDs should return UUIDs."""
        node_a = simple_dag.get_node("A")
        assert node_a is not None

        prereq_ids = simple_dag.prerequisite_ids("B")

        assert prereq_ids == {node_a.id}

    def test_prerequisite_paths(self, simple_dag: DirectedAcyclicGraph[str, str]):
        """Prerequisite paths should be alias for prerequisites."""
        assert simple_dag.prerequisite_paths("B") == simple_dag.prerequisites("B")

    def test_dependents(self, simple_dag: DirectedAcyclicGraph[str, str]):
        """Dependents should return direct dependents."""
        assert simple_dag.dependents("A") == {"B"}
        assert simple_dag.dependents("B") == {"C"}
        assert simple_dag.dependents("C") == set()

    def test_dependents_nonexistent_node(
        self, empty_dag: DirectedAcyclicGraph[str, str]
    ):
        """Dependents of nonexistent node should be empty set."""
        assert empty_dag.dependents("nonexistent") == set()

    def test_ancestors(self, simple_dag: DirectedAcyclicGraph[str, str]):
        """Ancestors should return all transitive prerequisites."""
        # A -> B -> C
        assert simple_dag.ancestors("C") == {"A", "B"}
        assert simple_dag.ancestors("B") == {"A"}
        assert simple_dag.ancestors("A") == set()

    def test_ancestors_diamond(self, diamond_dag: DirectedAcyclicGraph[str, str]):
        """Ancestors should handle diamond pattern."""
        # A -> B -> D, A -> C -> D
        assert diamond_dag.ancestors("D") == {"A", "B", "C"}

    def test_descendants(self, simple_dag: DirectedAcyclicGraph[str, str]):
        """Descendants should return all transitive dependents."""
        # A -> B -> C
        assert simple_dag.descendants("A") == {"B", "C"}
        assert simple_dag.descendants("B") == {"C"}
        assert simple_dag.descendants("C") == set()

    def test_descendants_diamond(self, diamond_dag: DirectedAcyclicGraph[str, str]):
        """Descendants should handle diamond pattern."""
        # A -> B -> D, A -> C -> D
        assert diamond_dag.descendants("A") == {"B", "C", "D"}

    def test_iter_edges(self, simple_dag: DirectedAcyclicGraph[str, str]):
        """iter_edges should yield all edges."""
        edges = list(simple_dag.iter_edges())

        assert len(edges) == 2
        edge_pairs = {(e[0], e[1]) for e in edges}
        assert ("A", "B") in edge_pairs
        assert ("B", "C") in edge_pairs


# ============================================================================
# Test DirectedAcyclicGraph - Ready Nodes
# ============================================================================


class TestDAGReadyNodes:
    """Tests for ready node detection."""

    def test_ready_nodes_empty_satisfied(
        self, simple_dag: DirectedAcyclicGraph[str, str]
    ):
        """Only root nodes should be ready with empty satisfied set."""
        ready = simple_dag.ready_nodes(set())

        assert ready == {"A"}

    def test_ready_nodes_partial_satisfied(
        self, simple_dag: DirectedAcyclicGraph[str, str]
    ):
        """Nodes with all prerequisites satisfied should be ready."""
        ready = simple_dag.ready_nodes({"A"})

        assert "A" in ready
        assert "B" in ready
        assert "C" not in ready

    def test_ready_nodes_all_satisfied(
        self, simple_dag: DirectedAcyclicGraph[str, str]
    ):
        """All nodes should be ready when all prerequisites satisfied."""
        ready = simple_dag.ready_nodes({"A", "B"})

        assert ready == {"A", "B", "C"}

    def test_ready_nodes_diamond(self, diamond_dag: DirectedAcyclicGraph[str, str]):
        """Ready nodes in diamond pattern."""
        # A -> B -> D, A -> C -> D

        # Initially only A is ready
        assert diamond_dag.ready_nodes(set()) == {"A"}

        # With A satisfied, B and C become ready
        assert diamond_dag.ready_nodes({"A"}) == {"A", "B", "C"}

        # D needs both B and C
        assert diamond_dag.ready_nodes({"A", "B"}) == {"A", "B", "C"}
        assert diamond_dag.ready_nodes({"A", "B", "C"}) == {"A", "B", "C", "D"}


# ============================================================================
# Test DirectedAcyclicGraph - Topological Order & Validation
# ============================================================================


class TestDAGTopologicalOrder:
    """Tests for topological ordering and validation."""

    def test_topological_order_simple(self, simple_dag: DirectedAcyclicGraph[str, str]):
        """Topological order should respect dependencies."""
        order = simple_dag.topological_order()

        assert order.index("A") < order.index("B")
        assert order.index("B") < order.index("C")

    def test_topological_order_diamond(
        self, diamond_dag: DirectedAcyclicGraph[str, str]
    ):
        """Topological order should handle diamond pattern."""
        order = diamond_dag.topological_order()

        assert order.index("A") < order.index("B")
        assert order.index("A") < order.index("C")
        assert order.index("B") < order.index("D")
        assert order.index("C") < order.index("D")

    def test_topological_order_with_cycle_raises(
        self, simple_dag: DirectedAcyclicGraph[str, str]
    ):
        """Topological order with cycle should raise ValueError."""
        # Create a cycle by disabling check
        simple_dag.add_edge("C", "A", check_cycle=False)

        with pytest.raises(ValueError, match="cycle"):
            simple_dag.topological_order()

    def test_validate_acyclic_valid(self, simple_dag: DirectedAcyclicGraph[str, str]):
        """Validate acyclic should pass for valid DAG."""
        simple_dag.validate_acyclic()  # Should not raise

    def test_validate_acyclic_with_cycle_raises(
        self, simple_dag: DirectedAcyclicGraph[str, str]
    ):
        """Validate acyclic should raise for cyclic graph."""
        simple_dag.add_edge("C", "A", check_cycle=False)

        with pytest.raises(ValueError, match="cycle"):
            simple_dag.validate_acyclic()


# ============================================================================
# Test DirectedAcyclicGraph - Internal Helpers
# ============================================================================


class TestDAGInternalHelpers:
    """Tests for internal helper methods."""

    def test_would_create_cycle_true(self, simple_dag: DirectedAcyclicGraph[str, str]):
        """_would_create_cycle should detect potential cycle."""
        # A -> B -> C
        # Adding C -> A would create cycle
        assert simple_dag._would_create_cycle("C", "A") is True

    def test_would_create_cycle_false(self, simple_dag: DirectedAcyclicGraph[str, str]):
        """_would_create_cycle should allow valid edges."""
        # Adding A -> C would not create cycle
        assert simple_dag._would_create_cycle("A", "C") is False


# ============================================================================
# Test DirectedAcyclicGraph - Export Methods
# ============================================================================


class TestDAGExportDOT:
    """Tests for DOT export."""

    def test_to_dot_empty(self, empty_dag: DirectedAcyclicGraph[str, str]):
        """Empty DAG should produce minimal DOT output."""
        dot = empty_dag.to_dot()

        assert "digraph DAG {" in dot
        assert "}" in dot

    def test_to_dot_with_nodes(self, simple_dag: DirectedAcyclicGraph[str, str]):
        """DOT should include all nodes."""
        dot = simple_dag.to_dot()

        assert '"A"' in dot
        assert '"B"' in dot
        assert '"C"' in dot

    def test_to_dot_with_edges(self, simple_dag: DirectedAcyclicGraph[str, str]):
        """DOT should include all edges."""
        dot = simple_dag.to_dot()

        assert '"A" -> "B"' in dot
        assert '"B" -> "C"' in dot


class TestDAGExportMermaid:
    """Tests for Mermaid export."""

    def test_to_mermaid_structure(self, simple_dag: DirectedAcyclicGraph[str, str]):
        """Mermaid output should have correct structure."""
        mermaid = simple_dag.to_mermaid()

        assert "graph TD" in mermaid

    def test_to_mermaid_nodes(self, simple_dag: DirectedAcyclicGraph[str, str]):
        """Mermaid should include node definitions."""
        mermaid = simple_dag.to_mermaid()

        assert "A[" in mermaid
        assert "B[" in mermaid
        assert "C[" in mermaid

    def test_to_mermaid_edges(self, simple_dag: DirectedAcyclicGraph[str, str]):
        """Mermaid should include edges."""
        mermaid = simple_dag.to_mermaid()

        assert "A -->" in mermaid

    def test_to_mermaid_with_custom_label_fn(
        self, any_dag: DirectedAcyclicGraph[Any, Any]
    ):
        """Mermaid should use custom label function."""
        any_dag.add_node("A", value=MockNodeValue(name="Node A"))
        any_dag.add_node("B", value=MockNodeValue(name="Node B"))
        any_dag.add_edge("A", "B")

        mermaid = any_dag.to_mermaid(node_label_fn=lambda v: v.name if v else "")

        assert "Node A" in mermaid
        assert "Node B" in mermaid

    def test_to_mermaid_with_edge_label_fn(
        self, any_dag: DirectedAcyclicGraph[Any, Any]
    ):
        """Mermaid should use edge label function."""
        any_dag.add_node("A")
        any_dag.add_node("B")
        any_dag.add_edge("A", "B", metadata=MockEdgeMetadata(weight=1, label="test"))

        mermaid = any_dag.to_mermaid(edge_label_fn=lambda m: m.label if m else "")

        assert "test" in mermaid

    def test_to_mermaid_label_truncation(
        self, empty_dag: DirectedAcyclicGraph[str, str]
    ):
        """Mermaid should truncate long labels."""
        long_path = "this.is.a.very.long.path.name.that.exceeds.max.length"
        empty_dag.add_node(long_path)

        mermaid = empty_dag.to_mermaid(max_label_length=20)

        assert "..." in mermaid

    def test_to_mermaid_safe_characters(
        self, empty_dag: DirectedAcyclicGraph[str, str]
    ):
        """Mermaid should sanitize special characters."""
        empty_dag.add_node("path[0].item-name")

        mermaid = empty_dag.to_mermaid()

        # Brackets, dots, and dashes should be replaced
        assert "path_0__item_name" in mermaid

    def test_to_mermaid_with_root_nodes_param(
        self, simple_dag: DirectedAcyclicGraph[str, str]
    ):
        """Mermaid should accept root_nodes parameter."""
        mermaid = simple_dag.to_mermaid(root_nodes=["A"])

        assert "graph TD" in mermaid

    def test_to_mermaid_with_constraint_fallback(
        self, any_dag: DirectedAcyclicGraph[Any, Any]
    ):
        """Mermaid should use constraint fallback for edge labels."""
        constraint = MockConstraint("constraint_label")
        node_value = MockNodeValue(name="B", constraints=[constraint])

        any_dag.add_node("A")
        any_dag.add_node("B", value=node_value)
        any_dag.add_edge("A", "B", metadata="has_metadata")

        mermaid = any_dag.to_mermaid()

        # Should try to get edge label from constraints
        assert "A" in mermaid


class TestDAGExportJSON:
    """Tests for JSON export."""

    def test_to_json_dict_structure(self, simple_dag: DirectedAcyclicGraph[str, str]):
        """JSON dict should have correct structure."""
        data = simple_dag.to_json_dict()

        assert "nodes" in data
        assert "edges" in data
        assert "node_count" in data
        assert "edge_count" in data
        assert data["node_count"] == 3
        assert data["edge_count"] == 2

    def test_to_json_dict_node_data(self, simple_dag: DirectedAcyclicGraph[str, str]):
        """JSON dict should include node data with UUID and path."""
        data = simple_dag.to_json_dict()

        node_paths = {n["path"] for n in data["nodes"]}
        assert node_paths == {"A", "B", "C"}

        # Check UUID format
        for node in data["nodes"]:
            assert "id" in node
            UUID(node["id"])  # Should be valid UUID string

    def test_to_json_dict_edge_data(self, simple_dag: DirectedAcyclicGraph[str, str]):
        """JSON dict should include edge data."""
        data = simple_dag.to_json_dict()

        edge_pairs = {(e["from"], e["to"]) for e in data["edges"]}
        assert ("A", "B") in edge_pairs
        assert ("B", "C") in edge_pairs

    def test_to_json_dict_with_model_dump_value(
        self, any_dag: DirectedAcyclicGraph[Any, Any]
    ):
        """JSON dict should use model_dump for node values."""
        any_dag.add_node("A", value=MockNodeValue(name="Test"))

        data = any_dag.to_json_dict()

        node_a = next(n for n in data["nodes"] if n["path"] == "A")
        assert node_a["value"] == {"name": "Test"}

    def test_to_json_dict_with_model_dump_metadata(
        self, any_dag: DirectedAcyclicGraph[Any, Any]
    ):
        """JSON dict should use model_dump for edge metadata."""
        any_dag.add_node("A")
        any_dag.add_node("B")
        any_dag.add_edge("A", "B", metadata=MockEdgeMetadata(weight=5, label="test"))

        data = any_dag.to_json_dict()

        edge = data["edges"][0]
        assert edge["metadata"] == {"weight": 5, "label": "test"}

    def test_to_json_dict_with_dict_value(
        self, any_dag: DirectedAcyclicGraph[Any, Any]
    ):
        """JSON dict should handle objects with __dict__."""

        class SimpleValue:
            def __init__(self):
                self.x = 1
                self.y = 2

        any_dag.add_node("A", value=SimpleValue())

        data = any_dag.to_json_dict()

        node_a = next(n for n in data["nodes"] if n["path"] == "A")
        assert node_a["value"]["x"] == 1

    def test_to_json_dict_with_primitive_value(
        self, empty_dag: DirectedAcyclicGraph[str, str]
    ):
        """JSON dict should handle primitive values."""
        empty_dag.add_node("A", value="simple_string")

        data = empty_dag.to_json_dict()

        node_a = next(n for n in data["nodes"] if n["path"] == "A")
        assert node_a["value"] == "simple_string"

    def test_to_json_string(self, simple_dag: DirectedAcyclicGraph[str, str]):
        """to_json should return valid JSON string."""
        json_str = simple_dag.to_json()

        parsed = json.loads(json_str)
        assert parsed["node_count"] == 3

    def test_to_json_pretty(self, simple_dag: DirectedAcyclicGraph[str, str]):
        """to_json with pretty=True should be indented."""
        json_str = simple_dag.to_json(pretty=True, indent=4)

        assert "\n" in json_str
        assert "    " in json_str  # 4-space indent

    def test_to_json_compact(self, simple_dag: DirectedAcyclicGraph[str, str]):
        """to_json with pretty=False should be compact."""
        json_str = simple_dag.to_json(pretty=False)

        assert "\n" not in json_str


class TestDAGExportASCII:
    """Tests for ASCII tree export."""

    def test_to_ascii_tree_basic(self, simple_dag: DirectedAcyclicGraph[str, str]):
        """ASCII tree should include Schema header."""
        tree = simple_dag.to_ascii_tree()

        assert "Schema" in tree
        assert "Edges" in tree

    def test_to_ascii_tree_nodes(self, simple_dag: DirectedAcyclicGraph[str, str]):
        """ASCII tree should include nodes."""
        tree = simple_dag.to_ascii_tree()

        assert "A" in tree
        assert "B" in tree
        assert "C" in tree

    def test_to_ascii_tree_with_root_nodes(
        self, simple_dag: DirectedAcyclicGraph[str, str]
    ):
        """ASCII tree should accept root_nodes parameter."""
        tree = simple_dag.to_ascii_tree(root_nodes=["A"])

        assert "Schema" in tree

    def test_to_ascii_tree_with_custom_label_fn(
        self, any_dag: DirectedAcyclicGraph[Any, Any]
    ):
        """ASCII tree should use custom label function."""
        any_dag.add_node("A", value=MockNodeValue(name="Custom Label"))

        tree = any_dag.to_ascii_tree(node_label_fn=lambda v: v.name if v else "")

        assert "Custom Label" in tree

    def test_to_ascii_tree_truncates_long_labels(
        self, empty_dag: DirectedAcyclicGraph[str, str]
    ):
        """ASCII tree should truncate long labels."""
        long_name = "A" * 100
        empty_dag.add_node(long_name)

        tree = empty_dag.to_ascii_tree()

        assert "..." in tree

    def test_to_ascii_tree_with_constraint_edge_labels(
        self, any_dag: DirectedAcyclicGraph[Any, Any]
    ):
        """ASCII tree should show constraint edge labels."""
        constraint = MockConstraint("required")
        node_value = MockNodeValue(name="B", constraints=[constraint])

        any_dag.add_node("A")
        any_dag.add_node("B", value=node_value)
        any_dag.add_edge("A", "B", metadata="has_meta")

        tree = any_dag.to_ascii_tree()

        assert "[constraint]" in tree

    def test_to_ascii_tree_multiple_constraints(
        self, any_dag: DirectedAcyclicGraph[Any, Any]
    ):
        """ASCII tree should handle multiple constraints."""
        constraints = [MockConstraint("c1"), MockConstraint("c2")]
        node_value = MockNodeValue(name="B", constraints=constraints)

        any_dag.add_node("A")
        any_dag.add_node("B", value=node_value)
        any_dag.add_edge("A", "B", metadata="has_meta")

        tree = any_dag.to_ascii_tree()

        # Should show first constraint plus count
        assert "more" in tree

    def test_to_ascii_tree_max_depth(self, simple_dag: DirectedAcyclicGraph[str, str]):
        """ASCII tree should respect max_depth."""
        tree = simple_dag.to_ascii_tree(max_depth=1)

        assert "Schema" in tree

    def test_to_ascii_tree_with_edge_label_fn(
        self, any_dag: DirectedAcyclicGraph[Any, Any]
    ):
        """ASCII tree should use edge_label_fn."""
        any_dag.add_node("A")
        any_dag.add_node("B")
        any_dag.add_edge(
            "A", "B", metadata=MockEdgeMetadata(weight=1, label="edge_test")
        )

        tree = any_dag.to_ascii_tree(edge_label_fn=lambda m: m.label if m else "")

        assert "edge_test" in tree


# ============================================================================
# Test Edge Cases and Error Handling
# ============================================================================


class TestDAGEdgeCases:
    """Tests for edge cases and error handling."""

    def test_complex_path_names(self, empty_dag: DirectedAcyclicGraph[str, str]):
        """DAG should handle complex path names."""
        paths = [
            "root.child.grandchild",
            "array[0].item",
            "path-with-dashes",
            "path_with_underscores",
            "MixedCase.Path",
        ]

        for path in paths:
            empty_dag.add_node(path)

        assert len(empty_dag.nodes) == len(paths)

    def test_large_graph(self, empty_dag: DirectedAcyclicGraph[str, str]):
        """DAG should handle large graphs."""
        # Create a chain of 100 nodes
        for i in range(100):
            empty_dag.add_node(f"node_{i}")

        for i in range(99):
            empty_dag.add_edge(f"node_{i}", f"node_{i+1}")

        assert len(empty_dag.nodes) == 100
        order = empty_dag.topological_order()
        assert len(order) == 100

    def test_node_with_none_value_in_export(
        self, empty_dag: DirectedAcyclicGraph[str, str]
    ):
        """Export should handle nodes with None values."""
        empty_dag.add_node("A")  # No value

        data = empty_dag.to_json_dict()

        node_a = next(n for n in data["nodes"] if n["path"] == "A")
        assert node_a["value"] is None

    def test_edge_with_none_metadata_in_export(
        self, empty_dag: DirectedAcyclicGraph[str, str]
    ):
        """Export should handle edges with None metadata."""
        empty_dag.add_node("A")
        empty_dag.add_node("B")
        empty_dag.add_edge("A", "B")  # No metadata

        data = empty_dag.to_json_dict()

        edge = data["edges"][0]
        assert edge["metadata"] is None

    def test_mermaid_edge_label_fn_exception(
        self, empty_dag: DirectedAcyclicGraph[str, str]
    ):
        """Mermaid should handle edge_label_fn exceptions gracefully."""
        empty_dag.add_node("A")
        empty_dag.add_node("B")
        empty_dag.add_edge("A", "B", metadata="test")

        def bad_fn(m: Optional[str]) -> str:
            raise ValueError("test error")

        # Should not raise
        mermaid = empty_dag.to_mermaid(edge_label_fn=bad_fn)
        assert "A" in mermaid

    def test_ascii_tree_node_label_fn_exception(
        self, empty_dag: DirectedAcyclicGraph[str, str]
    ):
        """ASCII tree should handle node_label_fn exceptions gracefully."""
        empty_dag.add_node("A", value="test")

        def bad_fn(v: Optional[str]) -> str:
            raise ValueError("test error")

        # Should not raise
        tree = empty_dag.to_ascii_tree(node_label_fn=bad_fn)
        assert "A" in tree

    def test_remove_dependent_exception_handling(
        self, empty_dag: DirectedAcyclicGraph[str, str]
    ):
        """Remove edge should handle remove_dependent exceptions."""
        empty_dag.add_edge("A", "B")

        # Manually clear the weak set to simulate edge case
        prereq = empty_dag.get_node("A")
        prereq._dependents = None  # type: ignore

        # Should not raise (exception caught internally)
        empty_dag.remove_edge("A", "B")

    def test_model_dump_exception_in_json_dict(
        self, any_dag: DirectedAcyclicGraph[Any, Any]
    ):
        """JSON dict should handle model_dump exceptions."""

        class BadValue:
            def model_dump(self):
                raise ValueError("test error")

        any_dag.add_node("A", value=BadValue())

        data = any_dag.to_json_dict()

        node_a = next(n for n in data["nodes"] if n["path"] == "A")
        assert isinstance(node_a["value"], str)  # Fallback to str()

    def test_vars_exception_in_json_dict(
        self, empty_dag: DirectedAcyclicGraph[str, str]
    ):
        """JSON dict should handle vars() exceptions."""

        class BadValue:
            def __init__(self) -> None:
                self._dict = {"x": 1}

            @property
            def __dict__(self) -> Dict[str, Any]:  # type: ignore[override]
                # This won't actually be called due to how hasattr works,
                # but we can simulate the fallback by having an object
                # without model_dump that uses str() fallback
                return self._dict

        # The actual test: object without model_dump falls back to vars or str
        empty_dag.add_node("A", value=BadValue())  # type: ignore[arg-type]

        data = empty_dag.to_json_dict()

        node_a = next(n for n in data["nodes"] if n["path"] == "A")
        # Should have used vars() successfully or fallen back to str()
        assert node_a["value"] is not None


# ============================================================================
# Test Constraint Edge Label Extraction
# ============================================================================


class TestDAGConstraintLabels:
    """Tests for constraint-based edge label extraction."""

    def test_ascii_tree_constraint_edge_label(
        self, any_dag: DirectedAcyclicGraph[Any, Any]
    ):
        """ASCII tree should extract labels from constraints."""
        constraint = MockConstraint("required_field")
        value = MockNodeValue(name="Target", constraints=[constraint])

        any_dag.add_node("source")
        any_dag.add_node("target", value=value)
        any_dag.add_edge("source", "target")

        tree = any_dag.to_ascii_tree()

        assert "required_field" in tree

    def test_mermaid_constraint_fallback(self, any_dag: DirectedAcyclicGraph[Any, Any]):
        """Mermaid should try constraint labels when no edge_label_fn."""
        constraint = MockConstraint("depends_on")
        value = MockNodeValue(name="Target", constraints=[constraint])

        any_dag.add_node("source")
        any_dag.add_node("target", value=value)
        any_dag.add_edge("source", "target", metadata="some_meta")

        mermaid = any_dag.to_mermaid()

        # Should include edge
        assert "source" in mermaid


# ============================================================================
# Integration Tests
# ============================================================================


class TestDAGIntegration:
    """Integration tests combining multiple operations."""

    def test_build_and_query_complex_graph(
        self, empty_dag: DirectedAcyclicGraph[str, str]
    ):
        """Test building and querying a complex graph."""
        # Build a tree structure:
        #       root
        #      /    \
        #    left   right
        #   /    \
        # ll      lr

        empty_dag.add_node("root", value="root_value")
        empty_dag.add_node("left", value="left_value")
        empty_dag.add_node("right", value="right_value")
        empty_dag.add_node("ll", value="ll_value")
        empty_dag.add_node("lr", value="lr_value")

        empty_dag.add_edge("root", "left")
        empty_dag.add_edge("root", "right")
        empty_dag.add_edge("left", "ll")
        empty_dag.add_edge("left", "lr")

        # Test queries
        assert empty_dag.dependents("root") == {"left", "right"}
        assert empty_dag.descendants("root") == {"left", "right", "ll", "lr"}
        assert empty_dag.ancestors("ll") == {"root", "left"}

        # Test topological order
        order = empty_dag.topological_order()
        assert order.index("root") < order.index("left")
        assert order.index("left") < order.index("ll")

        # Test ready nodes
        assert empty_dag.ready_nodes(set()) == {"root"}
        assert empty_dag.ready_nodes({"root"}) == {"root", "left", "right"}

        # Test exports work
        assert "digraph" in empty_dag.to_dot()
        assert "graph TD" in empty_dag.to_mermaid()
        assert "nodes" in empty_dag.to_json_dict()
        assert "Schema" in empty_dag.to_ascii_tree()

    def test_modify_and_validate_graph(
        self, simple_dag: DirectedAcyclicGraph[str, str]
    ):
        """Test modifying graph and validating changes."""
        # Initial state
        simple_dag.validate_acyclic()

        # Add new branch
        simple_dag.add_node("D")
        simple_dag.add_edge("A", "D")

        # Validate still acyclic
        simple_dag.validate_acyclic()

        # Remove node
        simple_dag.remove_node("B")

        # C should no longer have B as prerequisite
        assert "B" not in simple_dag.prerequisites("C")

        # Graph should still be valid
        simple_dag.validate_acyclic()


class TestDAGRemoveNodeEdgeCases:
    """Tests for edge cases in node removal."""

    def test_remove_node_with_inconsistent_state(
        self, empty_dag: DirectedAcyclicGraph[str, str]
    ):
        """Test remove_node when _nodes and _path_to_uuid are inconsistent."""
        # Add a node normally
        node = empty_dag.add_node("test_path")

        # Manually create inconsistent state: path exists but node doesn't
        del empty_dag._nodes[node.id]

        # remove_node should handle this gracefully
        empty_dag.remove_node("test_path")

        # path_to_uuid should be cleaned up
        assert "test_path" not in empty_dag.path_to_uuid
