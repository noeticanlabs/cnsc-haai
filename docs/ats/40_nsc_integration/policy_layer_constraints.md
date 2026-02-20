# Policy Layer Constraints

**ATS Constraints on NSC Policy Layer**

| Field | Value |
|-------|-------|
| **Module** | 40_nsc_integration |
| **Section** | Policy Layer Constraints |
| **Version** | 1.0.0 |

---

## 1. Overview

The NSC policy layer defines how the system selects actions. ATS imposes constraints to ensure policy operations remain verifiable and deterministic.

---

## 2. Policy Constraints

### 2.1 Determinism Requirement

All policy decisions must be deterministic:

```
policy.select(state) = policy.select(state)  # Always
```

### 2.2 No Randomness

| Prohibited | Reason |
|-----------|--------|
| **Random number generation** | Non-deterministic |
| **External API calls** | Non-deterministic |
| **Time-dependent decisions** | Platform-dependent |
| **Floating-point probabilities** | Precision issues |

### 2.3 Policy Representation

```
Policy = Map[StateRegion, Action]
```

Where:
- **StateRegion**: Deterministic key from state
- **Action**: Discrete action choice

---

## 3. Budget-Aware Policy

### 3.1 Budget Consideration

Policies should consider available budget:

```python
def budget_aware_select(policy, state, budget):
    """Select action considering budget."""
    candidates = policy.get_candidates(state)
    
    # Filter by affordability
    affordable = [
        a for a in candidates
        if budget >= estimate_cost(a, state)
    ]
    
    if not affordable:
        return None  # No affordable action
    
    return policy.select(affordable)
```

### 3.2 Cost Estimation

Policies must estimate action costs:

```python
def estimate_cost(action, state) -> QFixed:
    """Estimate budget cost of action."""
    # Deterministic cost estimation
    return compute_risk_delta(action, state) * kappa
```

---

## 4. Policy Updates

### 4.1 Versioning

Policy updates are versioned:

```json
{
  "policy_version": "v1",
  "previous_version": "v0",
  "update_type": "REINFORCE",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 4.2 Update Constraints

| Constraint | Description |
|------------|-------------|
| **Immutable history** | Old versions preserved |
| **Deterministic updates** | Same update rule, same result |
| **Reversible** | Can rollback to previous version |

---

## 5. Policy Verification

### 5.1 Verification Checklist

| Check | Description |
|-------|-------------|
| **Determinism** | Same state → same action |
| **Boundedness** | No infinite loops |
| **Budget awareness** | Considers available budget |
| **Type safety** | All actions well-typed |

### 5.2 Verification Process

```python
def verify_policy(policy) -> bool:
    # Check determinism on sample states
    for state in sample_states:
        result1 = policy.select(state)
        result2 = policy.select(state)
        if result1 != result2:
            return False
    
    return True
```

---

## 6. References

- [NSC VM to ATS Bridge](./nsc_vm_to_ats_bridge.md)
- [Cognitive System Embedding](./cognitive_system_embedding.md)
- [Budget Law](../10_mathematical_core/budget_law.md)
- [Action Algebra](../10_mathematical_core/action_algebra.md)
