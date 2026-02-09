"""
Trace to GraphGML Conversion Tool

Converts token/trace-centric GML data into GraphGML format.

This module provides:
- TraceToGraphConverter: Main converter class for transforming GML traces,
  receipts, and PhaseLoom threads into GraphGML graph structures.

Usage:
    python tools/trace_to_graph.py input.json output.json --format trace
    python tools/trace_to_graph.py receipts.json output.json --format receipt
    python tools/trace_to_graph.py phaseloom.json output.json --format phaseloom
"""

from cnsc.haai.graphgml import types, builder, core
from cnsc.haai.gml import trace, receipts, phaseloom
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import json
import argparse


class TraceToGraphConverter:
    """
    Converter for transforming token/trace-centric GML data into GraphGML format.
    
    This converter handles:
    - TraceEvent → StateNode conversion
    - TraceThread → sequence of StateNodes with scheduled_after edges
    - Receipt → CommitNode + ProofBundleNode
    - HashChain → ProofBundleNode
    - Gate evaluation → GateResultNode
    - PhaseLoomThread → complete GraphGML
    
    Example:
        >>> converter = TraceToGraphConverter()
        >>> graph = converter.convert_traceloom(thread)
        >>> graph.save("output.json")
    """
    
    def __init__(self) -> None:
        """Initialize the converter with a new GraphGML builder."""
        self._graph = core.GraphGML()
        self._node_counter = 0
    
    def _generate_node_id(self, prefix: str = "node") -> str:
        """Generate a unique node ID."""
        self._node_counter += 1
        return f"{prefix}_{self._node_counter}"
    
    def convert_trace_event(self, event: trace.TraceEvent) -> types.StateNode:
        """
        Convert a TraceEvent to a StateNode.
        
        Preserves: event_id, timestamp, level, event_type, message, details.
        Creates new node_id = f"state_{event.event_id}"
        
        Args:
            event: TraceEvent to convert
            
        Returns:
            StateNode representing the trace event
        """
        node_id = f"state_{event.event_id}"
        
        properties = {
            "event_id": event.event_id,
            "timestamp": event.timestamp.isoformat() if isinstance(event.timestamp, datetime) else event.timestamp,
            "level": event.level.to_string() if hasattr(event.level, 'to_string') else str(event.level),
            "event_type": event.event_type,
            "message": event.message,
            "details": event.details,
            "parent_event_id": event.parent_event_id,
            "causality_chain": event.causality_chain,
            "thread_id": event.thread_id,
            "span_id": event.span_id,
            "coherence_before": event.coherence_before,
            "coherence_after": event.coherence_after,
        }
        
        # Filter out None values
        properties = {k: v for k, v in properties.items() if v is not None}
        
        state_node = types.StateNode(
            state_id=node_id,
            state_type="trace_event",
            properties=properties,
            metadata={
                "source_module": event.source_module,
                "source_function": event.source_function,
                "source_line": event.source_line,
            }
        )
        
        self._graph.add_node(state_node)
        return state_node
    
    def convert_trace_thread(self, thread: trace.TraceThread) -> List[types.GraphNode]:
        """
        Convert entire TraceThread to graph representation.
        
        Creates StateNode for each event and adds scheduled_after edges
        between consecutive events to preserve execution order.
        
        Args:
            thread: TraceThread to convert
            
        Returns:
            List of created GraphNode instances
        """
        created_nodes: List[types.GraphNode] = []
        previous_event_id: Optional[str] = None
        
        for event in thread.events:
            state_node = self.convert_trace_event(event)
            created_nodes.append(state_node)
            
            # Add scheduled_after edge from previous event
            if previous_event_id is not None:
                self._graph.add_edge(
                    f"state_{previous_event_id}",
                    types.EdgeType.SCHEDULED_AFTER.value,
                    state_node.node_id
                )
            
            previous_event_id = event.event_id
        
        return created_nodes
    
    def convert_receipt(self, receipt: receipts.Receipt) -> Tuple[types.CommitNode, types.ProofBundleNode]:
        """
        Convert Receipt to CommitNode + ProofBundleNode.
        
        Extracts:
        - receipt_id → CommitNode.node_id (prefix: "commit_")
        - timestamp, step_type, decision, details → CommitNode properties
        - previous_receipt_id → requires_proof edge to previous CommitNode
        - hash chain info → ProofBundleNode
        
        Args:
            receipt: Receipt to convert
            
        Returns:
            Tuple of (CommitNode, ProofBundleNode)
        """
        # Create CommitNode
        commit_node = types.CommitNode(
            commit_id=f"commit_{receipt.receipt_id}",
            operation=receipt.content.step_type.name if hasattr(receipt.content.step_type, 'name') else str(receipt.content.step_type),
            properties={
                "receipt_id": receipt.receipt_id,
                "timestamp": receipt.provenance.timestamp.isoformat() if isinstance(receipt.provenance.timestamp, datetime) else str(receipt.provenance.timestamp),
                "step_type": receipt.content.step_type.name if hasattr(receipt.content.step_type, 'name') else str(receipt.content.step_type),
                "decision": receipt.content.decision.name if hasattr(receipt.content.decision, 'name') else str(receipt.content.decision),
                "input_hash": receipt.content.input_hash,
                "output_hash": receipt.content.output_hash,
                "coherence_before": receipt.content.coherence_before,
                "coherence_after": receipt.content.coherence_after,
                "source": receipt.provenance.source,
                "phase": receipt.provenance.phase,
            },
            metadata={
                "version": receipt.version,
                "chain_hash": receipt.chain_hash,
            }
        )
        
        self._graph.add_node(commit_node)
        
        # Create ProofBundleNode for hash chain
        proof_bundle = types.ProofBundleNode(
            bundle_id=f"proof_{receipt.receipt_id}",
            proof_type="receipt_chain",
            properties={
                "chain_length": 1,
                "verification_function": "sha256",
            }
        )
        
        self._graph.add_node(proof_bundle)
        
        # Add requires_proof edge from commit to proof bundle
        self._graph.add_edge(
            commit_node.node_id,
            types.EdgeType.REQUIRES_PROOF.value,
            proof_bundle.node_id
        )
        
        # Add requires_proof edge to previous receipt if exists
        if receipt.previous_receipt_id:
            previous_commit_id = f"commit_{receipt.previous_receipt_id}"
            self._graph.add_edge(
                commit_node.node_id,
                types.EdgeType.REQUIRES_PROOF.value,
                previous_commit_id
            )
        
        return commit_node, proof_bundle
    
    def convert_hash_chain(self, chain: receipts.HashChain) -> types.ProofBundleNode:
        """
        Convert HashChain to ProofBundleNode.
        
        Stores:
        - chain_id, head_hash, length, verification_function
        
        Args:
            chain: HashChain to convert
            
        Returns:
            ProofBundleNode representing the hash chain
        """
        bundle_id = self._generate_node_id("hash_chain")
        
        bundle = types.ProofBundleNode(
            bundle_id=bundle_id,
            proof_type="hash_chain",
            properties={
                "chain_id": bundle_id,
                "head_hash": chain.get_tip(),
                "length": chain.get_length(),
                "genesis_hash": chain.get_root(),
                "verification_function": "sha256",
            }
        )
        
        self._graph.add_node(bundle)
        return bundle
    
    def convert_gate_result(
        self, 
        gate_type: str, 
        passed: bool, 
        value: Any = None, 
        reason: Optional[str] = None,
        result_id: Optional[str] = None
    ) -> types.GateResultNode:
        """
        Convert gate evaluation result to GateResultNode.
        
        Args:
            gate_type: Type of gate (e.g., "affordability", "safety")
            passed: Whether the gate passed
            value: Optional gate value
            reason: Optional reason for pass/fail
            result_id: Optional custom result ID
            
        Returns:
            GateResultNode representing the gate evaluation
        """
        node_id = result_id or self._generate_node_id("gate_result")
        
        result_node = types.GateResultNode(
            result_id=node_id,
            gate_type=gate_type,
            passed=passed,
            properties={
                "value": value,
                "reason": reason,
            }
        )
        
        self._graph.add_node(result_node)
        return result_node
    
    def convert_gate_stack_run(
        self, 
        stack_id: str, 
        gate_sequence: List[str], 
        results: List[types.GateResultNode]
    ) -> types.GateStackRunNode:
        """
        Convert gate stack execution to GateStackRunNode.
        
        Links individual GateResultNodes to the stack run node.
        
        Args:
            stack_id: Unique identifier for the stack run
            gate_sequence: List of gate types in execution order
            results: List of GateResultNode instances
            
        Returns:
            GateStackRunNode with linked results
        """
        stack_node = types.GateStackRunNode(
            run_id=f"gate_stack_{stack_id}",
            gate_sequence=gate_sequence,
            properties={
                "result_count": len(results),
            }
        )
        
        self._graph.add_node(stack_node)
        
        # Link each result to the stack run
        for result in results:
            self._graph.add_edge(
                result.node_id,
                types.EdgeType.EVALUATES.value,
                stack_node.node_id
            )
        
        return stack_node
    
    def convert_traceloom(self, traceloom: phaseloom.PhaseLoomThread) -> core.GraphGML:
        """
        Convert entire PhaseLoom thread to GraphGML.
        
        Processes all events, receipts, and dependencies to build
        a complete graph with all nodes and edges.
        
        Args:
            traceloom: PhaseLoomThread to convert
            
        Returns:
            GraphGML instance containing the converted graph
        """
        # Create thread node
        thread_node_id = f"thread_{traceloom.thread_id}"
        
        # Add thread state node
        thread_node = types.StateNode(
            state_id=thread_node_id,
            state_type="phaseloom_thread",
            properties={
                "thread_id": traceloom.thread_id,
                "name": traceloom.name,
                "loom_id": traceloom.loom_id,
                "state": traceloom.state.to_string() if hasattr(traceloom.state, 'to_string') else str(traceloom.state),
                "depends_on": traceloom.depends_on,
                "produced_for": traceloom.produced_for,
                "coherence_level": traceloom.coherence_level,
                "progress": traceloom.progress,
            }
        )
        
        self._graph.add_node(thread_node)
        
        # Add dependency edges
        for dep_id in traceloom.depends_on:
            dep_node_id = f"thread_{dep_id}"
            self._graph.add_edge(
                thread_node_id,
                types.EdgeType.PROPOSED_FROM.value,
                dep_node_id
            )
        
        return self._graph
    
    def convert_receipt_list(self, receipts_list: List[receipts.Receipt]) -> core.GraphGML:
        """
        Convert a list of receipts to a connected graph.
        
        Creates edges between sequential receipts in the chain.
        
        Args:
            receipts_list: List of receipts to convert
            
        Returns:
            GraphGML with all receipts and chain edges
        """
        previous_node_id: Optional[str] = None
        
        for receipt in receipts_list:
            commit_node, proof_bundle = self.convert_receipt(receipt)
            
            if previous_node_id is not None:
                # Add edge from previous commit to current
                self._graph.add_edge(
                    previous_node_id,
                    types.EdgeType.REQUIRES_PROOF.value,
                    commit_node.node_id
                )
            
            previous_node_id = commit_node.node_id
        
        return self._graph
    
    def get_graph(self) -> core.GraphGML:
        """Get the converted graph."""
        return self._graph
    
    def save(self, filepath: str) -> None:
        """
        Save the graph to a JSON file.
        
        Args:
            filepath: Path to save the graph JSON
        """
        output = {
            "nodes": [
                {
                    "node_id": node.node_id,
                    "node_type": node.node_type,
                    "properties": node.properties,
                    "metadata": node.metadata,
                }
                for node in self._graph.nodes.values()
            ],
            "edges": list(self._graph.edges),
            "metadata": {
                "version": "1.0",
                "converted_from": "trace",
                "node_count": len(self._graph.nodes),
                "edge_count": len(self._graph.edges),
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(output, f, indent=2)
    
    @staticmethod
    def load(input_path: str) -> Any:
        """
        Load GML data from a JSON file.
        
        Args:
            input_path: Path to the input JSON file
            
        Returns:
            Loaded GML data structure
        """
        with open(input_path, 'r') as f:
            data = json.load(f)
        
        # Determine type and load accordingly
        if "events" in data:
            # TraceThread format
            return trace.TraceThread.from_dict(data)
        elif "receipt_id" in data:
            # Single receipt format
            return receipts.Receipt.from_dict(data)
        elif "thread_id" in data and "loom_id" in data:
            # PhaseLoomThread format
            return phaseloom.PhaseLoomThread.from_dict(data)
        else:
            # Assume list of receipts
            return [receipts.Receipt.from_dict(r) for r in data]


def convert_file(input_path: str, output_path: str, format: str = "trace") -> None:
    """
    Convert a GML file to GraphGML format.
    
    Args:
        input_path: Path to input GML file (JSON)
        output_path: Path to output GraphGML file (JSON)
        format: Format of input file ("trace", "receipt", "phaseloom")
    """
    converter = TraceToGraphConverter()
    
    # Load input data
    data = converter.load(input_path)
    
    # Convert based on format
    if format == "trace":
        if isinstance(data, trace.TraceThread):
            converter.convert_trace_thread(data)
        else:
            raise ValueError(f"Expected TraceThread for format 'trace', got {type(data)}")
    
    elif format == "receipt":
        if isinstance(data, list):
            converter.convert_receipt_list(data)
        elif isinstance(data, receipts.Receipt):
            converter.convert_receipt(data)
        else:
            raise ValueError(f"Expected Receipt or list for format 'receipt', got {type(data)}")
    
    elif format == "phaseloom":
        if isinstance(data, phaseloom.PhaseLoomThread):
            converter.convert_traceloom(data)
        else:
            raise ValueError(f"Expected PhaseLoomThread for format 'phaseloom', got {type(data)}")
    
    else:
        raise ValueError(f"Unknown format: {format}")
    
    # Save output
    converter.save(output_path)
    print(f"Converted {input_path} -> {output_path}")
    print(f"Nodes: {len(converter.get_graph().nodes)}, Edges: {len(converter.get_graph().edges)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert token/trace GML to GraphGML format"
    )
    parser.add_argument(
        "input", 
        help="Input trace/receipt file (JSON)"
    )
    parser.add_argument(
        "output", 
        help="Output GraphGML file (JSON)"
    )
    parser.add_argument(
        "--format",
        choices=["trace", "receipt", "phaseloom"],
        default="trace",
        help="Input format (default: trace)"
    )
    
    args = parser.parse_args()
    
    convert_file(args.input, args.output, args.format)
