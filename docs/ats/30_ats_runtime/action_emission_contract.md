# Action Emission Contract

**Contract Between Runtime and ATS Kernel**

| Field | Value |
|-------|-------|
| **Module** | 30_ats_runtime |
| **Section** | Action Emission Contract |
| **Version** | 1.0.0 |

---

## 1. Overview

The Action Emission Contract defines the interface between the untrusted runtime (NSC VM) and the ATS kernel. The runtime emits actions; the kernel verifies them.

---

## 2. Contract Parties

### 2.1 Runtime (Untrusted)

```
┌─────────────────────────────────────────────┐
│              NSC VM Runtime                  │
│  - Executes cognitive programs              │
│  - Produces state transitions              │
│  - Emits receipts                          │
│  - UNTRUSTED                               │
└─────────────────────────────────────────────┘
```

### 2.2 Kernel (Trusted)

```
┌─────────────────────────────────────────────┐
│              ATS Kernel                      │
│  - Verifies receipts                        │
│  - Enforces budget law                     │
│  - Issues ACCEPT/REJECT                    │
│  - TRUSTED                                 │
└─────────────────────────────────────────────┘
```

---

## 3. Emission Interface

### 3.1 Runtime → Kernel

```python
def emit_step(
    state_before: State,
    action: Action,
    state_after: State,
    budget_before: QFixed,
    budget_after: QFixed,
    kappa: QFixed
) -> Receipt
```

### 3.2 Kernel → Runtime

```python
# Returns:
ACCEPT:
    receipt: Receipt
    next_state: State
    next_budget: QFixed

REJECT(code):
    error_code: str
    reason: str
    diagnostic: bytes (optional)
```

---

## 4. Required Data for Emission

### 4.1 Pre-Step Data

| Data | Source | Description |
|------|--------|-------------|
| **state_before** | Runtime | Current cognitive state |
| **action** | Runtime | Action to execute |
| **budget_before** | Kernel | Current budget |

### 4.2 Post-Step Data

| Data | Source | Description |
|------|--------|-------------|
| **state_after** | Runtime | State after action |
| **risk_before** | Runtime | V(state_before) claim |
| **risk_after** | Runtime | V(state_after) claim |
| **budget_after** | Runtime | Budget after action |

---

## 5. Receipt Emission Flow

### 5.1 Step Execution

```
1. Runtime has state x_k and budget B_k
2. Runtime selects action a_k
3. Runtime executes action → produces x_{k+1}
4. Runtime computes risk claims:
   - r_k = V(x_k)
   - r_{k+1} = V(x_{k+1})
5. Runtime computes budget claim:
   - B_{k+1} = budget_after_action
6. Runtime constructs receipt with all claims
7. Runtime sends to Kernel for verification
```

### 5.2 Kernel Verification

```
1. Kernel recomputes:
   - state_hash_before = sha256(x_k)
   - state_hash_after = sha256(x_{k+1})
   - delta = r_{k+1} - r_k
   - budget check per law
2. Kernel verifies receipt hash
3. Kernel returns ACCEPT or REJECT
```

---

## 6. Contract Invariants

### 6.1 State Validity

The runtime must ensure:
- `state_before` is valid X
- `state_after` is valid X
- `action` is valid A

### 6.2 Claim Honesty

The runtime honestly claims:
- Risk values computed (even if incorrectly)
- Budget values per budget law
- No fabricated data

### 6.3 Kernel Skepticism

The kernel verifies:
- All hashes recomputed
- All deltas recomputed
- All budgets recomputed

---

## 7. Failure Modes

### 7.1 Runtime Failures

| Failure | Kernel Response |
|---------|-----------------|
| Invalid state serialization | REJECT |
| Invalid action type | REJECT |
| Non-deterministic execution | REJECT (detected by hash mismatch) |

### 7.2 Verification Failures

| Failure | Kernel Response |
|---------|-----------------|
| Hash mismatch | REJECT |
| Budget violation | REJECT |
| Receipt invalid | REJECT |

---

## 8. Example Flow

### 8.1 Runtime Code

```python
# Step execution
state = current_state
budget = current_budget
action = select_action(state)

# Execute
new_state = action.execute(state)

# Compute risk claims
risk_before = V(state)
risk_after = V(new_state)

# Compute budget
if risk_after <= risk_before:
    budget_after = budget
else:
    delta = risk_after - risk_before
    budget_after = budget - kappa * delta

# Emit receipt
receipt = Receipt(
    state_hash_before=sha256(state),
    state_hash_after=sha256(new_state),
    risk_before_q=str(risk_before),
    risk_after_q=str(risk_after),
    budget_before_q=str(budget),
    budget_after_q=str(budget_after),
    kappa_q=str(kappa)
)

# Verify
result = kernel.verify(state, new_state, action, receipt, budget, budget_after, kappa)
```

### 8.2 Kernel Response

```python
if result == ACCEPT:
    current_state = new_state
    current_budget = budget_after
else:
    rollback()
    raise VerificationError(result.reason)
```

---

## 9. References

- [RV Step Specification](../20_coh_kernel/rv_step_spec.md)
- [Action Algebra](../10_mathematical_core/action_algebra.md)
- [State Space](../10_mathematical_core/state_space.md)
- [Budget Law](../10_mathematical_core/budget_law.md)
- [Risk Functional V](../10_mathematical_core/risk_functional_V.md)
- [NSC Integration](../40_nsc_integration/nsc_vm_to_ats_bridge.md)
