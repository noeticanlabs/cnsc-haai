# Minimal Descent Trace

**Test Vector: Pure Risk Decrease Trajectory**

| Field | Value |
|-------|-------|
| **Module** | 60_test_vectors |
| **Vector** | Minimal Descent |
| **Version** | 1.0.0 |

---

## 1. Test Description

This test verifies a trajectory where risk continuously decreases. Budget should remain unchanged.

---

## 2. Initial Conditions

```
B₀ = 1000000000000000000 (1.0 in QFixed)
κ = 1000000000000000000 (1.0 in QFixed)
```

---

## 3. Trajectory Steps

### Step 0

```
Action: BELIEF_UPDATE
V(x₀) = 1000000000000000000 (risk = 1.0)
V(x₁) = 800000000000000000  (risk = 0.8)
ΔV = -200000000000000000

Budget: B₀ → B₁ = 1000000000000000000 (no consumption)
```

### Step 1

```
Action: MEMORY_WRITE
V(x₁) = 800000000000000000
V(x₂) = 600000000000000000
ΔV = -200000000000000000

Budget: B₁ → B₂ = 1000000000000000000 (no consumption)
```

### Step 2

```
Action: PLAN_APPEND
V(x₂) = 600000000000000000
V(x₃) = 400000000000000000
ΔV = -200000000000000000

Budget: B₂ → B₃ = 1000000000000000000 (no consumption)
```

---

## 4. Receipts

### Receipt 0

```json
{
  "receipt_id": "a1b2c3d4",
  "content": {
    "step_type": "VM_EXECUTION",
    "risk_before_q": "1000000000000000000",
    "risk_after_q": "800000000000000000",
    "delta_plus_q": "0",
    "budget_before_q": "1000000000000000000",
    "budget_after_q": "1000000000000000000",
    "kappa_q": "1000000000000000000",
    "state_hash_before": "sha256:0000...",
    "state_hash_after": "sha256:1111...",
    "decision": "PASS"
  }
}
```

---

## 5. Verification

### Expected Result

```
ACCEPT for all steps
Final budget = 1000000000000000000 (unchanged)
```

### Verification Commands

```bash
# Verify each step
python -m ats.verify --trajectory descent_trace.json

# Expected output:
# Step 0: ACCEPT
# Step 1: ACCEPT
# Step 2: ACCEPT
# Final Budget: 1000000000000000000
```

---

## 6. References

- [Budget Law](../10_mathematical_core/budget_law.md)
- [RV Step Specification](../20_coh_kernel/rv_step_spec.md)
- [Test Vector: Paid Amplification](./paid_amplification_trace.md)
