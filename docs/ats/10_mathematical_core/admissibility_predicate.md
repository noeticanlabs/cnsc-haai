# Admissibility Predicate

**Formal Definition of ATS Admissibility**

| Field | Value |
|-------|-------|
| **Module** | 10_mathematical_core |
| **Section** | Admissibility Predicate |
| **Version** | 1.0.0 |

---

## 1. Predicate Definition

The admissibility predicate determines whether a single step is valid within the ATS:

```
Adm(step) : (x_k, a_k, x_{k+1}, B_k, B_{k+1}, ρ_k) → {ACCEPT, REJECT(code)}
```

---

## 2. Component Checks

A step is admissible if and only if all of the following checks pass:

### 2.1 Action Type Validity (AT)

```
AT: a_k ∈ A
```

The action must be a valid element of the action algebra.

**Rejection Code:** `INVALID_ACTION_TYPE`

### 2.2 Deterministic Serialization (DS)

```
DS: 
  - canonical_bytes(x_k) produces valid bytes
  - canonical_bytes(x_{k+1}) produces valid bytes
  - sha256(canonical_bytes(x_k)) = receipt.state_hash_before
  - sha256(canonical_bytes(x_{k+1})) = receipt.state_hash_after
```

**Rejection Code:** `INVALID_STATE_SERIALIZATION`

### 2.3 Receipt Hash Validity (RH)

```
RH: receipt_id = first8(sha256(canonical_receipt_bytes(receipt)))
```

The receipt must be self-consistent.

**Rejection Code:** `INVALID_RECEIPT_HASH`

### 2.4 Risk Delta Verification (RV)

```
RV:
  - V(x_k) = receipt.risk_before_q
  - V(x_{k+1}) = receipt.risk_after_q
  - ΔV_k = receipt.risk_after_q - receipt.risk_before_q
```

Risk values must be recomputed independently.

**Rejection Code:** `RISK_MISMATCH`

### 2.5 Budget Law Satisfaction (BL)

```
BL:
  If ΔV_k ≤ 0:
      B_{k+1} = B_k  (must match receipt)
  
  If ΔV_k > 0:
      Require: B_k ≥ κ × ΔV_k
      B_{k+1} = B_k - κ × ΔV_k
```

**Rejection Code:** `BUDGET_VIOLATION`

---

## 3. Combined Predicate

### 3.1 Full Definition

```
Adm(step) = 
    AT(step) ∧
    DS(step) ∧
    RH(step) ∧
    RV(step) ∧
    BL(step)
```

If any component fails, the step is rejected.

### 3.2 Rejection Codes

| Code | Component | Description |
|------|-----------|-------------|
| `INVALID_ACTION_TYPE` | AT | Action not in algebra |
| `INVALID_STATE_SERIALIZATION` | DS | State hash mismatch |
| `INVALID_RECEIPT_HASH` | RH | Receipt self-invalid |
| `RISK_MISMATCH` | RV | Risk recompute mismatch |
| `BUDGET_VIOLATION` | BL | Budget law not satisfied |

---

## 4. Trajectory Admissibility

### 4.1 Definition

A trajectory τ = (x₀ → x₁ → ... → x_T) is admissible if:

```
∀k ∈ [0, T-1]: Adm(x_k, a_k, x_{k+1}, B_k, B_{k+1}, ρ_k) = ACCEPT
```

### 4.2 Empty Trajectory

The empty trajectory (no steps) is always admissible.

---

## 5. Verification Algorithm

```python
def verify_step(state_before, state_after, action, receipt, 
                budget_before, budget_after, kappa):
    
    # 1. Check action type
    if action not in ACTION_ALGEBRA:
        return REJECT("INVALID_ACTION_TYPE")
    
    # 2. Verify state serialization
    hash_before = sha256(canonical_bytes(state_before))
    hash_after = sha256(canonical_bytes(state_after))
    
    if hash_before != receipt.state_hash_before:
        return REJECT("INVALID_STATE_SERIALIZATION")
    if hash_after != receipt.state_hash_after:
        return REJECT("INVALID_STATE_SERIALIZATION")
    
    # 3. Verify receipt hash
    computed_id = first8(sha256(canonical_receipt_bytes(receipt)))
    if computed_id != receipt.receipt_id:
        return REJECT("INVALID_RECEIPT_HASH")
    
    # 4. Verify risk delta
    risk_before = V(state_before)
    risk_after = V(state_after)
    
    if risk_before != receipt.risk_before_q:
        return REJECT("RISK_MISMATCH")
    if risk_after != receipt.risk_after_q:
        return REJECT("RISK_MISMATCH")
    
    delta = risk_after - risk_before
    
    # 5. Verify budget law
    if delta <= 0:
        if budget_after != budget_before:
            return REJECT("BUDGET_VIOLATION")
    else:
        required = kappa * delta
        if budget_before < required:
            return REJECT("BUDGET_VIOLATION")
        expected_after = budget_before - required
        if budget_after != expected_after:
            return REJECT("BUDGET_VIOLATION")
    
    return ACCEPT
```

---

## 6. References

- [ATS Definition](../00_identity/ats_definition.md)
- [Budget Law](./budget_law.md)
- [Risk Functional V](./risk_functional_V.md)
- [RV Step Specification](../20_coh_kernel/rv_step_spec.md)
- [Rejection Reason Codes](../50_security_model/rejection_reason_codes.md)
