"""
Conversion Tests for GraphGML.

Tests for converting traces, receipts, and PhaseLoom structures to GraphGML format.
"""

import pytest
from cnsc.haai.graphgml.builder import GraphBuilder
from cnsc.haai.graphgml.core import GraphGML
from cnsc.haai.graphgml.types import (
    CommitNode,
    StateNode,
    CandidateNode,
    GateStackRunNode,
    GateResultNode,
    ProofBundleNode,
    EdgeType,
)


class TestTraceEventConversion:
    """Tests for converting trace events to graph structures."""

    def test_convert_state_event(self):
        """Test converting a state event to a StateNode."""
        builder = GraphBuilder()

        # Simulate trace event
        trace_event = {
            "event_type": "state",
            "state_id": "s1",
            "state_type": "initial",
            "data": {"balance": 100},
        }

        # Convert using builder pattern
        graph = builder.add_state(
            trace_event["state_id"],
            state_type=trace_event["state_type"],
            **trace_event.get("data", {}),
        ).build()

        state = graph.get_node("s1")
        assert state is not None
        assert state.node_type == "state"
        assert state.properties["state_type"] == "initial"
        assert state.properties["balance"] == 100

    def test_convert_candidate_event(self):
        """Test converting a candidate event to a CandidateNode."""
        builder = GraphBuilder()

        trace_event = {"event_type": "candidate", "candidate_id": "c1", "value": 150}

        graph = builder.add_candidate(
            trace_event["candidate_id"], value=trace_event["value"]
        ).build()

        candidate = graph.get_node("c1")
        assert candidate is not None
        assert candidate.node_type == "candidate"
        assert candidate.properties["value"] == 150

    def test_convert_proposed_from_relationship(self):
        """Test converting proposed_from relationship."""
        builder = GraphBuilder()

        graph = (
            builder.add_state("s1", state_type="initial")
            .add_candidate("c1", value=100)
            .link_proposed_from("c1", "s1")
            .build()
        )

        candidates = graph.find_nodes_by_type("candidate")
        assert len(candidates) == 1

        # Verify edge exists
        edges = graph.edges
        assert len(edges) == 1
        assert edges[0] == ("c1", EdgeType.PROPOSED_FROM.value, "s1")


class TestReceiptToGraphConversion:
    """Tests for converting receipts to graph structures."""

    def test_convert_receipt_commit(self):
        """Test converting a receipt commit to graph."""
        builder = GraphBuilder()

        receipt = {"receipt_id": "r1", "commit_id": "commit1", "operation": "balance_update"}

        graph = builder.begin_commit(receipt["commit_id"], operation=receipt["operation"]).build()

        commit = graph.get_node("commit1")
        assert commit is not None
        assert commit.node_type == "commit"
        assert commit.properties["operation"] == "balance_update"

    def test_convert_receipt_with_proof_bundle(self):
        """Test converting receipt with proof bundle."""
        builder = GraphBuilder()

        receipt = {"commit_id": "commit1", "proof_bundle_id": "pb1", "proof_type": "zk_snark"}

        graph = (
            builder.begin_commit(receipt["commit_id"])
            .add_proof_bundle(receipt["proof_bundle_id"], proof_type=receipt["proof_type"])
            .link_requires_proof(receipt["commit_id"], receipt["proof_bundle_id"])
            .build()
        )

        commit = graph.get_node("commit1")
        proof_bundle = graph.get_node("pb1")

        assert commit is not None
        assert proof_bundle is not None
        assert proof_bundle.properties["proof_type"] == "zk_snark"

    def test_convert_receipt_chain(self):
        """Test converting a chain of receipts."""
        builder = GraphBuilder()

        receipts = [
            {"id": "r1", "commit_id": "commit1", "prev": None},
            {"id": "r2", "commit_id": "commit2", "prev": "r1"},
            {"id": "r3", "commit_id": "commit3", "prev": "r2"},
        ]

        for receipt in receipts:
            builder.begin_commit(receipt["commit_id"])
            if receipt["prev"]:
                # In a real scenario, this would create hash chain links
                # For testing, we use scheduled_after to show order
                builder.link_scheduled_after(
                    receipt["commit_id"], receipt["prev"].replace("r", "commit")
                )

        graph = builder.build()

        assert graph.node_count() == 3
        assert graph.edge_count() == 2


class TestPhaseLoomToGraphConversion:
    """Tests for converting PhaseLoom threads to graph structures."""

    def test_convert_phase_loom_thread(self):
        """Test converting a PhaseLoom thread to graph."""
        builder = GraphBuilder()

        thread = {
            "thread_id": "thread1",
            "states": [
                {"state_id": "s1", "state_type": "initial"},
                {"state_id": "s2", "state_type": "intermediate"},
                {"state_id": "s3", "state_type": "final"},
            ],
            "transitions": [
                {"from": "s1", "to": "s2", "gate": "affordability"},
                {"from": "s2", "to": "s3", "gate": "no_smuggling"},
            ],
        }

        # Add states
        for state in thread["states"]:
            builder.add_state(state["state_id"], state_type=state["state_type"])

        # Add transitions as edges
        for transition in thread["transitions"]:
            # Create gate stack run for each transition
            gate_run_id = f"gtr_{transition['from']}_{transition['to']}"
            builder.add_gate_stack_run(gate_run_id, gate_sequence=[transition["gate"]])
            builder.link_applies(gate_run_id, transition["from"])

        graph = builder.build()

        assert graph.node_count() == 5  # 3 states + 2 gate runs
        assert graph.edge_count() == 2  # 2 applies edges (one per gate run)

    def test_convert_coupled_threads(self):
        """Test converting coupled PhaseLoom threads."""
        builder = GraphBuilder()

        coupled_threads = {
            "thread_a": {
                "states": [{"state_id": "sa1", "state_type": "initial"}],
                "transitions": [],
            },
            "thread_b": {
                "states": [{"state_id": "sb1", "state_type": "initial"}],
                "transitions": [],
            },
        }

        for thread_id, thread_data in coupled_threads.items():
            for state in thread_data["states"]:
                builder.add_state(
                    state["state_id"], state_type=state["state_type"], thread=thread_id
                )

        graph = builder.build()

        assert graph.node_count() == 2

        # Verify states have thread metadata
        sa1 = graph.get_node("sa1")
        sb1 = graph.get_node("sb1")
        assert sa1.properties.get("thread") == "thread_a"
        assert sb1.properties.get("thread") == "thread_b"


class TestConversionPreservesSemantics:
    """Tests that conversion preserves graph semantics."""

    def test_candidate_proposed_from_semantics(self):
        """Test that candidate -> state edge semantics are preserved."""
        builder = GraphBuilder()

        graph = (
            builder.add_state("s1", state_type="initial", balance=100)
            .add_candidate("c1", value=150)
            .link_proposed_from("c1", "s1")
            .build()
        )

        # Query: get all candidates proposed from state s1 using correct reverse key
        candidates = graph.get_neighbors("s1", f"rev_{EdgeType.PROPOSED_FROM.value}")

        assert len(candidates) == 1
        assert candidates[0].node_id == "c1"
        assert candidates[0].properties["value"] == 150

    def test_commit_summarizes_semantics(self):
        """Test that commit -> gate_run edge semantics are preserved."""
        builder = GraphBuilder()

        graph = (
            builder.add_gate_stack_run("gtr1", gate_sequence=["affordability"])
            .begin_commit("commit1", operation="update")
            .link_summarizes("commit1", "gtr1")
            .build()
        )

        # Query: find commits that summarize a gate run using correct reverse key
        commits = graph.get_neighbors("gtr1", f"rev_{EdgeType.SUMMARIZES.value}")

        assert len(commits) == 1
        assert commits[0].node_id == "commit1"

    def test_gate_result_evaluates_semantics(self):
        """Test that gate_result -> candidate edge semantics are preserved."""
        builder = GraphBuilder()

        graph = (
            builder.add_candidate("c1", value=100)
            .add_gate_result("gr1", "affordability", True)
            .link_evaluates("gr1", "c1")
            .build()
        )

        # Query: find gate results that evaluate a candidate using correct reverse key
        results = graph.get_neighbors("c1", f"rev_{EdgeType.EVALUATES.value}")

        assert len(results) == 1
        assert results[0].node_id == "gr1"
        assert results[0].properties["passed"] is True

    def test_commit_requires_proof_semantics(self):
        """Test that commit -> proof_bundle edge semantics are preserved."""
        builder = GraphBuilder()

        graph = (
            builder.add_proof_bundle("pb1", proof_type="zk")
            .begin_commit("commit1", operation="update")
            .link_requires_proof("commit1", "pb1")
            .build()
        )

        # Query: find proof bundles required by a commit
        bundles = graph.get_neighbors("commit1", EdgeType.REQUIRES_PROOF)

        assert len(bundles) == 1
        assert bundles[0].node_id == "pb1"


class TestConversionFromStructuredData:
    """Tests for converting from structured data formats."""

    def test_convert_from_dict_list(self):
        """Test converting from list of dictionaries."""
        data = [
            {"type": "state", "id": "s1", "props": {"state_type": "initial"}},
            {"type": "state", "id": "s2", "props": {"state_type": "final"}},
            {"type": "candidate", "id": "c1", "props": {"value": 100}},
        ]

        builder = GraphBuilder()
        for item in data:
            if item["type"] == "state":
                builder.add_state(item["id"], **item["props"])
            elif item["type"] == "candidate":
                builder.add_candidate(item["id"], **item["props"])

        graph = builder.build()

        assert graph.node_count() == 3
        assert graph.get_node("s1") is not None
        assert graph.get_node("s2") is not None
        assert graph.get_node("c1") is not None

    def test_convert_with_edge_definitions(self):
        """Test converting with edge definitions."""
        nodes = [
            {"type": "state", "id": "s1", "props": {"state_type": "initial"}},
            {"type": "candidate", "id": "c1", "props": {"value": 100}},
        ]
        edges = [{"from": "c1", "type": "proposed_from", "to": "s1"}]

        builder = GraphBuilder()
        for node in nodes:
            if node["type"] == "state":
                builder.add_state(node["id"], **node["props"])
            elif node["type"] == "candidate":
                builder.add_candidate(node["id"], **node["props"])

        for edge in edges:
            edge_type = getattr(EdgeType, edge["type"].upper(), edge["type"])
            builder._graph.add_edge(edge["from"], edge_type, edge["to"])

        graph = builder.build()

        assert graph.edge_count() == 1
        assert graph.edges[0] == ("c1", "proposed_from", "s1")


class TestConversionEdgeCases:
    """Tests for edge cases in conversion."""

    def test_convert_empty_trace(self):
        """Test converting an empty trace."""
        builder = GraphBuilder()
        graph = builder.build()

        assert graph.node_count() == 0
        assert graph.edge_count() == 0

    def test_convert_single_node(self):
        """Test converting a trace with single node."""
        builder = GraphBuilder()
        graph = builder.add_state("s1", state_type="initial").build()

        assert graph.node_count() == 1
        assert graph.edge_count() == 0

    def test_convert_node_with_self_loop(self):
        """Test converting a node with self-loop edge."""
        builder = GraphBuilder()
        builder.add_state("s1", state_type="initial")
        # Self-loop edge (edge from node to itself)
        builder._graph.add_edge("s1", EdgeType.SCHEDULED_AFTER, "s1")
        graph = builder.build()

        assert graph.node_count() == 1
        assert graph.edge_count() == 1
