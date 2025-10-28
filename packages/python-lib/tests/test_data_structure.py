"""Test the data structure implementations (Tree and DAG)."""

import pytest
from langstate.data_structure.tree import TreeNode
from langstate.data_structure.dag import (
    DirectedAcyclicGraphNode,
    DirectedAcyclicGraphEdge,
    DirectedAcyclicGraph,
)


# =============================================================================
# TreeNode Tests
# =============================================================================

class TestTreeNode:
    """Test suite for TreeNode."""

    def test_create_empty_node(self):
        """Test creating an empty tree node."""
        node = TreeNode[str]()
        assert node.value is None
        assert node.children == []

    def test_create_node_with_value(self):
        """Test creating a tree node with a value."""
        node = TreeNode[str](value="root")
        assert node.value == "root"
        assert node.children == []

    def test_add_single_child(self):
        """Test adding a single child to a node."""
        root = TreeNode[str](value="root")
        child = TreeNode[str](value="child")
        root.add_child(child)
        
        assert len(root.children) == 1
        assert root.children[0] == child
        assert root.children[0].value == "child"

    def test_add_multiple_children(self):
        """Test adding multiple children to a node."""
        root = TreeNode[int](value=1)
        child1 = TreeNode[int](value=2)
        child2 = TreeNode[int](value=3)
        child3 = TreeNode[int](value=4)
        
        root.add_child(child1)
        root.add_child(child2)
        root.add_child(child3)
        
        assert len(root.children) == 3
        assert root.children[0].value == 2
        assert root.children[1].value == 3
        assert root.children[2].value == 4

    def test_walk_single_node(self):
        """Test walking a tree with a single node."""
        node = TreeNode[str](value="only")
        result = node.walk()
        
        assert len(result) == 1
        assert result[0] == node

    def test_walk_simple_tree(self):
        """Test walking a simple tree."""
        root = TreeNode[str](value="root")
        child1 = TreeNode[str](value="child1")
        child2 = TreeNode[str](value="child2")
        
        root.add_child(child1)
        root.add_child(child2)
        
        result = root.walk()
        
        assert len(result) == 3
        assert result[0] == root
        assert result[1] == child1
        assert result[2] == child2

    def test_walk_nested_tree(self):
        """Test walking a nested tree structure."""
        root = TreeNode[str](value="root")
        child1 = TreeNode[str](value="child1")
        child2 = TreeNode[str](value="child2")
        grandchild1 = TreeNode[str](value="grandchild1")
        grandchild2 = TreeNode[str](value="grandchild2")
        
        root.add_child(child1)
        root.add_child(child2)
        child1.add_child(grandchild1)
        child1.add_child(grandchild2)
        
        result = root.walk()
        
        # Should be in depth-first order: root, child1, grandchild1, grandchild2, child2
        assert len(result) == 5
        assert result[0].value == "root"
        assert result[1].value == "child1"
        assert result[2].value == "grandchild1"
        assert result[3].value == "grandchild2"
        assert result[4].value == "child2"

    def test_tree_with_none_values(self):
        """Test tree nodes can have None values."""
        root = TreeNode[str]()
        child = TreeNode[str]()
        root.add_child(child)
        
        result = root.walk()
        assert len(result) == 2
        assert result[0].value is None
        assert result[1].value is None

    def test_tree_with_complex_types(self):
        """Test tree with complex value types."""
        data1 = {"key": "value1"}
        data2 = {"key": "value2"}
        
        root = TreeNode[dict](value=data1)
        child = TreeNode[dict](value=data2)
        root.add_child(child)
        
        assert root.value == data1
        assert root.children[0].value == data2


# =============================================================================
# DirectedAcyclicGraphNode Tests
# =============================================================================

class TestDirectedAcyclicGraphNode:
    """Test suite for DirectedAcyclicGraphNode."""

    def test_create_node(self):
        """Test creating a DAG node."""
        node = DirectedAcyclicGraphNode[str, None](id="node1", value="test")
        assert node.id == "node1"
        assert node.value == "test"
        assert len(node.depends_on) == 0

    def test_node_equality(self):
        """Test node equality based on ID."""
        node1 = DirectedAcyclicGraphNode[str, None](id="same_id", value="value1")
        node2 = DirectedAcyclicGraphNode[str, None](id="same_id", value="value2")
        node3 = DirectedAcyclicGraphNode[str, None](id="different_id", value="value1")
        
        assert node1 == node2  # Same ID
        assert node1 != node3  # Different ID

    def test_node_hashable(self):
        """Test that nodes are hashable by ID."""
        node1 = DirectedAcyclicGraphNode[str, None](id="node1")
        node2 = DirectedAcyclicGraphNode[str, None](id="node2")
        
        node_set = {node1, node2}
        assert len(node_set) == 2
        assert node1 in node_set
        assert node2 in node_set

    def test_prerequisites(self):
        """Test getting prerequisites of a node."""
        node1 = DirectedAcyclicGraphNode[str, None](id="node1")
        node2 = DirectedAcyclicGraphNode[str, None](id="node2")
        node3 = DirectedAcyclicGraphNode[str, None](id="node3")
        
        # Manually set up dependencies
        node1.depends_on["node2"] = DirectedAcyclicGraphEdge(target=node2)
        node1.depends_on["node3"] = DirectedAcyclicGraphEdge(target=node3)
        
        prereqs = node1.prerequisites()
        assert prereqs == {"node2", "node3"}

    def test_prerequisite_nodes(self):
        """Test getting prerequisite node objects."""
        node1 = DirectedAcyclicGraphNode[str, None](id="node1")
        node2 = DirectedAcyclicGraphNode[str, None](id="node2")
        node3 = DirectedAcyclicGraphNode[str, None](id="node3")
        
        node1.depends_on["node2"] = DirectedAcyclicGraphEdge(target=node2)
        node1.depends_on["node3"] = DirectedAcyclicGraphEdge(target=node3)
        
        prereq_nodes = node1.prerequisite_nodes()
        assert prereq_nodes == {node2, node3}

    def test_is_ready(self):
        """Test checking if a node is ready based on satisfied prerequisites."""
        node1 = DirectedAcyclicGraphNode[str, None](id="node1")
        node2 = DirectedAcyclicGraphNode[str, None](id="node2")
        node3 = DirectedAcyclicGraphNode[str, None](id="node3")
        
        node1.depends_on["node2"] = DirectedAcyclicGraphEdge(target=node2)
        node1.depends_on["node3"] = DirectedAcyclicGraphEdge(target=node3)
        
        assert not node1.is_ready(set())
        assert not node1.is_ready({"node2"})
        assert node1.is_ready({"node2", "node3"})
        assert node1.is_ready({"node2", "node3", "node4"})


# =============================================================================
# DirectedAcyclicGraphEdge Tests
# =============================================================================

class TestDirectedAcyclicGraphEdge:
    """Test suite for DirectedAcyclicGraphEdge."""

    def test_create_edge_without_metadata(self):
        """Test creating an edge without metadata."""
        target = DirectedAcyclicGraphNode[str, None](id="target")
        edge = DirectedAcyclicGraphEdge[None](target=target)
        
        assert edge.target == target
        assert edge.metadata is None

    def test_create_edge_with_metadata(self):
        """Test creating an edge with metadata."""
        target = DirectedAcyclicGraphNode[str, str](id="target")
        edge = DirectedAcyclicGraphEdge[str](target=target, metadata="edge_data")
        
        assert edge.target == target
        assert edge.metadata == "edge_data"

    def test_edge_with_complex_metadata(self):
        """Test edge with complex metadata type."""
        target = DirectedAcyclicGraphNode[str, dict](id="target")
        metadata = {"weight": 10, "label": "important"}
        edge = DirectedAcyclicGraphEdge[dict](target=target, metadata=metadata)
        
        assert edge.metadata == metadata
        assert edge.metadata["weight"] == 10


# =============================================================================
# DirectedAcyclicGraph Tests
# =============================================================================

class TestDirectedAcyclicGraph:
    """Test suite for DirectedAcyclicGraph."""

    def test_create_empty_graph(self):
        """Test creating an empty graph."""
        graph = DirectedAcyclicGraph[str, None]()
        assert len(graph.nodes) == 0

    def test_create_graph_with_nodes(self):
        """Test creating a graph with initial nodes."""
        node1 = DirectedAcyclicGraphNode[str, None](id="node1", value="val1")
        node2 = DirectedAcyclicGraphNode[str, None](id="node2", value="val2")
        
        graph = DirectedAcyclicGraph[str, None](nodes=[node1, node2])
        
        assert len(graph.nodes) == 2
        assert "node1" in graph.nodes
        assert "node2" in graph.nodes

    def test_add_node(self):
        """Test adding a node to the graph."""
        graph = DirectedAcyclicGraph[str, None]()
        node = graph.add_node("node1", value="test")
        
        assert node.id == "node1"
        assert node.value == "test"
        assert "node1" in graph.nodes

    def test_add_node_idempotent(self):
        """Test that adding the same node ID is idempotent."""
        graph = DirectedAcyclicGraph[str, None]()
        node1 = graph.add_node("node1", value="value1")
        node2 = graph.add_node("node1", value="value2")
        
        assert node1 is node2  # Same object
        assert node1.value == "value2"  # Value updated
        assert len(graph.nodes) == 1

    def test_get_node(self):
        """Test getting a node from the graph."""
        graph = DirectedAcyclicGraph[str, None]()
        graph.add_node("node1", value="test")
        
        node = graph.get_node("node1")
        assert node is not None
        assert node.id == "node1"
        
        missing = graph.get_node("nonexistent")
        assert missing is None

    def test_add_edge_simple(self):
        """Test adding a simple edge between two nodes."""
        graph = DirectedAcyclicGraph[str, None]()
        graph.add_edge("node1", "node2")
        
        assert "node1" in graph.nodes
        assert "node2" in graph.nodes
        
        node2 = graph.get_node("node2")
        assert "node1" in node2.depends_on

    def test_add_edge_with_metadata(self):
        """Test adding an edge with metadata."""
        graph = DirectedAcyclicGraph[str, str]()
        graph.add_edge("a", "b", metadata="edge_info")
        
        node_b = graph.get_node("b")
        edge = node_b.depends_on["a"]
        assert edge.metadata == "edge_info"

    def test_add_edge_creates_nodes(self):
        """Test that adding an edge creates nodes if they don't exist."""
        graph = DirectedAcyclicGraph[str, None]()
        graph.add_edge("prereq", "dependent")
        
        assert graph.get_node("prereq") is not None
        assert graph.get_node("dependent") is not None

    def test_add_edge_idempotent(self):
        """Test that adding the same edge multiple times is idempotent."""
        graph = DirectedAcyclicGraph[str, str]()
        graph.add_edge("a", "b", metadata="first")
        graph.add_edge("a", "b", metadata="second")
        
        node_b = graph.get_node("b")
        assert len(node_b.depends_on) == 1
        assert node_b.depends_on["a"].metadata == "second"

    def test_add_edge_self_dependency_raises(self):
        """Test that self-dependency raises an error."""
        graph = DirectedAcyclicGraph[str, None]()
        
        with pytest.raises(ValueError, match="Self dependency"):
            graph.add_edge("node1", "node1")

    def test_add_edge_cycle_detection(self):
        """Test cycle detection when adding edges."""
        graph = DirectedAcyclicGraph[str, None]()
        graph.add_edge("a", "b")
        graph.add_edge("b", "c")
        
        # Adding c -> a would create a cycle
        with pytest.raises(ValueError, match="cycle detected"):
            graph.add_edge("c", "a")

    def test_add_edge_no_cycle_check(self):
        """Test adding edge without cycle check."""
        graph = DirectedAcyclicGraph[str, None]()
        graph.add_edge("a", "b")
        graph.add_edge("b", "c")
        
        # This would create a cycle, but we're not checking
        graph.add_edge("c", "a", check_cycle=False)
        
        # Verify cycle was created (topological_order should fail)
        with pytest.raises(ValueError, match="cycle"):
            graph.topological_order()

    def test_remove_edge(self):
        """Test removing an edge."""
        graph = DirectedAcyclicGraph[str, None]()
        graph.add_edge("a", "b")
        
        assert "a" in graph.get_node("b").depends_on
        
        graph.remove_edge("a", "b")
        
        assert "a" not in graph.get_node("b").depends_on

    def test_remove_edge_nonexistent(self):
        """Test removing a nonexistent edge doesn't raise error."""
        graph = DirectedAcyclicGraph[str, None]()
        graph.add_node("a")
        
        # Should not raise
        graph.remove_edge("a", "b")
        graph.remove_edge("nonexistent1", "nonexistent2")

    def test_remove_node(self):
        """Test removing a node."""
        graph = DirectedAcyclicGraph[str, None]()
        graph.add_edge("a", "b")
        graph.add_edge("b", "c")
        
        assert "b" in graph.nodes
        
        graph.remove_node("b")
        
        assert "b" not in graph.nodes
        # a and c should still exist
        assert "a" in graph.nodes
        assert "c" in graph.nodes

    def test_remove_node_cleans_edges(self):
        """Test that removing a node cleans up all its edges."""
        graph = DirectedAcyclicGraph[str, None]()
        graph.add_edge("a", "b")
        graph.add_edge("b", "c")
        graph.add_edge("d", "b")
        
        graph.remove_node("b")
        
        # c should no longer depend on b
        node_c = graph.get_node("c")
        assert "b" not in node_c.depends_on
        
        # d should exist but have no dependents through b
        node_d = graph.get_node("d")
        assert node_d is not None

    def test_prerequisites(self):
        """Test getting prerequisites of a node."""
        graph = DirectedAcyclicGraph[str, None]()
        graph.add_edge("a", "c")
        graph.add_edge("b", "c")
        
        prereqs = graph.prerequisites("c")
        assert prereqs == {"a", "b"}
        
        # Node with no prerequisites
        assert graph.prerequisites("a") == set()
        
        # Nonexistent node
        assert graph.prerequisites("nonexistent") == set()

    def test_dependents(self):
        """Test getting dependents of a node."""
        graph = DirectedAcyclicGraph[str, None]()
        graph.add_edge("a", "b")
        graph.add_edge("a", "c")
        graph.add_edge("a", "d")
        
        deps = graph.dependents("a")
        assert deps == {"b", "c", "d"}
        
        # Node with no dependents
        assert graph.dependents("b") == set()

    def test_ancestors(self):
        """Test getting all transitive prerequisites."""
        graph = DirectedAcyclicGraph[str, None]()
        graph.add_edge("a", "b")
        graph.add_edge("b", "c")
        graph.add_edge("d", "c")
        
        ancestors = graph.ancestors("c")
        assert ancestors == {"a", "b", "d"}
        
        assert graph.ancestors("b") == {"a"}
        assert graph.ancestors("a") == set()

    def test_descendants(self):
        """Test getting all transitive dependents."""
        graph = DirectedAcyclicGraph[str, None]()
        graph.add_edge("a", "b")
        graph.add_edge("b", "c")
        graph.add_edge("c", "d")
        
        descendants = graph.descendants("a")
        assert descendants == {"b", "c", "d"}
        
        assert graph.descendants("b") == {"c", "d"}
        assert graph.descendants("d") == set()

    def test_ready_nodes(self):
        """Test getting nodes that are ready to execute."""
        graph = DirectedAcyclicGraph[str, None]()
        graph.add_edge("a", "b")
        graph.add_edge("b", "c")
        graph.add_node("d")  # Independent node
        
        # Initially, only nodes with no prerequisites are ready
        ready = graph.ready_nodes(set())
        assert ready == {"a", "d"}
        
        # After 'a' is satisfied
        ready = graph.ready_nodes({"a"})
        assert ready == {"a", "b", "d"}
        
        # After 'a' and 'b' are satisfied
        ready = graph.ready_nodes({"a", "b"})
        assert ready == {"a", "b", "c", "d"}

    def test_topological_order(self):
        """Test topological ordering of nodes."""
        graph = DirectedAcyclicGraph[str, None]()
        graph.add_edge("a", "c")
        graph.add_edge("b", "c")
        graph.add_edge("c", "d")
        
        order = graph.topological_order()
        
        # Verify order constraints
        assert order.index("a") < order.index("c")
        assert order.index("b") < order.index("c")
        assert order.index("c") < order.index("d")

    def test_topological_order_with_cycle_raises(self):
        """Test that topological order raises on cycles."""
        graph = DirectedAcyclicGraph[str, None]()
        graph.add_edge("a", "b", check_cycle=False)
        graph.add_edge("b", "c", check_cycle=False)
        graph.add_edge("c", "a", check_cycle=False)
        
        with pytest.raises(ValueError, match="cycle"):
            graph.topological_order()

    def test_validate_acyclic(self):
        """Test validating that graph is acyclic."""
        graph = DirectedAcyclicGraph[str, None]()
        graph.add_edge("a", "b")
        graph.add_edge("b", "c")
        
        # Should not raise
        graph.validate_acyclic()

    def test_validate_acyclic_with_cycle_raises(self):
        """Test that validate_acyclic raises on cycles."""
        graph = DirectedAcyclicGraph[str, None]()
        graph.add_edge("a", "b", check_cycle=False)
        graph.add_edge("b", "a", check_cycle=False)
        
        with pytest.raises(ValueError, match="cycle"):
            graph.validate_acyclic()

    def test_iter_edges(self):
        """Test iterating over all edges."""
        graph = DirectedAcyclicGraph[str, str]()
        graph.add_edge("a", "b", metadata="ab")
        graph.add_edge("b", "c", metadata="bc")
        graph.add_edge("a", "c", metadata="ac")
        
        edges = list(graph.iter_edges())
        
        assert len(edges) == 3
        assert ("a", "b", "ab") in edges
        assert ("b", "c", "bc") in edges
        assert ("a", "c", "ac") in edges

    def test_to_dot(self):
        """Test generating DOT representation."""
        graph = DirectedAcyclicGraph[str, None]()
        graph.add_edge("a", "b")
        graph.add_edge("b", "c")
        
        dot = graph.to_dot()
        
        assert "digraph DAG" in dot
        assert '"a"' in dot
        assert '"b"' in dot
        assert '"c"' in dot
        assert '"a" -> "b"' in dot
        assert '"b" -> "c"' in dot

    def test_complex_graph_scenario(self):
        """Test a complex graph scenario with multiple paths."""
        graph = DirectedAcyclicGraph[str, int]()
        
        # Build a diamond dependency graph
        #     a
        #    / \
        #   b   c
        #    \ /
        #     d
        graph.add_edge("a", "b", metadata=1)
        graph.add_edge("a", "c", metadata=2)
        graph.add_edge("b", "d", metadata=3)
        graph.add_edge("c", "d", metadata=4)
        
        # Test various queries
        assert graph.prerequisites("d") == {"b", "c"}
        assert graph.ancestors("d") == {"a", "b", "c"}
        assert graph.dependents("a") == {"b", "c"}
        assert graph.descendants("a") == {"b", "c", "d"}
        
        # Test topological order
        order = graph.topological_order()
        assert order.index("a") < order.index("b")
        assert order.index("a") < order.index("c")
        assert order.index("b") < order.index("d")
        assert order.index("c") < order.index("d")
        
        # Test ready nodes
        assert graph.ready_nodes(set()) == {"a"}
        assert graph.ready_nodes({"a"}) == {"a", "b", "c"}
        assert graph.ready_nodes({"a", "b", "c"}) == {"a", "b", "c", "d"}

    def test_weakref_dependents(self):
        """Test that dependents are tracked with weak references."""
        graph = DirectedAcyclicGraph[str, None]()
        graph.add_edge("a", "b")
        
        node_a = graph.get_node("a")
        
        # b should be in a's dependents initially
        dependents_before = graph.dependents("a")
        assert "b" in dependents_before
        
        # Remove node b from graph
        graph.remove_node("b")
        
        # b should no longer be in a's dependents (via graph method)
        dependents_after = graph.dependents("a")
        assert "b" not in dependents_after
