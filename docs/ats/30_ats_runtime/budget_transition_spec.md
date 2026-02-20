# Budget Transition Specification

**Formal Budget State Transitions**

| Field | Value |
|-------|-------|
| **Module** | 30_ats_runtime |
| **Section** | Budget Transition |
| **Version** | 1.0.0 |

---

## 1. Budget State

### 1.1 Budget Representation

```
Budget = QFixed(18)
```

A non-negative fixed-point value representing available coherence budget.

### 1.2 Budget States

| State | Condition |
|-------|-----------|
| **Active** | B > 0 |
| **Exhausted** | B = 0 and ΔV > 0 would cause rejection |
| **Full** | B = B_initial |

---

## 2. Transition Rules

### 2.1 Descent (Risk Decrease)

When ΔV ≤ 0:

```
B_{k+1} = B_k
```

The budget is preserved when risk decreases.

### 2.2 Ascent (Risk Increase)

When ΔV > 0:

```
Required: B_k ≥ κ × ΔV
B_{k+1} = B_k - κ × ΔV
```

Budget is consumed proportionally to risk increase.

### 2.3 Complete Transition Function

```python
def budget_transition(
    budget_before: QFixed,
    risk_delta: QFixed,
    kappa: QFixed
) -> (QFixed, bool):
    """
    Compute budget after a step.
    
    Returns: (budget_after, accepted)
    """
    if risk_delta <= 0:
        # Risk decreased - budget preserved
        return budget_before, True
    
    # Risk increased - check sufficiency
    required = kappa * risk_delta
    if budget_before < required:
        return None, False  # REJECT
    
    # Budget consumed
    budget_after = budget_before - required
    return budget_after, True
```

---

## 3. Transition Examples

### 3.1 Pure Descent

```
Initial: B₀ = 100, κ = 1

Step 0: ΔV = -30 → B₁ = 100
Step 1: ΔV = -20 → B₂ = 100  
Step 2: ΔV = -10 → B₃ = 100

Final: B = 100 (unchanged)
```

### 3.2 Controlled Ascent

```
Initial: B₀ = 100, κ = 1

Step 0: ΔV = +30 → B₁ = 70 (consumed: 30)
Step 1: ΔV = +20 → B₂ = 50 (consumed: 20)
Step 2: ΔV = -10 → B₃ = 50 (no consumption)

Final: B = 50
Total consumed: 50
```

### 3.3 Overbudget Rejection

```
Initial: B₀ = 100, κ = 1

Step 0: ΔV = +60 → B₁ = 40 (consumed: 60)
Step 1: ΔV = +50 → REJECT!

Reason: B₁ = 40 < required = 1 × 50 = 50
```

---

## 4. Edge Cases

### 4.1 Zero Budget

```
If B_k = 0 and ΔV > 0:
    REJECT("INSUFFICIENT_BUDGET")
```

### 4.2 Exact Budget

```
If B_k = κ × ΔV:
    B_{k+1} = 0
    ACCEPT (exact consumption)
```

### 4.3 Negative Delta

```
If ΔV < 0:
    B_{k+1} = B_k
    (Risk decreased - budget preserved)
```

---

## 5. Budget Tracking

### 5.1 Accumulation

The kernel tracks:

```
budget_consumed = B_initial - B_current
```

### 5.2 Invariant

At all times:

```
budget_consumed ≤ B_initial
```

---

## 6. Serialization

### 6.1 Receipt Fields

```json
{
  "content": {
    "budget_before_q": "1000000000000000000",
    "budget_after_q": "700000000000000000",
    "kappa_q": "1000000000000000000"
  }
}
```

### 6.2 QFixed Format

All budget values are QFixed(18):
- String representation
- 18 decimal places
- No scientific notation

---

## 7. References

- [Budget Law](../10_mathematical_core/budget_law.md)
- [Risk Functional V](../10_mathematical_core/risk_functional_V.md)
- [RV Step Specification](../20_coh_kernel/rv_step_spec.md)
- [Receipt Schema](../20_coh_kernel/receipt_schema.md)
