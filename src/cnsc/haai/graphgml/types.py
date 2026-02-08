"""
GraphGML Type Definitions

Graph-based node and edge types for representing execution traces,
proofs, and constraint systems in a graph structure.

This module defines the core types used by the GraphGML layer,
enabling a shift from token/trace-centric GML to a graph-based representation.
"""

from dataclasses import dataclass, field
from typing import Any, Optional
from enum import Enum


class EdgeType(str, Enum):
    """Enumeration of edge types in GraphGML."""
    PROPOSED_FROM = "proposed_from"
    EVALUATES = "evaluates"
    SUMMARIZES = "summarizes"
    REQUIRES_PROOF = "requires_proof"
    APPLIES = "applies"
    PRODUCES = "produces"
    READS = "reads"
    WRITES = "writes"
    EMITS = "emits"
    SCHEDULED_AFTER = "scheduled_after"


@dataclass
class GraphNode:
    """
    Base class for all GraphGML nodes.
    
    Attributes:
        node_id: Unique identifier for this node
        node_type: Type classification (e.g., 'commit', 'state', 'candidate')
        properties: Key-value pairs representing node attributes
        metadata: Additional metadata for provenance and auditing
    """
    node_id: str
    node_type: str
    properties: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def __hash__(self) -> int:
        return hash(self.node_id)
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GraphNode):
            return False
        return self.node_id == other.node_id


@dataclass
class CommitNode(GraphNode):
    """
    Represents a commit operation in the execution trace.
    
    Commits represent atomic operations that modify state and
    produce receipts for later verification.
    """
    def __init__(self, commit_id: str, operation: str = "unknown", **kwargs):
        super().__init__(
            node_id=commit_id,
            node_type="commit",
            properties={"operation": operation, **kwargs.get("properties", {})},
            metadata=kwargs.get("metadata", {})
        )


@dataclass
class EmitNode(GraphNode):
    """
    Represents an emit operation that produces output.
    
    Emits are used to signal side effects, outputs, or state
    transitions to external observers.
    """
    def __init__(self, emit_id: str, emit_type: str = "unknown", value: Any = None, **kwargs):
        props = {"emit_type": emit_type, "value": value, **kwargs.get("properties", {})}
        super().__init__(
            node_id=emit_id,
            node_type="emit",
            properties=props,
            metadata=kwargs.get("metadata", {})
        )


@dataclass
class StateNode(GraphNode):
    """
    Represents program state at a point in execution.
    
    States capture the complete or partial state of the computation,
    including variable bindings, stack contents, and heap references.
    """
    def __init__(self, state_id: str, state_type: str = "unknown", **kwargs):
        props = {"state_type": state_type, **kwargs.get("properties", {})}
        super().__init__(
            node_id=state_id,
            node_type="state",
            properties=props,
            metadata=kwargs.get("metadata", {})
        )


@dataclass
class CandidateNode(GraphNode):
    """
    Represents a candidate value under consideration.
    
    Candidates are values that have been proposed but not yet
    validated by gate evaluation. They may be accepted or rejected.
    """
    def __init__(self, candidate_id: str, value: Any, **kwargs):
        props = {"value": value, **kwargs.get("properties", {})}
        super().__init__(
            node_id=candidate_id,
            node_type="candidate",
            properties=props,
            metadata=kwargs.get("metadata", {})
        )


@dataclass
class ConstraintSetNode(GraphNode):
    """
    Represents a set of constraints in the constraint system.
    
    Constraint sets define the conditions that must be satisfied
    for a proof to be valid.
    """
    def __init__(self, constraint_id: str, constraints: list[Any] = None, **kwargs):
        props = {"constraints": constraints or [], **kwargs.get("properties", {})}
        super().__init__(
            node_id=constraint_id,
            node_type="constraint_set",
            properties=props,
            metadata=kwargs.get("metadata", {})
        )


@dataclass
class GateStackRunNode(GraphNode):
    """
    Represents the execution of a gate stack.
    
    Gate stack runs encapsulate the execution of multiple gates
    in sequence, with their individual results and transitions.
    """
    def __init__(self, run_id: str, gate_sequence: list[str] = None, **kwargs):
        props = {"gate_sequence": gate_sequence or [], **kwargs.get("properties", {})}
        super().__init__(
            node_id=run_id,
            node_type="gate_stack_run",
            properties=props,
            metadata=kwargs.get("metadata", {})
        )


@dataclass
class GateResultNode(GraphNode):
    """
    Represents the result of gate evaluation.
    
    Gate results capture whether a gate passed or failed, along
    with any diagnostic information.
    """
    def __init__(self, result_id: str, gate_type: str, passed: bool, **kwargs):
        props = {"gate_type": gate_type, "passed": passed, **kwargs.get("properties", {})}
        super().__init__(
            node_id=result_id,
            node_type="gate_result",
            properties=props,
            metadata=kwargs.get("metadata", {})
        )


@dataclass
class ProofBundleNode(GraphNode):
    """
    Represents a bundle of proofs supporting a claim.
    
    Proof bundles contain the evidence needed to verify claims
    made during execution.
    """
    def __init__(self, bundle_id: str, proof_type: str = "unknown", **kwargs):
        props = {"proof_type": proof_type, **kwargs.get("properties", {})}
        super().__init__(
            node_id=bundle_id,
            node_type="proof_bundle",
            properties=props,
            metadata=kwargs.get("metadata", {})
        )


@dataclass
class MemoryReadNode(GraphNode):
    """
    Represents a memory read operation.
    
    Memory reads capture the location accessed, the value read,
    and the ordering guarantees in effect.
    """
    def __init__(self, read_id: str, address: Any, **kwargs):
        props = {"address": address, "operation": "read", **kwargs.get("properties", {})}
        super().__init__(
            node_id=read_id,
            node_type="memory_read",
            properties=props,
            metadata=kwargs.get("metadata", {})
        )


@dataclass
class MemoryWriteNode(GraphNode):
    """
    Represents a memory write operation.
    
    Memory writes capture the location written, the value written,
    and any ordering guarantees.
    """
    def __init__(self, write_id: str, address: Any, value: Any, **kwargs):
        props = {"address": address, "value": value, "operation": "write", **kwargs.get("properties", {})}
        super().__init__(
            node_id=write_id,
            node_type="memory_write",
            properties=props,
            metadata=kwargs.get("metadata", {})
        )


@dataclass
class SolverCallNode(GraphNode):
    """
    Represents an invocation of a constraint solver.
    
    Solver calls capture the constraints provided, the solution
    found (if any), and the solver's response.
    """
    def __init__(self, call_id: str, solver_type: str = "unknown", **kwargs):
        props = {"solver_type": solver_type, **kwargs.get("properties", {})}
        super().__init__(
            node_id=call_id,
            node_type="solver_call",
            properties=props,
            metadata=kwargs.get("metadata", {})
        )


# Type aliases for convenience
Node = GraphNode | CommitNode | EmitNode | StateNode | CandidateNode | ConstraintSetNode | GateStackRunNode | GateResultNode | ProofBundleNode | MemoryReadNode | MemoryWriteNode | SolverCallNode

__all__ = [
    "EdgeType",
    "GraphNode",
    "CommitNode",
    "EmitNode",
    "StateNode",
    "CandidateNode",
    "ConstraintSetNode",
    "GateStackRunNode",
    "GateResultNode",
    "ProofBundleNode",
    "MemoryReadNode",
    "MemoryWriteNode",
    "SolverCallNode",
    "Node",
]
