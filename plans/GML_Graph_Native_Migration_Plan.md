# Plan: Migrate GML to Graph-Native Representation

## Goal

Replace **token/trace-centric GML** with a **GraphGML** layer:

* **Nodes** = typed artifacts (State, Candidate, GateResult, Proof, ConstraintSet, MemoryRead/Write, SolverCall, Effect/Emit)
* **Edges** = causal + dependency relations (derived-from, validated-by, produced-by, reads, writes, commits, emits, scheduled-after)
* **Graph invariants** enforce "no bypass," "fresh proof," "no future leak," etc.

Success metric: you can answer hard questions *by querying the graph*, and you can enforce critical safety invariants structurally.

## Why Graphs Beat Tokens

Tokens/traces are good for "what happened in order."
Graphs are good for "what depended on what, and what was certified by what."

That's exactly what the system claims to care about: gates, receipts, provenance, and reproducibility.

---

## Phase 0 — Definition Ledger

**Deliverable:** `docs/gml_graph_spec.md`

Include:
- **Node types** (with fields + hash rules)
- **Edge types** (semantics + allowed directionality)
- **Required subgraphs** for Commit/Emit
- **Canonical hashing** rules (content hashes, stable ordering)
- **Versioning**: GraphGML v0, v1, etc.

This prevents "graph spaghetti."

---

## Phase 1 — Model the Minimal "Proof-Carrying Commit" Graph

Start with the smallest subgraph that proves the most important claim.

### Minimal Required Nodes

| Node Type | Fields |
|-----------|--------|
| `State` | hash, timestamp, domain tags |
| `Candidate` | hash, proposal metadata |
| `ConstraintSet` | hash, active constraints |
| `GateStackRun` | stack id, order, runtime stats |
| `GateResult` | PASS/FAIL/SOFT, reason codes |
| `ProofBundle` | hash, signatures, registry hash |
| `Commit` | delta hash, new state hash |
| `Emit` | effect hash (optional) |

### Minimal Required Edges

```
Candidate --proposed_from--> State
GateStackRun --evaluates--> (State, Candidate, ConstraintSet)
ProofBundle --summarizes--> GateStackRun
Commit --requires_proof--> ProofBundle
Commit --applies--> Candidate
Commit --produces--> State'
```

### Invariant (VM Enforceable)

No `Commit` node is valid unless:
- there exists a `ProofBundle` node,
- whose inputs match `(state_hash, candidate_hash, constraints_hash, gate_registry_hash)`.

This is where "graphs" become *structural truth*.

---

## Phase 2 — Build GraphGML Alongside Existing GML (Dual-Write)

Don't break everything. Add a **GraphEmitter** that runs in parallel.

### Implementation Steps

1. Add a `GraphBuilder` in the kernel/VM:
   - Every existing receipt/trace event becomes either:
     - a node creation, or
     - an edge insertion, or
     - an attribute update (avoid if possible; prefer immutability)

2. Output format:
   - **JSON Lines** for nodes + edges (easy to diff and stream), or
   - a single JSON graph document per run, or
   - both

3. Add a `graph_hash` at end-of-run to ledger

**Success metric:** the graph fully reconstructs the same audit story as the trace.

---

## Phase 3 — Provide a Strict Mapping: Trace → Graph

Reviewers will ask: "how do we know graph didn't lie?"

**Deliverable:** `tools/trace_to_graph.py` (deterministic translator)

- Consumes old GML trace logs
- Produces GraphGML
- Recomputes hashes
- Emits a reconciliation report:
  - events mapped %
  - unmatched events
  - missing dependencies

This also lets you replay historical data into graphs.

---

## Phase 4 — Make the Graph Queryable and Useful

Add a tiny query layer (don't overbuild).

### Minimum Queries That Prove It's Better Than Tokens

| Query | Purpose |
|-------|---------|
| "Show the proof chain for this commit/emit." | Audit trail |
| "Which gate failed most often, and what repairs followed?" | Diagnostics |
| "Which memory entry influenced this decision?" | Provenance |
| "Find all commits made under constraint-set X." | Filtering |
| "Detect any commit whose proof is stale or mismatched." | Validation |

**Deliverable:** `tools/graph_query.py` with 10–15 built-in queries.

Optional storage:
- Start with in-memory + JSONL
- Graduate to SQLite (tables nodes/edges) or a graph DB later

---

## Phase 5 — Replace Token-Level Reasoning with Graph-Level Reasoning

This is the real upgrade: "intelligence" becomes graph navigation.

### Examples

- **Repair policy** chooses next move based on subgraph patterns:
  - repeated dt reductions + same gate failure ⇒ change strategy
- **Scheduler** uses dependency structure:
  - only advance phase if required upstream proofs exist
- **Memory policy** uses provenance:
  - forbid warm-start unless it descends from allowed scenario tags

**Deliverable:** one policy that becomes simpler and more reliable using graph queries.

---

## Phase 6 — Enforce Graph Invariants as Tests (GraphCAT)

Add a `GraphCAT` suite that validates invariants purely from GraphGML.

### Core Tests

1. **No bypass**: no commit without matching proof bundle
2. **Freshness**: proof input hashes match exact committed artifacts
3. **Causality**: no edge from future timestamp to past
4. **Taint rules**: no prohibited memory provenance edges
5. **Deterministic graph hash**: same run ⇒ same graph hash

This makes the graph not "documentation," but *a verifiable artifact.*

---

## Phase 7 — Deprecate Old GML Tokens (Gradually)

Once GraphCAT passes in CI and you're dual-writing for a while:

- Mark token GML format as "legacy"
- Keep a compatibility reader for older runs
- Switch default tooling and docs to graphs

---

## Practical Design Choices

- Prefer **immutable nodes** with content hashes
- Treat edges as first-class (edges should be typed)
- Store **gate registry version hash** inside proofs (critical)
- Keep node payloads **small**, reference large blobs by hash/path
- Build a "cheap-first" graph: avoid high-frequency field dumps unless needed

---

## Deliverables Checklist

| Phase | Deliverable | File Path |
|-------|-------------|-----------|
| 0 | GraphGML specification | `docs/gml_graph_spec.md` |
| 1 | Typed schema | `src/cnsc/haai/graphgml/types.py` |
| 2 | Dual-write emitter | `src/cnsc/haai/graphgml/builder.py` |
| 3 | Trace-to-graph translator | `tools/trace_to_graph.py` |
| 4 | Graph query layer | `tools/graph_query.py` |
| 6 | GraphCAT test suite | `tests/test_graphcat_*.py` |
| - | README update | `README.md` |

---

## The First Thing to Implement (Highest Leverage)

**Graph subgraph for Commit/Emit + invariant test.**

That single change turns "we have gates" into "we can prove the gates were obeyed," and it's exactly the kind of "this is real" artifact reviewers respect.

---

## Node/Edge Schema (Reference Implementation)

```python
# Node Types
class NodeType(Enum):
    STATE = "State"
    CANDIDATE = "Candidate"
    CONSTRAINT_SET = "ConstraintSet"
    GATE_STACK_RUN = "GateStackRun"
    GATE_RESULT = "GateResult"
    PROOF_BUNDLE = "ProofBundle"
    COMMIT = "Commit"
    EMIT = "Emit"
    MEMORY_READ = "MemoryRead"
    MEMORY_WRITE = "MemoryWrite"
    SOLVER_CALL = "SolverCall"

# Edge Types
class EdgeType(Enum):
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
```

---

## Success Metrics

- [ ] Graph fully reconstructs audit story from trace
- [ ] All GraphCAT invariants pass
- [ ] Query layer answers all 5 minimum queries
- [ ] At least one policy upgraded to graph-level reasoning
- [ ] Dual-write mode verified for 100+ runs
- [ ] Legacy format marked deprecated
