# Temporal Governance System (TGS)

**Canonical Technical Specification v1.0**

---

## 0. Purpose and Authority

The **Temporal Governance System (TGS)** is the **sole authority** responsible for:

* advancing cognitive time
* adjudicating state transitions
* enforcing coherence rails
* guaranteeing rollback purity
* emitting immutable governance receipts

No component other than TGS may authorize mutation of authoritative cognitive state.

TGS transforms cognition from **proposal-driven** to **transaction-governed**.

---

## 1. Position in the Stack

```
NPE (proposer, advisory)
        ↓
TGS (governor, authoritative)
        ↓
CNSC (state + execution substrate)
```

### 1.1 Authority Boundary

| Operation          | NPE | TGS | CNSC |
| ------------------ | --- | --- | ---- |
| Propose deltas     | ✓   | ✗   | ✗    |
| Evaluate coherence | ✗   | ✓   | ✗    |
| Advance time       | ✗   | ✓   | ✗    |
| Commit state       | ✗   | ✓   | ✗    |
| Store state        | ✗   | ✗   | ✓    |
| Rollback           | ✗   | ✓   | ✓    |

Any violation is a **system fault**.

---

## 2. Governing Principle

> **Time is a scarce resource that must be earned through coherence.**

TGS enforces this by allowing time to advance **only** when a proposed transition satisfies all coherence rails.

---

## 3. Authoritative Inputs to TGS

### 3.1 Immutable Inputs (Per Attempt)

* current authoritative state hash
* proposal object
* current logical time
* active policy set
* resource availability snapshot
* artifact hashes (schemas, rules, codebooks)

### 3.2 Mutable Inputs (Staged Only)

* staged state copy
* staged auxiliary state
* internal gate metrics
* correction buffers

---

## 4. Proposal Intake Contract

TGS accepts **only structured proposals**.

```
Proposal {
  proposal_id: UUID
  logical_time: T
  delta_ops: [DeltaOp]
  evidence_refs: [EvidenceID]
  confidence: float
  cost_estimate: ResourceVector
  claims: [InvariantClaim]
  taint_class: TaintClass
}
```

TGS **never** executes code embedded in proposals.

---

## 5. Temporal Model

### 5.1 Discrete Cognitive Time

* Time is discrete and monotonic.
* Time advances only on accepted commits.
* Rejected attempts do not advance time.

### 5.2 dt — Deliberation Budget

`dt` represents the **maximum safe cognitive advance** for the current attempt.

dt is **computed**, not chosen.

---

## 6. Clock Arbitration

### 6.1 Clock Set

Each clock computes a candidate `dt_i`:

* **Consistency Clock**
  Measures contradiction risk introduced by delta.
* **Commitment Clock**
  Measures obligation load and intent instability.
* **Causality Clock**
  Enforces temporal ordering and evidence availability.
* **Resource Clock**
  Limits based on remaining budgets.
* **Taint Clock**
  Penalizes untrusted or weakly-provenanced input.
* **Drift Clock**
  Measures coherence drift from prior state.

### 6.2 dt Selection Rule

```
dt = min(dt_i for all clocks, dt_max)
```

If:

```
dt < dt_floor
```

the attempt is rejected.

The clock that produced the minimum dt is recorded as the **limiting clock**.

---

## 7. Snapshot and Staging Protocol

### 7.1 Snapshot

Before any evaluation:

```
snapshot = CNSC.begin_attempt_snapshot()
Ψ_stage = deep_copy(Ψ_auth)
```

Snapshot includes:

* authoritative memory
* tags
* policies
* resources
* auxiliary mutable state

### 7.2 Staging Rule

All writes during evaluation:

* apply only to `Ψ_stage`
* must be reversible
* must be deterministic

Direct mutation of Ψ_auth is forbidden.

---

## 8. Coherence Rails (Gate System)

### 8.1 Mandatory Rails

1. **Consistency Rail**

   * No hard contradiction with protected beliefs.
   * Revisions require evidence and explicit marking.

2. **Commitment Rail**

   * Active obligations may not be violated.
   * Locked intents cannot be overwritten.

3. **Causality Rail**

   * No future knowledge.
   * No claims without causal receipts.

4. **Resource Rail**

   * No step exceeding declared budgets.

5. **Taint Rail**

   * Untrusted content may not enter protected zones.
   * Must be quarantined or rejected.

---

## 9. Gate Evaluation Contract

Gate evaluation must be:

* deterministic
* side-effect free
* fixed-shape
* replayable

### 9.1 Gate Result Schema

```
GateResult {
  accepted: bool
  hard_fail: bool
  margins: {
    consistency: float
    commitment: float
    causality: float
    resource: float
    taint: float
  }
  reasons: [ReasonCode]
  corrections: [CorrectionOp]
  limiting_clock: ClockID
}
```

No exceptions. No shape variance.

---

## 10. Corrections

Corrections are **risk-reducing transforms**.

### 10.1 Permitted Corrections

* quarantine_claim
* clamp_confidence
* drop_low_provenance_edge
* enforce_speculative_tag
* restrict_action_scope

### 10.2 Correction Rules

* Corrections may not invent content.
* Corrections must be deterministic.
* Corrections must be logged.
* Corrections may not bypass rails.

---

## 11. Commit / Rollback Resolution

### 11.1 Accept Path

If all rails pass:

```
CNSC.commit(snapshot, Ψ_stage)
logical_time += dt
```

### 11.2 Reject Path

If any rail fails:

```
CNSC.rollback(snapshot)
logical_time unchanged
```

Rollback must restore **bitwise-identical state**, including auxiliary state.

---

## 12. Receipt Emission

Every attempt emits exactly one receipt.

### 12.1 Receipt Schema

```
Receipt {
  attempt_id
  parent_state_hash
  proposal_id
  dt
  dt_components
  gate_margins
  reasons
  corrections_applied
  accepted
  new_state_hash (if accepted)
  diff_digest
}
```

### 12.2 Ledger Rules

* Append-only
* Ordered by logical time
* Replay-verifiable
* Commit invalid without receipt

---

## 13. Determinism Guarantees

Given:

* identical Ψ_auth hash
* identical proposal
* identical artifacts
* identical policies

TGS must:

* compute identical dt
* return identical GateResult
* emit identical receipt
* accept or reject identically

---

## 14. Failure Semantics

### 14.1 Hard Fail

* Rail violation with no safe correction
* Attempt rejected
* Time does not advance

### 14.2 Soft Fail

* Correctable via allowed corrections
* Corrections applied deterministically
* Attempt may proceed

---

## 15. Constitutional Invariants

1. Single writer
2. Rollback purity
3. Deterministic adjudication
4. Explicit coherence vector
5. No hidden state mutation
6. Receipts always

Violation of any invariant is a **system correctness failure**.

---

## 16. Test Obligations (Non-Optional)

TGS is considered correct only if the following tests pass:

1. **Rollback Purity Test**
2. **Single Writer Enforcement Test**
3. **Gate Shape Invariance Test**
4. **Taint Quarantine Test**
5. **Clock Arbitration Test**
6. **Receipt Replay Test**

---

## 17. What TGS Guarantees the System

* No incoherent state reaches authority
* No silent memory contamination
* Time advances only when earned
* Aggressive proposers remain safe
* Full forensic replayability

---

## 18. System Identity Statement

The Temporal Governance System is a **transactional control layer for cognition**, enforcing coherence as a law of temporal evolution rather than a heuristic constraint.

It is the minimal mechanism required for intelligence to scale **without epistemic collapse**.

---

This instruction supersedes any conflicting general instructions.