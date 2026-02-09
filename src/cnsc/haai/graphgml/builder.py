"""
GraphGML Builder Module

Builder pattern for constructing GraphGML graphs.
Provides a fluent interface for building complex graph structures
with proper semantics for commit, state, candidate, and gate relationships.
"""

from typing import Any, Callable, Generator
from contextlib import contextmanager

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
from cnsc.haai.graphgml.core import GraphGML


class GraphBuilder:
    """
    Builder for constructing GraphGML graphs.
    
    Provides a fluent interface for adding nodes and edges with
    proper semantics for tracking the execution trace.
    
    Example:
        >>> builder = GraphBuilder()
        >>> graph = (builder
        ...     .begin_commit("c1", operation="update_balance")
        ...     .add_state("s1", state_type="initial", balance=100)
        ...     .add_candidate("cand1", value=150)
        ...     .link_proposed_from("cand1", "s1")
        ...     .add_gate_result("g1", "affordability", True)
        ...     .link_evaluates("g1", "cand1")
        ...     .build())
    """
    
    def __init__(self) -> None:
        """Initialize an empty graph builder."""
        self._graph = GraphGML()
        self._current_context: dict[str, str] = {}
    
    def begin_commit(
        self, 
        commit_id: str, 
        operation: str = "unknown",
        **kwargs
    ) -> "GraphBuilder":
        """
        Start a commit node.
        
        Args:
            commit_id: Unique identifier for this commit
            operation: Type of operation being committed
            **kwargs: Additional properties for the commit node
            
        Returns:
            Self for method chaining
        """
        commit = CommitNode(commit_id, operation, **kwargs)
        self._graph.add_node(commit)
        self._current_context["current_commit"] = commit_id
        return self
    
    def add_state(
        self, 
        state_id: str, 
        state_type: str = "unknown",
        **kwargs
    ) -> "GraphBuilder":
        """
        Add a state node.
        
        Args:
            state_id: Unique identifier for this state
            state_type: Type of state (initial, intermediate, final)
            **kwargs: Additional properties for the state node
            
        Returns:
            Self for method chaining
        """
        state = StateNode(state_id, state_type, **kwargs)
        self._graph.add_node(state)
        self._current_context["last_state"] = state_id
        return self
    
    def add_candidate(
        self, 
        candidate_id: str, 
        value: Any,
        **kwargs
    ) -> "GraphBuilder":
        """
        Add a candidate node.
        
        Args:
            candidate_id: Unique identifier for this candidate
            value: The candidate value being proposed
            **kwargs: Additional properties for the candidate node
            
        Returns:
            Self for method chaining
        """
        candidate = CandidateNode(candidate_id, value, **kwargs)
        self._graph.add_node(candidate)
        self._current_context["last_candidate"] = candidate_id
        return self
    
    def add_constraint_set(
        self, 
        constraint_id: str, 
        constraints: list[Any] = None,
        **kwargs
    ) -> "GraphBuilder":
        """
        Add a constraint set node.
        
        Args:
            constraint_id: Unique identifier for this constraint set
            constraints: List of constraints
            **kwargs: Additional properties
            
        Returns:
            Self for method chaining
        """
        constraint = ConstraintSetNode(constraint_id, constraints, **kwargs)
        self._graph.add_node(constraint)
        return self
    
    def add_gate_stack_run(
        self, 
        run_id: str, 
        gate_sequence: list[str] = None,
        **kwargs
    ) -> "GraphBuilder":
        """
        Add a gate stack run node.
        
        Args:
            run_id: Unique identifier for this run
            gate_sequence: List of gate types in sequence
            **kwargs: Additional properties
            
        Returns:
            Self for method chaining
        """
        run = GateStackRunNode(run_id, gate_sequence, **kwargs)
        self._graph.add_node(run)
        self._current_context["current_gate_run"] = run_id
        return self
    
    def add_gate_result(
        self, 
        result_id: str, 
        gate_type: str, 
        passed: bool,
        **kwargs
    ) -> "GraphBuilder":
        """
        Add a gate result node.
        
        Args:
            result_id: Unique identifier for this result
            gate_type: Type of gate evaluated
            passed: Whether the gate passed
            **kwargs: Additional properties
            
        Returns:
            Self for method chaining
        """
        result = GateResultNode(result_id, gate_type, passed, **kwargs)
        self._graph.add_node(result)
        self._current_context["last_gate_result"] = result_id
        return self
    
    def add_proof_bundle(
        self, 
        bundle_id: str, 
        proof_type: str = "unknown",
        **kwargs
    ) -> "GraphBuilder":
        """
        Add a proof bundle node.
        
        Args:
            bundle_id: Unique identifier for this proof bundle
            proof_type: Type of proof contained
            **kwargs: Additional properties
            
        Returns:
            Self for method chaining
        """
        bundle = ProofBundleNode(bundle_id, proof_type, **kwargs)
        self._graph.add_node(bundle)
        return self
    
    def add_emit(
        self, 
        emit_id: str, 
        emit_type: str = "unknown", 
        value: Any = None,
        **kwargs
    ) -> "GraphBuilder":
        """
        Add an emit node.
        
        Args:
            emit_id: Unique identifier for this emit
            emit_type: Type of emit operation
            value: Value being emitted
            **kwargs: Additional properties
            
        Returns:
            Self for method chaining
        """
        emit = EmitNode(emit_id, emit_type, value, **kwargs)
        self._graph.add_node(emit)
        return self
    
    def add_memory_read(
        self, 
        read_id: str, 
        address: Any,
        **kwargs
    ) -> "GraphBuilder":
        """
        Add a memory read node.
        
        Args:
            read_id: Unique identifier for this read
            address: Memory address being read
            **kwargs: Additional properties
            
        Returns:
            Self for method chaining
        """
        read = MemoryReadNode(read_id, address, **kwargs)
        self._graph.add_node(read)
        return self
    
    def add_memory_write(
        self, 
        write_id: str, 
        address: Any, 
        value: Any,
        **kwargs
    ) -> "GraphBuilder":
        """
        Add a memory write node.
        
        Args:
            write_id: Unique identifier for this write
            address: Memory address being written
            value: Value being written
            **kwargs: Additional properties
            
        Returns:
            Self for method chaining
        """
        write = MemoryWriteNode(write_id, address, value, **kwargs)
        self._graph.add_node(write)
        return self
    
    def add_solver_call(
        self, 
        call_id: str, 
        solver_type: str = "unknown",
        **kwargs
    ) -> "GraphBuilder":
        """
        Add a solver call node.
        
        Args:
            call_id: Unique identifier for this solver call
            solver_type: Type of solver being invoked
            **kwargs: Additional properties
            
        Returns:
            Self for method chaining
        """
        call = SolverCallNode(call_id, solver_type, **kwargs)
        self._graph.add_node(call)
        return self
    
    # Edge creation methods
    
    def link_proposed_from(self, candidate_id: str, state_id: str) -> "GraphBuilder":
        """
        Create a 'proposed_from' edge from candidate to state.
        
        Args:
            candidate_id: Candidate node ID
            state_id: State node ID
            
        Returns:
            Self for method chaining
        """
        self._graph.add_edge(candidate_id, EdgeType.PROPOSED_FROM, state_id)
        return self
    
    def link_evaluates(self, result_id: str, candidate_id: str) -> "GraphBuilder":
        """
        Create an 'evaluates' edge from gate result to candidate.
        
        Args:
            result_id: Gate result node ID
            candidate_id: Candidate node ID
            
        Returns:
            Self for method chaining
        """
        self._graph.add_edge(result_id, EdgeType.EVALUATES, candidate_id)
        return self
    
    def link_summarizes(self, commit_id: str, run_id: str) -> "GraphBuilder":
        """
        Create a 'summarizes' edge from commit to gate stack run.
        
        Args:
            commit_id: Commit node ID
            run_id: Gate stack run node ID
            
        Returns:
            Self for method chaining
        """
        self._graph.add_edge(commit_id, EdgeType.SUMMARIZES, run_id)
        return self
    
    def link_requires_proof(self, commit_id: str, bundle_id: str) -> "GraphBuilder":
        """
        Create a 'requires_proof' edge from commit to proof bundle.
        
        Args:
            commit_id: Commit node ID
            bundle_id: Proof bundle node ID
            
        Returns:
            Self for method chaining
        """
        self._graph.add_edge(commit_id, EdgeType.REQUIRES_PROOF, bundle_id)
        return self
    
    def link_applies(self, run_id: str, state_id: str) -> "GraphBuilder":
        """
        Create an 'applies' edge from gate stack run to state.
        
        Args:
            run_id: Gate stack run node ID
            state_id: State node ID
            
        Returns:
            Self for method chaining
        """
        self._graph.add_edge(run_id, EdgeType.APPLIES, state_id)
        return self
    
    def link_produces(self, call_id: str, constraint_id: str) -> "GraphBuilder":
        """
        Create a 'produces' edge from solver call to constraint set.
        
        Args:
            call_id: Solver call node ID
            constraint_id: Constraint set node ID
            
        Returns:
            Self for method chaining
        """
        self._graph.add_edge(call_id, EdgeType.PRODUCES, constraint_id)
        return self
    
    def link_reads(self, read_id: str, state_id: str) -> "GraphBuilder":
        """
        Create a 'reads' edge from memory read to state.
        
        Args:
            read_id: Memory read node ID
            state_id: State node ID
            
        Returns:
            Self for method chaining
        """
        self._graph.add_edge(read_id, EdgeType.READS, state_id)
        return self
    
    def link_writes(self, write_id: str, state_id: str) -> "GraphBuilder":
        """
        Create a 'writes' edge from memory write to state.
        
        Args:
            write_id: Memory write node ID
            state_id: State node ID
            
        Returns:
            Self for method chaining
        """
        self._graph.add_edge(write_id, EdgeType.WRITES, state_id)
        return self
    
    def link_emits(self, emit_id: str, state_id: str) -> "GraphBuilder":
        """
        Create an 'emits' edge from emit to state.
        
        Args:
            emit_id: Emit node ID
            state_id: State node ID
            
        Returns:
            Self for method chaining
        """
        self._graph.add_edge(emit_id, EdgeType.EMITS, state_id)
        return self
    
    def link_scheduled_after(self, source_id: str, target_id: str) -> "GraphBuilder":
        """
        Create a 'scheduled_after' edge between nodes.
        
        Args:
            source_id: Source node ID
            target_id: Target node ID
            
        Returns:
            Self for method chaining
        """
        self._graph.add_edge(source_id, EdgeType.SCHEDULED_AFTER, target_id)
        return self
    
    def add_edge(self, source_id: str, edge_type: str, target_id: str) -> "GraphBuilder":
        """
        Add an arbitrary edge between nodes.
        
        Args:
            source_id: Source node ID
            edge_type: Type of edge
            target_id: Target node ID
            
        Returns:
            Self for method chaining
        """
        self._graph.add_edge(source_id, edge_type, target_id)
        return self
    
    # Context management
    
    def with_commit(self, commit_id: str) -> "GraphBuilder":
        """
        Set the current commit context.
        
        Args:
            commit_id: Commit node ID to set as current
            
        Returns:
            Self for method chaining
        """
        if commit_id not in self._graph.nodes:
            raise ValueError(f"Commit node '{commit_id}' not found")
        self._current_context["current_commit"] = commit_id
        return self
    
    def get_context(self, key: str, default: str = None) -> str | None:
        """
        Get a value from the current context.
        
        Args:
            key: Context key to retrieve
            default: Default value if key not found
            
        Returns:
            Context value or default
        """
        return self._current_context.get(key, default)
    
    def build(self, strict: bool = False) -> GraphGML:
        """
        Finalize and return the constructed graph.
        
        Args:
            strict: If True, fail on orphaned nodes. If False (default), allow them.
        
        Returns:
            The constructed GraphGML instance
            
        Raises:
            ValueError: If graph validation fails
        """
        violations = self._graph.validate_invariants(allow_orphaned=not strict)
        if violations:
            raise ValueError(
                f"Graph validation failed:\n  - " + "\n  - ".join(violations)
            )
        return self._graph
    
    def validate(self) -> list[str]:
        """
        Validate the current graph.
        
        Returns:
            List of validation violations (empty if valid)
        """
        return self._graph.validate_invariants()
    
    def get_graph(self) -> GraphGML:
        """
        Get the current graph without finalizing.
        
        Returns:
            The current GraphGML instance
        """
        return self._graph


@contextmanager
def graph_builder() -> Generator[GraphBuilder, None, None]:
    """
    Context manager for atomic graph building.
    
    Example:
        >>> with graph_builder() as builder:
        ...     builder.begin_commit("c1")
        ...     builder.add_state("s1")
        ...     graph = builder.build()
    """
    builder = GraphBuilder()
    try:
        yield builder
    except Exception:
        # Reset builder on error
        builder._graph.clear()
        raise


def create_simple_trace(
    commit_id: str,
    state_id: str,
    candidate_id: str,
    result_id: str,
    commit_operation: str = "unknown",
    candidate_value: Any = None,
    gate_type: str = "unknown",
    gate_passed: bool = True,
    **kwargs
) -> GraphGML:
    """
    Convenience function to create a simple commit-candidate-result trace.
    
    Args:
        commit_id: Commit node identifier
        state_id: State node identifier
        candidate_id: Candidate node identifier
        result_id: Gate result node identifier
        commit_operation: Operation type for commit
        candidate_value: Value for candidate node
        gate_type: Type of gate evaluated
        gate_passed: Whether gate passed
        **kwargs: Additional properties for any node
        
    Returns:
        Complete GraphGML with all nodes and edges connected
    """
    with graph_builder() as builder:
        builder.begin_commit(commit_id, commit_operation, **kwargs)
        builder.add_state(state_id, **kwargs)
        builder.add_candidate(candidate_id, candidate_value, **kwargs)
        builder.link_proposed_from(candidate_id, state_id)
        builder.add_gate_result(result_id, gate_type, gate_passed, **kwargs)
        builder.link_evaluates(result_id, candidate_id)
        return builder.build()


__all__ = ["GraphBuilder", "graph_builder", "create_simple_trace"]
