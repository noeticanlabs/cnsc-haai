# Replay Verification

**Deterministic Trajectory Replay**

| Field | Value |
|-------|-------|
| **Module** | 30_ats_runtime |
| **Section** | Replay Verification |
| **Version** | 1.0.0 |

---

## 1. Overview

Replay verification allows independent reconstruction of trajectory execution. Given only the initial state and receipts, any verifier can recompute the final state.

---

## 2. Replay Properties

### 2.1 Determinism

| Property | Guarantee |
|----------|-----------|
| **Same Inputs** | Same outputs (always) |
| **No Randomness** | All operations deterministic |
| **Reproducible** | Any verifier can reproduce |

### 2.2 What Is Replayed

| Data | Source | Purpose |
|------|--------|---------|
| **Initial State** | Provided | Starting point |
| **Receipts** | Provided | Each step's record |
| **Actions** | Implied by receipts | What was executed |

---

## 3. Replay Algorithm

### 3.1 Full Replay

```python
def replay_trajectory(
    initial_state: State,
    receipts: List[Receipt],
    initial_budget: QFixed,
    kappa: QFixed
) -> (final_state, final_budget, result):
    """
    Replay a trajectory from initial state and receipts.
    
    Returns: (final_state, final_budget, verification_result)
    """
    current_state = initial_state
    current_budget = initial_budget
    
    for i, receipt in enumerate(receipts):
        # Verify each step
        result = verify_step(
            current_state,
            receipt,
            current_budget,
            kappa
        )
        
        if result != ACCEPT:
            return current_state, current_budget, result
        
        # Apply step (if we had the action)
        # For pure verification, we don't need to apply
        current_budget = receipt.budget_after_q
    
    return current_state, current_budget, ACCEPT
```

### 3.2 Verification-Only Replay

```python
def verify_trajectory(
    initial_state: State,
    receipts: List[Receipt],
    initial_budget: QFixed,
    kappa: QFixed
) -> result:
    """
    Verify trajectory without applying actions.
    """
    current_state = initial_state
    current_budget = initial_budget
    
    for receipt in receipts:
        # Verify receipt hash
        if not verify_receipt_hash(receipt):
            return REJECT("INVALID_RECEIPT_HASH")
        
        # Verify state hashes
        computed_before = sha256(canonical_bytes(current_state))
        if computed_before != receipt.state_hash_before:
            return REJECT("STATE_HASH_MISMATCH")
        
        # Verify budget law
        delta = receipt.risk_after_q - receipt.risk_before_q
        if not verify_budget_law(current_budget, delta, kappa, receipt.budget_after_q):
            return REJECT("BUDGET_VIOLATION")
        
        # Update for next iteration
        current_budget = receipt.budget_after_q
    
    return ACCEPT
```

---

## 4. Chain Verification

### 4.1 Sequential Verification

```python
def verify_chain(receipts: List[Receipt]) -> bool:
    """Verify receipt chain integrity."""
    for i in range(len(receipts)):
        if i == 0:
            # Genesis receipt
            if receipts[i].previous_receipt_id != "00000000":
                return False
        else:
            # Link to previous
            if receipts[i].previous_receipt_id != receipts[i-1].receipt_id:
                return False
            
            # Verify chain hash
            expected_chain = sha256(
                receipts[i-1].receipt_id + receipts[i].receipt_id
            )
            if receipts[i].chain_digest != expected_chain_digest:
                return False
    
    return True
```

---

## 5. Replay vs Execution

### 5.1 Comparison

| Aspect | Execution | Replay |
|--------|-----------|--------|
| **Input** | State + Action | Receipts only |
| **Output** | New State + Receipt | Verification Result |
| **Runtime** | May be slow | Fast (no execution) |
| **Purpose** | Progress | Verification |

### 5.2 Use Cases

| Use Case | Replay Type |
|----------|-------------|
| **Audit** | Full replay |
| **Debugging** | Step-by-step |
| **Verification** | Receipt-only |
| **Checkpointing** | State reconstruction |

---

## 6. References

- [RV Step Specification](../20_coh_kernel/rv_step_spec.md)
- [Chain Hash Universal](../20_coh_kernel/chain_hash_universal.md)
- [Receipt Identity](../20_coh_kernel/receipt_identity.md)
- [Action Emission Contract](./action_emission_contract.md)
