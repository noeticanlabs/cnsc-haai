"""
Node Type Tests for GraphGML.

Tests for GraphNode creation, properties, and all node type subclasses.
"""

import pytest
from cnsc.haai.graphgml.types import (
    GraphNode,
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


class TestGraphNode:
    """Tests for the base GraphNode class."""

    def test_create_graph_node(self):
        """Test creating a basic GraphNode with required fields."""
        node = GraphNode("test_id", "test_type")

        assert node.node_id == "test_id"
        assert node.node_type == "test_type"
        assert node.properties == {}
        assert node.metadata == {}

    def test_create_graph_node_with_properties(self):
        """Test creating a GraphNode with properties and metadata."""
        props = {"key": "value", "count": 42}
        meta = {"source": "test"}

        node = GraphNode("test_id", "test_type", properties=props, metadata=meta)

        assert node.properties == props
        assert node.metadata == meta

    def test_graph_node_hash(self):
        """Test that GraphNode hash is based on node_id."""
        node1 = GraphNode("id1", "type1")
        node2 = GraphNode("id1", "type2")
        node3 = GraphNode("id2", "type1")

        assert hash(node1) == hash(node2)
        assert hash(node1) != hash(node3)

    def test_graph_node_equality(self):
        """Test GraphNode equality is based on node_id."""
        node1 = GraphNode("id1", "type1")
        node2 = GraphNode("id1", "type2")
        node3 = GraphNode("id2", "type1")

        assert node1 == node2
        assert node1 != node3
        assert node1 != "not a node"

    def test_graph_node_properties_modifiable(self):
        """Test that node properties can be modified after creation."""
        node = GraphNode("test_id", "test_type")

        node.properties["new_key"] = "new_value"
        assert node.properties["new_key"] == "new_value"

        node.metadata["source"] = "test"
        assert node.metadata["source"] == "test"


class TestCommitNode:
    """Tests for CommitNode."""

    def test_create_commit_node(self):
        """Test creating a CommitNode."""
        commit = CommitNode("commit1", "balance_update")

        assert commit.node_id == "commit1"
        assert commit.node_type == "commit"
        assert commit.properties["operation"] == "balance_update"

    def test_commit_node_default_operation(self):
        """Test CommitNode default operation value."""
        commit = CommitNode("commit1")

        assert commit.properties["operation"] == "unknown"


class TestEmitNode:
    """Tests for EmitNode."""

    def test_create_emit_node(self):
        """Test creating an EmitNode."""
        emit = EmitNode("emit1", "state_change", {"old": 1, "new": 2})

        assert emit.node_id == "emit1"
        assert emit.node_type == "emit"
        assert emit.properties["emit_type"] == "state_change"
        assert emit.properties["value"] == {"old": 1, "new": 2}

    def test_emit_node_default_values(self):
        """Test EmitNode default values."""
        emit = EmitNode("emit1")

        assert emit.properties["emit_type"] == "unknown"
        assert emit.properties["value"] is None


class TestStateNode:
    """Tests for StateNode."""

    def test_create_state_node(self):
        """Test creating a StateNode."""
        state = StateNode("s1", "initial", balance=100)

        assert state.node_id == "s1"
        assert state.node_type == "state"
        assert state.properties["state_type"] == "initial"
        assert state.properties["balance"] == 100

    def test_state_node_default_type(self):
        """Test StateNode default state_type."""
        state = StateNode("s1")

        assert state.properties["state_type"] == "unknown"


class TestCandidateNode:
    """Tests for CandidateNode."""

    def test_create_candidate_node(self):
        """Test creating a CandidateNode."""
        candidate = CandidateNode("c1", value=42)

        assert candidate.node_id == "c1"
        assert candidate.node_type == "candidate"
        assert candidate.properties["value"] == 42

    def test_candidate_node_with_complex_value(self):
        """Test CandidateNode with complex value types."""
        complex_value = {"nested": {"key": "value"}, "list": [1, 2, 3]}
        candidate = CandidateNode("c1", value=complex_value)

        assert candidate.properties["value"] == complex_value


class TestConstraintSetNode:
    """Tests for ConstraintSetNode."""

    def test_create_constraint_set_node(self):
        """Test creating a ConstraintSetNode."""
        constraints = ["x > 0", "y < 100"]
        cs = ConstraintSetNode("cs1", constraints)

        assert cs.node_id == "cs1"
        assert cs.node_type == "constraint_set"
        assert cs.properties["constraints"] == constraints

    def test_constraint_set_node_default_constraints(self):
        """Test ConstraintSetNode default constraints."""
        cs = ConstraintSetNode("cs1")

        assert cs.properties["constraints"] == []


class TestGateStackRunNode:
    """Tests for GateStackRunNode."""

    def test_create_gate_stack_run_node(self):
        """Test creating a GateStackRunNode."""
        sequence = ["affordability", "no_smuggling"]
        run = GateStackRunNode("gtr1", sequence)

        assert run.node_id == "gtr1"
        assert run.node_type == "gate_stack_run"
        assert run.properties["gate_sequence"] == sequence

    def test_gate_stack_run_node_default_sequence(self):
        """Test GateStackRunNode default gate_sequence."""
        run = GateStackRunNode("gtr1")

        assert run.properties["gate_sequence"] == []


class TestGateResultNode:
    """Tests for GateResultNode."""

    def test_create_gate_result_node_passed(self):
        """Test creating a GateResultNode for a passing gate."""
        result = GateResultNode("gr1", "affordability", True)

        assert result.node_id == "gr1"
        assert result.node_type == "gate_result"
        assert result.properties["gate_type"] == "affordability"
        assert result.properties["passed"] is True

    def test_create_gate_result_node_failed(self):
        """Test creating a GateResultNode for a failing gate."""
        result = GateResultNode("gr1", "affordability", False)

        assert result.properties["passed"] is False


class TestProofBundleNode:
    """Tests for ProofBundleNode."""

    def test_create_proof_bundle_node(self):
        """Test creating a ProofBundleNode."""
        bundle = ProofBundleNode("pb1", "zk_snark")

        assert bundle.node_id == "pb1"
        assert bundle.node_type == "proof_bundle"
        assert bundle.properties["proof_type"] == "zk_snark"

    def test_proof_bundle_node_default_type(self):
        """Test ProofBundleNode default proof_type."""
        bundle = ProofBundleNode("pb1")

        assert bundle.properties["proof_type"] == "unknown"


class TestMemoryReadNode:
    """Tests for MemoryReadNode."""

    def test_create_memory_read_node(self):
        """Test creating a MemoryReadNode."""
        read = MemoryReadNode("read1", address=0x1000)

        assert read.node_id == "read1"
        assert read.node_type == "memory_read"
        assert read.properties["address"] == 0x1000
        assert read.properties["operation"] == "read"


class TestMemoryWriteNode:
    """Tests for MemoryWriteNode."""

    def test_create_memory_write_node(self):
        """Test creating a MemoryWriteNode."""
        write = MemoryWriteNode("write1", address=0x1000, value=42)

        assert write.node_id == "write1"
        assert write.node_type == "memory_write"
        assert write.properties["address"] == 0x1000
        assert write.properties["value"] == 42
        assert write.properties["operation"] == "write"


class TestSolverCallNode:
    """Tests for SolverCallNode."""

    def test_create_solver_call_node(self):
        """Test creating a SolverCallNode."""
        call = SolverCallNode("call1", "z3")

        assert call.node_id == "call1"
        assert call.node_type == "solver_call"
        assert call.properties["solver_type"] == "z3"

    def test_solver_call_node_default_type(self):
        """Test SolverCallNode default solver_type."""
        call = SolverCallNode("call1")

        assert call.properties["solver_type"] == "unknown"


class TestNodeIdUniqueness:
    """Tests for node ID uniqueness requirements."""

    def test_different_id_different_hash(self):
        """Test that nodes with different IDs have different hashes."""
        node1 = GraphNode("id1", "type")
        node2 = GraphNode("id2", "type")

        assert hash(node1) != hash(node2)


class TestEdgeType:
    """Tests for EdgeType enumeration."""

    def test_edge_type_values(self):
        """Test all edge types have correct string values."""
        assert EdgeType.PROPOSED_FROM.value == "proposed_from"
        assert EdgeType.EVALUATES.value == "evaluates"
        assert EdgeType.SUMMARIZES.value == "summarizes"
        assert EdgeType.REQUIRES_PROOF.value == "requires_proof"
        assert EdgeType.APPLIES.value == "applies"
        assert EdgeType.PRODUCES.value == "produces"
        assert EdgeType.READS.value == "reads"
        assert EdgeType.WRITES.value == "writes"
        assert EdgeType.EMITS.value == "emits"
        assert EdgeType.SCHEDULED_AFTER.value == "scheduled_after"

    def test_edge_type_is_string(self):
        """Test that EdgeType members are strings."""
        assert isinstance(EdgeType.PROPOSED_FROM, str)
