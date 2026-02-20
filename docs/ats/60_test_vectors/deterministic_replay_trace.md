# Deterministic Replay Trace

**Test Vector: Determinism Verification**

| Field | Value |
|-------|-------|
| **Module** | 60_test_vectors |
| **Vector** | Deterministic Replay |
| **Version** | 1.0.0 |

---

## 1. Test Description

This test verifies that the same trajectory, when replayed, produces identical results. This ensures deterministic execution.

---

## 2. Original Execution

### 2.1 Initial State

```
x₀ = {
  "belief": {"concept_a": [0.5, 0.5]},
  "memory": [],
  "plan": [],
  "policy": {},
  "io": {"input": [], "output": []}
}

B₀ = 1000000000000000000
κ = 1000000000000000000
```

### 2.2 Execution Steps

```
Step 0: BELIEF_UPDATE (risk: 1.0 → 0.8) → ACCEPT
Step 1: MEMORY_WRITE (risk: 0.8 → 0.6) → ACCEPT
Step 2: PLAN_APPEND (risk: 0.6 → 0.4) → ACCEPT
```

### 2.3 Final State

```
x_T = {
  "belief": {"concept_a": [0.8, 0.2]},
  "memory": [Cell(42)],
  "plan": [{"action": "test"}],
  "policy": {},
  "io": {"input": [], "output": []}
}

B_T = 1000000000000000000
```

---

## 3. Replay Execution

### 3.1 Replay Input

Same initial state and receipts from original execution.

### 3.2 Replay Process

```python
def replay(initial_state, receipts):
    state = initial_state
    for receipt in receipts:
        # Verify receipt
        if not verify(receipt):
            return REJECT
        
        # Apply action (from receipt)
        state = apply(state, receipt.action)
    
    return state
```

### 3.3 Replay Result

```
x_T (replayed) = x_T (original)
```

---

## 4. Verification

### 4.1 Determinism Check

```python
def verify_determinism(original, replayed):
    return original == replayed
```

### 4.2 Expected Result

```
ACCEPT
All steps reproduce identical states
Final state match: ✓
Final budget match: ✓
```

### 4.3 Verification Commands

```bash
python -m ats.replay --initial-state initial.json --receipts trace.json

# Expected output:
# Step 0: ACCEPT
# Step 1: ACCEPT
# Step 2: ACCEPT
# Final state matches: True
# Final budget matches: True
```

---

## 5. Non-Determinism Detection

### 5.1 If Non-Deterministic

If replay produces different result:

```
REJECT(STATE_HASH_MISMATCH)
Reason: Replayed state doesn't match claimed final state
```

### 5.2 Common Causes

| Cause | Detection |
|-------|-----------|
| Float usage | Hash mismatch |
| Random numbers | Hash mismatch |
| Time dependencies | Hash mismatch |
| Dictionary ordering | Hash mismatch |

---

## 6. References

- [Deterministic Replay Requirements](../50_security_model/deterministic_replay_requirements.md)
- [Replay Verification](../30_ats_runtime/replay_verification.md)
- [Test Vector: Minimal Descent](./minimal_descent_trace.md)
