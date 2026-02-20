# Overbudget Rejection Trace

**Test Vector: Budget Exhaustion Rejection**

| Field | Value |
|-------|-------|
| **Module** | 60_test_vectors |
| **Vector** | Overbudget Rejection |
| **Version** | 1.0.0 |

---

## 1. Test Description

This test verifies that the ATS correctly rejects a step when budget is insufficient for the risk increase.

---

## 2. Initial Conditions

```
B₀ = 1000000000000000000 (1.0 in QFixed)
κ = 1000000000000000000 (1.0 in QFixed)
```

---

## 3. Trajectory Steps

### Step 0: First Risk Increase

```
Action: REASONING_STEP_1
V(x₀) = 0
V(x₁) = 600000000000000000  (risk = 0.6)
ΔV = +600000000000000000

Budget: B₀ → B₁ = 1000000000000000000 - 600000000000000000 = 400000000000000000

Result: ACCEPT
```

### Step 2: Overbudget Attempt

```
Action: REASONING_STEP_2
V(x₁) = 600000000000000000
V(x₂) = 1100000000000000000  (risk = 1.1)
ΔV = +500000000000000000

Required Budget: κ × ΔV = 1 × 500000000000000000 = 500000000000000000
Available Budget: B₁ = 400000000000000000

Result: REJECT(INSUFFICIENT_BUDGET)
```

---

## 4. Expected Rejection

### Rejection Details

```json
{
  "result": "REJECT",
  "code": "INSUFFICIENT_BUDGET",
  "reason": "Budget 400000000000000000 < required 500000000000000000",
  "details": {
    "budget_before": "400000000000000000",
    "budget_required": "500000000000000000",
    "risk_delta": "500000000000000000",
    "kappa": "1000000000000000000"
  }
}
```

---

## 5. Verification

### Expected Result

```
Step 0: ACCEPT
Step 1: REJECT(INSUFFICIENT_BUDGET)
Final state: x₁ (not x₂)
Final budget: 400000000000000000
```

### Verification Commands

```bash
python -m ats.verify --trajectory overbudget_trace.json

# Expected output:
# Step 0: ACCEPT
# Step 1: REJECT(INSUFFICIENT_BUDGET)
# Error: Budget insufficient for risk increase
```

---

## 6. References

- [Budget Law](../10_mathematical_core/budget_law.md)
- [Rejection Reason Codes](../50_security_model/rejection_reason_codes.md)
- [Test Vector: Paid Amplification](./paid_amplification_trace.md)
