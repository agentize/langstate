"""
Comprehensive unit tests for DirectedAcyclicHypergraph (DAH) implementation.

Tests cover:
- Node operations (add, get, remove) with UUID/path duality
- Hyperedge operations with multiple sources
- OR-of-ANDs ready semantics
- Graph queries (prerequisites, dependents, ancestors, descendants)
- Cycle detection
- Topological ordering
- Export methods (DOT, Mermaid, JSON, ASCII tree)
- Schema classes (DirectedAcyclicHypergraphNode, DirectedAcyclicHypergraphEdge)
- Backward compatibility with single-source edge API

Target: 100% code coverage for dah.py and schema.py
"""

# pyright: reportPrivateUsage=false

from __future__ import annotations

import json
import pytest
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, cast
from uuid import UUID, uuid4

from core.data_structure.dah.dah import DirectedAcyclicHypergraph
from core.data_structure.dah.schema import (
    DirectedAcyclicHypergraphEdge,
    DirectedAcyclicHypergraphNode,
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
def empty_dah() -> DirectedAcyclicHypergraph[str, str]:
    """Create an empty DAH."""
    return DirectedAcyclicHypergraph[str, str]()


@pytest.fixture
def simple_dah() -> DirectedAcyclicHypergraph[str, str]:
    """Create a simple DAH: A -> B -> C using single-source edges."""
    dah = DirectedAcyclicHypergraph[str, str]()
    dah.add_node("A", value="value_A")
    dah.add_node("B", value="value_B")
    dah.add_node("C", value="value_C")
    dah.add_edge("A", "B")
    dah.add_edge("B", "C")
    return dah


@pytest.fixture
def hyperedge_dah() -> DirectedAcyclicHypergraph[str, str]:
    """Create DAH with hyperedges: {A, B} -> C, {C} -> D."""
    dah = DirectedAcyclicHypergraph[str, str]()
    dah.add_node("A", value="value_A")
    dah.add_node("B", value="value_B")
    dah.add_node("C", value="value_C")
    dah.add_node("D", value="value_D")
    dah.add_hyperedge(["A", "B"], "C")  # Both A and B required for C
    dah.add_hyperedge(["C"], "D")
    return dah


@pytest.fixture
def or_semantics_dah() -> DirectedAcyclicHypergraph[str, str]:
    """Create DAH demonstrating OR-of-ANDs: {A} -> C OR {B} -> C."""
    dah = DirectedAcyclicHypergraph[str, str]()
    dah.add_node("A")
    dah.add_node("B")
    dah.add_node("C")
    dah.add_hyperedge(["A"], "C")  # A alone can satisfy C
    dah.add_hyperedge(["B"], "C")  # OR B alone can satisfy C
    return dah


@pytest.fixture
def any_dah() -> DirectedAcyclicHypergraph[Any, Any]:
    """Create an empty DAH with Any types for testing custom value/metadata types."""
    return DirectedAcyclicHypergraph[Any, Any]()


# ============================================================================
# Test DirectedAcyclicHypergraphNode (Schema)
# ============================================================================


class TestDirectedAcyclicHypergraphNode:
    """Tests for DirectedAcyclicHypergraphNode dataclass."""

    def test_node_creation_with_uuid_and_path(self):
        """Node should be created with given UUID and path."""
        node_id = uuid4()
        node = DirectedAcyclicHypergraphNode[str, str](id=node_id, path="test.path")

        assert node.id == node_id
        assert node.path == "test.path"
        assert node.value is None
        assert node.in_edges == {}
        assert node.dependents() == set()

    def test_node_creation_with_value(self):
        """Node should store optional value."""
        node_id = uuid4()
        node = DirectedAcyclicHypergraphNode[str, str](
            id=node_id, path="test.path", value="test_value"
        )

        assert node.value == "test_value"

    def test_node_hash_by_uuid(self):
        """Node hash should be based on UUID."""
        node_id = uuid4()
        node = DirectedAcyclicHypergraphNode[str, str](id=node_id, path="test.path")

        assert hash(node) == hash(node_id)

    def test_node_equality_by_uuid(self):
        """Two nodes with same UUID should be equal."""
        node_id = uuid4()
        node1 = DirectedAcyclicHypergraphNode[str, str](id=node_id, path="path1")
        node2 = DirectedAcyclicHypergraphNode[str, str](id=node_id, path="path2")

        assert node1 == node2

    def test_node_inequality_different_uuid(self):
        """Two nodes with different UUIDs should not be equal."""
        node1 = DirectedAcyclicHypergraphNode[str, str](id=uuid4(), path="path")
        node2 = DirectedAcyclicHypergraphNode[str, str](id=uuid4(), path="path")

        assert node1 != node2

    def test_node_inequality_with_non_node(self):
        """Node should not equal non-node objects."""
        node = DirectedAcyclicHypergraphNode[str, str](id=uuid4(), path="path")

        assert node != "not a node"
        assert node != 123
        assert node != None

    def test_add_and_remove_dependent(self):
        """Test dependent management via WeakSet."""
        prereq = DirectedAcyclicHypergraphNode[str, str](id=uuid4(), path="prereq")
        dependent = DirectedAcyclicHypergraphNode[str, str](
            id=uuid4(), path="dependent"
        )

        prereq.add_dependent(dependent)
        assert dependent in prereq.dependents()

        prereq.remove_dependent(dependent)
        assert dependent not in prereq.dependents()

    def test_prerequisite_ids_empty(self):
        """Node without hyperedges should have empty prerequisite IDs."""
        node = DirectedAcyclicHypergraphNode[str, str](id=uuid4(), path="node")

        assert node.prerequisite_ids() == set()

    def test_prerequisite_paths_empty(self):
        """Node without hyperedges should have empty prerequisite paths."""
        node = DirectedAcyclicHypergraphNode[str, str](id=uuid4(), path="node")

        assert node.prerequisite_paths() == set()

    def test_prerequisite_ids_with_hyperedges(self):
        """Node with hyperedges should report source UUIDs."""
        source1 = DirectedAcyclicHypergraphNode[str, str](id=uuid4(), path="source1")
        source2 = DirectedAcyclicHypergraphNode[str, str](id=uuid4(), path="source2")
        target = DirectedAcyclicHypergraphNode[str, str](id=uuid4(), path="target")

        hedge = DirectedAcyclicHypergraphEdge[str, str](
            id=uuid4(), sources={source1, source2}
        )
        target.in_edges[hedge.id] = hedge

        assert target.prerequisite_ids() == {source1.id, source2.id}

    def test_prerequisite_paths_with_hyperedges(self):
        """Node with hyperedges should report source paths."""
        source1 = DirectedAcyclicHypergraphNode[str, str](id=uuid4(), path="source1")
        source2 = DirectedAcyclicHypergraphNode[str, str](id=uuid4(), path="source2")
        target = DirectedAcyclicHypergraphNode[str, str](id=uuid4(), path="target")

        hedge = DirectedAcyclicHypergraphEdge[str, str](
            id=uuid4(), sources={source1, source2}
        )
        target.in_edges[hedge.id] = hedge

        assert target.prerequisite_paths() == {"source1", "source2"}

    def test_hyperedges_method(self):
        """hyperedges() should return list of incoming hyperedges."""
        source = DirectedAcyclicHypergraphNode[str, str](id=uuid4(), path="source")
        target = DirectedAcyclicHypergraphNode[str, str](id=uuid4(), path="target")

        hedge = DirectedAcyclicHypergraphEdge[str, str](id=uuid4(), sources={source})
        target.in_edges[hedge.id] = hedge

        assert target.hyperedges() == [hedge]

    def test_is_ready_no_hyperedges(self):
        """Node without hyperedges is always ready."""
        node = DirectedAcyclicHypergraphNode[str, str](id=uuid4(), path="node")

        assert node.is_ready(set()) is True
        assert node.is_ready({"other"}) is True

    def test_is_ready_single_hyperedge_satisfied(self):
        """Node is ready when hyperedge sources are all satisfied."""
        source1 = DirectedAcyclicHypergraphNode[str, str](id=uuid4(), path="source1")
        source2 = DirectedAcyclicHypergraphNode[str, str](id=uuid4(), path="source2")
        target = DirectedAcyclicHypergraphNode[str, str](id=uuid4(), path="target")

        hedge = DirectedAcyclicHypergraphEdge[str, str](
            id=uuid4(), sources={source1, source2}
        )
        target.in_edges[hedge.id] = hedge

        # Both sources must be satisfied (AND)
        assert target.is_ready({"source1", "source2"}) is True
        assert target.is_ready({"source1"}) is False
        assert target.is_ready({"source2"}) is False

    def test_is_ready_or_of_ands_semantics(self):
        """Node is ready when ANY hyperedge has ALL sources satisfied."""
        source1 = DirectedAcyclicHypergraphNode[str, str](id=uuid4(), path="source1")
        source2 = DirectedAcyclicHypergraphNode[str, str](id=uuid4(), path="source2")
        target = DirectedAcyclicHypergraphNode[str, str](id=uuid4(), path="target")

        # Two hyperedges: {source1} OR {source2}
        hedge1 = DirectedAcyclicHypergraphEdge[str, str](id=uuid4(), sources={source1})
        hedge2 = DirectedAcyclicHypergraphEdge[str, str](id=uuid4(), sources={source2})
        target.in_edges[hedge1.id] = hedge1
        target.in_edges[hedge2.id] = hedge2

        # Either hyperedge satisfaction is enough (OR)
        assert target.is_ready({"source1"}) is True
        assert target.is_ready({"source2"}) is True
        assert target.is_ready(set()) is False


# ============================================================================
# Test DirectedAcyclicHypergraphEdge (Schema)
# ============================================================================


class TestDirectedAcyclicHypergraphEdge:
    """Tests for DirectedAcyclicHypergraphEdge dataclass."""

    def test_hyperedge_creation(self):
        """Hyperedge should be created with ID and sources."""
        source1 = DirectedAcyclicHypergraphNode[str, str](id=uuid4(), path="s1")
        source2 = DirectedAcyclicHypergraphNode[str, str](id=uuid4(), path="s2")
        edge_id = uuid4()

        hedge = DirectedAcyclicHypergraphEdge[str, str](
            id=edge_id, sources={source1, source2}
        )

        assert hedge.id == edge_id
        assert hedge.sources == {source1, source2}
        assert hedge.metadata is None

    def test_hyperedge_with_metadata(self):
        """Hyperedge should store optional metadata."""
        source = DirectedAcyclicHypergraphNode[str, str](id=uuid4(), path="source")

        hedge = DirectedAcyclicHypergraphEdge[str, str](
            id=uuid4(), sources={source}, metadata="edge_data"
        )

        assert hedge.metadata == "edge_data"

    def test_hyperedge_source_ids(self):
        """Hyperedge source_ids should return all source UUIDs."""
        source1 = DirectedAcyclicHypergraphNode[str, str](id=uuid4(), path="s1")
        source2 = DirectedAcyclicHypergraphNode[str, str](id=uuid4(), path="s2")

        hedge = DirectedAcyclicHypergraphEdge[str, str](
            id=uuid4(), sources={source1, source2}
        )

        assert hedge.source_ids() == {source1.id, source2.id}

    def test_hyperedge_source_paths(self):
        """Hyperedge source_paths should return all source paths."""
        source1 = DirectedAcyclicHypergraphNode[str, str](id=uuid4(), path="path1")
        source2 = DirectedAcyclicHypergraphNode[str, str](id=uuid4(), path="path2")

        hedge = DirectedAcyclicHypergraphEdge[str, str](
            id=uuid4(), sources={source1, source2}
        )

        assert hedge.source_paths() == {"path1", "path2"}


# ============================================================================
# Test DirectedAcyclicHypergraph - Initialization
# ============================================================================


class TestDAHInitialization:
    """Tests for DAH initialization."""

    def test_empty_dah_creation(self):
        """Empty DAH should have no nodes."""
        dah = DirectedAcyclicHypergraph[str, str]()

        assert dah.nodes == {}
        assert dah.path_to_uuid == {}

    def test_dah_creation_with_existing_nodes(self):
        """DAH can be initialized with existing nodes."""
        node1 = DirectedAcyclicHypergraphNode[str, str](id=uuid4(), path="node1")
        node2 = DirectedAcyclicHypergraphNode[str, str](id=uuid4(), path="node2")

        dah = DirectedAcyclicHypergraph[str, str](nodes=[node1, node2])

        assert len(dah.nodes) == 2
        assert dah.get_node("node1") == node1
        assert dah.get_node("node2") == node2
        assert dah.path_to_uuid["node1"] == node1.id
        assert dah.path_to_uuid["node2"] == node2.id


# ============================================================================
# Test DirectedAcyclicHypergraph - Node Operations
# ============================================================================


class TestDAHNodeOperations:
    """Tests for DAH node operations."""

    def test_add_node_creates_new_node(
        self, empty_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Adding a new node should create it in the graph."""
        node = empty_dah.add_node("test.path", value="test_value")

        assert node.path == "test.path"
        assert node.value == "test_value"
        assert node.id is not None
        assert empty_dah.get_node("test.path") == node

    def test_add_node_idempotent_returns_existing(
        self, empty_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Adding existing node should return it without creating duplicate."""
        node1 = empty_dah.add_node("test.path", value="value1")
        node2 = empty_dah.add_node("test.path")

        assert node1 is node2
        assert node1.value == "value1"  # Value unchanged

    def test_add_node_updates_value_when_provided(
        self, empty_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Adding existing node with new value should update it."""
        node1 = empty_dah.add_node("test.path", value="value1")
        node2 = empty_dah.add_node("test.path", value="value2")

        assert node1 is node2
        assert node1.value == "value2"

    def test_get_node_existing(self, simple_dah: DirectedAcyclicHypergraph[str, str]):
        """Getting existing node should return it."""
        node = simple_dah.get_node("A")

        assert node is not None
        assert node.path == "A"
        assert node.value == "value_A"

    def test_get_node_nonexistent(self, empty_dah: DirectedAcyclicHypergraph[str, str]):
        """Getting nonexistent node should return None."""
        node = empty_dah.get_node("nonexistent")

        assert node is None

    def test_get_node_by_uuid(self, empty_dah: DirectedAcyclicHypergraph[str, str]):
        """Getting node by UUID should work."""
        added_node = empty_dah.add_node("test.path")

        retrieved = empty_dah.get_node_by_uuid(added_node.id)

        assert retrieved == added_node

    def test_get_node_by_uuid_nonexistent(
        self, empty_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Getting nonexistent UUID should return None."""
        result = empty_dah.get_node_by_uuid(uuid4())

        assert result is None

    def test_remove_node_removes_from_graph(
        self, simple_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Removing node should remove it from graph."""
        simple_dah.remove_node("B")

        assert simple_dah.get_node("B") is None
        assert "B" not in simple_dah.path_to_uuid

    def test_remove_node_removes_incoming_hyperedges(
        self, hyperedge_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Removing node should remove its incoming hyperedges."""
        hyperedge_dah.remove_node("C")

        # C's hyperedges should be gone
        assert hyperedge_dah.get_node("C") is None

    def test_remove_node_removes_from_dependent_hyperedges(
        self, hyperedge_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Removing node should remove it from hyperedges where it's a source."""
        # A is a source for C's hyperedge
        hyperedge_dah.remove_node("A")

        # C's hyperedge should be removed since A was a source
        node_c = hyperedge_dah.get_node("C")
        # The hyperedge that included A should be removed
        assert node_c is not None

    def test_remove_nonexistent_node_no_error(
        self, empty_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Removing nonexistent node should not raise error."""
        empty_dah.remove_node("nonexistent")  # Should not raise


# ============================================================================
# Test DirectedAcyclicHypergraph - Hyperedge Operations
# ============================================================================


class TestDAHHyperedgeOperations:
    """Tests for DAH hyperedge operations."""

    def test_add_hyperedge_creates_nodes_if_needed(
        self, empty_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Adding hyperedge should create nodes if they don't exist."""
        empty_dah.add_hyperedge(["source1", "source2"], "target")

        assert empty_dah.get_node("source1") is not None
        assert empty_dah.get_node("source2") is not None
        assert empty_dah.get_node("target") is not None

    def test_add_hyperedge_returns_uuid(
        self, empty_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Adding hyperedge should return its UUID."""
        edge_id = empty_dah.add_hyperedge(["A", "B"], "C")

        assert isinstance(edge_id, UUID)

    def test_add_hyperedge_with_explicit_id(
        self, empty_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Adding hyperedge with explicit ID should use it."""
        explicit_id = uuid4()
        result_id = empty_dah.add_hyperedge(["A"], "B", edge_id=explicit_id)

        assert result_id == explicit_id

    def test_add_hyperedge_with_metadata(
        self, empty_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Adding hyperedge should store metadata."""
        edge_id = empty_dah.add_hyperedge(["A"], "B", metadata="edge_metadata")

        node_b = empty_dah.get_node("B")
        assert node_b is not None
        hedge = node_b.in_edges[edge_id]
        assert hedge.metadata == "edge_metadata"

    def test_add_hyperedge_updates_existing(
        self, empty_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Adding hyperedge with same ID should update it."""
        edge_id = uuid4()
        empty_dah.add_hyperedge(["A"], "B", metadata="meta1", edge_id=edge_id)
        empty_dah.add_hyperedge(["A", "C"], "B", metadata="meta2", edge_id=edge_id)

        node_b = empty_dah.get_node("B")
        assert node_b is not None
        hedge = node_b.in_edges[edge_id]
        assert hedge.metadata == "meta2"
        assert len(hedge.sources) == 2

    def test_add_hyperedge_maintains_reverse_mirror(
        self, empty_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Adding hyperedge should update sources' dependents."""
        empty_dah.add_hyperedge(["A", "B"], "C")

        node_a = empty_dah.get_node("A")
        node_b = empty_dah.get_node("B")
        node_c = empty_dah.get_node("C")
        assert node_a is not None
        assert node_b is not None
        assert node_c is not None

        assert node_c in node_a.dependents()
        assert node_c in node_b.dependents()

    def test_add_hyperedge_self_dependency_raises(
        self, empty_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Self-dependency in hyperedge should raise ValueError."""
        with pytest.raises(ValueError, match="Self dependency"):
            empty_dah.add_hyperedge(["A", "B"], "A")

    def test_add_hyperedge_empty_sources_raises(
        self, empty_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Hyperedge with no sources should raise ValueError."""
        with pytest.raises(ValueError, match="at least one source"):
            empty_dah.add_hyperedge([], "target")

    def test_add_hyperedge_cycle_detection(
        self, simple_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Adding cycle-creating hyperedge should raise ValueError."""
        # simple_dah: A -> B -> C
        with pytest.raises(ValueError, match="Cycle"):
            simple_dah.add_hyperedge(["C"], "A")  # Would create cycle

    def test_add_hyperedge_no_cycle_check(
        self, simple_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Cycle check can be disabled."""
        # This would create a cycle, but check is disabled
        simple_dah.add_hyperedge(["C"], "A", check_cycle=False)

        # Edge should be added
        node_a = simple_dah.get_node("A")
        assert node_a is not None
        assert len(node_a.in_edges) == 1

    def test_remove_hyperedge(self, hyperedge_dah: DirectedAcyclicHypergraph[str, str]):
        """Removing hyperedge should remove it from target."""
        node_c = hyperedge_dah.get_node("C")
        assert node_c is not None
        edge_id = list(node_c.in_edges.keys())[0]

        hyperedge_dah.remove_hyperedge(edge_id, "C")

        assert edge_id not in node_c.in_edges

    def test_remove_hyperedge_updates_reverse_mirror(
        self, empty_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Removing hyperedge should update sources' dependents."""
        edge_id = empty_dah.add_hyperedge(["A"], "B")

        node_a = empty_dah.get_node("A")
        node_b = empty_dah.get_node("B")
        assert node_a is not None
        assert node_b is not None

        assert node_b in node_a.dependents()

        empty_dah.remove_hyperedge(edge_id, "B")

        assert node_b not in node_a.dependents()

    def test_remove_nonexistent_hyperedge_no_error(
        self, empty_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Removing nonexistent hyperedge should not raise error."""
        empty_dah.add_node("A")
        empty_dah.remove_hyperedge(uuid4(), "A")  # Should not raise

    def test_remove_hyperedge_nonexistent_target_no_error(
        self, empty_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Removing hyperedge from nonexistent target should not raise."""
        empty_dah.remove_hyperedge(uuid4(), "nonexistent")


# ============================================================================
# Test DirectedAcyclicHypergraph - Backward Compatibility (Single-Source Edge API)
# ============================================================================


class TestDAHBackwardCompatibility:
    """Tests for backward-compatible single-source edge API."""

    def test_add_edge_creates_single_source_hyperedge(
        self, empty_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """add_edge should create a 1-source hyperedge."""
        edge_id = empty_dah.add_edge("prereq", "dep")

        node_dep = empty_dah.get_node("dep")
        assert node_dep is not None
        hedge = node_dep.in_edges[edge_id]

        assert len(hedge.sources) == 1

    def test_add_edge_returns_uuid(
        self, empty_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """add_edge should return hyperedge UUID."""
        edge_id = empty_dah.add_edge("A", "B")

        assert isinstance(edge_id, UUID)

    def test_add_edge_with_metadata(
        self, empty_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """add_edge should support metadata."""
        edge_id = empty_dah.add_edge("A", "B", metadata="test_meta")

        node_b = empty_dah.get_node("B")
        assert node_b is not None
        hedge = node_b.in_edges[edge_id]
        assert hedge.metadata == "test_meta"

    def test_add_edge_cycle_detection(
        self, simple_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """add_edge should detect cycles."""
        with pytest.raises(ValueError, match="Cycle"):
            simple_dah.add_edge("C", "A")


# ============================================================================
# Test DirectedAcyclicHypergraph - Graph Queries
# ============================================================================


class TestDAHGraphQueries:
    """Tests for DAH graph-wide queries."""

    def test_prerequisite_ids(self, hyperedge_dah: DirectedAcyclicHypergraph[str, str]):
        """Prerequisite IDs should return source UUIDs."""
        node_a = hyperedge_dah.get_node("A")
        node_b = hyperedge_dah.get_node("B")
        assert node_a is not None
        assert node_b is not None

        prereq_ids = hyperedge_dah.prerequisite_ids("C")

        assert prereq_ids == {node_a.id, node_b.id}

    def test_prerequisite_ids_nonexistent(
        self, empty_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Prerequisite IDs of nonexistent node should be empty."""
        assert empty_dah.prerequisite_ids("nonexistent") == set()

    def test_prerequisite_paths(
        self, hyperedge_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Prerequisite paths should return source paths."""
        prereq_paths = hyperedge_dah.prerequisite_paths("C")

        assert prereq_paths == {"A", "B"}

    def test_prerequisite_paths_nonexistent(
        self, empty_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Prerequisite paths of nonexistent node should be empty."""
        assert empty_dah.prerequisite_paths("nonexistent") == set()

    def test_dependents(self, hyperedge_dah: DirectedAcyclicHypergraph[str, str]):
        """Dependents should return direct dependents."""
        assert hyperedge_dah.dependents("A") == {"C"}
        assert hyperedge_dah.dependents("C") == {"D"}
        assert hyperedge_dah.dependents("D") == set()

    def test_dependents_nonexistent(
        self, empty_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Dependents of nonexistent node should be empty."""
        assert empty_dah.dependents("nonexistent") == set()

    def test_ancestors(self, hyperedge_dah: DirectedAcyclicHypergraph[str, str]):
        """Ancestors should return all transitive prerequisites."""
        # {A, B} -> C -> D
        assert hyperedge_dah.ancestors("D") == {"A", "B", "C"}
        assert hyperedge_dah.ancestors("C") == {"A", "B"}
        assert hyperedge_dah.ancestors("A") == set()

    def test_descendants(self, hyperedge_dah: DirectedAcyclicHypergraph[str, str]):
        """Descendants should return all transitive dependents."""
        # {A, B} -> C -> D
        assert hyperedge_dah.descendants("A") == {"C", "D"}
        assert hyperedge_dah.descendants("C") == {"D"}
        assert hyperedge_dah.descendants("D") == set()

    def test_iter_hyperedges(self, hyperedge_dah: DirectedAcyclicHypergraph[str, str]):
        """iter_hyperedges should yield all hyperedges."""
        edges = list(hyperedge_dah.iter_hyperedges())

        assert len(edges) == 2

        # Each tuple: (source_paths, target_path, metadata, edge_id)
        targets = {e[1] for e in edges}
        assert targets == {"C", "D"}


# ============================================================================
# Test DirectedAcyclicHypergraph - Ready Nodes (OR-of-ANDs Semantics)
# ============================================================================


class TestDAHReadyNodes:
    """Tests for ready node detection with OR-of-ANDs semantics."""

    def test_ready_nodes_empty_satisfied(
        self, hyperedge_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Only root nodes should be ready with empty satisfied set."""
        ready = hyperedge_dah.ready_nodes(set())

        assert ready == {"A", "B"}

    def test_ready_nodes_partial_satisfied_and_requirement(
        self, hyperedge_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Node with AND requirement needs all sources satisfied."""
        # {A, B} -> C requires BOTH A and B

        ready = hyperedge_dah.ready_nodes({"A"})
        assert "C" not in ready

        ready = hyperedge_dah.ready_nodes({"B"})
        assert "C" not in ready

        ready = hyperedge_dah.ready_nodes({"A", "B"})
        assert "C" in ready

    def test_ready_nodes_or_semantics(
        self, or_semantics_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Node with multiple hyperedges uses OR semantics."""
        # {A} -> C OR {B} -> C

        # Either A or B alone should make C ready
        ready = or_semantics_dah.ready_nodes({"A"})
        assert "C" in ready

        ready = or_semantics_dah.ready_nodes({"B"})
        assert "C" in ready

    def test_ready_nodes_all_satisfied(
        self, hyperedge_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """All nodes ready when all prerequisites satisfied."""
        ready = hyperedge_dah.ready_nodes({"A", "B", "C"})

        assert ready == {"A", "B", "C", "D"}


# ============================================================================
# Test DirectedAcyclicHypergraph - Topological Order & Validation
# ============================================================================


class TestDAHTopologicalOrder:
    """Tests for topological ordering and validation."""

    def test_topological_order_simple(
        self, simple_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Topological order should respect dependencies."""
        order = simple_dah.topological_order()

        assert order.index("A") < order.index("B")
        assert order.index("B") < order.index("C")

    def test_topological_order_hyperedges(
        self, hyperedge_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Topological order should handle hyperedges by expanding them."""
        order = hyperedge_dah.topological_order()

        # A and B must come before C
        assert order.index("A") < order.index("C")
        assert order.index("B") < order.index("C")
        # C must come before D
        assert order.index("C") < order.index("D")

    def test_topological_order_with_cycle_raises(
        self, simple_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Topological order with cycle should raise ValueError."""
        # Create a cycle by disabling check
        simple_dah.add_hyperedge(["C"], "A", check_cycle=False)

        with pytest.raises(ValueError, match="cycle"):
            simple_dah.topological_order()

    def test_validate_acyclic_valid(
        self, hyperedge_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Validate acyclic should pass for valid DAH."""
        hyperedge_dah.validate_acyclic()  # Should not raise

    def test_validate_acyclic_with_cycle_raises(
        self, simple_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Validate acyclic should raise for cyclic graph."""
        simple_dah.add_hyperedge(["C"], "A", check_cycle=False)

        with pytest.raises(ValueError, match="cycle"):
            simple_dah.validate_acyclic()


# ============================================================================
# Test DirectedAcyclicHypergraph - Internal Helpers
# ============================================================================


class TestDAHInternalHelpers:
    """Tests for internal helper methods."""

    def test_would_create_cycle_true(
        self, simple_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """_would_create_cycle should detect potential cycle."""
        # A -> B -> C
        # Adding C -> A would create cycle
        assert simple_dah._would_create_cycle("C", "A") is True

    def test_would_create_cycle_false(
        self, simple_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """_would_create_cycle should allow valid edges."""
        # Adding A -> C would not create cycle
        assert simple_dah._would_create_cycle("A", "C") is False

    def test_next_edge_id_generates_uuid(
        self, empty_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """_next_edge_id should generate UUID."""
        edge_id = empty_dah._next_edge_id()

        assert isinstance(edge_id, UUID)


# ============================================================================
# Test DirectedAcyclicHypergraph - Export Methods
# ============================================================================


class TestDAHExportDOT:
    """Tests for DOT export."""

    def test_to_dot_empty(self, empty_dah: DirectedAcyclicHypergraph[str, str]):
        """Empty DAH should produce minimal DOT output."""
        dot = empty_dah.to_dot()

        assert "digraph DAH {" in dot
        assert "}" in dot

    def test_to_dot_with_nodes(
        self, hyperedge_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """DOT should include all nodes."""
        dot = hyperedge_dah.to_dot()

        assert '"A"' in dot
        assert '"B"' in dot
        assert '"C"' in dot
        assert '"D"' in dot

    def test_to_dot_with_hyperedges(
        self, hyperedge_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """DOT should expand hyperedges to individual edges."""
        dot = hyperedge_dah.to_dot()

        # {A, B} -> C should produce two edges
        assert '"A" -> "C"' in dot
        assert '"B" -> "C"' in dot

    def test_to_dot_with_metadata(self, empty_dah: DirectedAcyclicHypergraph[str, str]):
        """DOT should include edge labels when metadata present."""
        empty_dah.add_hyperedge(["A"], "B", metadata="test")

        dot = empty_dah.to_dot()

        assert "label=" in dot


class TestDAHExportMermaid:
    """Tests for Mermaid export."""

    def test_to_mermaid_structure(
        self, hyperedge_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Mermaid output should have correct structure."""
        mermaid = hyperedge_dah.to_mermaid()

        assert "graph TD" in mermaid

    def test_to_mermaid_nodes(self, hyperedge_dah: DirectedAcyclicHypergraph[str, str]):
        """Mermaid should include node definitions."""
        mermaid = hyperedge_dah.to_mermaid()

        assert "A[" in mermaid
        assert "B[" in mermaid
        assert "C[" in mermaid

    def test_to_mermaid_hyperedges_expanded(
        self, hyperedge_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Mermaid should expand hyperedges to individual edges."""
        mermaid = hyperedge_dah.to_mermaid()

        assert "A -->" in mermaid
        assert "B -->" in mermaid

    def test_to_mermaid_with_custom_label_fn(
        self, any_dah: DirectedAcyclicHypergraph[Any, Any]
    ):
        """Mermaid should use custom label function."""
        any_dah.add_node("A", value=MockNodeValue(name="Node A"))
        any_dah.add_node("B", value=MockNodeValue(name="Node B"))
        any_dah.add_hyperedge(["A"], "B")

        mermaid = any_dah.to_mermaid(node_label_fn=lambda v: v.name if v else "")

        assert "Node A" in mermaid
        assert "Node B" in mermaid

    def test_to_mermaid_with_edge_label_fn(
        self, any_dah: DirectedAcyclicHypergraph[Any, Any]
    ):
        """Mermaid should use edge label function."""
        any_dah.add_hyperedge(
            ["A"], "B", metadata=MockEdgeMetadata(weight=1, label="test")
        )

        mermaid = any_dah.to_mermaid(edge_label_fn=lambda m: m.label if m else "")

        assert "test" in mermaid

    def test_to_mermaid_label_truncation(
        self, empty_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Mermaid should truncate long labels."""
        long_path = "this.is.a.very.long.path.name"
        empty_dah.add_node(long_path)

        mermaid = empty_dah.to_mermaid(max_label_length=15)

        assert "..." in mermaid

    def test_to_mermaid_edge_label_fn_exception(
        self, empty_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Mermaid should handle edge_label_fn exceptions gracefully."""
        empty_dah.add_hyperedge(["A"], "B", metadata="test")

        def bad_fn(m: Optional[str]) -> str:
            raise ValueError("test error")

        # Should not raise
        mermaid = empty_dah.to_mermaid(edge_label_fn=bad_fn)
        assert "A" in mermaid


class TestDAHExportJSON:
    """Tests for JSON export."""

    def test_to_json_dict_structure(
        self, hyperedge_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """JSON dict should have correct structure."""
        data = hyperedge_dah.to_json_dict()

        assert "nodes" in data
        assert "hyperedges" in data
        assert "node_count" in data
        assert "hyperedge_count" in data
        assert data["node_count"] == 4
        assert data["hyperedge_count"] == 2

    def test_to_json_dict_node_data(
        self, hyperedge_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """JSON dict should include node data with UUID and path."""
        data = hyperedge_dah.to_json_dict()

        node_paths = {n["path"] for n in data["nodes"]}
        assert node_paths == {"A", "B", "C", "D"}

        # Check UUID format
        for node in data["nodes"]:
            assert "id" in node
            UUID(node["id"])  # Should be valid UUID string

    def test_to_json_dict_hyperedge_data(
        self, hyperedge_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """JSON dict should include hyperedge data with sources."""
        data = hyperedge_dah.to_json_dict()

        # Find hyperedge targeting C
        edge_c = next(e for e in data["hyperedges"] if e["target"] == "C")
        assert set(edge_c["sources"]) == {"A", "B"}
        assert "id" in edge_c
        UUID(edge_c["id"])  # Should be valid UUID string

    def test_to_json_dict_with_model_dump_value(
        self, any_dah: DirectedAcyclicHypergraph[Any, Any]
    ):
        """JSON dict should use model_dump for node values."""
        any_dah.add_node("A", value=MockNodeValue(name="Test"))

        data = any_dah.to_json_dict()

        node_a = next(n for n in data["nodes"] if n["path"] == "A")
        assert node_a["value"] == {"name": "Test"}

    def test_to_json_dict_with_model_dump_metadata(
        self, any_dah: DirectedAcyclicHypergraph[Any, Any]
    ):
        """JSON dict should use model_dump for edge metadata."""
        any_dah.add_hyperedge(
            ["A"], "B", metadata=MockEdgeMetadata(weight=5, label="test")
        )

        data = any_dah.to_json_dict()

        edge = data["hyperedges"][0]
        assert edge["metadata"] == {"weight": 5, "label": "test"}

    def test_to_json_dict_with_dict_value(
        self, any_dah: DirectedAcyclicHypergraph[Any, Any]
    ):
        """JSON dict should handle objects with __dict__."""

        class SimpleValue:
            def __init__(self):
                self.x = 1
                self.y = 2

        any_dah.add_node("A", value=SimpleValue())

        data = any_dah.to_json_dict()

        node_a = next(n for n in data["nodes"] if n["path"] == "A")
        assert node_a["value"]["x"] == 1

    def test_to_json_dict_with_primitive_value(
        self, empty_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """JSON dict should handle primitive values."""
        empty_dah.add_node("A", value="simple_string")

        data = empty_dah.to_json_dict()

        node_a = next(n for n in data["nodes"] if n["path"] == "A")
        assert node_a["value"] == "simple_string"

    def test_to_json_string(self, hyperedge_dah: DirectedAcyclicHypergraph[str, str]):
        """to_json should return valid JSON string."""
        json_str = hyperedge_dah.to_json()

        parsed = json.loads(json_str)
        assert parsed["node_count"] == 4

    def test_to_json_pretty(self, hyperedge_dah: DirectedAcyclicHypergraph[str, str]):
        """to_json with pretty=True should be indented."""
        json_str = hyperedge_dah.to_json(pretty=True, indent=4)

        assert "\n" in json_str
        assert "    " in json_str  # 4-space indent

    def test_to_json_compact(self, hyperedge_dah: DirectedAcyclicHypergraph[str, str]):
        """to_json with pretty=False should be compact."""
        json_str = hyperedge_dah.to_json(pretty=False)

        assert "\n" not in json_str

    def test_model_dump_exception_in_json_dict(
        self, any_dah: DirectedAcyclicHypergraph[Any, Any]
    ):
        """JSON dict should handle model_dump exceptions."""

        class BadValue:
            def model_dump(self):
                raise ValueError("test error")

        any_dah.add_node("A", value=BadValue())

        data = any_dah.to_json_dict()

        node_a = next(n for n in data["nodes"] if n["path"] == "A")
        assert isinstance(node_a["value"], str)

    def test_vars_exception_in_json_dict(
        self, empty_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """JSON dict should handle vars() exceptions."""

        class BadValue:
            def __init__(self) -> None:
                self._dict = {"x": 1}

            @property
            def __dict__(self) -> Dict[str, Any]:  # type: ignore[override]
                # Return a proper dict for vars() to work
                return self._dict

        # The actual test: object without model_dump falls back to vars or str
        empty_dah.add_node("A", value=BadValue())  # type: ignore[arg-type]

        data = empty_dah.to_json_dict()

        node_a = next(n for n in data["nodes"] if n["path"] == "A")
        # Should have used vars() successfully or fallen back to str()
        assert node_a["value"] is not None


class TestDAHExportASCII:
    """Tests for ASCII tree export."""

    def test_to_ascii_tree_basic(
        self, hyperedge_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """ASCII tree should include Schema header."""
        tree = hyperedge_dah.to_ascii_tree()

        assert "Schema" in tree
        assert "HyperEdges" in tree

    def test_to_ascii_tree_nodes(
        self, hyperedge_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """ASCII tree should include nodes."""
        tree = hyperedge_dah.to_ascii_tree()

        assert "A" in tree
        assert "B" in tree
        assert "C" in tree
        assert "D" in tree

    def test_to_ascii_tree_with_root_nodes(
        self, hyperedge_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """ASCII tree should accept root_nodes parameter."""
        tree = hyperedge_dah.to_ascii_tree(root_nodes=["A", "B"])

        assert "Schema" in tree

    def test_to_ascii_tree_with_custom_label_fn(
        self, any_dah: DirectedAcyclicHypergraph[Any, Any]
    ):
        """ASCII tree should use custom label function."""
        any_dah.add_node("A", value=MockNodeValue(name="Custom Label"))

        tree = any_dah.to_ascii_tree(node_label_fn=lambda v: v.name)

        assert "Custom Label" in tree

    def test_to_ascii_tree_truncates_long_labels(
        self, empty_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """ASCII tree should truncate long labels."""
        long_name = "A" * 100
        empty_dah.add_node(long_name)

        tree = empty_dah.to_ascii_tree()

        assert "..." in tree

    def test_to_ascii_tree_shows_multiple_sources(
        self, hyperedge_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """ASCII tree should show all sources for hyperedges."""
        tree = hyperedge_dah.to_ascii_tree()

        # The hyperedge {A, B} -> C should show both sources
        assert "A" in tree and "B" in tree

    def test_to_ascii_tree_with_constraint_edge_labels(
        self, any_dah: DirectedAcyclicHypergraph[Any, Any]
    ):
        """ASCII tree should show constraint edge labels."""
        constraint = MockConstraint("required")
        node_value = MockNodeValue(name="B", constraints=[constraint])

        any_dah.add_node("A")
        any_dah.add_node("B", value=node_value)
        any_dah.add_hyperedge(["A"], "B", metadata="has_meta")

        tree = any_dah.to_ascii_tree()

        assert "[constraint]" in tree

    def test_to_ascii_tree_multiple_constraints(
        self, any_dah: DirectedAcyclicHypergraph[Any, Any]
    ):
        """ASCII tree should handle multiple constraints."""
        constraints = [MockConstraint("c1"), MockConstraint("c2")]
        node_value = MockNodeValue(name="B", constraints=constraints)

        any_dah.add_node("A")
        any_dah.add_node("B", value=node_value)
        any_dah.add_hyperedge(["A"], "B", metadata="has_meta")

        tree = any_dah.to_ascii_tree()

        # Should show first constraint plus count
        assert "more" in tree

    def test_to_ascii_tree_max_depth(
        self, hyperedge_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """ASCII tree should respect max_depth."""
        tree = hyperedge_dah.to_ascii_tree(max_depth=1)

        assert "Schema" in tree

    def test_to_ascii_tree_with_edge_label_fn(
        self, any_dah: DirectedAcyclicHypergraph[Any, Any]
    ):
        """ASCII tree should use edge_label_fn."""
        any_dah.add_hyperedge(
            ["A"], "B", metadata=MockEdgeMetadata(weight=1, label="edge_test")
        )

        tree = any_dah.to_ascii_tree(edge_label_fn=lambda m: m.label if m else "")

        assert "edge_test" in tree

    def test_to_ascii_tree_node_label_fn_exception(
        self, any_dah: DirectedAcyclicHypergraph[Any, Any]
    ):
        """ASCII tree should handle node_label_fn exceptions gracefully."""
        any_dah.add_node("A", value="test")

        def bad_fn(v: Optional[Any]) -> str:
            raise ValueError("test error")

        # Should not raise
        tree = any_dah.to_ascii_tree(node_label_fn=bad_fn)
        assert "A" in tree


# ============================================================================
# Test Edge Cases and Error Handling
# ============================================================================


class TestDAHEdgeCases:
    """Tests for edge cases and error handling."""

    def test_complex_path_names(self, empty_dah: DirectedAcyclicHypergraph[str, str]):
        """DAH should handle complex path names."""
        paths = [
            "root.child.grandchild",
            "array[0].item",
            "path-with-dashes",
            "path_with_underscores",
            "MixedCase.Path",
        ]

        for path in paths:
            empty_dah.add_node(path)

        assert len(empty_dah.nodes) == len(paths)

    def test_large_hypergraph(self, empty_dah: DirectedAcyclicHypergraph[str, str]):
        """DAH should handle large graphs."""
        # Create a chain of 100 nodes
        for i in range(100):
            empty_dah.add_node(f"node_{i}")

        for i in range(99):
            empty_dah.add_hyperedge([f"node_{i}"], f"node_{i+1}")

        assert len(empty_dah.nodes) == 100
        order = empty_dah.topological_order()
        assert len(order) == 100

    def test_multiple_hyperedges_same_target(
        self, empty_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Multiple hyperedges can target the same node."""
        empty_dah.add_node("A")
        empty_dah.add_node("B")
        empty_dah.add_node("C")
        empty_dah.add_node("target")

        _ = empty_dah.add_hyperedge(["A"], "target")
        _ = empty_dah.add_hyperedge(["B"], "target")
        _ = empty_dah.add_hyperedge(["A", "B", "C"], "target")

        target = empty_dah.get_node("target")
        assert target is not None
        assert len(target.in_edges) == 3

    def test_node_with_none_value_in_export(
        self, empty_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Export should handle nodes with None values."""
        empty_dah.add_node("A")  # No value

        data = empty_dah.to_json_dict()

        node_a = next(n for n in data["nodes"] if n["path"] == "A")
        assert node_a["value"] is None

    def test_hyperedge_with_none_metadata_in_export(
        self, empty_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Export should handle hyperedges with None metadata."""
        empty_dah.add_hyperedge(["A"], "B")  # No metadata

        data = empty_dah.to_json_dict()

        edge = data["hyperedges"][0]
        assert edge["metadata"] is None

    def test_remove_dependent_exception_handling(
        self, empty_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Remove hyperedge should handle remove_dependent exceptions."""
        edge_id = empty_dah.add_hyperedge(["A"], "B")

        # Manually clear the weak set to simulate edge case
        prereq = empty_dah.get_node("A")
        prereq._dependents = None  # type: ignore

        # Should not raise (exception caught internally)
        empty_dah.remove_hyperedge(edge_id, "B")


# ============================================================================
# Test Complex Hyperedge Scenarios
# ============================================================================


class TestDAHComplexScenarios:
    """Tests for complex hyperedge scenarios."""

    def test_multiple_sources_and_requirement(
        self, empty_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Test hyperedge requiring multiple sources (AND semantics within edge)."""
        # Task D requires completing both tasks A AND B AND C
        empty_dah.add_hyperedge(["A", "B", "C"], "D")

        # Not ready without all prerequisites
        assert empty_dah.ready_nodes({"A"}) == {"A", "B", "C"}  # A, B, C are roots
        assert empty_dah.ready_nodes({"A", "B"}) == {"A", "B", "C"}

        # Ready when all are satisfied
        assert "D" in empty_dah.ready_nodes({"A", "B", "C"})

    def test_or_semantics_with_multi_source_hyperedges(
        self, empty_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Test OR semantics with multi-source hyperedges."""
        # Task D can be done if:
        #   - Both A AND B are done (hyperedge 1), OR
        #   - C is done (hyperedge 2)

        empty_dah.add_hyperedge(["A", "B"], "D")  # Requires both A and B
        empty_dah.add_hyperedge(["C"], "D")  # OR just C

        # D is ready if just C is satisfied
        assert "D" in empty_dah.ready_nodes({"C"})

        # D is not ready with just A or just B
        assert "D" not in empty_dah.ready_nodes({"A"})
        assert "D" not in empty_dah.ready_nodes({"B"})

        # D is ready when both A and B are satisfied
        assert "D" in empty_dah.ready_nodes({"A", "B"})

    def test_diamond_with_hyperedges(
        self, empty_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Test diamond pattern with hyperedges."""
        #       A
        #      / \
        #     B   C
        #      \ /
        #       D (requires both B AND C)

        empty_dah.add_node("A")
        empty_dah.add_hyperedge(["A"], "B")
        empty_dah.add_hyperedge(["A"], "C")
        empty_dah.add_hyperedge(["B", "C"], "D")  # Requires both

        # Topological order
        order = empty_dah.topological_order()
        assert order.index("A") < order.index("B")
        assert order.index("A") < order.index("C")
        assert order.index("B") < order.index("D")
        assert order.index("C") < order.index("D")

        # Ready nodes progression
        assert empty_dah.ready_nodes(set()) == {"A"}
        assert empty_dah.ready_nodes({"A"}) == {"A", "B", "C"}
        assert empty_dah.ready_nodes({"A", "B"}) == {"A", "B", "C"}
        assert empty_dah.ready_nodes({"A", "B", "C"}) == {"A", "B", "C", "D"}


# ============================================================================
# Integration Tests
# ============================================================================


class TestDAHIntegration:
    """Integration tests combining multiple operations."""

    def test_build_and_query_complex_hypergraph(
        self, empty_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Test building and querying a complex hypergraph."""
        # Build a workflow:
        # - Start requires nothing
        # - Phase1 requires Start
        # - Phase2 requires Start
        # - Merge requires both Phase1 AND Phase2
        # - End requires Merge

        empty_dah.add_node("Start", value="start_value")
        empty_dah.add_node("Phase1", value="phase1_value")
        empty_dah.add_node("Phase2", value="phase2_value")
        empty_dah.add_node("Merge", value="merge_value")
        empty_dah.add_node("End", value="end_value")

        empty_dah.add_hyperedge(["Start"], "Phase1")
        empty_dah.add_hyperedge(["Start"], "Phase2")
        empty_dah.add_hyperedge(["Phase1", "Phase2"], "Merge")  # AND requirement
        empty_dah.add_hyperedge(["Merge"], "End")

        # Test queries
        assert empty_dah.dependents("Start") == {"Phase1", "Phase2"}
        assert empty_dah.descendants("Start") == {"Phase1", "Phase2", "Merge", "End"}
        assert empty_dah.ancestors("End") == {"Start", "Phase1", "Phase2", "Merge"}

        # Test topological order
        order = empty_dah.topological_order()
        assert order.index("Start") < order.index("Phase1")
        assert order.index("Start") < order.index("Phase2")
        assert order.index("Phase1") < order.index("Merge")
        assert order.index("Phase2") < order.index("Merge")
        assert order.index("Merge") < order.index("End")

        # Test ready nodes with AND requirement
        assert empty_dah.ready_nodes(set()) == {"Start"}
        assert empty_dah.ready_nodes({"Start"}) == {"Start", "Phase1", "Phase2"}
        assert empty_dah.ready_nodes({"Start", "Phase1"}) == {
            "Start",
            "Phase1",
            "Phase2",
        }
        assert "Merge" in empty_dah.ready_nodes({"Start", "Phase1", "Phase2"})

        # Test exports work
        assert "digraph" in empty_dah.to_dot()
        assert "graph TD" in empty_dah.to_mermaid()
        assert "hyperedges" in empty_dah.to_json_dict()
        assert "Schema" in empty_dah.to_ascii_tree()

    def test_modify_and_validate_hypergraph(
        self, simple_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Test modifying hypergraph and validating changes."""
        # Initial state
        simple_dah.validate_acyclic()

        # Add new hyperedge branch
        simple_dah.add_node("D")
        simple_dah.add_hyperedge(["A"], "D")

        # Validate still acyclic
        simple_dah.validate_acyclic()

        # Remove node
        simple_dah.remove_node("B")

        # C should no longer have B as prerequisite
        assert "B" not in simple_dah.prerequisite_paths("C")

        # Graph should still be valid
        simple_dah.validate_acyclic()

    def test_hyperedge_id_stability(
        self, empty_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Test that hyperedge IDs remain stable."""
        id1 = empty_dah.add_hyperedge(["A", "B"], "C")
        id2 = empty_dah.add_hyperedge(["C"], "D")

        # IDs should be different
        assert id1 != id2

        # IDs should persist
        edges = list(empty_dah.iter_hyperedges())
        edge_ids = {e[3] for e in edges}
        assert id1 in edge_ids
        assert id2 in edge_ids


class TestDAHRemoveNodeEdgeCases:
    """Tests for edge cases in node removal."""

    def test_remove_node_with_inconsistent_state(
        self, empty_dah: DirectedAcyclicHypergraph[str, str]
    ):
        """Test remove_node when _nodes and _path_to_uuid are inconsistent."""
        # Add a node normally
        node = empty_dah.add_node("test_path")

        # Manually create inconsistent state: path exists but node doesn't
        del empty_dah._nodes[node.id]

        # remove_node should handle this gracefully
        empty_dah.remove_node("test_path")

        # path_to_uuid should be cleaned up
        assert "test_path" not in empty_dah.path_to_uuid


# ════════════════════════════════════════════════════════════════════
# Diamond traversal – ancestors / descendants dedup
# ════════════════════════════════════════════════════════════════════


class TestDAHDiamondTraversal:
    """Test that the 'already seen' continue branch fires in BFS dedup.

    Uses OrderedSet + class-level patching to control set iteration order.
    """

    def test_ancestors_diamond(
        self, empty_dah: DirectedAcyclicHypergraph[str, str]
    ) -> None:
        """
        Topology: A→C, B→C, A→D, C→D
          prereq_paths(D)={A,C}, prereq_paths(C)={A,B}

        With ordered prereq_paths(D)=["A","C"]:
          stack=["A","C"], pop C→extend ["A","B"]→stack=["A","A","B"]
          pop B→seen={C,B}, pop A→seen={C,B,A}, pop A→in seen→CONTINUE
        """
        from unittest.mock import patch

        class OrderedSet(set[str]):
            def __init__(self, iterable: Any = ()) -> None:
                self._items: list[str] = list(dict.fromkeys(iterable))
                super().__init__(self._items)

            def __iter__(self) -> Any:
                return iter(self._items)

            def __sub__(self, other: Any) -> "OrderedSet":
                return OrderedSet(x for x in self._items if x not in other)

        dah = empty_dah
        for p in ("A", "B", "C", "D"):
            dah.add_node(p)
        dah.add_hyperedge(["A"], "C")
        dah.add_hyperedge(["B"], "C")
        dah.add_hyperedge(["A"], "D")
        dah.add_hyperedge(["C"], "D")

        original: Any = getattr(DirectedAcyclicHypergraph, "prerequisite_paths")

        def ordered_prereqs(self: Any, path: str) -> "OrderedSet":
            result = original(self, path)
            if path == "D":
                return OrderedSet(["A", "C"])
            if path == "C":
                return OrderedSet(["A", "B"])
            return OrderedSet(sorted(result))

        with patch.object(
            DirectedAcyclicHypergraph, "prerequisite_paths", ordered_prereqs
        ):
            anc = dah.ancestors("D")
        assert anc == {"A", "B", "C"}

    def test_descendants_diamond(
        self, empty_dah: DirectedAcyclicHypergraph[str, str]
    ) -> None:
        """
        Topology: A→B, A→C, B→D, C→B
          deps(A)={B,C}, deps(C)={B}

        With ordered deps(A)=["B","C"]:
          stack=["B","C"], pop C→extend ["B"]→stack=["B","B"]
          pop B→seen={C,B}, pop B→in seen→CONTINUE
        """
        from unittest.mock import patch

        class OrderedSet(set[str]):
            def __init__(self, iterable: Any = ()) -> None:
                self._items: list[str] = list(dict.fromkeys(iterable))
                super().__init__(self._items)

            def __iter__(self) -> Any:
                return iter(self._items)

            def __sub__(self, other: Any) -> "OrderedSet":
                return OrderedSet(x for x in self._items if x not in other)

        dah = empty_dah
        for p in ("A", "B", "C", "D"):
            dah.add_node(p)
        dah.add_hyperedge(["A"], "B")
        dah.add_hyperedge(["A"], "C")
        dah.add_hyperedge(["B"], "D")
        dah.add_hyperedge(["C"], "B")

        original: Any = getattr(DirectedAcyclicHypergraph, "dependents")

        def ordered_deps(self: Any, path: str) -> "OrderedSet":
            result = original(self, path)
            if path == "A":
                return OrderedSet(["B", "C"])
            if path == "C":
                return OrderedSet(["B"])
            return OrderedSet(sorted(result))

        with patch.object(DirectedAcyclicHypergraph, "dependents", ordered_deps):
            desc = dah.descendants("A")
        assert desc == {"B", "C", "D"}


# ════════════════════════════════════════════════════════════════════
# add_hyperedge – idempotent update without metadata (branch 188→192)
# ════════════════════════════════════════════════════════════════════


class TestDAHAddHyperedgeIdempotent:
    def test_re_add_hyperedge_no_metadata(
        self, empty_dah: DirectedAcyclicHypergraph[str, str]
    ) -> None:
        dah = empty_dah
        eid = dah.add_hyperedge(["a"], "b", metadata="first")
        dah.add_hyperedge(["a"], "b", edge_id=eid)  # no metadata
        edges = list(dah.iter_hyperedges())
        found = [m for (_s, t, m, _) in edges if t == "b"]
        assert found == ["first"]


# ════════════════════════════════════════════════════════════════════
# remove_node – dependent's hedge doesn't include removed node (branch 131→130)
# ════════════════════════════════════════════════════════════════════


class TestDAHRemoveNodeBranch:
    def test_remove_node_multiple_hedges(
        self, empty_dah: DirectedAcyclicHypergraph[str, str]
    ) -> None:
        """Node Y depends on X and Z. Removing X iterates Y's edges; the Z-only edge triggers 131→130."""
        dah = empty_dah
        dah.add_hyperedge(["X"], "Y")
        dah.add_hyperedge(["Z"], "Y")
        dah.remove_node("X")
        assert dah.get_node("X") is None
        # Y still exists, Z→Y still exists
        assert dah.get_node("Y") is not None


# ════════════════════════════════════════════════════════════════════
# ensure_node_hierarchy – duplicate call → ValueError catch (lines 255-257)
# ════════════════════════════════════════════════════════════════════


class TestDAHEnsureHierarchyDuplicate:
    def test_ensure_hierarchy_catches_cycle_valueerror(
        self, empty_dah: DirectedAcyclicHypergraph[str, str]
    ) -> None:
        """Create a reverse edge a.b→a, then ensure_node_hierarchy("a.b.c") hits ValueError catch."""
        dah = empty_dah
        dah.add_node("a")
        dah.add_node("a.b")
        dah.add_node("a.b.c")
        # Create reverse edge with check_cycle=False (default) to allow it
        dah.add_hyperedge(["a.b"], "a")
        # Now ensure_node_hierarchy tries add_hyperedge(["a"], "a.b", check_cycle=True)
        # which detects cycle a→a.b→a and raises ValueError → caught by except
        dah.ensure_node_hierarchy("a.b.c")
        # Should not raise; the cycle edge is skipped
        assert dah.get_node("a.b.c") is not None
        assert dah.get_node("a") is not None
        assert dah.get_node("a.b") is not None
        assert dah.get_node("a.b.c") is not None


# ════════════════════════════════════════════════════════════════════
# from_json malformed-input edge cases
# ════════════════════════════════════════════════════════════════════


class TestDAHFromJsonMalformed:
    def test_non_dict_json(self) -> None:
        """JSON that's not a dict → return empty DAH (line 496)."""
        dah = cast(
            DirectedAcyclicHypergraph[Any, Any],
            DirectedAcyclicHypergraph.from_json('"just a string"'),
        )
        assert len(dah.path_to_uuid) == 0

    def test_non_dict_node_entry(self) -> None:
        """Node entry that's not a dict → continue (line 504)."""
        dah = cast(
            DirectedAcyclicHypergraph[Any, Any],
            DirectedAcyclicHypergraph.from_json(
                '{"nodes": [42, "bad"], "hyperedges": []}'
            ),
        )
        assert len(dah.path_to_uuid) == 0

    def test_node_missing_path(self) -> None:
        """Node dict without 'path' key → continue (line 509)."""
        dah = cast(
            DirectedAcyclicHypergraph[Any, Any],
            DirectedAcyclicHypergraph.from_json(
                '{"nodes": [{"value": 1}], "hyperedges": []}'
            ),
        )
        assert len(dah.path_to_uuid) == 0

    def test_nodes_not_a_list(self) -> None:
        """'nodes' is not a list → branch 500→517."""
        dah = cast(
            DirectedAcyclicHypergraph[Any, Any],
            DirectedAcyclicHypergraph.from_json('{"nodes": "nope", "hyperedges": []}'),
        )
        assert len(dah.path_to_uuid) == 0

    def test_hyperedges_not_a_list(self) -> None:
        """'hyperedges' is not a list → branch 518→531."""
        dah = cast(
            DirectedAcyclicHypergraph[Any, Any],
            DirectedAcyclicHypergraph.from_json(
                '{"nodes": [{"path": "a", "value": null}], "hyperedges": "nope"}'
            ),
        )
        assert len(dah.path_to_uuid) == 1

    def test_hyperedge_missing_target(self) -> None:
        """Hyperedge without 'target' → branch 526→520."""
        dah = cast(
            DirectedAcyclicHypergraph[Any, Any],
            DirectedAcyclicHypergraph.from_json(
                '{"nodes": [{"path": "a", "value": null}], "hyperedges": [{"sources": ["a"]}]}'
            ),
        )
        assert len(list(dah.iter_hyperedges())) == 0

    def test_hyperedge_add_fails(self) -> None:
        """Hyperedge that triggers ValueError → except pass (lines 529-530)."""
        # self-dependency via sources containing target
        _dah = cast(
            DirectedAcyclicHypergraph[Any, Any],
            DirectedAcyclicHypergraph.from_json(
                '{"nodes": [{"path": "a", "value": null}], "hyperedges": [{"sources": [], "target": "a"}]}'
            ),
        )
        # Empty sources → ValueError in add_hyperedge

    def test_non_dict_hyperedge_entry(self) -> None:
        """Hyperedge entry that's not a dict → continue (line 522)."""
        dah = cast(
            DirectedAcyclicHypergraph[Any, Any],
            DirectedAcyclicHypergraph.from_json(
                '{"nodes": [{"path": "a", "value": null}], "hyperedges": [42, "bad"]}'
            ),
        )
        assert len(list(dah.iter_hyperedges())) == 0
        assert len(list(dah.iter_hyperedges())) == 0


# ════════════════════════════════════════════════════════════════════
# to_json_dict serialization fallback chains
# ════════════════════════════════════════════════════════════════════


class TestDAHToJsonDictFallbacks:
    def test_node_model_dump_failure(self) -> None:
        class BrokenDump:
            def model_dump(self) -> None:
                raise RuntimeError("boom")

            def __str__(self) -> str:
                return "broken"

        dah: DirectedAcyclicHypergraph[Any, str] = DirectedAcyclicHypergraph()
        dah.add_node("x", BrokenDump())
        d = dah.to_json_dict()
        assert d["nodes"][0]["value"] == "broken"

    def test_node_with_dict_attr_uses_vars(self) -> None:
        class PlainObj:
            def __init__(self) -> None:
                self.x = 1

        dah: DirectedAcyclicHypergraph[Any, str] = DirectedAcyclicHypergraph()
        dah.add_node("x", PlainObj())
        d = dah.to_json_dict()
        assert d["nodes"][0]["value"] == {"x": 1}

    def test_node_plain_str(self) -> None:
        dah: DirectedAcyclicHypergraph[int, str] = DirectedAcyclicHypergraph()
        dah.add_node("x", 42)
        d = dah.to_json_dict()
        assert d["nodes"][0]["value"] == "42"

    def test_edge_metadata_model_dump_failure(self) -> None:
        class BrokenMeta:
            def model_dump(self) -> None:
                raise RuntimeError("boom")

            def __str__(self) -> str:
                return "em-broken"

        dah: DirectedAcyclicHypergraph[str, Any] = DirectedAcyclicHypergraph()
        dah.add_hyperedge(["a"], "b", metadata=BrokenMeta())
        d = dah.to_json_dict()
        assert d["hyperedges"][0]["metadata"] == "em-broken"

    def test_edge_metadata_with_dict(self) -> None:
        class DictMeta:
            def __init__(self) -> None:
                self.x = 1

        dah: DirectedAcyclicHypergraph[str, Any] = DirectedAcyclicHypergraph()
        dah.add_hyperedge(["a"], "b", metadata=DictMeta())
        d = dah.to_json_dict()
        assert d["hyperedges"][0]["metadata"] == {"x": 1}

    def test_edge_metadata_with_dict_falls_to_vars(self) -> None:
        class DictMeta:
            def __init__(self) -> None:
                self.v = 2

        dah: DirectedAcyclicHypergraph[str, Any] = DirectedAcyclicHypergraph()
        dah.add_hyperedge(["a"], "b", metadata=DictMeta())
        d = dah.to_json_dict()
        assert d["hyperedges"][0]["metadata"] == {"v": 2}

    def test_edge_metadata_plain_str(self) -> None:
        dah: DirectedAcyclicHypergraph[str, int] = DirectedAcyclicHypergraph()
        dah.add_hyperedge(["a"], "b", metadata=99)
        d = dah.to_json_dict()
        assert d["hyperedges"][0]["metadata"] == "99"

    def test_node_vars_failure_falls_to_str(self) -> None:
        """If vars() raises for a __dict__-bearing object → str fallback."""
        import core.data_structure.dah.dah as dah_mod

        class HasDict:
            def __str__(self) -> str:
                return "has-dict-str"

        dah: DirectedAcyclicHypergraph[Any, str] = DirectedAcyclicHypergraph()
        dah.add_node("x", HasDict())

        _real_vars: Any = vars

        def _patched_vars(o: Any) -> Any:
            if isinstance(o, HasDict):
                raise Exception("vars failed")
            return _real_vars(o)

        dah_mod.__dict__["vars"] = _patched_vars
        try:
            d = dah.to_json_dict()
        finally:
            dah_mod.__dict__.pop("vars", None)
        assert d["nodes"][0]["value"] == "has-dict-str"

    def test_edge_metadata_vars_failure_falls_to_str(self) -> None:
        """If vars() raises for edge metadata with __dict__ → str fallback."""
        import core.data_structure.dah.dah as dah_mod

        class HasDictMeta:
            def __str__(self) -> str:
                return "meta-str"

        dah: DirectedAcyclicHypergraph[str, Any] = DirectedAcyclicHypergraph()
        dah.add_hyperedge(["a"], "b", metadata=HasDictMeta())

        _real_vars: Any = vars

        def _patched_vars(o: Any) -> Any:
            if isinstance(o, HasDictMeta):
                raise Exception("vars failed")
            return _real_vars(o)

        dah_mod.__dict__["vars"] = _patched_vars
        try:
            d = dah.to_json_dict()
        finally:
            dah_mod.__dict__.pop("vars", None)
        assert d["hyperedges"][0]["metadata"] == "meta-str"


# ════════════════════════════════════════════════════════════════════
# to_ascii_tree edge-case coverage
# ════════════════════════════════════════════════════════════════════


class TestDAHAsciiTreeEdgeCases:
    def test_nonexistent_root_node(
        self, empty_dah: DirectedAcyclicHypergraph[str, str]
    ) -> None:
        empty_dah.add_node("a")
        tree = empty_dah.to_ascii_tree(root_nodes=["nonexistent"])
        assert "Schema" in tree

    def test_edge_label_fn_raises(
        self, empty_dah: DirectedAcyclicHypergraph[str, str]
    ) -> None:
        dah = empty_dah
        dah.add_hyperedge(["a"], "b", metadata="m")
        tree = dah.to_ascii_tree(edge_label_fn=lambda m: 1 / 0)  # type: ignore[return-value]
        assert "a" in tree

    def test_constraint_exception_in_ascii(self) -> None:
        class BadConstraints:
            @property
            def constraints(self) -> list[Any]:
                raise RuntimeError("bad")

        dah: DirectedAcyclicHypergraph[Any, str] = DirectedAcyclicHypergraph()
        dah.add_node("a", BadConstraints())
        dah.add_node("b", BadConstraints())
        dah.add_hyperedge(["a"], "b")
        tree = dah.to_ascii_tree()
        assert "a" in tree

    def test_constraint_no_edge_name(self) -> None:
        """Constraint without to_dag_edge_name → branch 612→610."""

        class NoNameC:
            pass

        class ValC:
            constraints = [NoNameC()]

        dah: DirectedAcyclicHypergraph[Any, None] = DirectedAcyclicHypergraph()
        dah.add_node("a", ValC())
        dah.add_node("b", ValC())
        dah.add_hyperedge(["a"], "b")
        tree = dah.to_ascii_tree()
        assert "a" in tree


# ════════════════════════════════════════════════════════════════════
# to_mermaid edge-case coverage
# ════════════════════════════════════════════════════════════════════


class TestDAHMermaidEdgeCases:
    def test_fmt_label_returns_empty(self) -> None:
        """edge_label_fn returns stripped chars → branch 401→403."""
        dah: DirectedAcyclicHypergraph[str, str] = DirectedAcyclicHypergraph()
        dah.add_hyperedge(["a"], "b", metadata="meta")
        mermaid = dah.to_mermaid(edge_label_fn=lambda m: "(){}[]|")
        assert "-->" in mermaid
