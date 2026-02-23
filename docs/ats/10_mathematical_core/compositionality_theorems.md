# Compositionality Theorems

**Theorems for Composing ATS Components**

| Field | Value |
|-------|-------|
| **Module** | 10_mathematical_core |
| **Section** | Compositionality Theorems |
| **Version** | 1.0.0 |

---

## 1. Compositional Receipt Theorem

### Theorem: Receipt Composition

Given two consecutive admissible steps:

```
Step 1: (x₀ → x₁) with receipt ρ₀
Step 2: (x₁ → x₂) with receipt ρ₁
```

The composed receipt ρ₁₂ satisfies:

```
receipt_id(ρ₁₂) = first8(sha256(
    canonical_bytes(ρ₀) ||
    canonical_bytes(ρ₁)
))
```

**Proof:** By definition of chain digest (see [Chain Hash Universal](../20_coh_kernel/chain_hash_universal.md)), receipts chain via SHA-256 concatenation. ∎

---

## 2. Budget Composition Theorem

### Theorem: Budget Invariant Under Composition

If τ₁ and τ₂ are admissible trajectories with budgets B₁ and B₂ respectively, and the terminal state of τ₁ equals the initial state of τ₂, then:

```
Budget(τ₁ ; τ₂) = Budget(τ₁) - Budget_consumed(τ₁)
```

Where:

```
Budget_consumed(τ) = Σ_{k} κ × max(0, ΔV_k)
```

**Proof:** Direct application of the budget law (see [Budget Law](./budget_law.md)) to each step. ∎

---

## 3. Risk Composition Theorem

### Theorem: Risk Aggregation

For a composed trajectory τ = τ₁ ; τ₂:

```
V(x_final) = V(x_initial) + Σ ΔV_k
```

The total risk delta equals the sum of step deltas.

**Proof:** By definition of V as a function, V(x₂) - V(x₀) = [V(x₁) - V(x₀)] + [V(x₂) - V(x₁)] = ΔV₀ + ΔV₁. ∎

---

## 4. State Composition Theorem

### Theorem: Component Independence

State components are composable if and only if they operate on disjoint subspaces:

```
X = X₁ × X₂

If act₁ : X₁ → X₁ and act₂ : X₂ → X₂,
then (act₁, act₂) : X → X is valid.

However, if act₁ : X → X and act₂ : X → X,
composition requires proof of non-interference.
```

**Proof:** Follows from the definition of X as a Cartesian product. ∎

---

## 5. Action Composition Theorems

### Theorem: Sequential Composition

If act₁ : X → X and act₂ : X → X are both valid actions, then:

```
act₁ ; act₂ : X → X
```

is also a valid action (composition of deterministic functions).

**Proof:** The composition of deterministic functions is deterministic. ∎

### Theorem: Parallel Composition

For state components X = X_a × X_b:

```
If act_a : X_a → X_a
and act_b : X_b → X_b
then (act_a || act_b) : X → X
```

is valid and:

```
V(x') = V(act_a(x_a), act_b(x_b)) = V(x)
       + V_a(x_a') - V_a(x_a)
       + V_b(x_b') - V_b(x_b)
```

---

## 6. Admissibility Composition Theorem

### Theorem: Transitive Admissibility

If τ₁ = (x₀ → ... → x_n) is admissible and τ₂ = (x_n → ... → x_m) is admissible, then:

```
τ = τ₁ ; τ₂ = (x₀ → ... → x_m)
```

is admissible.

**Proof:** By induction on the admissibility predicate. Each step in τ₁ satisfies Adm, each step in τ₂ satisfies Adm, therefore all steps in τ satisfy Adm. ∎

---

## 7. Verification Scaling Theorem

### Theorem: Verification Complexity

For a trajectory of length T:

```
Time(verify(τ)) = O(T)
Space(verify(τ)) = O(1) + O(T) for receipt storage
```

Verification is linear in trajectory length because:
- Each step requires constant-time hash verification
- Each step requires constant-time budget check
- Receipts can be verified independently

---

## 8. References

- [ATS Definition](../00_identity/ats_definition.md)
- [Budget Law](./budget_law.md)
- [Risk Functional V](./risk_functional_V.md)
- [Chain Hash Universal](../20_coh_kernel/chain_hash_universal.md)
- [RV Step Specification](../20_coh_kernel/rv_step_spec.md)
