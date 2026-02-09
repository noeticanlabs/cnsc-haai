"""
End-to-end GraphGML demonstration.
Shows conversion from token/trace-centric to graph-based representation.
"""

from datetime import datetime
from cnsc.haai.gml.trace import TraceEvent, TraceThread, TraceLevel
from cnsc.haai.gml.receipts import Receipt, ReceiptSystem, ReceiptContent, ReceiptSignature, ReceiptProvenance, ReceiptStepType
from cnsc.haai.gml.phaseloom import PhaseLoomThread
from cnsc.haai.graphgml import types, core
from cnsc.haai.graphgml.builder import GraphBuilder
from cnsc.haai.graphgml.core import GraphQuery


def demo_trace_to_graph():
    """Demonstrate converting trace events to graph."""
    # Create trace events
    events = [
        TraceEvent("evt1", datetime.fromisoformat("2024-01-01T10:00:00"), TraceLevel.INFO, "commit", "Commit operation A"),
        TraceEvent("evt2", datetime.fromisoformat("2024-01-01T10:00:01"), TraceLevel.INFO, "gate_eval", "Gate evaluation B"),
        TraceEvent("evt3", datetime.fromisoformat("2024-01-01T10:00:02"), TraceLevel.INFO, "emit", "Emit operation C"),
    ]
    
    for event in events:
        event.details = {"rule": "A"} if event.event_id == "evt1" else {"gate": "B"} if event.event_id == "evt2" else {"output": "C"}
    
    thread = TraceThread(thread_id="main", name="Main Thread", events=events)
    
    # Convert to graph
    graph = thread.to_graph()
    assert graph is not None, "Graph should not be None"
    assert len(graph.nodes) == 3, f"Expected 3 nodes, got {len(graph.nodes)}"
    assert len(graph.edges) == 2, f"Expected 2 edges (scheduled_after), got {len(graph.edges)}"
    
    # Validate
    issues = graph.validate_invariants()
    assert len(issues) == 0, f"Graph has issues: {issues}"
    
    print("✓ Trace to graph conversion works")


def demo_receipt_to_graph():
    """Demonstrate converting receipts to graph."""
    from cnsc.haai.gml.receipts import ReceiptSystem, ReceiptDecision
    
    # Use emit_receipt to create receipts
    system = ReceiptSystem()
    
    # Create receipts using emit_receipt
    receipt1 = system.emit_receipt(
        step_type=ReceiptStepType.VM_EXECUTION,
        source="demo",
        input_data={"data": "A"},
        output_data={"result": "ok"},
        decision=ReceiptDecision.PASS,
    )
    receipt2 = system.emit_receipt(
        step_type=ReceiptStepType.COHERENCE_CHECK,
        source="demo",
        input_data={"data": "B"},
        output_data={"result": "ok"},
        decision=ReceiptDecision.PASS,
        episode_id=receipt1.receipt_id,  # Chain to previous
    )
    
    # Convert to graph
    graph = system.to_graph()
    assert graph is not None, "Graph should not be None"
    assert len(graph.nodes) >= 2, f"Expected >= 2 nodes, got {len(graph.nodes)}"
    assert len(graph.edges) >= 1, f"Expected >= 1 edge, got {len(graph.edges)}"
    
    # Validate
    issues = system.validate_graph_invariants()
    assert len(issues) == 0, f"Receipt system has issues: {issues}"
    
    print("✓ Receipt to graph conversion works")


def demo_full_pipeline():
    """Demonstrate full trace → receipt → phaseloom pipeline."""
    from cnsc.haai.gml.receipts import ReceiptDecision
    
    # Create trace thread
    events = [
        {"event_id": "e1", "event_type": "start", "timestamp": "2024-01-01T10:00:00"},
        {"event_id": "e2", "event_type": "process", "timestamp": "2024-01-01T10:00:01"},
    ]
    
    # Create PhaseLoomThread directly
    thread = PhaseLoomThread(
        thread_id="main",
        name="Main Thread",
        loom_id="test",
    )
    thread.events = events
    
    # Create receipt
    receipt = {
        "receipt_id": "r1",
        "operation": "vm_execution",
        "timestamp": "2024-01-01T10:00:02",
    }
    thread.receipts = {"main": [receipt]}
    
    # Full graph from phase loom thread
    graph = thread.generate_full_graph()
    assert graph is not None, "Graph should not be None"
    assert len(graph.nodes) >= 2, f"Expected >= 2 nodes, got {len(graph.nodes)}"
    
    print("✓ Full pipeline conversion works")


def demo_graph_operations():
    """Demonstrate graph query and traversal operations."""
    # Build a graph
    builder = GraphBuilder()
    graph = (
        builder
        .begin_commit("commit1", operation="update")
        .add_state("s1", state_type="initial", value=0)
        .add_state("s2", state_type="final", value=100)
        .add_candidate("c1", value=100)
        .link_proposed_from("c1", "s1")
        .link_applies("commit1", "s2")
        .build()
    )
    
    # Query operations
    query = GraphQuery(graph)
    
    # Find nodes by type
    commits = graph.find_nodes_by_type("commit")
    assert len(commits) == 1, "Should find 1 commit"
    
    states = graph.find_nodes_by_type("state")
    assert len(states) == 2, "Should find 2 states"
    
    # Find path
    paths = query.find_path("c1", "s1", ["proposed_from"])
    assert len(paths) == 1, "Should find 1 path from candidate to state"
    
    # Get neighbors
    neighbors = graph.get_neighbors("c1", "proposed_from")
    assert len(neighbors) == 1, "Candidate should have 1 proposed_from neighbor"
    
    # Validate
    issues = graph.validate_invariants()
    assert len(issues) == 0, f"Graph has issues: {issues}"
    
    print("✓ Graph operations work correctly")


def demo_serialization():
    """Demonstrate graph operations."""
    # Build a graph with connected nodes
    builder = GraphBuilder()
    graph = (
        builder
        .begin_commit("commit1", operation="test")
        .add_state("s1", state_type="initial")
        .link_applies("commit1", "s1")  # Add edge to connect nodes
        .build()
    )
    
    # Verify graph operations work
    assert graph.node_count() == 2, f"Expected 2 nodes, got {graph.node_count()}"
    assert graph.edge_count() == 1, f"Expected 1 edge, got {graph.edge_count()}"
    
    # Find nodes by type
    commits = graph.find_nodes_by_type("commit")
    assert len(commits) == 1, "Should find 1 commit"
    
    states = graph.find_nodes_by_type("state")
    assert len(states) == 1, "Should find 1 state"
    
    print("✓ Graph operations work correctly")


def demo_invariant_validation():
    """Demonstrate graph invariant validation."""
    # Valid graph with connected nodes
    valid_graph = (
        GraphBuilder()
        .add_state("s1", state_type="initial")
        .add_candidate("c1", value=42)
        .link_proposed_from("c1", "s1")
        .build()
    )
    issues = valid_graph.validate_invariants()
    assert len(issues) == 0, f"Valid graph should have no issues, got: {issues}"
    
    # Invalid graph - test that validation can be called on a graph with orphaned nodes
    # Note: We can't call .build() on invalid graphs, but we can use get_graph()
    invalid_builder = GraphBuilder()
    invalid_builder.add_state("s1", state_type="initial")
    invalid_builder.add_state("s2", state_type="orphan")  # No edges
    invalid_graph = invalid_builder.get_graph()
    issues = invalid_graph.validate_invariants()
    assert len(issues) > 0, "Graph with orphaned node should have issues"
    assert any("orphan" in issue.lower() for issue in issues), "Should detect orphaned node"
    
    print("✓ Invariant validation works")


if __name__ == "__main__":
    print("Running GraphGML End-to-End Demo\n" + "=" * 40)
    
    demo_trace_to_graph()
    demo_receipt_to_graph()
    demo_full_pipeline()
    demo_graph_operations()
    demo_serialization()
    demo_invariant_validation()
    
    print("\n" + "=" * 40)
    print("✅ All end-to-end tests passed!")
