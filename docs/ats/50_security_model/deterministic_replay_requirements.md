# Deterministic Replay Requirements

**Requirements for Reproducible Execution**

| Field | Value |
|-------|-------|
| **Module** | 50_security_model |
| **Section** | Deterministic Replay Requirements |
| **Version** | 1.0.0 |

---

## 1. Replay Determinism

### 1.1 Core Requirement

> **All ATS execution must be deterministic. Same inputs must produce same outputs.**

### 1.2 Determinism Definition

```
∀inputs: f(inputs) = f(inputs)
```

Where `f` is the ATS execution function.

---

## 2. Determinism Requirements

### 2.1 Execution Determinism

| Requirement | Description |
|-------------|-------------|
| **D1** | Same initial state → same trajectory |
| **D2** | Same actions → same state changes |
| **D3** | No timing dependencies |
| **D4** | No random number generation |

### 2.2 Verification Determinism

| Requirement | Description |
|-------------|-------------|
| **V1** | Same receipt → same verification result |
| **V2** | No external dependencies |
| **V3** | Pure function implementation |

---

## 3. Sources of Non-Determinism

### 3.1 Forbidden Sources

| Source | Why Forbidden |
|--------|--------------|
| **float32/float64** | Platform-specific rounding |
| **random module** | Non-deterministic |
| **time.time()** | Returns current time |
| **hash randomization** | Python hash seed |
| **Dictionary iteration** | Unordered in Python <3.7 |

### 3.2 Mitigation

| Issue | Solution |
|-------|----------|
| Floats | Use QFixed |
| Random | Use deterministic seed or remove |
| Time | Use step index, not timestamp |
| Dictionary | Use OrderedDict or sort keys |
| Hash | Set PYTHONHASHSEED |

---

## 4. Replay Verification

### 4.1 Verification Process

```python
def verify_determinism(initial_state, receipts):
    """
    Verify trajectory is deterministic.
    
    1. Replay from initial state
    2. Compare final state with claimed final state
    3. Compare receipts
    """
    # Replay
    replayed_state, replayed_receipts = replay(
        initial_state,
        receipts
    )
    
    # Compare
    for i, receipt in enumerate(receipts):
        if receipt != replayed_receipts[i]:
            return False
    
    return True
```

### 4.2 Hash Comparison

```python
def verify_state_hash(state, expected_hash):
    """Verify state produces expected hash."""
    computed = sha256(canonical_bytes(state))
    return computed == expected_hash
```

---

## 5. Implementation Requirements

### 5.1 Environment

```bash
# Set deterministic hash seed
export PYTHONHASHSEED=0
```

### 5.2 Code Requirements

```python
# WRONG - uses random
import random
value = random.randint(0, 100)

# CORRECT - deterministic
value = deterministic_index(step_index, modulus)

# WRONG - uses float
risk = dynamical**2 + clock**2

# CORRECT - uses QFixed
risk = (dynamical_sq + clock_sq) >> SCALE_BITS
```

---

## 6. References

- [Adversary Model](./adversary_model.md)
- [Float Prohibition](./float_prohibition.md)
- [Deterministic Numeric Domain](../20_coh_kernel/deterministic_numeric_domain.md)
- [Replay Verification](../30_ats_runtime/replay_verification.md)
