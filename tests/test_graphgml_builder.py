"""
Graph Builder Tests for GraphGML.

Tests for GraphBuilder fluent API and building graphs.
"""

import pytest
from cnsc.haai.graphgml.builder import GraphBuilder
from cnsc.haai.graphgml.core import GraphGML
from cnsc.haai.graphgml.types import (
    CommitNode,
    EmitNode,
    StateNode,
    CandidateNode,
    ConstraintSetNode,
    GateStackRunNode,
    GateResultNode,
    ProofBundleNode,
    MemoryReadNode,
    MemoryWriteNode,
    SolverCallNode,
    EdgeType,
)


class TestGraphBuilderInitialization:
    """Tests for GraphBuilder initialization."""

    def test_new_builder_has_empty_graph(self):
        """Test that new builder has an empty graph."""
        builder = GraphBuilder()
        assert builder._graph.node_count() == 0

    def test_initial_context_is_empty(self):
        """Test that initial context is empty."""
        builder = GraphBuilder()
        assert builder._current_context == {}


class TestFluentAPI:
    """Tests for fluent API (method chaining)."""

    def test_method_chaining_state(self):
        """Test method chaining for adding states."""
        builder = GraphBuilder()
        builder.add_state("s1", state_type="initial")
        builder.add_state("s2", state_type="final")
        
        assert builder._graph.node_count() == 2
        assert builder._graph.get_node("s1") is not None
        assert builder._graph.get_node("s2") is not None

    def test_method_chaining_commit(self):
        """Test method chaining for commits."""
        builder = GraphBuilder()
        builder.begin_commit("commit1", operation="update")
        
        assert builder._graph.node_count() == 1
        commit = builder._graph.get_node("commit1")
        assert isinstance(commit, CommitNode)
        assert commit.properties["operation"] == "update"

    def test_method_chaining_candidate(self):
        """Test method chaining for candidates."""
        builder = GraphBuilder()
        builder.add_candidate("c1", value=42)
        
        candidate = builder._graph.get_node("c1")
        assert candidate is not None
        assert candidate.properties["value"] == 42

    def test_method_chaining_mixed(self):
        """Test method chaining with multiple node types."""
        builder = GraphBuilder()
        builder.add_state("s1", state_type="initial")
        builder.add_candidate("c1", value=100)
        builder.link_proposed_from("c1", "s1")
        
        assert builder._graph.node_count() == 2
        assert builder._graph.edge_count() == 1

    def test_full_fluent_chain(self):
        """Test complete fluent API chain."""
        builder = GraphBuilder()
        builder.begin_commit("commit1", operation="balance_update")
        builder.add_state("s1", state_type="initial", balance=100)
        builder.add_candidate("c1", value=150)
        builder.link_proposed_from("c1", "s1")
        builder.add_gate_stack_run("gtr1", gate_sequence=["affordability"])
        builder.add_gate_result("gr1", "affordability", True)
        builder.link_evaluates("gr1", "c1")
        builder.link_summarizes("commit1", "gtr1")
        builder.link_applies("gtr1", "s1")
        
        assert builder._graph.node_count() == 5  # commit1, s1, c1, gtr1, gr1
        assert builder._graph.edge_count() == 4  # proposed_from, evaluates, summarizes, applies


class TestNodeCreationMethods:
    """Tests for individual node creation methods."""

    def test_begin_commit(self):
        """Test begin_commit method."""
        builder = GraphBuilder()
        builder.begin_commit("commit1", operation="test")
        
        commit = builder._graph.get_node("commit1")
        assert isinstance(commit, CommitNode)

    def test_add_emit(self):
        """Test add_emit method."""
        builder = GraphBuilder()
        builder.add_emit("emit1", "state_change", {"old": 1})
        
        emit = builder._graph.get_node("emit1")
        assert emit.node_type == "emit"

    def test_add_state(self):
        """Test add_state method."""
        builder = GraphBuilder()
        builder.add_state("s1", state_type="initial")
        
        state = builder._graph.get_node("s1")
        assert state is not None
        assert state.node_type == "state"

    def test_add_candidate(self):
        """Test add_candidate method."""
        builder = GraphBuilder()
        builder.add_candidate("c1", value=100)
        
        candidate = builder._graph.get_node("c1")
        assert candidate is not None
        assert candidate.node_type == "candidate"

    def test_add_constraint_set(self):
        """Test add_constraint_set method."""
        builder = GraphBuilder()
        constraints = ["x > 0"]
        builder.add_constraint_set("cs1", constraints)
        
        cs = builder._graph.get_node("cs1")
        assert cs is not None

    def test_add_gate_stack_run(self):
        """Test add_gate_stack_run method."""
        builder = GraphBuilder()
        sequence = ["affordability", "no_smuggling"]
        builder.add_gate_stack_run("gtr1", sequence)
        
        run = builder._graph.get_node("gtr1")
        assert run is not None

    def test_add_gate_result(self):
        """Test add_gate_result method."""
        builder = GraphBuilder()
        builder.add_gate_result("gr1", "affordability", True)
        
        result = builder._graph.get_node("gr1")
        assert result is not None

    def test_add_proof_bundle(self):
        """Test add_proof_bundle method."""
        builder = GraphBuilder()
        builder.add_proof_bundle("pb1", proof_type="zk")
        
        bundle = builder._graph.get_node("pb1")
        assert bundle is not None

    def test_add_memory_read(self):
        """Test add_memory_read method."""
        builder = GraphBuilder()
        builder.add_memory_read("read1", address=0x1000)
        
        read = builder._graph.get_node("read1")
        assert read is not None

    def test_add_memory_write(self):
        """Test add_memory_write method."""
        builder = GraphBuilder()
        builder.add_memory_write("write1", address=0x1000, value=42)
        
        write = builder._graph.get_node("write1")
        assert write is not None

    def test_add_solver_call(self):
        """Test add_solver_call method."""
        builder = GraphBuilder()
        builder.add_solver_call("call1", "z3")
        
        call = builder._graph.get_node("call1")
        assert call is not None


class TestEdgeCreationMethods:
    """Tests for edge creation methods."""

    def test_link_proposed_from(self):
        """Test link_proposed_from creates correct edge."""
        builder = GraphBuilder()
        builder.add_state("s1", state_type="initial")
        builder.add_candidate("c1", value=100)
        builder.link_proposed_from("c1", "s1")
        
        assert builder._graph.edge_count() == 1

    def test_link_evaluates(self):
        """Test link_evaluates creates correct edge."""
        builder = GraphBuilder()
        builder.add_gate_result("gr1", "affordability", True)
        builder.add_candidate("c1", value=100)
        builder.link_evaluates("gr1", "c1")
        
        assert builder._graph.edge_count() == 1

    def test_link_summarizes(self):
        """Test link_summarizes creates correct edge."""
        builder = GraphBuilder()
        builder.begin_commit("commit1")
        builder.add_gate_stack_run("gtr1")
        builder.link_summarizes("commit1", "gtr1")
        
        assert builder._graph.edge_count() == 1

    def test_link_requires_proof(self):
        """Test link_requires_proof creates correct edge."""
        builder = GraphBuilder()
        builder.begin_commit("commit1")
        builder.add_proof_bundle("pb1")
        builder.link_requires_proof("commit1", "pb1")
        
        assert builder._graph.edge_count() == 1

    def test_link_applies(self):
        """Test link_applies creates correct edge."""
        builder = GraphBuilder()
        builder.add_gate_stack_run("gtr1")
        builder.add_state("s1", state_type="initial")
        builder.link_applies("gtr1", "s1")
        
        assert builder._graph.edge_count() == 1

    def test_link_produces(self):
        """Test link_produces creates correct edge."""
        builder = GraphBuilder()
        builder.add_solver_call("call1")
        builder.add_constraint_set("cs1")
        builder.link_produces("call1", "cs1")
        
        assert builder._graph.edge_count() == 1

    def test_link_reads(self):
        """Test link_reads creates correct edge."""
        builder = GraphBuilder()
        builder.add_memory_read("read1", address=0x1000)
        builder.add_state("s1", state_type="initial")
        builder.link_reads("read1", "s1")
        
        assert builder._graph.edge_count() == 1

    def test_link_writes(self):
        """Test link_writes creates correct edge."""
        builder = GraphBuilder()
        builder.add_memory_write("write1", address=0x1000, value=42)
        builder.add_state("s1", state_type="initial")
        builder.link_writes("write1", "s1")
        
        assert builder._graph.edge_count() == 1

    def test_link_emits(self):
        """Test link_emits creates correct edge."""
        builder = GraphBuilder()
        builder.add_emit("emit1", "state_change")
        builder.add_state("s1", state_type="initial")
        builder.link_emits("emit1", "s1")
        
        assert builder._graph.edge_count() == 1

    def test_link_scheduled_after(self):
        """Test link_scheduled_after creates correct edge."""
        builder = GraphBuilder()
        builder.begin_commit("commit1", operation="first")
        builder.begin_commit("commit2", operation="second")
        builder.link_scheduled_after("commit2", "commit1")
        
        assert builder._graph.edge_count() == 1


class TestComplexGraphBuilding:
    """Tests for building complex graph structures."""

    def test_multi_commit_chain(self):
        """Test building a chain of commits."""
        builder = GraphBuilder()
        builder.begin_commit("commit1", operation="init")
        builder.add_state("s1", state_type="initial")
        builder.link_applies("commit1", "s1")
        builder.begin_commit("commit2", operation="update")
        builder.add_state("s2", state_type="intermediate")
        builder.link_applies("commit2", "s2")
        builder.link_scheduled_after("commit2", "commit1")
        
        assert builder._graph.node_count() == 4  # commit1, s1, commit2, s2
        assert builder._graph.edge_count() == 3  # applies(commit1,s1), applies(commit2,s2), scheduled_after(commit2,commit1)

    def test_complex_gate_evaluation(self):
        """Test building complex gate evaluation structure."""
        builder = GraphBuilder()
        builder.add_state("s1", state_type="initial")
        builder.add_candidate("c1", value=100)
        builder.link_proposed_from("c1", "s1")
        builder.add_gate_stack_run("gtr1", gate_sequence=["affordability", "no_smuggling"])
        builder.add_gate_result("gr1", "affordability", True)
        builder.add_gate_result("gr2", "no_smuggling", True)
        builder.link_evaluates("gr1", "c1")
        builder.link_evaluates("gr2", "c1")
        builder.begin_commit("commit1", operation="update")
        builder.link_summarizes("commit1", "gtr1")
        builder.add_proof_bundle("pb1", proof_type="zk")
        builder.link_requires_proof("commit1", "pb1")
        
        assert builder._graph.node_count() == 7  # s1, c1, gtr1, gr1, gr2, commit1, pb1
        assert builder._graph.edge_count() == 5  # proposed_from, evaluates(gr1), evaluates(gr2), summarizes, requires_proof


class TestBuildMethod:
    """Tests for the build() method."""

    def test_build_clears_builder(self):
        """Test that build allows orphaned nodes (no longer clears builder)."""
        builder = GraphBuilder()
        builder.add_state("s1", state_type="initial")
        graph = builder.build()
        
        # The build should succeed with orphaned node allowed
        assert graph.node_count() == 1
        # Builder state remains (use get_graph() to access)
        assert builder._graph.node_count() == 1

    def test_build_preserves_graph(self):
        """Test that build returns a copy of the graph."""
        builder = GraphBuilder()
        builder.add_state("s1", state_type="initial")
        builder.add_state("s2", state_type="final")
        
        graph = builder.build()
        
        # The returned graph should have 2 nodes
        assert graph.node_count() == 2
        # Builder graph should also have 2 nodes (not cleared)
        assert builder._graph.node_count() == 2
