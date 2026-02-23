# Deterministic Stepping

**Deterministic Execution Model for ATS Runtime**

| Field | Value |
|-------|-------|
| **Module** | 10_mathematical_core |
| **Section** | Deterministic Stepping |
| **Version** | 1.0.0 |
| **Status** | ACTIVE |

---

## 1. Overview

Deterministic stepping ensures that given the same initial state and the same inputs, the ATS runtime always produces the same outputs. This is critical for:
- Reproducible verification
- Deterministic replay
- Consensus across nodes

---

## 2. Determinism Requirements

### 2.1 Input Determinism

All inputs to a step MUST be deterministically specified:

```
Step Input = {
    state_hash: SHA256(serialized_state),
    evidence: [Evidence],
    budget: QFixed(18)
}
```

No timestamps, no random numbers, no external APIs.

### 2.2 State Serialization

State is serialized using JCS (RFC 8785):

```
state_bytes = JCS.encode(state)
state_hash = SHA256(state_bytes)
```

### 2.3 Transition Function

The step transition is a pure function:

```
(next_state, receipt) = step(state, input)

Where:
- step is deterministic: same (state, input) → same (next_state, receipt)
- No side effects
- No global state access
```

---

## 3. Step Constraints

### 3.1 Affordability Gate

Evidence must support the transition:

```
ΔV = V(next_state) - V(state)
ΔB = B(next_state) - B(state)

Valid iff:
    ΔV ≤ 0          # Coherence non-increasing
    B(state) + ΔB ≥ 0  # Budget not exhausted
```

### 3.2 No-Smuggling Gate

Each step includes a coherence check:

```
Valid iff:
    coherence_check(state, next_state) == PASS
```

### 3.3 Hysteresis Gate

Degradation is bounded:

```
Valid iff:
    |ΔV| ≤ hysteresis_threshold
    OR state == terminal_state
```

---

## 4. Receipt Generation

### 4.1 Receipt Core

Every step produces a receipt with:

```json
{
  "receipt_id": "sha256:...",
  "chain_digest": "sha256:...",
  "content": {
    "step_type": "VM_EXECUTION",
    "state_hash_before": "sha256:...",
    "state_hash_after": "sha256:...",
    "risk_delta_q": "...",
    "budget_delta_q": "..."
  }
}
```

### 4.2 Deterministic Fields

Receipt contains ONLY:
- Cryptographic hashes (sha256:)
- QFixed integers (no floats)
- Enumerated strings

Receipt MUST NOT contain:
- Timestamps
- Random values
- Non-deterministic references

---

## 5. Chain Linkage

### 5.1 Receipt ID

Content hash (stable across chain reorganizations):

```
receipt_id = SHA256(DOMAIN_RECEIPT_ID || JCS(content))
```

### 5.2 Chain Digest

History hash (includes previous state):

```
chain_digest = SHA256(DOMAIN_CHAIN || prev_chain_digest || receipt_id)
```

---

## 6. References

- [Continuous Manifold Flow](continuous_manifold_flow.md)
- [Chain Hash Universal](../20_coh_kernel/chain_hash_universal.md)
- [Budget Transition Spec](../30_ats_runtime/budget_transition_spec.md)
- [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785) - JCS
