# Rejection Reason Codes

**Complete List of ATS Rejection Codes**

| Field | Value |
|-------|-------|
| **Module** | 50_security_model |
| **Section** | Rejection Reason Codes |
| **Version** | 1.0.0 |

---

## 1. Code Categories

### 1.1 Verification Failures

| Code | Category | Description |
|------|----------|-------------|
| `INVALID_ACTION_TYPE` | Verification | Action not in action algebra |
| `INVALID_STATE_SERIALIZATION` | Verification | State cannot be serialized |
| `STATE_HASH_MISMATCH` | Verification | Recomputed hash doesn't match |
| `INVALID_RECEIPT_HASH` | Verification | Receipt self-invalid |
| `RISK_MISMATCH` | Verification | Risk recompute doesn't match |

### 1.2 Budget Violations

| Code | Category | Description |
|------|----------|-------------|
| `BUDGET_VIOLATION` | Budget | Budget law not satisfied |
| `INSUFFICIENT_BUDGET` | Budget | Not enough budget for risk increase |
| `NEGATIVE_BUDGET` | Budget | Budget went negative |

### 1.3 Chain Failures

| Code | Category | Description |
|------|----------|-------------|
| `INVALID_CHAIN_LINK` | Chain | Receipt chain broken |
| `GENESIS_REQUIRED` | Chain | Expected genesis receipt |
| `CHAIN_TOO_SHORT` | Chain | Not enough receipts |

---

## 2. Detailed Codes

### 2.1 INVALID_ACTION_TYPE

```
Reason: Action type not in action algebra
Context: Action validation
Recovery: Use valid action type
```

### 2.2 STATE_HASH_MISMATCH

```
Reason: State hash doesn't match receipt claim
Context: Hash verification
Recovery: Fix state serialization or computation
```

### 2.3 RISK_MISMATCH

```
Reason: Risk value doesn't match receipt claim
Context: Risk verification
Recovery: Fix V(x) computation
```

### 2.4 BUDGET_VIOLATION

```
Reason: Budget transition doesn't follow law
Context: Budget law check
Recovery: Ensure budget = f(previous_budget, delta)
```

### 2.5 INSUFFICIENT_BUDGET

```
Reason: B_k < κ × ΔV_k for positive delta
Context: Budget check
Recovery: Reduce risk increase or start with more budget
```

---

## 3. Error Response Format

### 3.1 Rejection Response

```json
{
  "result": "REJECT",
  "code": "BUDGET_VIOLATION",
  "reason": "Insufficient budget for risk increase",
  "details": {
    "budget_before": "500000000000000000",
    "budget_required": "600000000000000000",
    "risk_delta": "600000000000000000"
  },
  "diagnostic": null
}
```

---

## 4. References

- [RV Step Specification](../20_coh_kernel/rv_step_spec.md)
- [Budget Law](../10_mathematical_core/budget_law.md)
- [Admissibility Predicate](../10_mathematical_core/admissibility_predicate.md)
