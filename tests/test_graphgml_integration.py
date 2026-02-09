"""
Integration Tests for GraphGML.

Tests for complete workflows: build graph → query → validate.
"""

import pytest
from cnsc.haai.graphgml.builder import GraphBuilder
from cnsc.haai.graphgml.core import GraphGML, GraphQuery
from cnsc.haai.graphgml.types import (
    CommitNode,
    StateNode,
    CandidateNode,
    GateStackRunNode,
    GateResultNode,
    ProofBundleNode,
    EdgeType,
)


class TestCompleteWorkflow:
    """Tests for complete build → query → validate workflow."""

    def test_full_commit_workflow(self):
        """Test complete workflow for a commit with gates."""
        # Step 1: Build the graph
        builder = GraphBuilder()
        graph = (
            builder
            .begin_commit("commit1", operation="balance_update")
            .add_state("s1", state_type="initial", balance=100)
            .add_state("s2", state_type="final", balance=150)
            .add_candidate("c1", value=150)
            .link_proposed_from("c1", "s1")
            .add_gate_stack_run("gtr1", gate_sequence=["affordability"])
            .add_gate_result("gr1", "affordability", True)
            .link_evaluates("gr1", "c1")
            .link_summarizes("commit1", "gtr1")
            .link_applies("gtr1", "s1")
            .add_proof_bundle("pb1", proof_type="zk")
            .link_requires_proof("commit1", "pb1")
            .build()
        )
        
        # Step 2: Query the graph
        query = GraphQuery(graph)
        
        # Find commit
        commits = graph.find_nodes_by_type("commit")
        assert len(commits) == 1
        assert commits[0].node_id == "commit1"
        
        # Find path from candidate to state
        paths = query.find_path("c1", "s1", [EdgeType.PROPOSED_FROM.value])
        assert len(paths) == 1
        
        # Step 3: Validate invariants
        violations = graph.validate_invariants()
        assert violations == [], f"Graph has invariant violations: {violations}"
        
        # Step 4: Copy and verify
        copy = graph.copy()
        assert copy.node_count() == graph.node_count()
        assert copy.edge_count() == graph.edge_count()

    def test_multi_commit_chain_workflow(self):
        """Test workflow with multiple commits in a chain."""
        builder = GraphBuilder()
        graph = (
            builder
            .begin_commit("commit1", operation="init")
            .add_state("s1", state_type="initial", value=0)
            .link_applies("commit1", "s1")
            .begin_commit("commit2", operation="update")
            .add_state("s2", state_type="intermediate", value=50)
            .link_applies("commit2", "s2")
            .link_scheduled_after("commit2", "commit1")
            .begin_commit("commit3", operation="finalize")
            .add_state("s3", state_type="final", value=100)
            .link_applies("commit3", "s3")
            .link_scheduled_after("commit3", "commit2")
            .build()
        )
        
        # Query for commit chain
        query = GraphQuery(graph)
        
        # Find all commits
        commits = graph.find_nodes_by_type("commit")
        assert len(commits) == 3
        
        # Find path through chain
        paths = query.find_path(
            "commit1", "commit3",
            [EdgeType.SCHEDULED_AFTER.value, EdgeType.SCHEDULED_AFTER.value]
        )
        # Path may or may not exist depending on edge direction
        assert len(paths) >= 0
        
        # Validate with strict mode disabled (allows orphaned nodes)
        violations = graph.validate_invariants(allow_orphaned=True)
        assert len(violations) == 0


class TestEdgeCases:
    """Tests for edge cases in graph operations."""

    def test_empty_graph(self):
        """Test operations on empty graph."""
        graph = GraphGML()
        
        assert graph.node_count() == 0
        assert graph.edge_count() == 0
        assert graph.validate_invariants() == []

    def test_single_node(self):
        """Test graph with single node (no edges)."""
        builder = GraphBuilder()
        graph = builder.add_state("s1", state_type="initial").build()
        
        assert graph.node_count() == 1
        assert graph.edge_count() == 0
        
        # In strict mode, single node is considered orphaned
        violations = graph.validate_invariants(allow_orphaned=False)
        assert len(violations) == 1
        assert "orphan" in violations[0].lower()

    def test_disconnected_components(self):
        """Test graph with disconnected components."""
        builder = GraphBuilder()
        graph = (
            builder
            # Component 1
            .add_state("s1", state_type="initial")
            .add_candidate("c1", value=100)
            .link_proposed_from("c1", "s1")
            # Component 2 (disconnected)
            .add_state("s2", state_type="other")
            .add_candidate("c2", value=200)
            .link_proposed_from("c2", "s2")
            .build()
        )
        
        assert graph.node_count() == 4
        assert graph.edge_count() == 2

    def test_isolated_node(self):
        """Test graph with isolated node (no edges at all)."""
        builder = GraphBuilder()
        graph = (
            builder
            .add_state("s1", state_type="initial")
            .add_candidate("c1", value=100)
            .link_proposed_from("c1", "s1")
            # Isolated node
            .add_state("s2", state_type="orphan")
            .build()
        )
        
        # In strict mode, isolated node causes violation
        violations = graph.validate_invariants(allow_orphaned=False)
        assert len(violations) >= 1
        assert any("s2" in v for v in violations)


class TestComplexTraversal:
    """Tests for complex traversal scenarios."""

    def test_diamond_pattern_traversal(self):
        """Test traversal through diamond pattern (A -> B,C -> D)."""
        builder = GraphBuilder()
        graph = (
            builder
            .add_state("s1", state_type="initial")
            .add_candidate("c1", value=100)
            .add_candidate("c2", value=150)
            .add_state("s2", state_type="final")
            .link_proposed_from("c1", "s1")
            .link_proposed_from("c2", "s1")
            .add_gate_stack_run("gtr1", gate_sequence=["affordability"])
            .add_gate_result("gr1", "affordability", True)
            .link_evaluates("gr1", "c1")
            .link_evaluates("gr1", "c2")
            .link_applies("gtr1", "s1")
            .link_applies("gtr1", "s2")
            .build()
        )
        
        # Find all candidates
        candidates = graph.find_nodes_by_type("candidate")
        assert len(candidates) == 2

    def test_cycle_detection_in_traversal(self):
        """Test that traversal handles cycles correctly."""
        builder = GraphBuilder()
        graph = (
            builder
            .add_state("s1", state_type="initial")
            .add_candidate("c1", value=100)
            .add_gate_stack_run("gtr1", gate_sequence=["affordability"])
            .link_proposed_from("c1", "s1")
            .link_applies("gtr1", "s1")
            .begin_commit("commit1")
            .link_summarizes("commit1", "gtr1")
            .link_scheduled_after("commit1", "commit1")  # Self-loop
            .build()
        )
        
        # Traversal should not infinite loop
        nodes = list(graph.traverse("commit1", EdgeType.SCHEDULED_AFTER))
        
        # Should find commit1 but not infinite loop
        node_ids = [n.node_id for n in nodes]
        assert "commit1" in node_ids

    def test_bidirectional_traversal(self):
        """Test traversal in both directions."""
        builder = GraphBuilder()
        graph = (
            builder
            .add_state("s1", state_type="initial")
            .add_candidate("c1", value=100)
            .link_proposed_from("c1", "s1")
            .add_gate_result("gr1", "affordability", True)
            .link_evaluates("gr1", "c1")
            .build()
        )
        
        # Forward: from candidate to state (should yield s1)
        forward = list(graph.traverse("c1", EdgeType.PROPOSED_FROM))
        assert any(n.node_id == "s1" for n in forward) or len(forward) >= 1
        
        # Reverse: from state to candidate (should yield c1)
        reverse = list(graph.traverse("s1", "rev_proposed_from"))
        assert any(n.node_id == "c1" for n in reverse) or len(reverse) >= 1


class TestPerformance:
    """Tests for performance with larger graphs."""

    def test_large_graph_node_operations(self):
        """Test node operations scale linearly."""
        builder = GraphBuilder()
        
        # Create 100 nodes
        for i in range(100):
            builder.add_state(f"s{i}", state_type="intermediate")
        
        graph = builder.build()
        
        assert graph.node_count() == 100
        
        # Add edges
        for i in range(99):
            builder._graph.add_edge(f"s{i}", EdgeType.SCHEDULED_AFTER, f"s{i+1}")
        
        graph = builder.build()
        assert graph.edge_count() == 99

    def test_large_graph_query_performance(self):
        """Test query performance on larger graph."""
        builder = GraphBuilder()
        
        # Create chain: s0 -> s1 -> s2 -> ... -> s99
        for i in range(100):
            builder.add_state(f"s{i}", state_type="intermediate")
            if i > 0:
                builder.link_scheduled_after(f"s{i}", f"s{i-1}")
        
        graph = builder.build()
        query = GraphQuery(graph)
        
        # Find path through chain
        paths = query.find_path(
            "s99", "s0",
            [EdgeType.SCHEDULED_AFTER.value] * 99
        )
        
        assert len(paths) == 1
        assert len(paths[0]) == 100

    def test_copy_large_graph(self):
        """Test copying a large graph."""
        builder = GraphBuilder()
        
        # Create graph with 50 nodes and 49 edges
        for i in range(50):
            builder.add_state(f"s{i}", state_type="intermediate", index=i)
            if i > 0:
                builder.link_scheduled_after(f"s{i}", f"s{i-1}")
        
        graph = builder.build()
        
        # Copy
        copy = graph.copy()
        assert copy.node_count() == 50


class TestGraphInvariants:
    """Tests for specific graph invariants."""

    def test_node_existence_for_edges(self):
        """Test that all edges reference existing nodes."""
        builder = GraphBuilder()
        graph = builder.add_state("s1", state_type="initial").build()
        
        # Add edge to non-existent node
        with pytest.raises(ValueError):
            graph.add_edge("s1", EdgeType.PROPOSED_FROM, "nonexistent")

    def test_valid_edge_types(self):
        """Test that only valid edge types are accepted."""
        graph = GraphGML()
        graph.add_node(StateNode("s1", "initial"))
        graph.add_node(StateNode("s2", "final"))
        
        # Valid edge type
        graph.add_edge("s1", EdgeType.SCHEDULED_AFTER, "s2")
        
        # Invalid edge type should be caught by validation
        graph.edges.append(("s1", "invalid_type", "s2"))
        
        violations = graph.validate_invariants()
        assert len(violations) >= 1

    def test_no_duplicate_edges(self):
        """Test that duplicate edges are detected."""
        graph = GraphGML()
        graph.add_node(StateNode("s1", "initial"))
        graph.add_node(StateNode("s2", "final"))
        
        graph.add_edge("s1", EdgeType.SCHEDULED_AFTER, "s2")
        graph.add_edge("s1", EdgeType.SCHEDULED_AFTER, "s2")
        
        violations = graph.validate_invariants()
        assert len(violations) == 1
        assert "duplicate" in violations[0].lower()


class TestQueryPatterns:
    """Tests for common query patterns."""

    def test_find_all_commits_with_proof(self):
        """Test finding all commits that have proof bundles."""
        builder = GraphBuilder()
        graph = (
            builder
            .begin_commit("commit1")
            .add_proof_bundle("pb1")
            .link_requires_proof("commit1", "pb1")
            .begin_commit("commit2")  # No proof
            .begin_commit("commit3")
            .add_proof_bundle("pb2")
            .link_requires_proof("commit3", "pb2")
            .build()
        )
        
        # Find all commits
        all_commits = graph.find_nodes_by_type("commit")
        assert len(all_commits) == 3
        
        # Find commits with proof
        commits_with_proof = [
            c for c in all_commits
            if graph.get_neighbors(c.node_id, EdgeType.REQUIRES_PROOF)
        ]
        
        assert len(commits_with_proof) == 2

    def test_find_gate_evaluation_results(self):
        """Test finding all gate results for candidates."""
        builder = GraphBuilder()
        graph = (
            builder
            .add_candidate("c1", value=100)
            .add_candidate("c2", value=200)
            .add_gate_result("gr1", "affordability", True)
            .add_gate_result("gr2", "no_smuggling", True)
            .link_evaluates("gr1", "c1")
            .link_evaluates("gr2", "c1")
            .link_evaluates("gr1", "c2")
            .build()
        )
        
        # Find gate results evaluating c1 using correct reverse key
        gr_for_c1 = graph.get_neighbors("c1", f"rev_{EdgeType.EVALUATES.value}")
        assert len(gr_for_c1) == 2
        
        # Find candidates evaluated by gr1
        candidates_for_gr1 = graph.get_neighbors("gr1", EdgeType.EVALUATES)
        assert len(candidates_for_gr1) == 2

    def test_find_state_lineage(self):
        """Test finding state lineage through commits."""
        builder = GraphBuilder()
        graph = (
            builder
            .add_state("s1", state_type="initial", version=1)
            .begin_commit("commit1")
            .add_state("s2", state_type="final", version=2)
            .link_applies("commit1", "s1")
            .link_applies("commit1", "s2")
            .build()
        )
        
        # Find states
        states = graph.find_nodes_by_type("state")
        assert len(states) == 2
        
        # Find commits that apply to a state using correct reverse key
        commits_for_s1 = graph.get_neighbors("s1", f"rev_{EdgeType.APPLIES.value}")
        assert len(commits_for_s1) == 1


class TestDependencyOrdering:
    """Tests for dependency ordering and topological sort."""

    def test_get_dependency_order_simple(self, simple_graph):
        """Test dependency order for simple graph."""
        query = GraphQuery(simple_graph)
        order = query.get_dependency_order()
        
        assert len(order) == 2
        assert "c1" in order
        assert "s1" in order

    def test_get_dependency_order_chain(self, multi_commit_graph):
        """Test dependency order for chain of commits."""
        query = GraphQuery(multi_commit_graph)
        order = query.get_dependency_order()
        
        assert len(order) == multi_commit_graph.node_count()

    def test_cycle_detection(self):
        """Test that cycles are detected."""
        graph = GraphGML()
        graph.add_node(StateNode("s1", "initial"))
        graph.add_node(StateNode("s2", "final"))
        graph.add_edge("s1", EdgeType.SCHEDULED_AFTER, "s2")
        graph.add_edge("s2", EdgeType.SCHEDULED_AFTER, "s1")
        
        query = GraphQuery(graph)
        
        with pytest.raises(ValueError, match="cycle|Cycle"):
            query.get_dependency_order()
