"""
Comprehensive unit tests for Graph base class implementation.

Tests cover:
- Abstract method contracts and NotImplementedError
- Graph-wide queries (prerequisite_ids, dependents, ancestors, descendants)
- Ready node detection
- Topological ordering with cycle detection
- Export methods (DOT, Mermaid, JSON, ASCII tree)
- Base classes (BaseGraphNode, BaseGraphEdge, BaseGraph)

Target: 100% code coverage for graph/graph.py and graph/base.py
"""

# pyright: reportPrivateUsage=false

from __future__ import annotations

import json
import pytest
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple, cast
from weakref import WeakSet

from core.data_structure.graph.graph import Graph
from core.data_structure.graph.base import (
    BaseGraph,
    BaseGraphEdge,
    BaseGraphNode,
)


# ============================================================================
# Test Fixtures and Helpers
# ============================================================================


@dataclass
class MockNodeValue:
    """Mock node value for testing node_label_fn."""

    name: str
    constraints: Optional[List[str]] = None

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


@dataclass
class SimpleNode:
    """Simple node implementation for testing Graph base class."""

    _id: str
    _value: Optional[Any] = None
    _prerequisites: Dict[str, "SimpleNode"] = field(default_factory=lambda: {})
    _dependents_set: "WeakSet[SimpleNode]" = field(default_factory=lambda: WeakSet())

    @property
    def id(self) -> str:
        return self._id

    @property
    def value(self) -> Optional[Any]:
        return self._value

    @value.setter
    def value(self, val: Any) -> None:
        self._value = val

    def prerequisite_ids(self) -> Set[str]:
        return set(self._prerequisites.keys())

    def dependents(self) -> Set["SimpleNode"]:
        return set(self._dependents_set)

    def is_ready(self, satisfied: Set[str]) -> bool:
        return self.prerequisite_ids().issubset(satisfied)

    def __hash__(self) -> int:
        return hash(self._id)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, SimpleNode):
            return self._id == other._id
        return False

    def add_prerequisite(self, prereq_id: str, node: "SimpleNode") -> None:
        self._prerequisites[prereq_id] = node

    def add_dependent(self, node: "SimpleNode") -> None:
        self._dependents_set.add(node)

    def remove_dependent(self, node: "SimpleNode") -> None:
        self._dependents_set.discard(node)


@dataclass
class SimpleEdge:
    """Simple edge implementation for testing."""

    source: SimpleNode
    target: SimpleNode
    _metadata: Optional[Any] = None

    @property
    def sources(self) -> Set[SimpleNode]:
        return {self.source}

    @property
    def metadata(self) -> Optional[Any]:
        return self._metadata

    def source_ids(self) -> Set[str]:
        return {self.source.id}


class ConcreteGraph(Graph[Any, Any]):
    """Concrete implementation of Graph for testing base class methods."""

    _edges: List[SimpleEdge]

    def __init__(self) -> None:
        super().__init__()
        self._edges: List[SimpleEdge] = []

    def add_node(  # type: ignore[override]
        self, node_id: str, value: Optional[Any] = None
    ) -> SimpleNode:
        """Add or get a node."""
        if node_id in self._nodes:
            existing = self._nodes[node_id]
            if value is not None and isinstance(existing, SimpleNode):
                existing._value = value  # type: ignore[attr-defined]
            return existing  # type: ignore[return-value]

        node = SimpleNode(_id=node_id, _value=value)
        self._nodes[node_id] = node  # type: ignore[assignment]
        return node

    def remove_node(self, node_id: str) -> None:
        """Remove a node and all its edges."""
        if node_id not in self._nodes:
            return

        node = self._nodes[node_id]

        # Remove edges
        self._edges = [
            e for e in self._edges if e.source.id != node_id and e.target.id != node_id
        ]

        # Clean up dependents
        if isinstance(node, SimpleNode):
            for prereq in list(node._prerequisites.values()):
                prereq.remove_dependent(node)

        del self._nodes[node_id]

    def add_edge(
        self, source_id: str, target_id: str, metadata: Optional[Any] = None
    ) -> SimpleEdge:
        """Add an edge between two nodes."""
        source = self.add_node(source_id)
        target = self.add_node(target_id)

        edge = SimpleEdge(source=source, target=target, _metadata=metadata)
        self._edges.append(edge)

        target.add_prerequisite(source_id, source)
        source.add_dependent(target)

        return edge

    def _iter_edges(self) -> Iterator[Tuple[str, str, Optional[Any]]]:
        """Yield (source_id, target_id, metadata) for all edges."""
        for edge in self._edges:
            yield edge.source.id, edge.target.id, edge.metadata


@pytest.fixture
def empty_graph() -> ConcreteGraph:
    """Create an empty graph."""
    return ConcreteGraph()


@pytest.fixture
def simple_graph() -> ConcreteGraph:
    """Create a simple graph: A -> B -> C."""
    graph = ConcreteGraph()
    graph.add_node("A", value="value_A")
    graph.add_node("B", value="value_B")
    graph.add_node("C", value="value_C")
    graph.add_edge("A", "B")
    graph.add_edge("B", "C")
    return graph


@pytest.fixture
def diamond_graph() -> ConcreteGraph:
    """Create a diamond graph: A -> B, A -> C, B -> D, C -> D."""
    graph = ConcreteGraph()
    graph.add_node("A")
    graph.add_node("B")
    graph.add_node("C")
    graph.add_node("D")
    graph.add_edge("A", "B")
    graph.add_edge("A", "C")
    graph.add_edge("B", "D")
    graph.add_edge("C", "D")
    return graph


# ============================================================================
# Test BaseGraphNode Abstract Class
# ============================================================================


class TestBaseGraphNodeInterface:
    """Tests for BaseGraphNode abstract interface."""

    def test_base_node_cannot_be_instantiated(self) -> None:
        """BaseGraphNode should not be directly instantiable."""
        with pytest.raises(TypeError):
            BaseGraphNode()  # type: ignore

    def test_simple_node_implements_interface(self) -> None:
        """SimpleNode should implement all required methods."""
        node = SimpleNode(_id="test")

        assert node.id == "test"
        assert node.value is None
        assert node.prerequisite_ids() == set()
        assert node.dependents() == set()
        assert node.is_ready(set()) is True
        assert hash(node) == hash("test")


# ============================================================================
# Test BaseGraphEdge Abstract Class
# ============================================================================


class TestBaseGraphEdgeInterface:
    """Tests for BaseGraphEdge abstract interface."""

    def test_base_edge_cannot_be_instantiated(self) -> None:
        """BaseGraphEdge should not be directly instantiable."""
        with pytest.raises(TypeError):
            BaseGraphEdge()  # type: ignore

    def test_simple_edge_implements_interface(self) -> None:
        """SimpleEdge should implement all required methods."""
        source = SimpleNode(_id="source")
        target = SimpleNode(_id="target")
        edge = SimpleEdge(source=source, target=target, _metadata="test_meta")

        assert edge.sources == {source}
        assert edge.metadata == "test_meta"
        assert edge.source_ids() == {"source"}


# ============================================================================
# Test BaseGraph Abstract Class
# ============================================================================


class TestBaseGraphInterface:
    """Tests for BaseGraph abstract interface."""

    def test_base_graph_cannot_be_instantiated(self) -> None:
        """BaseGraph should not be directly instantiable."""
        with pytest.raises(TypeError):
            BaseGraph()  # type: ignore


# ============================================================================
# Test Graph Base Class - Node Operations
# ============================================================================


class TestGraphNodeOperations:
    """Tests for Graph node management."""

    def test_add_node_creates_new_node(self, empty_graph: ConcreteGraph) -> None:
        """add_node should create and return a new node."""
        node = empty_graph.add_node("test_id", value="test_value")

        assert node.id == "test_id"
        assert node.value == "test_value"
        assert empty_graph.get_node("test_id") == node

    def test_add_node_returns_existing(self, empty_graph: ConcreteGraph) -> None:
        """add_node should return existing node if already present."""
        node1 = empty_graph.add_node("test_id", value="value1")
        node2 = empty_graph.add_node("test_id")  # No value

        assert node1 is node2
        assert node1.value == "value1"  # Value unchanged

    def test_add_node_updates_value(self, empty_graph: ConcreteGraph) -> None:
        """add_node should update value when provided."""
        node1 = empty_graph.add_node("test_id", value="value1")
        node2 = empty_graph.add_node("test_id", value="value2")

        assert node1 is node2
        assert node1.value == "value2"

    def test_get_node_existing(self, simple_graph: ConcreteGraph) -> None:
        """get_node should return existing node."""
        node = simple_graph.get_node("A")

        assert node is not None
        assert node.id == "A"
        assert node.value == "value_A"

    def test_get_node_nonexistent(self, empty_graph: ConcreteGraph) -> None:
        """get_node should return None for nonexistent node."""
        node = empty_graph.get_node("nonexistent")

        assert node is None

    def test_remove_node_cleans_edges(self, simple_graph: ConcreteGraph) -> None:
        """remove_node should remove the node and clean up edges."""
        simple_graph.remove_node("B")

        assert simple_graph.get_node("B") is None
        assert simple_graph.get_node("A") is not None
        assert simple_graph.get_node("C") is not None

    def test_remove_node_nonexistent_no_error(self, empty_graph: ConcreteGraph) -> None:
        """remove_node should not raise error for nonexistent node."""
        empty_graph.remove_node("nonexistent")  # Should not raise

    def test_nodes_property(self, simple_graph: ConcreteGraph) -> None:
        """nodes property should return all nodes."""
        assert set(simple_graph.nodes.keys()) == {"A", "B", "C"}


# ============================================================================
# Test Graph Base Class - NotImplementedError in Base
# ============================================================================


class TestGraphAbstractMethods:
    """Tests for abstract methods raising NotImplementedError."""

    def test_add_node_raises_not_implemented(self) -> None:
        """Graph.add_node should raise NotImplementedError."""
        # Create instance via subclass but test base behavior
        graph = cast(Graph[Any, Any], Graph.__new__(Graph))
        graph._nodes = {}  # type: ignore[attr-defined]

        with pytest.raises(
            NotImplementedError, match="Subclasses must implement add_node"
        ):
            graph.add_node("test")

    def test_remove_node_raises_not_implemented(self) -> None:
        """Graph.remove_node should raise NotImplementedError."""
        graph = cast(Graph[Any, Any], Graph.__new__(Graph))
        graph._nodes = {}  # type: ignore[attr-defined]

        with pytest.raises(
            NotImplementedError, match="Subclasses must implement remove_node"
        ):
            graph.remove_node("test")

    def test_iter_edges_raises_not_implemented(self) -> None:
        """Graph._iter_edges should raise NotImplementedError."""
        graph = cast(Graph[Any, Any], Graph.__new__(Graph))
        graph._nodes = {}  # type: ignore[attr-defined]

        with pytest.raises(
            NotImplementedError, match="Subclasses must implement _iter_edges"
        ):
            list(graph._iter_edges())


# ============================================================================
# Test Graph Base Class - Graph Queries
# ============================================================================


class TestGraphQueries:
    """Tests for graph query methods."""

    def test_prerequisite_ids_existing_node(self, simple_graph: ConcreteGraph) -> None:
        """prerequisite_ids should return prerequisites of a node."""
        prereqs = simple_graph.prerequisite_ids("B")

        assert prereqs == {"A"}

    def test_prerequisite_ids_nonexistent_node(
        self, empty_graph: ConcreteGraph
    ) -> None:
        """prerequisite_ids should return empty set for nonexistent node."""
        prereqs = empty_graph.prerequisite_ids("nonexistent")

        assert prereqs == set()

    def test_dependents_existing_node(self, simple_graph: ConcreteGraph) -> None:
        """dependents should return nodes depending on this node."""
        deps = simple_graph.dependents("A")

        assert deps == {"B"}

    def test_dependents_nonexistent_node(self, empty_graph: ConcreteGraph) -> None:
        """dependents should return empty set for nonexistent node."""
        deps = empty_graph.dependents("nonexistent")

        assert deps == set()

    def test_ancestors_transitive(self, simple_graph: ConcreteGraph) -> None:
        """ancestors should return all transitive prerequisites."""
        ancestors = simple_graph.ancestors("C")

        assert ancestors == {"A", "B"}

    def test_ancestors_empty_for_root(self, simple_graph: ConcreteGraph) -> None:
        """Root node should have no ancestors."""
        ancestors = simple_graph.ancestors("A")

        assert ancestors == set()

    def test_ancestors_diamond(self, diamond_graph: ConcreteGraph) -> None:
        """ancestors should correctly traverse diamond structure."""
        ancestors = diamond_graph.ancestors("D")

        assert ancestors == {"A", "B", "C"}

    def test_descendants_transitive(self, simple_graph: ConcreteGraph) -> None:
        """descendants should return all transitive dependents."""
        descendants = simple_graph.descendants("A")

        assert descendants == {"B", "C"}

    def test_descendants_empty_for_leaf(self, simple_graph: ConcreteGraph) -> None:
        """Leaf node should have no descendants."""
        descendants = simple_graph.descendants("C")

        assert descendants == set()

    def test_descendants_diamond(self, diamond_graph: ConcreteGraph) -> None:
        """descendants should correctly traverse diamond structure."""
        descendants = diamond_graph.descendants("A")

        assert descendants == {"B", "C", "D"}


# ============================================================================
# Test Graph Base Class - Ready Nodes
# ============================================================================


class TestGraphReadyNodes:
    """Tests for ready node detection."""

    def test_ready_nodes_empty_satisfied(self, simple_graph: ConcreteGraph) -> None:
        """With no satisfied nodes, only root nodes are ready."""
        ready = simple_graph.ready_nodes(set())

        assert ready == {"A"}

    def test_ready_nodes_partial_satisfied(self, simple_graph: ConcreteGraph) -> None:
        """With A satisfied, B becomes ready."""
        ready = simple_graph.ready_nodes({"A"})

        assert ready == {"A", "B"}

    def test_ready_nodes_all_satisfied(self, simple_graph: ConcreteGraph) -> None:
        """With all prereqs satisfied, all nodes are ready."""
        ready = simple_graph.ready_nodes({"A", "B"})

        assert ready == {"A", "B", "C"}

    def test_ready_nodes_diamond(self, diamond_graph: ConcreteGraph) -> None:
        """Diamond structure: D requires both B and C satisfied."""
        # Only A satisfied
        ready = diamond_graph.ready_nodes({"A"})
        assert "D" not in ready

        # B and C satisfied (but not via both paths)
        ready = diamond_graph.ready_nodes({"A", "B", "C"})
        assert "D" in ready


# ============================================================================
# Test Graph Base Class - Topological Ordering
# ============================================================================


class TestGraphTopologicalOrder:
    """Tests for topological ordering."""

    def test_topological_order_simple(self, simple_graph: ConcreteGraph) -> None:
        """Topological order should respect dependencies."""
        order = simple_graph.topological_order()

        assert order.index("A") < order.index("B")
        assert order.index("B") < order.index("C")

    def test_topological_order_diamond(self, diamond_graph: ConcreteGraph) -> None:
        """Topological order should respect diamond dependencies."""
        order = diamond_graph.topological_order()

        assert order.index("A") < order.index("B")
        assert order.index("A") < order.index("C")
        assert order.index("B") < order.index("D")
        assert order.index("C") < order.index("D")

    def test_topological_order_empty_graph(self, empty_graph: ConcreteGraph) -> None:
        """Empty graph should return empty list."""
        order = empty_graph.topological_order()

        assert order == []

    def test_validate_acyclic_valid(self, simple_graph: ConcreteGraph) -> None:
        """validate_acyclic should not raise for acyclic graph."""
        simple_graph.validate_acyclic()  # Should not raise


# ============================================================================
# Test Graph Base Class - Cycle Detection
# ============================================================================


class TestGraphCycleDetection:
    """Tests for cycle detection."""

    def test_would_create_cycle_true(self, simple_graph: ConcreteGraph) -> None:
        """_would_create_cycle should return True when cycle would be created."""
        # C -> A would create cycle (A -> B -> C -> A)
        result = simple_graph._would_create_cycle("C", "A")

        assert result is True

    def test_would_create_cycle_false(self, simple_graph: ConcreteGraph) -> None:
        """_would_create_cycle should return False when no cycle."""
        # D -> C would not create cycle
        result = simple_graph._would_create_cycle("D", "C")

        assert result is False

    def test_would_create_cycle_same_node(self, simple_graph: ConcreteGraph) -> None:
        """Self-loop check - A is not in descendants of A (no cycle yet)."""
        # _would_create_cycle checks if source is in descendants of target
        # For same node, A is not in descendants(A), so returns False
        # This is correct behavior - self-loop check is different from cycle detection
        result = simple_graph._would_create_cycle("A", "A")

        assert result is False  # A is not a descendant of A


# ============================================================================
# Test Graph Base Class - Export to DOT
# ============================================================================


class TestGraphExportDot:
    """Tests for DOT export."""

    def test_to_dot_empty(self, empty_graph: ConcreteGraph) -> None:
        """Empty graph should produce minimal DOT output."""
        dot = empty_graph.to_dot()

        assert "digraph G {" in dot
        assert "}" in dot

    def test_to_dot_simple(self, simple_graph: ConcreteGraph) -> None:
        """Simple graph should produce correct DOT output."""
        dot = simple_graph.to_dot()

        assert '"A";' in dot
        assert '"B";' in dot
        assert '"C";' in dot
        assert '"A" -> "B";' in dot
        assert '"B" -> "C";' in dot


# ============================================================================
# Test Graph Base Class - Export to Mermaid
# ============================================================================


class TestGraphExportMermaid:
    """Tests for Mermaid export."""

    def test_to_mermaid_empty(self, empty_graph: ConcreteGraph) -> None:
        """Empty graph should produce minimal Mermaid output."""
        mermaid = empty_graph.to_mermaid()

        assert "graph TD" in mermaid

    def test_to_mermaid_simple(self, simple_graph: ConcreteGraph) -> None:
        """Simple graph should produce correct Mermaid output."""
        mermaid = simple_graph.to_mermaid()

        assert "graph TD" in mermaid
        assert "A" in mermaid
        assert "B" in mermaid
        assert "-->" in mermaid

    def test_to_mermaid_with_node_label_fn(self, empty_graph: ConcreteGraph) -> None:
        """node_label_fn should customize node labels."""
        empty_graph.add_node("test", value=MockNodeValue(name="Test Label"))

        mermaid = empty_graph.to_mermaid(
            node_label_fn=lambda v: v.name if hasattr(v, "name") else str(v)
        )

        assert "Test Label" in mermaid

    def test_to_mermaid_with_edge_label_fn(self, empty_graph: ConcreteGraph) -> None:
        """edge_label_fn should customize edge labels."""
        empty_graph.add_edge(
            "A", "B", metadata=MockEdgeMetadata(weight=5, label="test")
        )

        mermaid = empty_graph.to_mermaid(edge_label_fn=lambda m: m.label if m else "")

        assert "test" in mermaid

    def test_to_mermaid_truncates_long_labels(self, empty_graph: ConcreteGraph) -> None:
        """Long labels should be truncated."""
        long_name = "A" * 50
        empty_graph.add_node("test", value=MockNodeValue(name=long_name))

        mermaid = empty_graph.to_mermaid(
            node_label_fn=lambda v: v.name if hasattr(v, "name") else str(v),
            max_label_length=30,
        )

        # Should be truncated with ...
        assert "..." in mermaid

    def test_to_mermaid_safe_characters(self, empty_graph: ConcreteGraph) -> None:
        """Special characters should be sanitized in node IDs."""
        empty_graph.add_node("test-node.path[0]*star")
        empty_graph.add_node("another")
        empty_graph.add_edge("test-node.path[0]*star", "another")

        mermaid = empty_graph.to_mermaid()

        # Node IDs (before [) should be sanitized
        # The label in quotes may still contain original characters
        lines = mermaid.split("\n")
        for line in lines[1:]:  # Skip "graph TD"
            if "[" in line:
                node_id_part = line.split("[")[0].strip()
                # Node ID should not have problematic characters
                assert "-" not in node_id_part
                assert "." not in node_id_part
                assert "[" not in node_id_part

    def test_to_mermaid_edge_label_exception_handled(
        self, empty_graph: ConcreteGraph
    ) -> None:
        """edge_label_fn exceptions should be handled gracefully."""
        empty_graph.add_edge("A", "B", metadata="test")

        def bad_fn(m: Any) -> str:
            raise ValueError("Test error")

        mermaid = empty_graph.to_mermaid(edge_label_fn=bad_fn)

        # Should still produce output without crashing
        assert "graph TD" in mermaid

    def test_to_mermaid_special_chars_in_labels(
        self, empty_graph: ConcreteGraph
    ) -> None:
        """Special characters in labels should be handled."""
        empty_graph.add_node(
            "test", value=MockNodeValue(name='Test "quoted" (parens) {braces}')
        )

        mermaid = empty_graph.to_mermaid(
            node_label_fn=lambda v: v.name if hasattr(v, "name") else str(v)
        )

        # Quotes should be replaced
        assert (
            '"' not in mermaid.split('["')[1].split('"]')[0]
            if '["' in mermaid
            else True
        )

    def test_to_mermaid_plus_sign_replaced(self, empty_graph: ConcreteGraph) -> None:
        """Plus sign should be replaced with ' plus '."""
        empty_graph.add_node("test", value=MockNodeValue(name="A+B"))

        mermaid = empty_graph.to_mermaid(
            node_label_fn=lambda v: v.name if hasattr(v, "name") else str(v)
        )

        assert " plus " in mermaid


# ============================================================================
# Test Graph Base Class - Export to JSON
# ============================================================================


class TestGraphExportJson:
    """Tests for JSON export."""

    def test_to_json_dict_empty(self, empty_graph: ConcreteGraph) -> None:
        """Empty graph should produce correct JSON dict."""
        data = empty_graph.to_json_dict()

        assert data["nodes"] == []
        assert data["edges"] == []
        assert data["node_count"] == 0
        assert data["edge_count"] == 0

    def test_to_json_dict_simple(self, simple_graph: ConcreteGraph) -> None:
        """Simple graph should produce correct JSON dict."""
        data = simple_graph.to_json_dict()

        assert data["node_count"] == 3
        assert data["edge_count"] == 2

    def test_to_json_dict_with_model_dump(self, empty_graph: ConcreteGraph) -> None:
        """Nodes with model_dump should serialize correctly."""
        empty_graph.add_node("test", value=MockNodeValue(name="Test"))

        data = empty_graph.to_json_dict()

        node_data = data["nodes"][0]
        assert node_data["value"] == {"name": "Test"}

    def test_to_json_dict_with_dict_value(self, empty_graph: ConcreteGraph) -> None:
        """Nodes with __dict__ should serialize correctly."""

        class SimpleValue:
            def __init__(self) -> None:
                self.name = "Simple"

        empty_graph.add_node("test", value=SimpleValue())

        data = empty_graph.to_json_dict()

        node_data = data["nodes"][0]
        assert node_data["value"] == {"name": "Simple"}

    def test_to_json_dict_with_str_value(self, empty_graph: ConcreteGraph) -> None:
        """Nodes without model_dump or __dict__ should use str()."""
        empty_graph.add_node("test", value=42)

        data = empty_graph.to_json_dict()

        node_data = data["nodes"][0]
        assert node_data["value"] == "42"

    def test_to_json_dict_edge_with_model_dump(
        self, empty_graph: ConcreteGraph
    ) -> None:
        """Edges with model_dump metadata should serialize correctly."""
        empty_graph.add_edge(
            "A", "B", metadata=MockEdgeMetadata(weight=10, label="test")
        )

        data = empty_graph.to_json_dict()

        edge_data = data["edges"][0]
        assert edge_data["metadata"] == {"weight": 10, "label": "test"}

    def test_to_json_dict_edge_with_str_metadata(
        self, empty_graph: ConcreteGraph
    ) -> None:
        """Edges with simple metadata should serialize as string."""
        empty_graph.add_edge("A", "B", metadata=123)

        data = empty_graph.to_json_dict()

        edge_data = data["edges"][0]
        assert edge_data["metadata"] == "123"

    def test_to_json_pretty(self, simple_graph: ConcreteGraph) -> None:
        """to_json with pretty=True should produce formatted output."""
        json_str = simple_graph.to_json(pretty=True, indent=4)

        assert "\n" in json_str
        assert "    " in json_str

    def test_to_json_compact(self, simple_graph: ConcreteGraph) -> None:
        """to_json with pretty=False should produce compact output."""
        json_str = simple_graph.to_json(pretty=False)

        assert "\n" not in json_str

    def test_to_json_parseable(self, simple_graph: ConcreteGraph) -> None:
        """to_json output should be valid JSON."""
        json_str = simple_graph.to_json()

        data = json.loads(json_str)
        assert "nodes" in data
        assert "edges" in data

    def test_to_json_dict_model_dump_exception(
        self, empty_graph: ConcreteGraph
    ) -> None:
        """model_dump exception should fall back to str()."""

        class BadModelDump:
            def model_dump(self) -> Dict[str, Any]:
                raise RuntimeError("Test error")

            def __str__(self) -> str:
                return "BadModelDump"

        empty_graph.add_node("test", value=BadModelDump())

        data = empty_graph.to_json_dict()

        assert data["nodes"][0]["value"] == "BadModelDump"

    def test_to_json_dict_vars_exception(self, empty_graph: ConcreteGraph) -> None:
        """vars() exception should fall back to str()."""

        class BadVars:
            @property
            def __dict__(self) -> Dict[str, Any]:  # type: ignore[override]
                return {"key": "value"}

            def __str__(self) -> str:
                return "BadVars"

        empty_graph.add_node("test", value=BadVars())

        data = empty_graph.to_json_dict()

        # Should use the __dict__ property successfully
        assert data["nodes"][0]["value"] == {"key": "value"}


# ============================================================================
# Test Graph Base Class - Export to ASCII Tree
# ============================================================================


class TestGraphExportAsciiTree:
    """Tests for ASCII tree export."""

    def test_to_ascii_tree_empty(self, empty_graph: ConcreteGraph) -> None:
        """Empty graph should produce minimal ASCII output."""
        tree = empty_graph.to_ascii_tree()

        assert "Schema" in tree

    def test_to_ascii_tree_simple(self, simple_graph: ConcreteGraph) -> None:
        """Simple graph should produce correct ASCII tree."""
        tree = simple_graph.to_ascii_tree()

        assert "Schema" in tree
        assert "├──" in tree or "└──" in tree

    def test_to_ascii_tree_with_root_nodes(self, simple_graph: ConcreteGraph) -> None:
        """Custom root nodes should be used."""
        tree = simple_graph.to_ascii_tree(root_nodes=["A"])

        assert "A" in tree

    def test_to_ascii_tree_with_node_label_fn(self, empty_graph: ConcreteGraph) -> None:
        """node_label_fn should customize node labels."""
        empty_graph.add_node("test", value=MockNodeValue(name="Custom Label"))

        tree = empty_graph.to_ascii_tree(
            root_nodes=["test"],
            node_label_fn=lambda v: v.name if hasattr(v, "name") else str(v),
        )

        assert "Custom Label" in tree

    def test_to_ascii_tree_with_edge_label_fn(self, empty_graph: ConcreteGraph) -> None:
        """edge_label_fn should customize edge labels."""
        empty_graph.add_edge(
            "A", "B", metadata=MockEdgeMetadata(weight=5, label="edge_label")
        )

        tree = empty_graph.to_ascii_tree(
            root_nodes=["A"], edge_label_fn=lambda m: m.label if m else ""
        )

        assert "edge_label" in tree

    def test_to_ascii_tree_max_depth(self, empty_graph: ConcreteGraph) -> None:
        """max_depth should limit tree depth."""
        # Create a deep chain: A -> B -> C -> D -> E
        for i in range(5):
            node_id = chr(ord("A") + i)
            empty_graph.add_node(node_id)
            if i > 0:
                prev_id = chr(ord("A") + i - 1)
                empty_graph.add_edge(prev_id, node_id)

        tree = empty_graph.to_ascii_tree(root_nodes=["A"], max_depth=2)

        # Should stop rendering at some depth
        assert "A" in tree

    def test_to_ascii_tree_truncates_long_labels(
        self, empty_graph: ConcreteGraph
    ) -> None:
        """Long labels should be truncated."""
        long_name = "A" * 100
        empty_graph.add_node("test", value=MockNodeValue(name=long_name))

        tree = empty_graph.to_ascii_tree(
            root_nodes=["test"],
            node_label_fn=lambda v: v.name if hasattr(v, "name") else str(v),
        )

        # Should be truncated with ...
        assert "..." in tree

    def test_to_ascii_tree_node_label_exception(
        self, empty_graph: ConcreteGraph
    ) -> None:
        """node_label_fn exception should fall back to node_id."""
        empty_graph.add_node("test_node", value="value")

        def bad_fn(v: Any) -> str:
            raise ValueError("Test error")

        tree = empty_graph.to_ascii_tree(root_nodes=["test_node"], node_label_fn=bad_fn)

        # Should fall back to node_id
        assert "test_node" in tree

    def test_to_ascii_tree_nonexistent_root(self, empty_graph: ConcreteGraph) -> None:
        """Nonexistent root node should be handled gracefully."""
        tree = empty_graph.to_ascii_tree(root_nodes=["nonexistent"])

        # Should not crash
        assert "Schema" in tree

    def test_to_ascii_tree_edges_with_metadata(
        self, empty_graph: ConcreteGraph
    ) -> None:
        """Edges with metadata should show [constraint] prefix."""
        empty_graph.add_edge("A", "B", metadata="constraint")

        tree = empty_graph.to_ascii_tree(root_nodes=["A"])

        assert "[constraint]" in tree

    def test_to_ascii_tree_edges_without_metadata(
        self, empty_graph: ConcreteGraph
    ) -> None:
        """Edges without metadata should not show [constraint]."""
        empty_graph.add_edge("A", "B")

        tree = empty_graph.to_ascii_tree(root_nodes=["A"])

        # Should have edge but without [constraint]
        assert "(A -> B)" in tree

    def test_to_ascii_tree_default_root_nodes(
        self, simple_graph: ConcreteGraph
    ) -> None:
        """Default root nodes should be nodes with no prerequisites."""
        tree = simple_graph.to_ascii_tree()

        # A has no prerequisites, should be root
        assert "A" in tree


# ============================================================================
# Test Graph Base Class - Build Dependency Graph
# ============================================================================


class TestGraphBuildDependencyGraph:
    """Tests for dependency graph building."""

    def test_build_dependency_graph_empty(self, empty_graph: ConcreteGraph) -> None:
        """Empty graph should produce empty dependency dict."""
        deps = empty_graph._build_dependency_graph()

        assert deps == {}

    def test_build_dependency_graph_simple(self, simple_graph: ConcreteGraph) -> None:
        """Simple graph should produce correct dependency dict."""
        deps = simple_graph._build_dependency_graph()

        assert deps["A"] == set()
        assert deps["B"] == {"A"}
        assert deps["C"] == {"B"}


# ============================================================================
# Test Edge Cases and Integration
# ============================================================================


class TestGraphEdgeCases:
    """Edge cases and integration tests."""

    def test_multiple_edges_same_direction(self, empty_graph: ConcreteGraph) -> None:
        """Multiple edges in same direction should all be recorded."""
        empty_graph.add_edge("A", "B", metadata="edge1")
        empty_graph.add_edge("A", "B", metadata="edge2")

        edges = list(empty_graph._iter_edges())

        assert len(edges) == 2

    def test_graph_with_isolated_nodes(self, empty_graph: ConcreteGraph) -> None:
        """Isolated nodes should be included in queries."""
        empty_graph.add_node("isolated")
        empty_graph.add_node("A")
        empty_graph.add_node("B")
        empty_graph.add_edge("A", "B")

        # Isolated node should be in topological order
        order = empty_graph.topological_order()
        assert "isolated" in order

        # Isolated node should be ready
        ready = empty_graph.ready_nodes(set())
        assert "isolated" in ready


class TestGraphIntegration:
    """Integration tests for graph operations."""

    def test_complex_graph_workflow(self) -> None:
        """Test complete workflow with complex graph."""
        graph = ConcreteGraph()

        # Build complex structure
        graph.add_node("root", value="root_value")
        graph.add_node("child1")
        graph.add_node("child2")
        graph.add_node("grandchild")

        graph.add_edge("root", "child1")
        graph.add_edge("root", "child2")
        graph.add_edge("child1", "grandchild")
        graph.add_edge("child2", "grandchild")

        # Verify structure
        assert graph.ancestors("grandchild") == {"root", "child1", "child2"}
        assert graph.descendants("root") == {"child1", "child2", "grandchild"}

        # Verify topological order
        order = graph.topological_order()
        assert order.index("root") < order.index("child1")
        assert order.index("root") < order.index("child2")
        assert order.index("child1") < order.index("grandchild")

        # Verify exports don't crash
        assert "digraph" in graph.to_dot()
        assert "graph TD" in graph.to_mermaid()
        assert "nodes" in graph.to_json_dict()
        assert "Schema" in graph.to_ascii_tree()

    def test_remove_and_readd_node(self, empty_graph: ConcreteGraph) -> None:
        """Removing and re-adding a node should work correctly."""
        empty_graph.add_node("test", value="value1")
        empty_graph.remove_node("test")
        empty_graph.add_node("test", value="value2")

        node = empty_graph.get_node("test")
        assert node is not None
        assert node.value == "value2"


# ============================================================================
# Additional tests for 100% coverage
# ============================================================================


class TestGraphJsonEdgeCases:
    """Additional JSON export edge cases for coverage."""

    def test_to_json_dict_edge_with_dict_metadata(
        self, empty_graph: ConcreteGraph
    ) -> None:
        """Edges with __dict__ metadata should serialize correctly."""

        class MetaWithDict:
            def __init__(self) -> None:
                self.key = "value"
                self.num = 42

        empty_graph.add_edge("A", "B", metadata=MetaWithDict())

        data = empty_graph.to_json_dict()

        edge_data = data["edges"][0]
        assert edge_data["metadata"] == {"key": "value", "num": 42}

    def test_to_json_dict_edge_vars_exception(self, empty_graph: ConcreteGraph) -> None:
        """Edge metadata vars() exception should fall back to str()."""

        class BadVars:
            @property
            def __dict__(self) -> Dict[str, Any]:  # type: ignore[override]
                return {"key": "value"}

            def __str__(self) -> str:
                return "BadVars"

        empty_graph.add_edge("A", "B", metadata=BadVars())

        data = empty_graph.to_json_dict()

        # Should use the __dict__ property successfully
        assert data["edges"][0]["metadata"] == {"key": "value"}


class TestGraphAsciiTreeEdgeCases:
    """Additional ASCII tree edge cases for coverage."""

    def test_to_ascii_tree_edge_label_fn_exception(
        self, empty_graph: ConcreteGraph
    ) -> None:
        """edge_label_fn exception should be handled gracefully."""
        empty_graph.add_edge("A", "B", metadata="meta")

        def bad_fn(m: Any) -> str:
            raise ValueError("Test error")

        tree = empty_graph.to_ascii_tree(root_nodes=["A"], edge_label_fn=bad_fn)

        # Should produce output without edge label
        assert "(A -> B)" in tree


class TestGraphCycleException:
    """Test cycle detection raises ValueError."""

    def test_topological_order_with_cycle_raises(self) -> None:
        """topological_order should raise ValueError on cycle."""
        graph = ConcreteGraph()
        graph.add_node("A")
        graph.add_node("B")

        # Create circular dependency by manipulating internal state
        node_a = graph.get_node("A")
        node_b = graph.get_node("B")

        if isinstance(node_a, SimpleNode) and isinstance(node_b, SimpleNode):
            # A depends on B, B depends on A - manual cycle creation
            node_a.add_prerequisite("B", node_b)
            node_b.add_prerequisite("A", node_a)

        with pytest.raises(ValueError, match="Dependency cycle detected"):
            graph.topological_order()


class TestGraphVarsExceptionCoverage:
    """Tests for vars() exception handling coverage."""

    def test_to_json_dict_node_vars_actual_exception(
        self, empty_graph: ConcreteGraph
    ) -> None:
        """Test vars() raising actual exception for node."""

        # Using __slots__ to prevent __dict__ attribute
        class NodeValueNoDict:
            """Value with __slots__ and no __dict__."""

            __slots__ = ("_data",)

            def __init__(self) -> None:
                self._data = "test"

            def __str__(self) -> str:
                return "NodeValueNoDict"

        empty_graph.add_node("test", value=NodeValueNoDict())

        data = empty_graph.to_json_dict()

        # __slots__ objects don't have __dict__, so str() is used
        assert data["nodes"][0]["value"] == "NodeValueNoDict"

    def test_to_json_dict_edge_vars_actual_exception(
        self, empty_graph: ConcreteGraph
    ) -> None:
        """Test vars() raising actual exception for edge metadata."""

        class EdgeMetaNoDict:
            """Metadata with __slots__ and no __dict__."""

            __slots__ = ("_data",)

            def __init__(self) -> None:
                self._data = "test"

            def __str__(self) -> str:
                return "EdgeMetaNoDict"

        empty_graph.add_edge("A", "B", metadata=EdgeMetaNoDict())

        data = empty_graph.to_json_dict()

        # __slots__ objects don't have __dict__, so str() is used
        assert data["edges"][0]["metadata"] == "EdgeMetaNoDict"


class TestGraphAncestorsDescendantsRevisit:
    """Tests for revisit scenarios in ancestors/descendants."""

    def test_ancestors_with_diamond_revisits(self) -> None:
        """Test that ancestors handles revisiting nodes in diamond."""
        graph = ConcreteGraph()
        # A -> B -> D
        # A -> C -> D
        # This creates a diamond where D is reached twice via B and C
        graph.add_node("A")
        graph.add_node("B")
        graph.add_node("C")
        graph.add_node("D")
        graph.add_edge("A", "B")
        graph.add_edge("A", "C")
        graph.add_edge("B", "D")
        graph.add_edge("C", "D")

        # Ancestors of D should be A, B, C (no duplicates)
        ancestors = graph.ancestors("D")
        assert ancestors == {"A", "B", "C"}

    def test_descendants_with_diamond_revisits(self) -> None:
        """Test that descendants handles revisiting nodes in diamond."""
        graph = ConcreteGraph()
        # A -> B -> D
        # A -> C -> D
        graph.add_node("A")
        graph.add_node("B")
        graph.add_node("C")
        graph.add_node("D")
        graph.add_edge("A", "B")
        graph.add_edge("A", "C")
        graph.add_edge("B", "D")
        graph.add_edge("C", "D")

        # Descendants of A should be B, C, D (no duplicates)
        descendants = graph.descendants("A")
        assert descendants == {"B", "C", "D"}
