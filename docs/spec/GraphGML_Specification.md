# GraphGML Specification

## Overview

GraphGML is a graph-based representation for the Graph Merkle Language (GML) layer. It shifts from a token/trace-centric approach to a structured graph model that explicitly represents:

- **Execution traces** as sequences of state transitions
- **Proof structures** as bundles of evidence
- **Constraint systems** as sets of logical conditions
- **Scheduling dependencies** as explicit ordering constraints

### Motivation

The original GML implementation uses linear traces with tokens representing checkpoints and receipts. While functional, this approach has limitations:

1. **Poor query support** - Linear traces require sequential scanning
2. **Implicit relationships** - Dependencies are encoded in token order, not structure
3. **Limited auditability** - Proof chains require reconstruction from hashes
4. **No native pattern matching** - Complex queries require custom logic

GraphGML addresses these by making relationships explicit and queryable.

## Node Types

### Base Node (`GraphNode`)

All nodes share common attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `node_id` | `str` | Unique identifier |
| `node_type` | `str` | Type classification |
| `properties` | `dict` | Key-value attributes |
| `metadata` | `dict` | Provenance and auditing data |

### CommitNode

Represents atomic commit operations that modify state.

**Properties:**
- `operation`: Type of operation (e.g., "update_balance", "transfer_funds")

**Semantics:** A commit represents a point of no-return where state transitions become permanent and receipt-worthy.

### EmitNode

Represents output emissions to external systems or observers.

**Properties:**
- `emit_type`: Type of emission (e.g., "event", "log", "side_effect")
- `value`: The emitted value

**Semantics:** Emits signal state changes to external observers without necessarily modifying internal state.

### StateNode

Represents program state at a point in execution.

**Properties:**
- `state_type`: Classification (e.g., "initial", "intermediate", "final")

**Semantics:** States capture the complete or partial computation context, including variable bindings and heap references.

### CandidateNode

Represents candidate values pending gate evaluation.

**Properties:**
- `value`: The candidate value

**Semantics:** Candidates are proposed values that must pass gate evaluation before becoming committed state.

### ConstraintSetNode

Represents sets of constraints for proof verification.

**Properties:**
- `constraints`: List of constraint objects

**Semantics:** Constraint sets define conditions that must be satisfied for a proof to be valid.

### GateStackRunNode

Represents execution of a sequence of gates.

**Properties:**
- `gate_sequence`: Ordered list of gate types

**Semantics:** Gate stack runs encapsulate multiple gates executed in sequence, with their individual results.

### GateResultNode

Represents the outcome of gate evaluation.

**Properties:**
- `gate_type`: Type of gate evaluated
- `passed`: Boolean indicating success/failure

**Semantics:** Gate results determine whether candidates become valid state.

### ProofBundleNode

Represents bundles of supporting evidence.

**Properties:**
- `proof_type`: Classification of proof content

**Semantics:** Proof bundles contain the evidence needed to verify claims made during execution.

### MemoryReadNode / MemoryWriteNode

Represents memory operations.

**Properties:**
- `address`: Memory location accessed
- `value` (write only): Value being written

**Semantics:** Memory operations capture data flow and state mutations.

### SolverCallNode

Represents invocations of constraint solvers.

**Properties:**
- `solver_type`: Solver implementation used

**Semantics:** Solver calls capture constraint solving attempts and their results.

## Edge Types

| Edge Type | Source → Target | Description |
|-----------|-----------------|-------------|
| `proposed_from` | Candidate → State | Candidate derived from state |
| `evaluates` | GateResult → Candidate | Gate validates candidate |
| `summarizes` | Commit → GateStackRun | Commit aggregates gate run |
| `requires_proof` | Commit → ProofBundle | Commit needs proof |
| `applies` | GateStackRun → State | Gates affect state |
| `produces` | SolverCall → ConstraintSet | Solver generates constraints |
| `reads` | MemoryRead → State | Read accesses state |
| `writes` | MemoryWrite → State | Write affects state |
| `emits` | Emit → State | Emit relates to state |
| `scheduled_after` | Any → Any | Execution ordering |

## Graph Invariants

All valid GraphGML graphs must satisfy:

1. **No orphaned nodes**: Every node must have at least one edge
2. **No duplicate edges**: Same source/type/target must appear once
3. **Valid edge types**: All edges must use defined EdgeType values
4. **Node ID uniqueness**: No two nodes share the same ID

### Validation

```python
from cnsc.haai.graphgml import GraphGML, GraphBuilder

builder = GraphBuilder()
# ... add nodes and edges ...
graph = builder.build()  # Auto-validates

# Manual validation
violations = graph.validate_invariants()
if violations:
    print(f"Invalid: {violations}")
```

## Examples

### Simple Commit Flow

```python
from cnsc.haai.graphgml import GraphBuilder

builder = GraphBuilder()
graph = (
    builder
    .begin_commit("c1", operation="update")
    .add_state("s1", state_type="initial", value=100)
    .add_candidate("cand1", value=150)
    .link_proposed_from("cand1", "s1")
    .add_gate_result("g1", "affordability", True)
    .link_evaluates("g1", "cand1")
    .build()
)
```

### Complex Multi-Gate Run

```python
from cnsc.haai.graphgml import GraphBuilder

with graph_builder() as builder:
    builder.begin_commit("txn_abc", operation="transfer")
    
    # Initial state
    builder.add_state("state_before", balance=1000, sequence=5)
    
    # Gate stack run
    builder.add_gate_stack_run("gate_run_1", gate_sequence=["affordability", "bounds", "nonce"])
    
    # Gate results
    builder.add_gate_result("gr1", "affordability", True)
    builder.add_gate_result("gr2", "bounds", True)
    builder.add_gate_result("gr3", "nonce", True)
    
    # Link gates to run
    builder.link_summarizes("txn_abc", "gate_run_1")
    
    # Candidate and final state
    builder.add_candidate("cand_new", value={"balance": 900, "sequence": 6})
    builder.link_proposed_from("cand_new", "state_before")
    builder.link_evaluates("gr1", "cand_new")
    builder.link_evaluates("gr2", "cand_new")
    builder.link_evaluates("gr3", "cand_new")
    
    graph = builder.build()
```

## Query Operations

### Finding Paths

```python
from cnsc.haai.graphgml import GraphQuery, EdgeType

query = GraphQuery(graph)
paths = query.find_path(
    start="state_before",
    end="cand_new",
    edge_types=[EdgeType.PROPOSED_FROM, EdgeType.EVALUATES]
)
```

### Subgraph Extraction

```python
# Find all gate results
gate_results = query.find_subgraph({"node_type": "gate_result"})
```

### Topological Ordering

```python
order = query.get_dependency_order()
```

## Migration Guide from Token-Centric GML

### Before (Token-Centric)

```python
# Old trace-based approach
tokens = [
    {"type": "checkpoint", "id": "cp1", "state": {...}},
    {"type": "candidate", "id": "c1", "value": 150},
    {"type": "gate", "id": "g1", "gate": "affordability", "passed": True},
    {"type": "receipt", "id": "r1", "prev": "cp1", "proof": {...}}
]
```

### After (GraphGML)

```python
# New graph-based approach
from cnsc.haai.graphgml import GraphBuilder

builder = GraphBuilder()
graph = (
    builder
    .add_state("cp1", state_type="checkpoint", **{"state": {...}})
    .add_candidate("c1", value=150)
    .add_gate_result("g1", "affordability", True)
    .link_proposed_from("c1", "cp1")
    .link_evaluates("g1", "c1")
    .build()
)
```

### Key Differences

| Aspect | Token-Centric | GraphGML |
|--------|---------------|----------|
| Structure | Linear sequence | Directed graph |
| Relationships | Implicit (order) | Explicit (edges) |
| Queries | Sequential scan | Graph traversal |
| Provenance | Hash chains | Direct references |
| Validation | Manual checks | Built-in invariants |

## Integration with Existing GML

GraphGML is designed to coexist with the existing GML layer:

1. **Dual-write**: Existing code writes tokens; migration adds graph construction
2. **Parallel queries**: Both trace and graph queries available during transition
3. **Gradual migration**: Components can migrate one at a time

See `plans/GML_Graph_Native_Migration_Plan.md` for detailed migration steps.
