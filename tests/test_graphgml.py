"""
Main test file for GraphGML module.

This file provides a simple entry point for running GraphGML tests.
Run with: pytest tests/test_graphgml.py -v
"""

import pytest


def test_types_import():
    """Test that types module can be imported."""
    from cnsc.haai.graphgml.types import (
        GraphNode,
        EdgeType,
        CommitNode,
        StateNode,
        CandidateNode,
    )

    assert GraphNode is not None
    assert EdgeType is not None


def test_core_import():
    """Test that core module can be imported."""
    from cnsc.haai.graphgml.core import GraphGML, GraphQuery

    assert GraphGML is not None
    assert GraphQuery is not None


def test_builder_import():
    """Test that builder module can be imported."""
    from cnsc.haai.graphgml.builder import GraphBuilder

    assert GraphBuilder is not None


def test_basic_graph_operations():
    """Test basic graph creation and operations."""
    from cnsc.haai.graphgml.core import GraphGML
    from cnsc.haai.graphgml.types import StateNode, EdgeType

    graph = GraphGML()

    # Add nodes
    s1 = StateNode("s1", "initial")
    s2 = StateNode("s2", "final")

    graph.add_node(s1)
    graph.add_node(s2)

    assert graph.node_count() == 2

    # Add edge
    graph.add_edge("s1", EdgeType.SCHEDULED_AFTER, "s2")

    assert graph.edge_count() == 1

    # Get neighbors
    neighbors = graph.get_neighbors("s1", EdgeType.SCHEDULED_AFTER)
    assert len(neighbors) == 1
    assert neighbors[0].node_id == "s2"


def test_builder_fluent_api():
    """Test GraphBuilder fluent API."""
    from cnsc.haai.graphgml.builder import GraphBuilder
    from cnsc.haai.graphgml.types import EdgeType

    graph = (
        GraphBuilder()
        .add_state("s1", state_type="initial")
        .add_state("s2", state_type="final")
        .link_scheduled_after("s2", "s1")
        .build()
    )

    assert graph.node_count() == 2
    assert graph.edge_count() == 1


def test_query_operations():
    """Test GraphQuery operations."""
    from cnsc.haai.graphgml.builder import GraphBuilder
    from cnsc.haai.graphgml.core import GraphQuery
    from cnsc.haai.graphgml.types import EdgeType

    graph = (
        GraphBuilder()
        .add_state("s1", state_type="initial")
        .add_candidate("c1", value=100)
        .link_scheduled_after("c1", "s1")
        .build()
    )

    query = GraphQuery(graph)

    # Find nodes by type
    states = graph.find_nodes_by_type("state")
    assert len(states) == 1

    # Find path
    paths = query.find_path("c1", "s1", [EdgeType.SCHEDULED_AFTER.value])
    assert len(paths) == 1


def test_invariant_validation():
    """Test graph invariant validation."""
    from cnsc.haai.graphgml.core import GraphGML
    from cnsc.haai.graphgml.types import StateNode, EdgeType

    graph = GraphGML()

    # Add isolated node
    graph.add_node(StateNode("orphan", "isolated"))

    # In strict mode, orphaned nodes are detected
    violations = graph.validate_invariants(allow_orphaned=False)
    assert len(violations) == 1
    assert "orphan" in violations[0]


def test_graph_copy():
    """Test graph copying."""
    from cnsc.haai.graphgml.core import GraphGML
    from cnsc.haai.graphgml.types import StateNode, EdgeType

    graph = GraphGML()
    graph.add_node(StateNode("s1", "initial"))
    graph.add_node(StateNode("s2", "final"))
    graph.add_edge("s1", EdgeType.SCHEDULED_AFTER, "s2")

    # Copy
    copy = graph.copy()

    assert copy.node_count() == 2
    assert copy.edge_count() == 1

    # Verify independence
    copy.add_node(StateNode("s3", "extra"))
    assert graph.node_count() == 2
    assert copy.node_count() == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
