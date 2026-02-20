# Risk Functional V

**Deterministic Risk Mapping**

| Field | Value |
|-------|-------|
| **Module** | 10_mathematical_core |
| **Section** | Risk Functional |
| **Version** | 1.0.0 |

---

## 1. Risk Functional Definition

The risk functional V is a deterministic mapping from states to non-negative rationals:

```
V : X → Q≥0
```

Where Q≥0 represents the domain of non-negative fixed-point numbers (QFixed(18) or scaled int64).

---

## 2. Mathematical Properties

### 2.1 Determinism

```
∀x ∈ X: V(x) = V(x)
```

The same state always produces the same risk value. No randomness permitted.

### 2.2 Non-Negativity

```
∀x ∈ X: V(x) ≥ 0
```

Risk is always non-negative.

### 2.3 Fixed-Point Domain

| Property | Specification |
|----------|---------------|
| **Primary** | QFixed(18) - 18 decimal places |
| **Fallback** | Scaled int64 - 10^18 multiplier |
| **Forbidden** | Binary floating-point (float32, float64) |

---

## 3. Risk Interpretation

### 3.1 Coherence Distance

V(x) measures the "distance from ideal coherence":

| V(x) | Interpretation |
|------|----------------|
| **0** | Perfect coherence (ideal state) |
| **Low** | Minor inconsistencies detected |
| **High** | Significant coherence violations |
| **Maximum** | Critical failure state |

### 3.2 Components

V(x) aggregates multiple coherence metrics:

```
V(x) = w₁·V_belief(x_belief) + w₂·V_memory(x_memory) + w₃·V_plan(x_plan) + w₄·V_policy(x_policy) + w₅·V_io(x_io)
```

Where weights w_i ∈ Q≥0 sum to 1.

---

## 4. Risk Delta

### 4.1 Definition

The risk delta at step k is:

```
ΔV_k = V(x_{k+1}) - V(x_k)
```

### 4.2 Delta Classification

| Case | Classification | Budget Impact |
|------|---------------|---------------|
| **ΔV_k ≤ 0** | Risk Decrease | No budget consumed |
| **ΔV_k > 0** | Risk Increase | Budget consumed: κ·ΔV_k |

### 4.3 Positive Accumulation

```
(ΔV_k)^+ = max(0, ΔV_k)
```

Cumulative positive risk:

```
Σ (ΔV_k)^+  (sum over trajectory)
```

---

## 5. Formal Budget Rule

### 5.1 Update Rule

Given budget B_k and constant κ > 0:

```
If ΔV_k ≤ 0:
    B_{k+1} = B_k

If ΔV_k > 0:
    Require: B_k ≥ κ·ΔV_k
    B_{k+1} = B_k - κ·ΔV_k
```

### 5.2 Invariant

For trajectory τ with B₀:

```
Σ_{k=0}^{T-1} (ΔV_k)^+ ≤ B₀ / κ
```

This is the **core ATS theorem**.

---

## 6. Implementation Requirements

### 6.1 No Floats

```python
# WRONG - uses float
def V_bad(state):
    return state.dynamical**2 + state.clock**2

# CORRECT - uses QFixed
def V_good(state):
    return (state.dynamical_sq + state.clock_sq) >> SCALE
```

### 6.2 Deterministic Operations

All operations must be deterministic:
- Addition
- Subtraction  
- Multiplication (with scaling)
- Comparison

### 6.3 Overflow Handling

| Scenario | Behavior |
|----------|----------|
| **Overflow** | Reject step |
| **Underflow** | Treat as 0 |
| **NaN** | Reject step |
| **Infinity** | Reject step |

---

## 7. Example Computation

### 7.1 State Input

```python
state = {
    "belief": {"concept_a": [0.8, 0.2]},
    "memory": [Cell(1), Cell(2)],
    "plan": [Action("step1"), Action("step2")],
    "policy": {"state_1": {"action_a": 0.9}},
    "io": {"input": [], "output": []}
}
```

### 7.2 Risk Computation

```python
V_before = QFixed(100)  # 1.00 in QFixed(2)
V_after  = QFixed(80)   # 0.80 in QFixed(2)

delta = V_after - V_before  # -20
# ΔV ≤ 0: no budget consumed
```

---

## 8. References

- [ATS Definition](../00_identity/ats_definition.md)
- [Budget Law](./budget_law.md)
- [Deterministic Numeric Domain](../20_coh_kernel/deterministic_numeric_domain.md)
- [Admissibility Predicate](./admissibility_predicate.md)
