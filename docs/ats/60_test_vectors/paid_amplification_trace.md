# Paid Amplification Trace

**Test Vector: Budget-Consuming Risk Increase**

| Field | Value |
|-------|-------|
| **Module** | 60_test_vectors |
| **Vector** | Paid Amplification |
| **Version** | 1.0.0 |

---

## 1. Test Description

This test verifies a trajectory where risk increases but stays within budget limits.

---

## 2. Initial Conditions

```
B₀ = 1000000000000000000 (1.0 in QFixed)
κ = 1000000000000000000 (1.0 in QFixed)
```

---

## 3. Trajectory Steps

### Step 0: Risk Increase

```
Action: COMPLEX_REASONING
V(x₀) = 0
V(x₁) = 300000000000000000  (risk = 0.3)
ΔV = +300000000000000000

Budget: B₀ → B₁ = 1000000000000000000 - 300000000000000000 = 700000000000000000
```

### Step 1: Risk Increase

```
Action: LEARNING
V(x₁) = 300000000000000000
V(x₂) = 500000000000000000  (risk = 0.5)
ΔV = +200000000000000000

Budget: B₁ → B₂ = 700000000000000000 - 200000000000000000 = 500000000000000000
```

### Step 2: Risk Decrease (Recovery)

```
Action: CONSOLIDATION
V(x₂) = 500000000000000000
V(x₃) = 400000000000000000  (risk = 0.4)
ΔV = -100000000000000000

Budget: B₂ → B₃ = 500000000000000000 (no consumption)
```

---

## 4. Budget Summary

| Metric | Value |
|--------|-------|
| **Initial Budget** | 1000000000000000000 |
| **Total Risk Increase** | 500000000000000000 |
| **Final Budget** | 500000000000000000 |
| **Budget Consumed** | 500000000000000000 |

---

## 5. Verification

### Expected Result

```
ACCEPT for all steps
Final budget = 500000000000000000
Budget invariant: 500000000000000000 ≤ 1000000000000000000 ✓
```

### Verification Commands

```bash
python -m ats.verify --trajectory paid_amplification_trace.json

# Expected output:
# Step 0: ACCEPT (risk increased, budget consumed)
# Step 1: ACCEPT (risk increased, budget consumed)
# Step 2: ACCEPT (risk decreased, budget preserved)
# Final Budget: 500000000000000000
```

---

## 6. References

- [Budget Law](../10_mathematical_core/budget_law.md)
- [Test Vector: Minimal Descent](./minimal_descent_trace.md)
- [Test Vector: Overbudget Rejection](./overbudget_rejection_trace.md)
