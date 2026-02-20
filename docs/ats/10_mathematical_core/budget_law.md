# Budget Law

**Canonical Admissibility Rule for Risk Accumulation**

| Field | Value |
|-------|-------|
| **Module** | 10_mathematical_core |
| **Section** | Budget Law |
| **Version** | 1.0.0 |

---

## 1. Budget Law Statement

The Budget Law is the canonical admissibility rule governing risk accumulation:

```
Given:
  - B_k ∈ Q≥0 = budget at step k
  - ΔV_k = V(x_{k+1}) - V(x_k) = risk delta
  - κ ∈ Q>0 = risk coefficient (constant)

Update Rule:
  If ΔV_k ≤ 0:
      B_{k+1} = B_k                    # No budget consumed
  
  If ΔV_k > 0:
      Require: B_k ≥ κ·ΔV_k             # Sufficient budget
      B_{k+1} = B_k - κ·ΔV_k           # Budget consumed
```

---

## 2. The Core ATS Theorem

### Theorem: Budget Invariant

For any admissible trajectory τ = (x₀ → x₁ → ... → x_T) with initial budget B₀:

```
Σ_{k=0}^{T-1} (ΔV_k)^+ ≤ B₀ / κ
```

Where (ΔV_k)^+ = max(0, ΔV_k)

### Proof

By induction on trajectory length:

**Base Case (k=0):**
- If ΔV₀ ≤ 0: Σ = 0 ≤ B₀/κ ✓
- If ΔV₀ > 0: Require B₀ ≥ κ·ΔV₀, then Σ = ΔV₀ ≤ B₀/κ ✓

**Inductive Step:**
- Assume Σ_{i=0}^{k-1} (ΔV_i)^+ ≤ B₀/κ
- At step k:
  - If ΔV_k ≤ 0: Σ_k = Σ_{k-1} ≤ B₀/κ ✓
  - If ΔV_k > 0: Require B_k ≥ κ·ΔV_k
    - B_k = B₀ - κ·Σ_{k-1} ≥ κ·ΔV_k
    - Σ_k = Σ_{k-1} + ΔV_k ≤ B₀/κ ✓

∎

---

## 3. Budget Parameter (κ)

### 3.1 Definition

κ (kappa) is the **risk coefficient** - a constant that converts risk delta to budget consumption:

```
budget_consumed = κ × risk_increase
```

### 3.2 Selection

| κ Value | Behavior |
|---------|----------|
| **κ = 1** | 1:1 mapping (strict budget) |
| **0 < κ < 1** | Budget conserved (generous) |
| **κ > 1** | Budget depleted faster (conservative) |

### 3.3 Fixed Constant

κ is a **constant parameter** of the ATS instance:
- Set at initialization
- Cannot change during execution
- Stored in receipt for verification

---

## 4. Budget States

### 4.1 Valid Budget

A budget B is valid if:

```
B ∈ Q≥0  AND  B ≥ 0
```

### 4.2 Budget Exhaustion

When B = 0 and ΔV > 0:

```
If B_k = 0 AND ΔV_k > 0:
    REJECT: INSUFFICIENT_BUDGET
```

### 4.3 Negative Budget Forbidden

Negative budgets are invalid:

```
∀k: B_k ≥ 0
```

Any step resulting in B < 0 is rejected.

---

## 5. Budget Transition Examples

### Example 1: Pure Descent

```
B₀ = 100, κ = 1
Step 0: V: 50 → 30 (ΔV = -20) → B₁ = 100
Step 1: V: 30 → 10 (ΔV = -20) → B₂ = 100
Step 2: V: 10 → 0  (ΔV = -10) → B₃ = 100

Result: ACCEPT (budget never consumed)
```

### Example 2: Controlled Ascent

```
B₀ = 100, κ = 1
Step 0: V: 0 → 30  (ΔV = +30) → B₁ = 70
Step 1: V: 30 → 50 (ΔV = +20) → B₂ = 50
Step 2: V: 50 → 40 (ΔV = -10) → B₃ = 50

Result: ACCEPT (budget consumed = 30 + 20 = 50 ≤ 100)
```

### Example 3: Overbudget Rejection

```
B₀ = 100, κ = 1
Step 0: V: 0 → 60  (ΔV = +60) → B₁ = 40
Step 1: V: 40 → 90 (ΔV = +50) → REJECT!

Reason: B₁ = 40 < κ × ΔV = 1 × 50 = 50
```

---

## 6. Implementation

### 6.1 Budget Check Pseudocode

```python
def check_budget(budget_before, risk_delta, kappa):
    if risk_delta <= 0:
        # Risk decreased: budget preserved
        return budget_before, ACCEPT
    
    # Risk increased: check sufficiency
    required = kappa * risk_delta
    if budget_before < required:
        return None, REJECT(INSUFFICIENT_BUDGET)
    
    # Budget consumed
    budget_after = budget_before - required
    return budget_after, ACCEPT
```

### 6.2 Serialization

Budgets serialize as QFixed(18):

```json
{
  "budget_before_q": "1000000000000000000",
  "budget_after_q": "700000000000000000",
  "kappa_q": "1000000000000000000"
}
```

---

## 7. References

- [ATS Definition](../00_identity/ats_definition.md)
- [Risk Functional V](./risk_functional_V.md)
- [Admissibility Predicate](./admissibility_predicate.md)
- [RV Step Specification](../20_coh_kernel/rv_step_spec.md)
