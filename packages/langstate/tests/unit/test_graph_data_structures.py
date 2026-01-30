"""
Comprehensive tests for Graph data structures (Graph, DAG, DAH).

Tests cover:
- Node operations (add, get, remove)
- Edge operations (add, remove)
- Graph queries (prerequisites, dependents, ancestors, descendants)
- Ready nodes detection
- Topological ordering
- Cycle detection
- Export methods (DOT, Mermaid, JSON, ASCII tree)
"""

import json
import pytest

# Import implementations
from packages.langstate.core.data_structure.dag import (
    DirectedAcyclicGraph,
    DirectedAcyclicGraphNode,
)
from packages.langstate.core.data_structure.dah import (
    DirectedAcyclicHypergraph,
    DirectedAcyclicHypergraphNode,
)
from packages.langstate.core.data_structure.graph import Graph


# =============================================================================
# DAG Tests
# =============================================================================

class TestDAGNodeOperations:
    """Test DAG node add/get/remove operations."""
    
    def test_add_node_creates_new_node(self):
        """Adding a new node should create it in the graph."""
        dag = DirectedAcyclicGraph[str, None]()
        node = dag.add_node("A", value="value_A")
        
        assert node.id == "A"
        assert node.value == "value_A"
        assert "A" in dag.nodes
        assert dag.get_node("A") is node
    
    def test_add_node_updates_existing_value(self):
        """Adding an existing node with a value should update it."""
        dag = DirectedAcyclicGraph[str, None]()
        dag.add_node("A", value="old_value")
        dag.add_node("A", value="new_value")
        
        node = dag.get_node("A")
        assert node is not None
        assert node.value == "new_value"
    
    def test_add_node_preserves_value_when_none(self):
        """Adding an existing node with None value should preserve old value."""
        dag = DirectedAcyclicGraph[str, None]()
        dag.add_node("A", value="keep_me")
        dag.add_node("A", value=None)
        
        node = dag.get_node("A")
        assert node is not None
        assert node.value == "keep_me"
    
    def test_get_node_returns_none_for_missing(self):
        """Getting a non-existent node should return None."""
        dag = DirectedAcyclicGraph[str, None]()
        assert dag.get_node("missing") is None
    
    def test_remove_node_removes_from_graph(self):
        """Removing a node should remove it from the graph."""
        dag = DirectedAcyclicGraph[str, None]()
        dag.add_node("A")
        dag.add_node("B")
        dag.add_edge("A", "B")
        
        dag.remove_node("A")
        
        assert "A" not in dag.nodes
        assert dag.prerequisites("B") == set()
    
    def test_remove_nonexistent_node_is_safe(self):
        """Removing a non-existent node should not raise."""
        dag = DirectedAcyclicGraph[str, None]()
        dag.remove_node("missing")  # Should not raise


class TestDAGEdgeOperations:
    """Test DAG edge add/remove operations."""
    
    def test_add_edge_creates_dependency(self):
        """Adding an edge should create a dependency relationship."""
        dag = DirectedAcyclicGraph[str, None]()
        dag.add_edge("A", "B")
        
        assert dag.prerequisites("B") == {"A"}
        assert dag.dependents("A") == {"B"}
    
    def test_add_edge_creates_nodes_if_missing(self):
        """Adding an edge should auto-create nodes if they don't exist."""
        dag = DirectedAcyclicGraph[str, None]()
        dag.add_edge("A", "B")
        
        assert "A" in dag.nodes
        assert "B" in dag.nodes
    
    def test_add_edge_with_metadata(self):
        """Adding an edge with metadata should store it."""
        dag = DirectedAcyclicGraph[str, str]()
        dag.add_edge("A", "B", metadata="constraint_type")
        
        edges = list(dag.iter_edges())
        assert len(edges) == 1
        assert edges[0] == ("A", "B", "constraint_type")
    
    def test_add_self_edge_raises(self):
        """Adding a self-referential edge should raise ValueError."""
        dag = DirectedAcyclicGraph[str, None]()
        
        with pytest.raises(ValueError, match="Self dependency"):
            dag.add_edge("A", "A")
    
    def test_add_edge_cycle_detection(self):
        """Adding an edge that creates a cycle should raise ValueError."""
        dag = DirectedAcyclicGraph[str, None]()
        dag.add_edge("A", "B")
        dag.add_edge("B", "C")
        
        with pytest.raises(ValueError, match="cycle"):
            dag.add_edge("C", "A")
    
    def test_add_edge_no_cycle_check(self):
        """Disabling cycle check should allow cycles."""
        dag = DirectedAcyclicGraph[str, None]()
        dag.add_edge("A", "B", check_cycle=False)
        dag.add_edge("B", "A", check_cycle=False)
        
        # Both edges should exist (creates a cycle)
        assert dag.prerequisites("B") == {"A"}
        assert dag.prerequisites("A") == {"B"}
    
    def test_remove_edge(self):
        """Removing an edge should remove the dependency."""
        dag = DirectedAcyclicGraph[str, None]()
        dag.add_edge("A", "B")
        dag.remove_edge("A", "B")
        
        assert dag.prerequisites("B") == set()
        assert dag.dependents("A") == set()
    
    def test_remove_nonexistent_edge_is_safe(self):
        """Removing a non-existent edge should not raise."""
        dag = DirectedAcyclicGraph[str, None]()
        dag.add_node("A")
        dag.add_node("B")
        dag.remove_edge("A", "B")  # Should not raise
    
    def test_add_edge_idempotent(self):
        """Adding the same edge twice should be idempotent."""
        dag = DirectedAcyclicGraph[str, str]()
        dag.add_edge("A", "B", metadata="first")
        dag.add_edge("A", "B", metadata="second")
        
        # Should have one edge with updated metadata
        edges = list(dag.iter_edges())
        assert len(edges) == 1
        assert edges[0] == ("A", "B", "second")


class TestDAGGraphQueries:
    """Test DAG graph-wide query operations."""
    
    def setup_method(self):
        """Set up a test DAG: A -> B -> C, A -> D -> C"""
        self.dag = DirectedAcyclicGraph[str, None]()
        self.dag.add_edge("A", "B")
        self.dag.add_edge("B", "C")
        self.dag.add_edge("A", "D")
        self.dag.add_edge("D", "C")
    
    def test_prerequisites(self):
        """Test direct prerequisites."""
        assert self.dag.prerequisites("C") == {"B", "D"}
        assert self.dag.prerequisites("B") == {"A"}
        assert self.dag.prerequisites("A") == set()
    
    def test_prerequisite_ids_alias(self):
        """prerequisite_ids should be alias for prerequisites."""
        assert self.dag.prerequisite_ids("C") == self.dag.prerequisites("C")
    
    def test_dependents(self):
        """Test direct dependents."""
        assert self.dag.dependents("A") == {"B", "D"}
        assert self.dag.dependents("B") == {"C"}
        assert self.dag.dependents("C") == set()
    
    def test_ancestors(self):
        """Test transitive prerequisites."""
        assert self.dag.ancestors("C") == {"A", "B", "D"}
        assert self.dag.ancestors("B") == {"A"}
        assert self.dag.ancestors("A") == set()
    
    def test_descendants(self):
        """Test transitive dependents."""
        assert self.dag.descendants("A") == {"B", "C", "D"}
        assert self.dag.descendants("B") == {"C"}
        assert self.dag.descendants("C") == set()
    
    def test_queries_for_missing_node(self):
        """Queries for missing nodes should return empty sets."""
        assert self.dag.prerequisites("missing") == set()
        assert self.dag.dependents("missing") == set()
        assert self.dag.ancestors("missing") == set()
        assert self.dag.descendants("missing") == set()


class TestDAGReadyNodes:
    """Test DAG ready node detection."""
    
    def test_ready_nodes_all_prerequisites_satisfied(self):
        """Node is ready when all prerequisites are satisfied."""
        dag = DirectedAcyclicGraph[str, None]()
        dag.add_edge("A", "C")
        dag.add_edge("B", "C")
        
        # A and B are roots, so they're ready with no satisfied set
        # When A is satisfied, B is still ready (root), and C is not (missing B)
        assert dag.ready_nodes(set()) == {"A", "B"}  # Both roots are ready
        assert "C" not in dag.ready_nodes({"A"})      # C needs both A and B
        assert "C" not in dag.ready_nodes({"B"})      # C needs both A and B
        assert "C" in dag.ready_nodes({"A", "B"})     # Now C is ready
    
    def test_ready_nodes_root_nodes(self):
        """Root nodes (no prerequisites) are always ready."""
        dag = DirectedAcyclicGraph[str, None]()
        dag.add_edge("A", "B")
        dag.add_node("C")  # Standalone root
        
        assert dag.ready_nodes(set()) == {"A", "C"}
    
    def test_node_is_ready_method(self):
        """Test node-level is_ready method."""
        dag = DirectedAcyclicGraph[str, None]()
        dag.add_edge("A", "C")
        dag.add_edge("B", "C")
        
        node_c = dag.get_node("C")
        assert node_c is not None
        assert not node_c.is_ready({"A"})
        assert not node_c.is_ready({"B"})
        assert node_c.is_ready({"A", "B"})


class TestDAGTopologicalOrder:
    """Test DAG topological ordering."""
    
    def test_topological_order_simple(self):
        """Test topological order for simple chain."""
        dag = DirectedAcyclicGraph[str, None]()
        dag.add_edge("A", "B")
        dag.add_edge("B", "C")
        
        order = dag.topological_order()
        assert order.index("A") < order.index("B") < order.index("C")
    
    def test_topological_order_diamond(self):
        """Test topological order for diamond graph."""
        dag = DirectedAcyclicGraph[str, None]()
        dag.add_edge("A", "B")
        dag.add_edge("A", "C")
        dag.add_edge("B", "D")
        dag.add_edge("C", "D")
        
        order = dag.topological_order()
        assert order.index("A") < order.index("B")
        assert order.index("A") < order.index("C")
        assert order.index("B") < order.index("D")
        assert order.index("C") < order.index("D")
    
    def test_topological_order_cycle_raises(self):
        """Topological order should raise for cyclic graph."""
        dag = DirectedAcyclicGraph[str, None]()
        dag.add_edge("A", "B", check_cycle=False)
        dag.add_edge("B", "A", check_cycle=False)
        
        with pytest.raises(ValueError, match="cycle"):
            dag.topological_order()
    
    def test_validate_acyclic(self):
        """validate_acyclic should not raise for valid DAG."""
        dag = DirectedAcyclicGraph[str, None]()
        dag.add_edge("A", "B")
        dag.add_edge("B", "C")
        
        dag.validate_acyclic()  # Should not raise


class TestDAGExport:
    """Test DAG export methods."""
    
    def setup_method(self):
        """Set up a test DAG."""
        self.dag = DirectedAcyclicGraph[str, str]()
        self.dag.add_edge("A", "B", metadata="dep")
        self.dag.add_edge("B", "C")
    
    def test_to_dot(self):
        """Test DOT export."""
        dot = self.dag.to_dot()
        assert "digraph DAG" in dot
        assert '"A"' in dot
        assert '"B"' in dot
        assert '"C"' in dot
        assert '"A" -> "B"' in dot
        assert '"B" -> "C"' in dot
    
    def test_to_mermaid(self):
        """Test Mermaid export."""
        mermaid = self.dag.to_mermaid()
        assert "graph TD" in mermaid
        assert "A[" in mermaid or 'A["' in mermaid
    
    def test_to_json_dict(self):
        """Test JSON dict export."""
        data = self.dag.to_json_dict()
        assert "nodes" in data
        assert "edges" in data
        assert data["node_count"] == 3
        assert data["edge_count"] == 2
    
    def test_to_json(self):
        """Test JSON string export."""
        json_str = self.dag.to_json()
        data = json.loads(json_str)
        assert data["node_count"] == 3
    
    def test_to_ascii_tree(self):
        """Test ASCII tree export."""
        tree = self.dag.to_ascii_tree()
        assert "Schema" in tree
        assert "Edges" in tree
    
    def test_iter_edges(self):
        """Test edge iteration."""
        edges = list(self.dag.iter_edges())
        assert len(edges) == 2
        assert ("A", "B", "dep") in edges
        assert ("B", "C", None) in edges


class TestDAGNodeSchema:
    """Test DAG node schema dataclass."""
    
    def test_node_hash_by_id(self):
        """Nodes should hash by ID."""
        node1: DirectedAcyclicGraphNode[str, None] = DirectedAcyclicGraphNode(id="A", value="v1")
        node2: DirectedAcyclicGraphNode[str, None] = DirectedAcyclicGraphNode(id="A", value="v2")
        
        assert hash(node1) == hash(node2)
    
    def test_node_equality_by_id(self):
        """Nodes should be equal by ID."""
        node1: DirectedAcyclicGraphNode[str, None] = DirectedAcyclicGraphNode(id="A", value="v1")
        node2: DirectedAcyclicGraphNode[str, None] = DirectedAcyclicGraphNode(id="A", value="v2")
        
        assert node1 == node2
    
    def test_node_prerequisite_nodes(self):
        """Test node prerequisite_nodes method."""
        dag = DirectedAcyclicGraph[str, None]()
        dag.add_edge("A", "C")
        dag.add_edge("B", "C")
        
        node_c = dag.get_node("C")
        assert node_c is not None
        prereq_nodes = node_c.prerequisite_nodes()
        
        assert len(prereq_nodes) == 2
        assert {n.id for n in prereq_nodes} == {"A", "B"}


# =============================================================================
# DAH Tests
# =============================================================================

class TestDAHNodeOperations:
    """Test DAH node add/get/remove operations."""
    
    def test_add_node_creates_new_node(self):
        """Adding a new node should create it in the hypergraph."""
        dah = DirectedAcyclicHypergraph[str, None]()
        node = dah.add_node("A", value="value_A")
        
        assert node.id == "A"
        assert node.value == "value_A"
        assert "A" in dah.nodes
    
    def test_remove_node_removes_from_graph(self):
        """Removing a node should remove it and related hyperedges."""
        dah = DirectedAcyclicHypergraph[str, None]()
        dah.add_hyperedge(["A", "B"], "C")
        
        dah.remove_node("A")
        
        assert "A" not in dah.nodes
        # C's hyperedge should be removed too since it referenced A
        assert dah.prerequisite_ids("C") == set()


class TestDAHHyperedgeOperations:
    """Test DAH hyperedge add/remove operations."""
    
    def test_add_hyperedge_single_source(self):
        """Adding a hyperedge with single source should work."""
        dah = DirectedAcyclicHypergraph[str, None]()
        edge_id = dah.add_hyperedge(["A"], "B")
        
        assert edge_id is not None
        assert dah.prerequisite_ids("B") == {"A"}
    
    def test_add_hyperedge_multiple_sources(self):
        """Adding a hyperedge with multiple sources should work."""
        dah = DirectedAcyclicHypergraph[str, None]()
        _ = dah.add_hyperedge(["A", "B", "C"], "D")
        
        assert dah.prerequisite_ids("D") == {"A", "B", "C"}
    
    def test_add_hyperedge_with_metadata(self):
        """Adding a hyperedge with metadata should store it."""
        dah = DirectedAcyclicHypergraph[str, str]()
        dah.add_hyperedge(["A"], "B", metadata="and_constraint")
        
        edges = list(dah.iter_hyperedges())
        assert len(edges) == 1
        assert edges[0][2] == "and_constraint"  # metadata at index 2
    
    def test_add_hyperedge_self_dependency_raises(self):
        """Adding a hyperedge with target in sources should raise."""
        dah = DirectedAcyclicHypergraph[str, None]()
        
        with pytest.raises(ValueError, match="Self dependency"):
            dah.add_hyperedge(["A", "B"], "A")
    
    def test_add_hyperedge_empty_sources_raises(self):
        """Adding a hyperedge with no sources should raise."""
        dah = DirectedAcyclicHypergraph[str, None]()
        
        with pytest.raises(ValueError, match="at least one source"):
            dah.add_hyperedge([], "A")
    
    def test_add_hyperedge_cycle_detection(self):
        """Adding a hyperedge that creates a cycle should raise."""
        dah = DirectedAcyclicHypergraph[str, None]()
        dah.add_hyperedge(["A"], "B")
        dah.add_hyperedge(["B"], "C")
        
        with pytest.raises(ValueError, match="[Cc]ycle"):
            dah.add_hyperedge(["C"], "A")
    
    def test_add_hyperedge_custom_edge_id(self):
        """Adding a hyperedge with custom ID should use it."""
        dah = DirectedAcyclicHypergraph[str, None]()
        edge_id = dah.add_hyperedge(["A"], "B", edge_id="custom_id")
        
        assert edge_id == "custom_id"
    
    def test_remove_hyperedge(self):
        """Removing a hyperedge should remove it."""
        dah = DirectedAcyclicHypergraph[str, None]()
        edge_id = dah.add_hyperedge(["A"], "B")
        
        dah.remove_hyperedge(edge_id, "B")
        
        assert dah.prerequisite_ids("B") == set()
    
    def test_add_edge_backward_compat(self):
        """add_edge should work as backward-compatible single-source hyperedge."""
        dah = DirectedAcyclicHypergraph[str, None]()
        edge_id = dah.add_edge("A", "B")
        
        assert edge_id is not None
        assert dah.prerequisite_ids("B") == {"A"}


class TestDAHReadyNodes:
    """Test DAH ready node detection (OR-of-ANDs semantics)."""
    
    def test_ready_with_single_hyperedge(self):
        """Node is ready when all sources of a hyperedge are satisfied."""
        dah = DirectedAcyclicHypergraph[str, None]()
        dah.add_hyperedge(["A", "B"], "C")
        
        # C requires BOTH A AND B
        assert "C" not in dah.ready_nodes({"A"})
        assert "C" not in dah.ready_nodes({"B"})
        assert "C" in dah.ready_nodes({"A", "B"})
    
    def test_ready_with_multiple_hyperedges_or_semantics(self):
        """Node is ready when ANY hyperedge is fully satisfied (OR)."""
        dah = DirectedAcyclicHypergraph[str, None]()
        dah.add_hyperedge(["A", "B"], "D")  # Option 1: A AND B
        dah.add_hyperedge(["C"], "D")        # Option 2: just C
        
        # D is ready if (A AND B) OR C
        assert "D" not in dah.ready_nodes({"A"})
        assert "D" not in dah.ready_nodes({"B"})
        assert "D" in dah.ready_nodes({"A", "B"})  # Option 1 satisfied
        assert "D" in dah.ready_nodes({"C"})        # Option 2 satisfied
    
    def test_node_is_ready_with_no_hyperedges(self):
        """Node with no hyperedges (root) is always ready."""
        dah = DirectedAcyclicHypergraph[str, None]()
        dah.add_node("A")
        
        assert "A" in dah.ready_nodes(set())


class TestDAHTopologicalOrder:
    """Test DAH topological ordering."""
    
    def test_topological_order_with_hyperedges(self):
        """Test topological order with multi-source hyperedges."""
        dah = DirectedAcyclicHypergraph[str, None]()
        dah.add_hyperedge(["A", "B"], "C")
        dah.add_hyperedge(["C"], "D")
        
        order = dah.topological_order()
        
        assert order.index("A") < order.index("C")
        assert order.index("B") < order.index("C")
        assert order.index("C") < order.index("D")


class TestDAHExport:
    """Test DAH export methods."""
    
    def setup_method(self):
        """Set up a test DAH."""
        self.dah = DirectedAcyclicHypergraph[str, str]()
        self.dah.add_hyperedge(["A", "B"], "C", metadata="and_dep")
        self.dah.add_hyperedge(["C"], "D")
    
    def test_to_dot(self):
        """Test DOT export."""
        dot = self.dah.to_dot()
        assert "digraph DAH" in dot
    
    def test_to_mermaid(self):
        """Test Mermaid export."""
        mermaid = self.dah.to_mermaid()
        assert "graph TD" in mermaid
    
    def test_to_json_dict(self):
        """Test JSON dict export."""
        data = self.dah.to_json_dict()
        assert "nodes" in data
        assert "hyperedges" in data
        assert data["node_count"] == 4  # A, B, C, D
        assert data["hyperedge_count"] == 2
    
    def test_to_json(self):
        """Test JSON string export."""
        json_str = self.dah.to_json()
        data = json.loads(json_str)
        assert data["hyperedge_count"] == 2
    
    def test_to_ascii_tree(self):
        """Test ASCII tree export."""
        tree = self.dah.to_ascii_tree()
        assert "Schema" in tree
        assert "HyperEdges" in tree
    
    def test_iter_hyperedges(self):
        """Test hyperedge iteration."""
        edges = list(self.dah.iter_hyperedges())
        assert len(edges) == 2
        
        # Find the multi-source edge
        multi_source_edge = next(e for e in edges if len(e[0]) > 1)
        assert multi_source_edge[0] == {"A", "B"}
        assert multi_source_edge[1] == "C"
        assert multi_source_edge[2] == "and_dep"


class TestDAHNodeSchema:
    """Test DAH node schema dataclass."""
    
    def test_node_hash_by_id(self):
        """Nodes should hash by ID."""
        node1: DirectedAcyclicHypergraphNode[str, None] = DirectedAcyclicHypergraphNode(id="A", value="v1")
        node2: DirectedAcyclicHypergraphNode[str, None] = DirectedAcyclicHypergraphNode(id="A", value="v2")
        
        assert hash(node1) == hash(node2)
    
    def test_node_equality_by_id(self):
        """Nodes should be equal by ID."""
        node1: DirectedAcyclicHypergraphNode[str, None] = DirectedAcyclicHypergraphNode(id="A", value="v1")
        node2: DirectedAcyclicHypergraphNode[str, None] = DirectedAcyclicHypergraphNode(id="A", value="v2")
        
        assert node1 == node2
    
    def test_node_hyperedges(self):
        """Test node hyperedges method."""
        dah = DirectedAcyclicHypergraph[str, None]()
        dah.add_hyperedge(["A"], "C", edge_id="e1")
        dah.add_hyperedge(["B"], "C", edge_id="e2")
        
        node_c = dah.get_node("C")
        assert node_c is not None
        hyperedges = node_c.hyperedges()
        
        assert len(hyperedges) == 2


# =============================================================================
# Graph Base Class Tests
# =============================================================================

class TestGraphBase:
    """Test base Graph class functionality."""
    
    def test_graph_cannot_add_node_directly(self):
        """Base Graph should raise NotImplementedError for add_node."""
        graph: Graph[str, None] = Graph()
        
        with pytest.raises(NotImplementedError):
            graph.add_node("A")
    
    def test_graph_cannot_remove_node_directly(self):
        """Base Graph should raise NotImplementedError for remove_node."""
        graph: Graph[str, None] = Graph()
        
        with pytest.raises(NotImplementedError):
            graph.remove_node("A")


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests for complex scenarios."""
    
    def test_dag_complex_graph(self):
        """Test DAG with complex dependency structure."""
        dag = DirectedAcyclicGraph[str, None]()
        
        # Build a complex graph
        #       A
        #      / \
        #     B   C
        #    /|   |\
        #   D E   F G
        #    \|   |/
        #     H   I
        #      \ /
        #       J
        
        dag.add_edge("A", "B")
        dag.add_edge("A", "C")
        dag.add_edge("B", "D")
        dag.add_edge("B", "E")
        dag.add_edge("C", "F")
        dag.add_edge("C", "G")
        dag.add_edge("D", "H")
        dag.add_edge("E", "H")
        dag.add_edge("F", "I")
        dag.add_edge("G", "I")
        dag.add_edge("H", "J")
        dag.add_edge("I", "J")
        
        # Verify structure
        assert dag.ancestors("J") == {"A", "B", "C", "D", "E", "F", "G", "H", "I"}
        assert dag.descendants("A") == {"B", "C", "D", "E", "F", "G", "H", "I", "J"}
        
        # Verify topological order
        order = dag.topological_order()
        assert order.index("A") < order.index("J")
        assert order.index("B") < order.index("H")
        assert order.index("C") < order.index("I")
    
    def test_dah_alternative_paths(self):
        """Test DAH with alternative dependency paths."""
        dah = DirectedAcyclicHypergraph[str, None]()
        
        # Goal can be reached by:
        # - Path 1: A AND B
        # - Path 2: C AND D AND E
        # - Path 3: F alone
        
        dah.add_hyperedge(["A", "B"], "Goal")
        dah.add_hyperedge(["C", "D", "E"], "Goal")
        dah.add_hyperedge(["F"], "Goal")
        
        # Test each path
        assert "Goal" in dah.ready_nodes({"A", "B"})
        assert "Goal" in dah.ready_nodes({"C", "D", "E"})
        assert "Goal" in dah.ready_nodes({"F"})
        
        # Partial paths don't work
        assert "Goal" not in dah.ready_nodes({"A"})
        assert "Goal" not in dah.ready_nodes({"C", "D"})


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
