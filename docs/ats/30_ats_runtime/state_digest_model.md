# State Digest Model

**Deterministic State Hashing in the ATS Runtime**

| Field | Value |
|-------|-------|
| **Module** | 30_ats_runtime |
| **Section** | State Digest Model |
| **Version** | 1.0.0 |

---

## 1. Overview

The state digest model defines how cognitive states are hashed for verification. Every state in the ATS has a deterministic digest that serves as its unique identifier.

---

## 2. Digest Components

### 2.1 Full State Digest

```
state_digest = sha256(canonical_bytes(state))
```

### 2.2 Component Digests

Each state component can be hashed independently:

```
digest_belief   = sha256(canonical_bytes(state.belief))
digest_memory   = sha256(canonical_bytes(state.memory))
digest_plan     = sha256(canonical_bytes(state.plan))
digest_policy   = sha256(canonical_bytes(state.policy))
digest_io       = sha256(canonical_bytes(state.io))

_digest   state = sha256(
    digest_belief ||
    digest_memory ||
    digest_plan ||
    digest_policy ||
    digest_io
)
```

---

## 3. Digest Properties

### 3.1 Determinism

| Property | Guarantee |
|----------|-----------|
| **Same State** | Same digest (always) |
| **Different State** | Different digest (with overwhelming probability) |
| **No Collisions** | SHA-256 assumed collision-resistant |

### 3.2 Efficiency

| Operation | Complexity |
|-----------|------------|
| **Single Component** | O(n) where n = component size |
| **Full State** | O(N) where N = total state size |
| **Incremental Update** | O(Δ) where Δ = changed portion |

---

## 4. Digest in Receipts

### 4.1 Receipt Fields

```json
{
  "content": {
    "state_hash_before": "sha256:abc123...",
    "state_hash_after": "sha256:def456..."
  }
}
```

### 4.2 Verification

The verifier recomputes:

```
computed_before = sha256(canonical_bytes(state_before))
computed_after = sha256(canonical_bytes(state_after))

If computed_before != receipt.state_hash_before:
    REJECT("STATE_HASH_MISMATCH")

If computed_after != receipt.state_hash_after:
    REJECT("STATE_HASH_MISMATCH")
```

---

## 5. Compact Digests

### 5.1 Short Form

For logging and display:

```
short_digest = first16(state_digest)
Example: "abc123456789def0"
```

### 5.2 Full Form

For verification:

```
full_digest = state_digest (32 bytes / 64 hex chars)
Example: "abc123456789def0123456789abcdef0123456789abcdef0123456789abcdef"
```

---

## 6. Implementation

### 6.1 Python Example

```python
import hashlib

def state_digest(state: State) -> str:
    """Compute deterministic state digest."""
    canonical = canonical_bytes(state)
    return hashlib.sha256(canonical).hexdigest()

def verify_state_digest(state: State, expected_hash: str) -> bool:
    """Verify state matches expected digest."""
    computed = state_digest(state)
    return computed == expected_hash
```

---

## 7. References

- [State Space](../10_mathematical_core/state_space.md)
- [Canonical Serialization](../20_coh_kernel/canonical_serialization.md)
- [RV Step Specification](../20_coh_kernel/rv_step_spec.md)
- [Action Emission Contract](./action_emission_contract.md)
