# GraphGML Specification

## 1. Overview and Motivation

### 1.1 Why GraphGML?

The GraphGML format represents a fundamental shift from the token-centric approach to a graph-centric model for representing computation traces, receipts, and program state. Where the token-centric approach treated traces as linear sequences of events with hash chains for integrity, GraphGML captures the inherent structural and causal relationships in computation as a directed graph. This shift enables powerful new capabilities that were impractical or impossible with linear token streams.

The token-centric model, while effective for sequential program traces, struggled with several fundamental challenges. Multi-input dependencies—where a single operation depends on multiple prior states—required artificial sequencing or auxiliary data structures to represent. Pattern matching queries over traces required linear scanning with O(n) complexity for most operations. Structural invariants, such as the requirement that a candidate value derives from exactly one prior state, were enforced through convention rather than being structurally guaranteed by the data format.

### 1.2 Key Benefits

**Multi-Input Dependencies**: GraphGML natively represents n-ary relationships between nodes. A single `GateResultNode` can connect to multiple `StateNode` inputs through edges, making the dependency structure explicit rather than encoded in opaque hash values. This enables direct graph queries to understand exactly what inputs influenced a particular computation.

**Pattern Matching Queries**: The graph structure enables efficient subgraph pattern matching using established graph algorithms. Questions like "find all commits that evaluated a candidate against state X" become direct graph traversals rather than linear searches. This enables sophisticated trace analysis, debugging, and verification workflows.

**Structural Invariants**: GraphGML encodes invariants as structural properties of the graph itself. A valid GraphGML graph must satisfy specific constraints—every CandidateNode must have exactly one incoming `proposed_from` edge, every CommitNode must have exactly one `summarizes` edge to a GateStackRunNode. These invariants can be validated mechanically, ensuring graph integrity.

**Provenance Tracking**: The explicit edge structure provides complete provenance information. Given any node, you can trace backward through `proposed_from` and `evaluates` edges to understand exactly how a value was derived. Forward tracing through `scheduled_after` edges reveals all downstream consumers of a computation.

## 2. Node Type Definitions

### 2.1 CommitNode

**Purpose**: Represents an atomic unit of state change—a receipt that captures a verified transformation from one consistent state to another. Commits are the fundamental unit of commitment in the GraphGML model, analogous to transactions in a database or blocks in a blockchain.

**Required Properties**:
- `id`: Unique identifier (UUID or hash-based)
- `timestamp`: ISO 8601 timestamp of commitment
- `hash`: Cryptographic hash of the complete commit payload

**Optional Properties**:
- `parent_hashes`: Array of parent commit hashes (for chain topology)
- `metadata`: Arbitrary key-value metadata
- `signature`: Digital signature authorizing the commit

**Constraints**:
- Must have exactly one outgoing `summarizes` edge to a GateStackRunNode
- Must have exactly one outgoing `requires_proof` edge to a ProofBundleNode (if proofs are required)
- The `scheduled_after` edges must form a valid dependency ordering

### 2.2 EmitNode

**Purpose**: Represents an output or production emission from a computation. Emits capture the observable results of program execution—values written to output streams, return values, side effects visible to external observers.

**Required Properties**:
- `id`: Unique identifier
- `value`: The emitted value (serialized representation)
- `emitter_type`: Classification of the emitter (e.g., "return", "print", "write")

**Optional Properties**:
- `encoding`: Format of the value representation
- `channel`: Output channel or stream identifier
- `metadata`: Additional emission metadata

**Constraints**:
- Must have exactly one outgoing `emits` edge to a StateNode
- May have zero or more incoming `scheduled_after` edges from GateResultNodes

### 2.3 StateNode

**Purpose**: Represents a program or system state snapshot. States capture the complete configuration of a computation at a point in time, serving as the substrate from which candidates are proposed and to which commits transition.

**Required Properties**:
- `id`: Unique identifier
- `hash`: Cryptographic hash of the state content
- `content`: Serialized state representation

**Optional Properties**:
- `state_type`: Classification (e.g., "initial", "intermediate", "final")
- `parent_state_id`: Reference to parent state (for state lineage)
- `metadata`: Additional state metadata

**Constraints**:
- May have multiple outgoing `proposed_from` edges (one per candidate derived from it)
- May have multiple incoming `emits` edges (one per emit that produced it)
- May have multiple incoming `applies` edges (one per GateStackRun that applied to it)

### 2.4 CandidateNode

**Purpose**: Represents a proposed value or state transformation before commitment. Candidates are the "before" state of a potential commit—they capture what a computation proposes to do, subject to evaluation by gates.

**Required Properties**:
- `id`: Unique identifier
- `proposed_value`: The value being proposed (serialized)

**Optional Properties**:
- `proposal_type`: Classification of the proposal (e.g., "state_update", "value_assignment")
- `source_info`: Information about where the proposal originated
- `metadata`: Additional proposal metadata

**Constraints**:
- Must have exactly one outgoing `proposed_from` edge from a StateNode
- Must have exactly one outgoing `evaluates` edge to a GateResultNode
- The proposed value must be type-compatible with the state transition being proposed

### 2.5 ConstraintSetNode

**Purpose**: Represents a gathered set of constraints collected during computation. Constraint sets capture the logical conditions that must be satisfied for a candidate to be valid—gate requirements, preconditions, invariants.

**Required Properties**:
- `id`: Unique identifier
- `constraints`: Array or serialized representation of constraints

**Optional Properties**:
- `constraint_type`: Classification of constraints (e.g., "gate_requirements", "preconditions")
- `source_gate_ids`: References to gates that contributed constraints
- `metadata`: Additional constraint metadata

**Constraints**:
- May have multiple incoming `produces` edges from SolverCallNodes
- May have multiple outgoing `evaluates` edges to GateResultNodes

### 2.6 GateStackRunNode

**Purpose**: Represents a gate evaluation execution—a complete run of a gate stack that evaluates one or more candidates. The GateStackRunNode captures the holistic evaluation context, including all gates evaluated and their interactions.

**Required Properties**:
- `id`: Unique identifier
- `gate_stack_id`: Reference to the gate stack definition
- `run_timestamp`: When the evaluation occurred

**Optional Properties**:
- `execution_mode`: How the gates were evaluated (e.g., "parallel", "sequential")
- `resource_usage`: Computational resources consumed
- `metadata`: Additional execution metadata

**Constraints**:
- May have multiple outgoing `applies` edges to StateNodes
- May have multiple outgoing `evaluates` edges to GateResultNodes
- May have exactly one incoming `summarizes` edge from a CommitNode

### 2.7 GateResultNode

**Purpose**: Represents an individual gate result—the outcome of evaluating a single gate within a gate stack. Gate results capture the binary or graded outcome of a specific constraint check.

**Required Properties**:
- `id`: Unique identifier
- `gate_id`: Reference to the gate definition
- `result`: The evaluation result (boolean or graded value)

**Optional Properties**:
- `evaluation_details`: Detailed information about the evaluation
- `reason_code`: Classification of pass/fail reason
- `metadata`: Additional result metadata

**Constraints**:
- Must have exactly one outgoing `evaluates` edge to a CandidateNode
- May have exactly one incoming `evaluates` edge from a ConstraintSetNode
- Must have exactly one incoming `applies` edge from a GateStackRunNode

### 2.8 ProofBundleNode

**Purpose**: Represents a collection of cryptographic proofs that verify the correctness of a commit. Proof bundles provide the cryptographic assurance that a commit represents a valid state transition according to the system's rules.

**Required Properties**:
- `id`: Unique identifier
- `proofs`: Array of individual proofs
- `proof_type`: Classification of proof system used

**Optional Properties**:
- `verification_key_id`: Reference to the verification key
- `proof_metadata`: Additional proof-related metadata
- `timestamp`: When the proofs were generated

**Constraints**:
- May have multiple outgoing `requires_proof` edges to CommitNodes
- All proofs must verify against the referenced commit

### 2.9 MemoryReadNode

**Purpose**: Represents a memory read operation—accessing a value from the program's state or memory. Memory reads capture data dependencies and are essential for understanding how candidates derive from prior state.

**Required Properties**:
- `id`: Unique identifier
- `address`: Memory address or identifier being read
- `value`: The value that was read

**Optional Properties**:
- `read_type`: Classification of the read (e.g., "state_access", "memory_load")
- `scope`: Scope of the read (local, shared, global)
- `metadata`: Additional read metadata

**Constraints**:
- Must have exactly one outgoing `reads` edge to a StateNode
- May be referenced by multiple CandidateNodes that depend on the read value

### 2.10 MemoryWriteNode

**Purpose**: Represents a memory write operation—modifying state or memory. Memory writes capture the mutations that lead to new states and are the primary mechanism by which candidates propose changes.

**Required Properties**:
- `id`: Unique identifier
- `address`: Memory address or identifier being written
- `value`: The value being written

**Optional Properties**:
- `write_type`: Classification of the write (e.g., "state_update", "memory_store")
- `scope`: Scope of the write (local, shared, global)
- `metadata`: Additional write metadata

**Constraints**:
- Must have exactly one outgoing `writes` edge to a StateNode
- Must be referenced by exactly one CandidateNode that proposes the write

### 2.11 SolverCallNode

**Purpose**: Represents a solver invocation—a call to an external solver (constraint solver, theorem prover, SMT solver) to determine the satisfiability or validity of constraints.

**Required Properties**:
- `id`: Unique identifier
- `solver_type`: Type of solver invoked (e.g., "SMT", "ILP", "SAT")
- `input_formula`: The formula or constraints provided to the solver

**Optional Properties**:
- `solver_config`: Configuration parameters for the solver
- `result`: Solver result (SAT/UNSAT, solution if applicable)
- `execution_time`: Time taken by the solver
- `metadata`: Additional solver call metadata

**Constraints**:
- May have exactly one outgoing `produces` edge to a ConstraintSetNode
- The result must be consistent with the constraints produced

## 3. Edge Type Definitions

### 3.1 proposed_from

**Source**: CandidateNode
**Target**: StateNode

**Semantics**: Indicates that a candidate derives from (is based on) a particular state. This edge captures the fundamental relationship between a proposed transformation and the prior state it modifies. The candidate's proposed value represents a delta or modification to the source state.

**Constraints**:
- Every CandidateNode must have exactly one incoming `proposed_from` edge
- The source StateNode must exist in the graph
- The proposed value must be type-compatible with the state structure

### 3.2 evaluates

**Source**: GateResultNode | ConstraintSetNode
**Target**: CandidateNode

**Semantics**: Indicates that a gate result or constraint set evaluates a candidate. This edge captures the relationship between evaluation (either individual gate results or aggregate constraints) and the candidate being evaluated. For GateResultNode sources, this represents individual gate evaluations; for ConstraintSetNode sources, this represents aggregate constraint satisfaction.

**Constraints**:
- A CandidateNode may have multiple incoming `evaluates` edges
- The evaluation must be performed after the candidate is proposed
- The evaluation result determines commit eligibility

### 3.3 summarizes

**Source**: CommitNode
**Target**: GateStackRunNode

**Semantics**: Indicates that a commit summarizes (captures) a particular gate stack run. This edge is the primary relationship that binds a commitment to its evaluation context—showing what gates were evaluated and what the outcomes were.

**Constraints**:
- Every CommitNode must have exactly one outgoing `summarizes` edge
- The target GateStackRunNode must exist in the graph
- All candidates referenced by the GateStackRunNode must have passing evaluations

### 3.4 requires_proof

**Source**: CommitNode
**Target**: ProofBundleNode

**Semantics**: Indicates that a commit requires a particular proof bundle for verification. This edge captures the cryptographic assurance relationship—showing what proofs must be satisfied for the commit to be considered valid.

**Constraints**:
- A CommitNode may have zero or one outgoing `requires_proof` edge (zero if proofs are not required)
- The ProofBundleNode must exist in the graph
- All proofs in the bundle must verify against the commit

### 3.5 applies

**Source**: GateStackRunNode
**Target**: StateNode

**Semantics**: Indicates that a gate stack run applies to (is evaluated against) a particular state. This edge captures the evaluation context—what state the gates were checking constraints against.

**Constraints**:
- A GateStackRunNode may have multiple outgoing `applies` edges (one per state evaluated)
- The target StateNode must exist in the graph
- The state must be consistent with candidates being evaluated

### 3.6 produces

**Source**: SolverCallNode
**Target**: ConstraintSetNode

**Semantics**: Indicates that a solver call produces a particular constraint set. This edge captures the derivation of constraints from external solver invocations.

**Constraints**:
- A SolverCallNode may have zero or one outgoing `produces` edge (zero if no constraints produced)
- The target ConstraintSetNode must exist in the graph
- The constraint set must be derived from the solver's input formula

### 3.7 reads

**Source**: MemoryReadNode
**Target**: StateNode

**Semantics**: Indicates that a memory read operation reads from a particular state. This edge captures data dependencies—showing what state values were accessed.

**Constraints**:
- Every MemoryReadNode must have exactly one outgoing `reads` edge
- The target StateNode must exist in the graph
- The read value must match the value stored in the state

### 3.8 writes

**Source**: MemoryWriteNode
**Target**: StateNode

**Semantics**: Indicates that a memory write operation writes to (creates or updates) a particular state. This edge captures state mutations—showing what state changes were proposed.

**Constraints**:
- Every MemoryWriteNode must have exactly one outgoing `writes` edge
- The target StateNode must exist in the graph (or be newly created)
- The write value must be consistent with the candidate proposing it

### 3.9 emits

**Source**: EmitNode
**Target**: StateNode

**Semantics**: Indicates that an emit operation produces (emits to) a particular state. This edge captures output production—showing what state contains emitted values.

**Constraints**:
- Every EmitNode must have exactly one outgoing `emits` edge
- The target StateNode must exist in the graph
- The emitted value must be stored in the target state

### 3.10 scheduled_after

**Source**: Any Node
**Target**: Any Node

**Semantics**: Indicates a scheduling dependency—a node must be scheduled for execution after another node completes. This edge captures the temporal ordering of operations that may execute in parallel but have dependencies. Unlike `proposed_from` which captures semantic derivation, `scheduled_after` captures execution ordering.

**Constraints**:
- The graph of `scheduled_after` edges must be acyclic (no circular dependencies)
- A node may have multiple incoming and outgoing `scheduled_after` edges
- Cycles in `scheduled_after` indicate invalid scheduling

## 4. Graph Invariants

The following invariants must hold for any valid GraphGML graph. Violations indicate malformed or invalid graphs that should be rejected by validators.

### 4.1 Node Existence

**Invariant**: All edge source and target nodes must exist in the graph.

**Formal**: For every edge e = (s, t, type) in E, there exist nodes n_s and n_t in V such that n_s.id = s and n_t.id = t.

**Reasoning**: Edges reference nodes by identifier. Valid graphs must have all referenced nodes present. This invariant ensures referential integrity.

### 4.2 Candidate Uniqueness

**Invariant**: CandidateNodes must have exactly one `proposed_from` edge.

**Formal**: For every CandidateNode c ∈ V, |{ e ∈ E | e.source = c.id ∧ e.type = "proposed_from" }| = 1.

**Reasoning**: A candidate represents a proposed transformation based on a specific prior state. Having zero `proposed_from` edges means the candidate has no basis; having more than one creates ambiguity about the source state.

### 4.3 Commit Summarization

**Invariant**: CommitNodes must have exactly one `summarizes` edge.

**Formal**: For every CommitNode c ∈ V, |{ e ∈ E | e.source = c.id ∧ e.type = "summarizes" }| = 1.

**Reasoning**: A commit must summarize a specific gate stack run—capturing what evaluation context led to the commitment. Zero edges means no evaluation context; multiple edges create ambiguity.

### 4.4 Scheduling Acyclicity

**Invariant**: The subgraph formed by `scheduled_after` edges must be acyclic.

**Formal**: There exists no non-empty cycle in the graph (V, E_scheduled) where E_scheduled = { e ∈ E | e.type = "scheduled_after" }.

**Reasoning**: Scheduling dependencies must resolve to a total or partial order. Cycles indicate circular dependencies that cannot be scheduled—no node in a cycle can execute before all others, leading to deadlock.

### 4.5 Proof Dependency Order

**Invariant**: A CommitNode cannot complete (reach terminal state) without its required ProofBundleNode being present and valid.

**Formal**: For every CommitNode c with a `requires_proof` edge to ProofBundleNode p, p must exist and all proofs in p must verify against c before c is considered complete.

**Reasoning**: Proofs provide cryptographic assurance of commit validity. A commit without its required proofs is incomplete and should not be considered finalized.

### 4.6 Evaluation Temporal Order

**Invariant**: For any edge e = (s, t, type) where type ∈ {"evaluates", "proposed_from"}, the source node s must be created before the target node t in execution order.

**Formal**: If e.source = s and e.target = t, then timestamp(s) ≤ timestamp(t).

**Reasoning**: You cannot evaluate what doesn't exist. Candidates must be proposed before they can be evaluated; states must exist before candidates can derive from them.

### 4.7 GateResult Gate Stack Membership

**Invariant**: GateResultNodes must have a parent GateStackRunNode through a chain of `applies` edges.

**Formal**: For every GateResultNode g ∈ V, there exists a GateStackRunNode r ∈ V and a path of edges of type `applies` from r to some StateNode s, and a path from s through candidate evaluation to g.

**Reasoning**: Individual gate results must exist within the context of a gate stack evaluation. This ensures evaluations are properly scoped and recorded.

## 5. Migration Guide from Token-Centric

### 5.1 TraceEvent → StateNode + EventNode Pattern

In the token-centric model, `TraceEvent` objects captured individual events in program execution. In GraphGML, events are represented through a combination of StateNodes and their connecting edges.

**Token-Centric Pattern**:
```
TraceEvent {
    event_type: "state_update",
    state_before: hash_a,
    state_after: hash_b,
    delta: {...}
}
```

**GraphGML Pattern**:
```
StateNode(id="state_a", hash=hash_a)
CandidateNode(id="cand_1", proposed_value=delta)
StateNode(id="state_b", hash=hash_b)
proposed_from(source=CandidateNode, target=StateNode)
```

The `proposed_from` edge captures the semantic relationship between the candidate (the delta) and the prior state. The new state is implicit in the candidate's acceptance.

### 5.2 TraceThread → scheduled_after Edge Path

In the token-centric model, `TraceThread` represented a sequential execution path through events. In GraphGML, thread continuity is represented through `scheduled_after` edges connecting nodes.

**Token-Centric Pattern**:
```
TraceThread {
    events: [event_1, event_2, event_3, ...],
    thread_id: "thread_123"
}
```

**GraphGML Pattern**:
```
StateNode(id="event_1")
scheduled_after(source=StateNode(id="event_1"), target=StateNode(id="event_2"))
scheduled_after(source=StateNode(id="event_2"), target=StateNode(id="event_3"))
```

The `scheduled_after` edges form a path through nodes, representing the execution order. Unlike the token-centric model where thread membership was explicit, in GraphGML thread membership is derived from graph structure.

### 5.3 Receipt Chain → CommitNode + summarizes Edges

In the token-centric model, receipt chains maintained linear sequences of commits with hash links. In GraphGML, receipts become nodes with `summarizes` edges capturing the evaluation context.

**Token-Centric Pattern**:
```
Receipt {
    commit_hash: h,
    parent_hashes: [parent_h],
    gate_results: [...],
    state_transition: {...}
}
```

**GraphGML Pattern**:
```
CommitNode(id="commit_1", hash=h)
GateStackRunNode(id="gsr_1")
CommitNode.summarizes → GateStackRunRun
GateResultNode ... → CommitNode
```

The `summarizes` edge captures what GateStackRunNode was evaluated to produce the commit. Parent hash relationships can be represented as additional metadata or separate `scheduled_after` edges between commits.

### 5.4 Hash Chains → Provenance via Edges

In the token-centric model, hash chains provided integrity through cryptographic linking. In GraphGML, provenance is captured through explicit edge relationships.

**Token-Centric Pattern**:
```
h_state_n = hash(state_n)
h_candidate = hash(candidate_n | h_state_n)
h_commit = hash(commit_n | h_candidate | h_prev_commit)
```

**GraphGML Pattern**:
```
StateNode(id="state_n")
CandidateNode(id="candidate_n")
proposed_from(source=CandidateNode, target=StateNode)
CommitNode(id="commit_n")
summarizes(source=CommitNode, target=GateStackRunNode)
```

The graph structure itself provides provenance—you can trace from any node backward through edges to understand its derivation. Hash verification can be performed on individual nodes without requiring linear chain traversal.

## 6. Examples

### 6.1 Simple Commit with Gate Evaluation

This example shows a minimal commit where a single candidate is proposed from a state, evaluated by a gate, and committed.

```gml
[
  comment="Simple commit with gate evaluation"
  StateNode(id="state_001", hash="abc123", state_type="initial")
  CandidateNode(id="cand_001", proposed_value="x = 42")
  GateStackRunNode(id="gsr_001", gate_stack_id="stack_basic")
  GateResultNode(id="gate_result_001", gate_id="gate_assert", result=true)
  CommitNode(id="commit_001", timestamp="2024-01-15T10:30:00Z", hash="def456")
  
  proposed_from(source=CandidateNode(id="cand_001"), target=StateNode(id="state_001"))
  evaluates(source=GateResultNode(id="gate_result_001"), target=CandidateNode(id="cand_001"))
  applies(source=GateStackRunNode(id="gsr_001"), target=StateNode(id="state_001"))
  evaluates(source=GateStackRunNode(id="gsr_001"), target=CandidateNode(id="cand_001"))
  summarizes(source=CommitNode(id="commit_001"), target=GateStackRunNode(id="gsr_001"))
]
```

### 6.2 Complex Multi-Input Dependency

This example shows a commit that depends on multiple prior states—a common pattern in concurrent or dataflow computations.

```gml
[
  comment="Multi-input dependency commit"
  StateNode(id="state_left", hash="left_hash", state_type="intermediate")
  StateNode(id="state_right", hash="right_hash", state_type="intermediate")
  
  MemoryReadNode(id="read_left", address="addr_x", value="value_x")
  MemoryReadNode(id="read_right", address="addr_y", value="value_y")
  reads(source=MemoryReadNode(id="read_left"), target=StateNode(id="state_left"))
  reads(source=MemoryReadNode(id="read_right"), target=StateNode(id="state_right"))
  
  CandidateNode(id="cand_combined", proposed_value="combined = value_x + value_y")
  proposed_from(source=CandidateNode(id="cand_combined"), target=StateNode(id="state_left"))
  
  ConstraintSetNode(id="constraints_001", constraints=["value_x >= 0", "value_y >= 0"])
  SolverCallNode(id="solver_001", solver_type="SMT", input_formula="...")
  produces(source=SolverCallNode(id="solver_001"), target=ConstraintSetNode(id="constraints_001"))
  evaluates(source=ConstraintSetNode(id="constraints_001"), target=CandidateNode(id="cand_combined"))
  
  GateStackRunNode(id="gsr_combined", gate_stack_id="stack_combined")
  GateResultNode(id="gate_result_001", gate_id="gate_sum_positive", result=true)
  applies(source=GateStackRunNode(id="gsr_combined"), target=StateNode(id="state_left"))
  evaluates(source=GateResultNode(id="gate_result_001"), target=CandidateNode(id="cand_combined"))
  
  CommitNode(id="commit_combined", timestamp="2024-01-15T11:00:00Z", hash="combined_hash")
  summarizes(source=CommitNode(id="commit_combined"), target=GateStackRunNode(id="gsr_combined"))
  
  scheduled_after(source=StateNode(id="state_left"), target=MemoryReadNode(id="read_left"))
  scheduled_after(source=StateNode(id="state_right"), target=MemoryReadNode(id="read_right"))
  scheduled_after(source=MemoryReadNode(id="read_left"), target=CandidateNode(id="cand_combined"))
  scheduled_after(source=MemoryReadNode(id="read_right"), target=CandidateNode(id="cand_combined"))
]
```

### 6.3 Memory Operation Graph

This example shows a detailed memory operation graph with read-write dependencies and state transitions.

```gml
[
  comment="Memory operation graph with read-write dependencies"
  StateNode(id="mem_state_001", hash="mem_h1", content="{x: 10, y: 20}")
  StateNode(id="mem_state_002", hash="mem_h2", content="{x: 10, y: 20, z: 30}")
  
  MemoryReadNode(id="mem_read_x", address="x", value="10")
  MemoryReadNode(id="mem_read_y", address="y", value="20")
  reads(source=MemoryReadNode(id="mem_read_x"), target=StateNode(id="mem_state_001"))
  reads(source=MemoryReadNode(id="mem_read_y"), target=StateNode(id="mem_state_001"))
  
  MemoryWriteNode(id="mem_write_z", address="z", value="30")
  writes(source=MemoryWriteNode(id="mem_write_z"), target=StateNode(id="mem_state_002"))
  
  CandidateNode(id="mem_cand_001", proposed_value="z = 30")
  proposed_from(source=CandidateNode(id="mem_cand_001"), target=StateNode(id="mem_state_001"))
  
  GateStackRunNode(id="gsr_mem", gate_stack_id="stack_memory")
  GateResultNode(id="gate_mem_ok", gate_id="gate_memory_safety", result=true)
  applies(source=GateStackRunNode(id="gsr_mem"), target=StateNode(id="mem_state_001"))
  evaluates(source=GateResultNode(id="gate_mem_ok"), target=CandidateNode(id="mem_cand_001"))
  
  EmitNode(id="emit_result", value="30", emitter_type="return")
  emits(source=EmitNode(id="emit_result"), target=StateNode(id="mem_state_002"))
  
  CommitNode(id="commit_mem", timestamp="2024-01-15T12:00:00Z", hash="mem_commit_h")
  summarizes(source=CommitNode(id="commit_mem"), target=GateStackRunNode(id="gsr_mem"))
  
  scheduled_after(source=StateNode(id="mem_state_001"), target=MemoryReadNode(id="mem_read_x"))
  scheduled_after(source=StateNode(id="mem_state_001"), target=MemoryReadNode(id="mem_read_y"))
  scheduled_after(source=MemoryReadNode(id="mem_read_x"), target=CandidateNode(id="mem_cand_001"))
  scheduled_after(source=MemoryReadNode(id="mem_read_y"), target=CandidateNode(id="mem_cand_001"))
  scheduled_after(source=CandidateNode(id="mem_cand_001"), target=MemoryWriteNode(id="mem_write_z"))
  scheduled_after(source=MemoryWriteNode(id="mem_write_z"), target=CommitNode(id="commit_mem"))
  scheduled_after(source=CommitNode(id="commit_mem"), target=EmitNode(id="emit_result"))
]
```

## 7. Schema Validation

GraphGML documents should be validated against the GraphGML schema to ensure they satisfy all structural invariants. The schema enforces:

1. **Node Type Constraints**: Each node type has required and optional properties defined
2. **Edge Type Constraints**: Each edge type has defined source and target node types
3. **Cardinality Constraints**: Edges with cardinality requirements (e.g., exactly one) are validated
4. **Reference Validity**: All node references in edges must point to existing nodes

Validation should occur:
- At graph construction time (when building the graph programmatically)
- At deserialization time (when loading from GML format)
- Before any query or analysis operations

## 8. Appendix: Quick Reference

### Node Types Summary

| Node Type | Purpose | Key Constraint |
|-----------|---------|----------------|
| CommitNode | Atomic state change | Exactly one `summarizes` edge |
| EmitNode | Output emission | Exactly one `emits` edge |
| StateNode | Program state snapshot | Multiple `proposed_from` possible |
| CandidateNode | Proposed value | Exactly one `proposed_from` edge |
| ConstraintSetNode | Gathered constraints | Multiple `evaluates` possible |
| GateStackRunNode | Gate evaluation run | Multiple `applies` possible |
| GateResultNode | Individual gate result | Exactly one `evaluates` edge |
| ProofBundleNode | Cryptographic proofs | Multiple `requires_proof` possible |
| MemoryReadNode | Memory read | Exactly one `reads` edge |
| MemoryWriteNode | Memory write | Exactly one `writes` edge |
| SolverCallNode | Solver invocation | Zero or one `produces` edge |

### Edge Types Summary

| Edge Type | Source → Target | Cardinality |
|-----------|-----------------|-------------|
| proposed_from | CandidateNode → StateNode | 1 per CandidateNode |
| evaluates | GateResultNode → CandidateNode | Many per CandidateNode |
| summarizes | CommitNode → GateStackRunNode | 1 per CommitNode |
| requires_proof | CommitNode → ProofBundleNode | 0-1 per CommitNode |
| applies | GateStackRunNode → StateNode | Many per GateStackRunNode |
| produces | SolverCallNode → ConstraintSetNode | 0-1 per SolverCallNode |
| reads | MemoryReadNode → StateNode | 1 per MemoryReadNode |
| writes | MemoryWriteNode → StateNode | 1 per MemoryWriteNode |
| emits | EmitNode → StateNode | 1 per EmitNode |
| scheduled_after | Any → Any | Many per node |
