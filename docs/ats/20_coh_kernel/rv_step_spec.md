# RV Step Specification

**Receipt Verifier - Executable Law of ATS**

| Field | Value |
|-------|-------|
| **Module** | 20_coh_kernel |
| **Section** | RV Step Specification |
| **Version** | 1.0.0 |

---

## 1. Overview

The Receipt Verifier (RV) is the **sovereign verification component** of the ATS. Every state transition must pass through RV verification. The RV is a pure function - same inputs always produce same outputs.

---

## 2. RV Interface

### 2.1 Function Signature

```python
def RV(
    state_before: bytes,      # Canonical bytes of x_k
    state_after: bytes,        # Canonical bytes of x_{k+1}
    action: bytes,             # Serialized action
    receipt: Receipt,          # Receipt for this step
    budget_before: QFixed,    # B_k
    budget_after: QFixed,      # B_{k+1}
    kappa: QFixed              # κ constant
) -> (ACCEPT | REJECT(code))
```

### 2.2 Output

```
ACCEPT:
    - receipt_id verified
    - state hashes verified
    - risk delta verified
    - budget law satisfied

REJECT(code):
    - INVALID_ACTION_TYPE
    - INVALID_STATE_SERIALIZATION
    - INVALID_RECEIPT_HASH
    - STATE_HASH_MISMATCH
    - RISK_MISMATCH
    - BUDGET_VIOLATION
    - INVALID_CHAIN_LINK
```

---

## 3. Verification Steps

### Step 1: Recompute State Hash (Before)

```
1. Compute: state_hash_before_computed = sha256(state_before)
2. Compare: state_hash_before_computed == receipt.state_hash_before
3. If mismatch: REJECT("STATE_HASH_MISMATCH")
```

### Step 2: Recompute State Hash (After)

```
1. Compute: state_hash_after_computed = sha256(state_after)
2. Compare: state_hash_after_computed == receipt.state_hash_after
3. If mismatch: REJECT("STATE_HASH_MISMATCH")
```

### Step 3: Compute Risk Before

```
1. Deserialize: risk_before = parse_QFixed(receipt.risk_before_q)
2. Verify: risk_before >= 0
3. (Note: Actual V computation done by untrusted runtime; receipt contains claim)
```

### Step 4: Compute Risk After

```
1. Deserialize: risk_after = parse_QFixed(receipt.risk_after_q)
2. Verify: risk_after >= 0
```

### Step 5: Compute Delta Plus

```
1. Compute: delta = risk_after - risk_before
2. Compute: delta_plus = max(0, delta)
3. Verify: receipt.delta_plus_q == delta_plus
4. If mismatch: REJECT("RISK_MISMATCH")
```

### Step 6: Validate Budget Rule

```
If delta <= 0:
    # Risk decreased - budget preserved
    If budget_after != budget_before:
        REJECT("BUDGET_VIOLATION")

If delta > 0:
    # Risk increased - budget consumed
    required = kappa * delta
    If budget_before < required:
        REJECT("BUDGET_VIOLATION")
    
    expected_after = budget_before - required
    If budget_after != expected_after:
        REJECT("BUDGET_VIOLATION")
```

### Step 7: Validate Receipt Hash

```
1. Compute: receipt_hash_computed = sha256(canonical_bytes(receipt))
2. Compare: receipt_id_computed = first8(receipt_hash_computed)
3. If receipt_id_computed != receipt.receipt_id:
    REJECT("INVALID_RECEIPT_HASH")
```

### Step 8: Validate Chain Link

```
If this is first receipt:
    Verify: receipt.previous_receipt_id == "00000000"
Else:
    Verify: receipt.previous_receipt_id == previous_receipt_id
    Verify: receipt.chain_hash == sha256(prev_id || receipt_id)
```

---

## 4. Complete Pseudocode

```python
def RV(state_before, state_after, action, receipt, 
       budget_before, budget_after, kappa):
    
    # === Step 1: State Hash (Before) ===
    hash_before = sha256(state_before)
    if hash_before != receipt.state_hash_before:
        return REJECT("STATE_HASH_MISMATCH")
    
    # === Step 2: State Hash (After) ===
    hash_after = sha256(state_after)
    if hash_after != receipt.state_hash_after:
        return REJECT("STATE_HASH_MISMATCH")
    
    # === Step 3: Risk Before ===
    risk_before = QFixed(receipt.risk_before_q)
    if risk_before < 0:
        return REJECT("RISK_MISMATCH")
    
    # === Step 4: Risk After ===
    risk_after = QFixed(receipt.risk_after_q)
    if risk_after < 0:
        return REJECT("RISK_MISMATCH")
    
    # === Step 5: Delta Plus ===
    delta = risk_after - risk_before
    delta_plus = max(QFixed(0), delta)
    if delta_plus != QFixed(receipt.delta_plus_q):
        return REJECT("RISK_MISMATCH")
    
    # === Step 6: Budget Law ===
    if delta <= 0:
        # Risk decreased - budget preserved
        if budget_after != budget_before:
            return REJECT("BUDGET_VIOLATION")
    else:
        # Risk increased - budget consumed
        required = kappa * delta
        if budget_before < required:
            return REJECT("BUDGET_VIOLATION")
        
        expected_after = budget_before - required
        if budget_after != expected_after:
            return REJECT("BUDGET_VIOLATION")
    
    # === Step 7: Receipt Hash ===
    receipt_hash = sha256(canonical_bytes(receipt))
    receipt_id_computed = receipt_hash[:8]
    if receipt_id_computed != receipt.receipt_id:
        return REJECT("INVALID_RECEIPT_HASH")
    
    # === Step 8: Chain Link ===
    if receipt.previous_receipt_id != "00000000":
        # (Assumes previous_receipt_id is available)
        if receipt.chain_hash != sha256(prev_id + receipt.receipt_id):
            return REJECT("INVALID_CHAIN_LINK")
    
    # === All Checks Passed ===
    return ACCEPT
```

---

## 5. Error Codes

| Code | Step | Description |
|------|------|-------------|
| `STATE_HASH_MISMATCH` | 1, 2 | State hash does not match receipt |
| `RISK_MISMATCH` | 3, 4, 5 | Risk delta computation incorrect |
| `BUDGET_VIOLATION` | 6 | Budget law not satisfied |
| `INVALID_RECEIPT_HASH` | 7 | Receipt self-invalid |
| `INVALID_CHAIN_LINK` | 8 | Receipt chain broken |

---

## 6. Determinism Guarantees

### 6.1 Pure Function

The RV is a **pure function**:
- No side effects
- Same inputs → same output
- No access to external state

### 6.2 Deterministic Operations

All operations in RV are deterministic:
- SHA-256 (deterministic hash)
- QFixed arithmetic (fixed-point)
- Comparison (total order)

### 6.3 No Timestamps

The RV does **not** use timestamps:
- Step ordering is by index, not time
- Replay is deterministic
- No clock synchronization required

---

## 7. Security Properties

### 7.1 Sovereignty

> **The Receipt Verifier is sovereign. The Runtime is untrusted.**

All verification is done independently.

### 7.2 Fail-Secure

Any verification failure results in rejection:
- No "maybe" states
- No fallback to unsafe paths
- Rejection is always safe

### 7.3 No Trust Required

- RV can be implemented independently
- Same inputs always produce same result
- Verification can be done offline

---

## 8. References

- [ATS Definition](../00_identity/ats_definition.md)
- [Admissibility Predicate](../10_mathematical_core/admissibility_predicate.md)
- [Budget Law](../10_mathematical_core/budget_law.md)
- [Risk Functional V](../10_mathematical_core/risk_functional_V.md)
- [Receipt Schema](./receipt_schema.md)
- [Receipt Identity](./receipt_identity.md)
- [Chain Hash Rule](./chain_hash_rule.md)
- [Rejection Reason Codes](../50_security_model/rejection_reason_codes.md)
