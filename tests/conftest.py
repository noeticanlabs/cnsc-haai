"""
Pytest fixtures for GraphGML tests.

Provides common test setup and utilities for all GraphGML test modules.
"""

import pytest
import sys
import os
import importlib.util

# Add src to path
_root_dir = os.path.dirname(os.path.dirname(__file__))
_src_dir = os.path.join(_root_dir, "src")
sys.path.insert(0, _src_dir)


def import_graphgml_module(module_file: str, module_name: str):
    """Import a graphgml module directly, bypassing package init."""
    file_path = os.path.join(_src_dir, "cnsc", "haai", "graphgml", module_file)
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


# Import modules directly
types_module = import_graphgml_module("types.py", "graphgml_types")
core_module = import_graphgml_module("core.py", "graphgml_core")
builder_module = import_graphgml_module("builder.py", "graphgml_builder")

# Extract classes for fixtures
GraphNode = types_module.GraphNode
CommitNode = types_module.CommitNode
EmitNode = types_module.EmitNode
StateNode = types_module.StateNode
CandidateNode = types_module.CandidateNode
ConstraintSetNode = types_module.ConstraintSetNode
GateStackRunNode = types_module.GateStackRunNode
GateResultNode = types_module.GateResultNode
ProofBundleNode = types_module.ProofBundleNode
MemoryReadNode = types_module.MemoryReadNode
MemoryWriteNode = types_module.MemoryWriteNode
SolverCallNode = types_module.SolverCallNode
EdgeType = types_module.EdgeType

GraphGML = core_module.GraphGML
GraphQuery = core_module.GraphQuery
GraphBuilder = builder_module.GraphBuilder


@pytest.fixture
def empty_graph() -> GraphGML:
    """Create an empty GraphGML instance."""
    return GraphGML()


@pytest.fixture
def simple_graph() -> GraphGML:
    """Create a simple graph with a state and candidate."""
    graph = GraphGML()

    state = StateNode("s1", state_type="initial", balance=100)
    candidate = CandidateNode("c1", value=150)

    graph.add_node(state)
    graph.add_node(candidate)
    graph.add_edge("c1", EdgeType.PROPOSED_FROM, "s1")

    return graph


@pytest.fixture
def full_commit_graph() -> GraphGML:
    """Create a complete graph representing a commit with gates."""
    graph = GraphGML()

    # Proof bundle (must be added before edge)
    proof_bundle = ProofBundleNode("pb1", proof_type="zk_snark")
    graph.add_node(proof_bundle)

    # States
    state1 = StateNode("s1", state_type="initial", balance=100)
    state2 = StateNode("s2", state_type="final", balance=150)
    graph.add_node(state1)
    graph.add_node(state2)

    # Candidate
    candidate = CandidateNode("c1", value=150)
    graph.add_node(candidate)
    graph.add_edge("c1", EdgeType.PROPOSED_FROM, "s1")

    # Gate stack run
    gate_run = GateStackRunNode("gtr1", gate_sequence=["affordability", "no_smuggling"])
    graph.add_node(gate_run)
    graph.add_edge("gtr1", EdgeType.APPLIES, "s1")
    graph.add_edge("gtr1", EdgeType.APPLIES, "s2")

    # Gate results
    gate_result = GateResultNode("gr1", "affordability", True)
    graph.add_node(gate_result)
    graph.add_edge("gr1", EdgeType.EVALUATES, "c1")

    # Commit
    commit = CommitNode("commit1", operation="balance_update")
    graph.add_node(commit)
    graph.add_edge("commit1", EdgeType.SUMMARIZES, "gtr1")
    graph.add_edge("commit1", EdgeType.REQUIRES_PROOF, "pb1")

    return graph


@pytest.fixture
def builder() -> GraphBuilder:
    """Create a GraphBuilder instance."""
    return GraphBuilder()


@pytest.fixture
def multi_commit_graph() -> GraphGML:
    """Create a graph with multiple commits forming a chain."""
    graph = GraphGML()

    # First commit
    state1 = StateNode("s1", state_type="initial")
    commit1 = CommitNode("commit1", operation="init")
    gate_run1 = GateStackRunNode("gtr1")
    candidate1 = CandidateNode("c1", value=0)

    graph.add_node(state1)
    graph.add_node(commit1)
    graph.add_node(gate_run1)
    graph.add_node(candidate1)
    graph.add_edge("c1", EdgeType.PROPOSED_FROM, "s1")
    graph.add_edge("commit1", EdgeType.SUMMARIZES, "gtr1")
    graph.add_edge("gtr1", EdgeType.APPLIES, "s1")

    # Second commit (scheduled after first)
    state2 = StateNode("s2", state_type="intermediate")
    commit2 = CommitNode("commit2", operation="update")
    gate_run2 = GateStackRunNode("gtr2")
    candidate2 = CandidateNode("c2", value=100)

    graph.add_node(state2)
    graph.add_node(commit2)
    graph.add_node(gate_run2)
    graph.add_node(candidate2)
    graph.add_edge("c2", EdgeType.PROPOSED_FROM, "s2")
    graph.add_edge("commit2", EdgeType.SUMMARIZES, "gtr2")
    graph.add_edge("gtr2", EdgeType.APPLIES, "s2")
    graph.add_edge("commit2", EdgeType.SCHEDULED_AFTER, "commit1")

    return graph
