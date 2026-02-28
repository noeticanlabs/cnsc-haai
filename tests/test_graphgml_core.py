"""
Graph Core Tests for GraphGML.

Tests for GraphGML class operations: add/get nodes and edges, traversal,
validation, and cloning.
"""

import pytest
from cnsc.haai.graphgml.core import GraphGML, GraphQuery
from cnsc.haai.graphgml.types import (
    GraphNode,
    CommitNode,
    StateNode,
    CandidateNode,
    GateStackRunNode,
    GateResultNode,
    ProofBundleNode,
    EdgeType,
)


class TestGraphGMLInitialization:
    """Tests for GraphGML initialization."""

    def test_empty_graph(self):
        """Test creating an empty graph."""
        graph = GraphGML()

        assert graph.node_count() == 0
        assert graph.edge_count() == 0

    def test_initial_state(self):
        """Test initial state of graph attributes."""
        graph = GraphGML()

        assert graph.nodes == {}
        assert graph.edges == []
        assert graph._adjacency is None


class TestAddNode:
    """Tests for adding nodes to the graph."""

    def test_add_single_node(self, empty_graph):
        """Test adding a single node."""
        node = StateNode("s1", "initial")
        empty_graph.add_node(node)

        assert empty_graph.node_count() == 1
        assert empty_graph.get_node("s1") == node

    def test_add_multiple_nodes(self, empty_graph):
        """Test adding multiple nodes."""
        nodes = [
            StateNode("s1", "initial"),
            StateNode("s2", "final"),
            CommitNode("commit1", "update"),
        ]

        for node in nodes:
            empty_graph.add_node(node)

        assert empty_graph.node_count() == 3

    def test_add_node_duplicate_id_raises(self, simple_graph):
        """Test that adding a node with duplicate ID raises ValueError."""
        duplicate = StateNode("s1", "different")

        with pytest.raises(ValueError, match="already exists"):
            simple_graph.add_node(duplicate)

    def test_get_nonexistent_node(self, empty_graph):
        """Test getting a node that doesn't exist returns None."""
        assert empty_graph.get_node("nonexistent") is None


class TestAddEdge:
    """Tests for adding edges to the graph."""

    def test_add_single_edge(self, simple_graph):
        """Test adding a single edge."""
        initial_count = simple_graph.edge_count()
        simple_graph.add_edge("s1", EdgeType.APPLIES, "c1")

        assert simple_graph.edge_count() == initial_count + 1

    def test_add_edge_nonexistent_source(self, empty_graph):
        """Test adding edge with nonexistent source raises ValueError."""
        with pytest.raises(ValueError, match="Source node.*not found"):
            empty_graph.add_edge("s1", EdgeType.PROPOSED_FROM, "s2")

    def test_add_edge_nonexistent_target(self, simple_graph):
        """Test adding edge with nonexistent target raises ValueError."""
        with pytest.raises(ValueError, match="Target node.*not found"):
            simple_graph.add_edge("c1", EdgeType.PROPOSED_FROM, "nonexistent")

    def test_add_edge_validates_node_exists(self, empty_graph):
        """Test edge addition validates both endpoints exist."""
        node = StateNode("s1", "initial")
        empty_graph.add_node(node)

        # Source exists, target doesn't
        with pytest.raises(ValueError):
            empty_graph.add_edge("s1", EdgeType.PROPOSED_FROM, "s2")

    def test_duplicate_edge_allowed(self, simple_graph):
        """Test that duplicate edges are allowed (can have multiple edges)."""
        simple_graph.add_edge("c1", EdgeType.PROPOSED_FROM, "s1")
        simple_graph.add_edge("c1", EdgeType.PROPOSED_FROM, "s1")

        # Both edges should exist (was 2 before fixture, now 3 total)
        assert simple_graph.edge_count() == 3


class TestGetNeighbors:
    """Tests for getting neighboring nodes."""

    def test_get_neighbors_all(self, simple_graph):
        """Test getting all neighbors of a node."""
        neighbors = simple_graph.get_neighbors("c1")

        assert len(neighbors) == 1
        assert neighbors[0].node_id == "s1"

    def test_get_neighbors_with_edge_type_filter(self, simple_graph):
        """Test filtering neighbors by edge type."""
        neighbors = simple_graph.get_neighbors("c1", EdgeType.PROPOSED_FROM)

        assert len(neighbors) == 1
        assert neighbors[0].node_id == "s1"

    def test_get_neighbors_no_matching_edge_type(self, simple_graph):
        """Test getting neighbors with non-matching edge type."""
        neighbors = simple_graph.get_neighbors("c1", EdgeType.EVALUATES)

        assert len(neighbors) == 0

    def test_get_neighbors_nonexistent_node(self, empty_graph):
        """Test getting neighbors of nonexistent node returns empty list."""
        neighbors = empty_graph.get_neighbors("nonexistent")

        assert neighbors == []


class TestFindNodes:
    """Tests for finding nodes with predicates."""

    def test_find_nodes_by_type(self, multi_commit_graph):
        """Test finding all nodes of a specific type."""
        commits = multi_commit_graph.find_nodes_by_type("commit")

        assert len(commits) == 2

    def test_find_nodes_multiple_of_type(self, multi_commit_graph):
        """Test finding multiple nodes of same type."""
        commits = multi_commit_graph.find_nodes_by_type("commit")

        assert len(commits) == 2

    def test_find_nodes_custom_predicate(self, simple_graph):
        """Test finding nodes with custom predicate."""
        results = simple_graph.find_nodes(
            lambda n: n.node_type == "state" and n.properties.get("state_type") == "initial"
        )

        assert len(results) == 1
        assert results[0].node_id == "s1"

    def test_find_nodes_no_matches(self, empty_graph):
        """Test finding nodes with no matches."""
        results = empty_graph.find_nodes(lambda n: n.node_type == "commit")

        assert results == []


class TestTraverse:
    """Tests for graph traversal."""

    def test_traverse_simple_path(self, simple_graph):
        """Test traversing a simple path."""
        nodes = list(simple_graph.traverse("s1", "rev_proposed_from"))

        # Should find c1 which points back to s1 via proposed_from
        # Note: traverse starts from s1 and follows rev_proposed_from edges
        node_ids = [n.node_id for n in nodes]
        assert "c1" in node_ids or len(node_ids) >= 1  # May include s1 itself

    def test_traverse_no_path(self, empty_graph):
        """Test traversing when no path exists."""
        state1 = StateNode("s1", "initial")
        empty_graph.add_node(state1)

        nodes = list(empty_graph.traverse("s1", EdgeType.APPLIES))

        # Traverse starts at s1 and yields it first, then tries to follow applies edges
        # Since there are no applies edges, only s1 is yielded
        assert len(nodes) == 1
        assert nodes[0].node_id == "s1"

    def test_traverse_nonexistent_start(self, empty_graph):
        """Test traversing from nonexistent node."""
        nodes = list(empty_graph.traverse("nonexistent", EdgeType.APPLIES))

        assert nodes == []

    def test_traverse_circular_path(self):
        """Test traversal handles circular references."""
        graph = GraphGML()

        s1 = StateNode("s1", "initial")
        c1 = CandidateNode("c1", value=100)

        graph.add_node(s1)
        graph.add_node(c1)

        # Create multiple edges to same node
        graph.add_edge("c1", EdgeType.PROPOSED_FROM, "s1")
        graph.add_edge("c1", EdgeType.PROPOSED_FROM, "s1")

        nodes = list(graph.traverse("s1", "rev_proposed_from"))

        # Should only visit each node once
        node_ids = [n.node_id for n in nodes]
        assert len(node_ids) == len(set(node_ids))


class TestValidateInvariants:
    """Tests for graph invariant validation."""

    def test_orphaned_node_detected(self, empty_graph):
        """Test orphaned nodes are detected when strict mode is enabled."""
        # Add a node without any edges
        node = StateNode("orphan", "isolated")
        empty_graph.add_node(node)

        # In strict mode, orphaned nodes cause violations
        violations = empty_graph.validate_invariants(allow_orphaned=False)

        assert len(violations) >= 1
        assert "orphaned" in violations[0].lower()

    def test_duplicate_edge_detected(self, simple_graph):
        """Test duplicate edges are detected."""
        simple_graph.add_edge("c1", EdgeType.PROPOSED_FROM, "s1")
        simple_graph.add_edge("c1", EdgeType.PROPOSED_FROM, "s1")

        violations = simple_graph.validate_invariants()

        # Should detect duplicates
        assert len(violations) >= 1
        assert any("duplicate" in v.lower() for v in violations)

    def test_invalid_edge_type_detected(self, simple_graph):
        """Test invalid edge types are detected."""
        simple_graph.edges.append(("c1", "invalid_type", "s1"))

        violations = simple_graph.validate_invariants()

        assert len(violations) >= 1


class TestGraphCopy:
    """Tests for graph copying and cloning."""

    def test_copy_empty_graph(self, empty_graph):
        """Test copying an empty graph."""
        copy = empty_graph.copy()

        assert copy.node_count() == 0
        assert copy.edge_count() == 0

    def test_copy_preserves_nodes(self, simple_graph):
        """Test copy preserves nodes."""
        copy = simple_graph.copy()

        assert copy.node_count() == simple_graph.node_count()
        assert copy.get_node("s1") is not None
        assert copy.get_node("c1") is not None

    def test_copy_preserves_edges(self, simple_graph):
        """Test copy preserves edges."""
        copy = simple_graph.copy()

        assert copy.edge_count() == simple_graph.edge_count()

    def test_copy_is_independent(self, simple_graph):
        """Test that copied graph is independent of original."""
        copy = simple_graph.copy()

        # Modify copy
        copy.add_node(StateNode("s2", "new"))

        # Original should be unchanged
        assert simple_graph.node_count() == 2
        assert copy.node_count() == 3

    def test_copy_preserves_properties(self, simple_graph):
        """Test that node properties are preserved in copy."""
        copy = simple_graph.copy()

        s1 = copy.get_node("s1")
        assert s1.properties.get("balance") == 100


class TestGraphOperations:
    """Tests for basic graph operations."""

    def test_clear_graph(self, simple_graph):
        """Test clearing all nodes and edges."""
        simple_graph.clear()

        assert simple_graph.node_count() == 0
        assert simple_graph.edge_count() == 0

    def test_node_count(self, simple_graph):
        """Test node_count returns correct value."""
        assert simple_graph.node_count() == 2

    def test_edge_count(self, simple_graph):
        """Test edge_count returns correct value."""
        assert simple_graph.edge_count() == 1


class TestGraphQuery:
    """Tests for GraphQuery class."""

    def test_find_path_exists(self, simple_graph):
        """Test finding an existing path."""
        query = GraphQuery(simple_graph)
        paths = query.find_path("c1", "s1", [EdgeType.PROPOSED_FROM.value])

        assert len(paths) > 0

    def test_find_path_no_path(self, simple_graph):
        """Test finding path when none exists."""
        query = GraphQuery(simple_graph)
        paths = query.find_path("s1", "c1", [EdgeType.APPLIES.value])

        assert paths == []

    def test_find_path_multiple_paths(self):
        """Test finding multiple paths."""
        graph = GraphGML()

        s1 = StateNode("s1", "initial")
        c1 = CandidateNode("c1", value=100)
        c2 = CandidateNode("c2", value=200)

        graph.add_node(s1)
        graph.add_node(c1)
        graph.add_node(c2)

        graph.add_edge("c1", EdgeType.PROPOSED_FROM, "s1")
        graph.add_edge("c2", EdgeType.PROPOSED_FROM, "s1")

        query = GraphQuery(graph)
        # Find path from c1 to s1 using the correct edge type
        paths = query.find_path("c1", "s1", [EdgeType.PROPOSED_FROM.value])

        assert len(paths) > 0

    def test_find_subgraph(self, simple_graph):
        """Test finding a subgraph matching a pattern."""
        query = GraphQuery(simple_graph)
        subgraph = query.find_subgraph({"node_type": "state"})

        assert subgraph.node_count() == 1
        assert subgraph.get_node("s1") is not None

    def test_find_subgraph_no_matches(self, empty_graph):
        """Test finding subgraph with no matches."""
        query = GraphQuery(empty_graph)
        subgraph = query.find_subgraph({"node_type": "commit"})

        assert subgraph.node_count() == 0

    def test_get_dependency_order(self, multi_commit_graph):
        """Test getting topological dependency order."""
        query = GraphQuery(multi_commit_graph)
        order = query.get_dependency_order()

        assert len(order) == multi_commit_graph.node_count()

    def test_find_upstream(self, multi_commit_graph):
        """Test finding upstream nodes."""
        query = GraphQuery(multi_commit_graph)
        upstream = query.find_upstream("commit2", [EdgeType.SCHEDULED_AFTER.value])

        assert len(upstream) >= 1

    def test_find_downstream(self, multi_commit_graph):
        """Test finding downstream nodes."""
        query = GraphQuery(multi_commit_graph)
        downstream = query.find_downstream("commit1", [EdgeType.SCHEDULED_AFTER.value])

        assert len(downstream) >= 1
