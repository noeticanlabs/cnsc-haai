# ATS Definition

**Admissible Trajectory Space - Formal Mathematical Definition**

| Field | Value |
|-------|-------|
| **Module** | 00_identity |
| **Section** | ATS Definition |
| **Version** | 1.0.0 |

---

## 1. ATS Tuple Definition

An **Admissible Trajectory Space (ATS)** is formally defined as a 5-tuple:

```
ATS = (X, A, V, B, RV)
```

Where:

| Component | Type | Description |
|-----------|------|-------------|
| **X** | State Space | Canonical cognitive state space (deterministically serializable) |
| **A** | Action Algebra | Typed NSC operations / cognitive updates |
| **V** | Risk Functional | Deterministic risk mapping V: X → Q≥0 |
| **B** | Budget | Non-negative budget bound B ∈ Q≥0 |
| **RV** | Receipt Verifier | Deterministic verification predicate |

---

## 2. Component Specifications

### 2.1 State Space (X)

The canonical state space is structured as a Cartesian product:

```
X = X_belief × X_memory × X_plan × X_policy × X_io
```

Where each component must satisfy:
- **Canonical Serializability**: Every state x ∈ X has a deterministic byte representation
- **Deterministic Hashing**: sha256(canonical_bytes(x)) produces a unique state digest
- **Type Safety**: Each component has a static type known at verification time

### 2.2 Action Algebra (A)

The action algebra comprises typed cognitive operations:

```
A = { act | act : X → X }
```

Actions include:
- **Belief Updates**: Modify X_belief
- **Memory Operations**: Read/write X_memory
- **Planning Steps**: Update X_plan
- **Policy Adjustments**: Modify X_policy
- **I/O Operations**: Interact with X_io

### 2.3 Risk Functional (V)

The risk functional is a deterministic mapping:

```
V : X → Q≥0
```

Requirements:
- **Deterministic**: V(x) = V(x) always
- **Fixed-Point Domain**: Uses QFixed(18) or scaled int64
- **No Floats**: Binary floating-point forbidden in consensus-critical paths
- **Monotone Guard Semantics**: V measures "coherence distance" from ideal state

### 2.4 Budget (B)

The budget is a non-negative quantity:

```
B ∈ Q≥0
```

The budget law governs how risk accumulation affects available budget:
- If ΔV ≤ 0 (risk decreased): B_next = B_prev (no budget consumed)
- If ΔV > 0 (risk increased): B_next = B_prev − κ·ΔV (budget consumed)

### 2.5 Receipt Verifier (RV)

The receipt verifier is a deterministic predicate:

```
RV : State × Action × State × Budget × Budget × Receipt → {ACCEPT, REJECT(code)}
```

The verifier checks:
1. State hash correctness (before and after)
2. Risk delta computation
3. Budget law compliance
4. Receipt chain integrity

---

## 3. Admissible Trajectory

An **admissible trajectory** is a finite sequence:

```
τ = (x₀ → x₁ → ... → x_T)
```

Such that for every step k ∈ [0, T-1]:

```
RV(x_k, a_k, x_{k+1}, B_k, B_{k+1}, ρ_k) = ACCEPT
```

Where:
- x_k ∈ X is the state at step k
- a_k ∈ A is the action applied at step k
- B_k is the budget before step k
- B_{k+1} is the budget after step k
- ρ_k is the receipt for step k

---

## 4. The ATS Theorem

### Theorem: Budget Invariant

Given an ATS with initial budget B₀ and constant κ > 0:

```
Σ_{k=0}^{T-1} max(0, V(x_{k+1}) - V(x_k)) ≤ B₀ / κ
```

**Proof Sketch**: By induction on trajectory length, using the budget law update rule. ∎

### Corollary: Bounded Risk Accumulation

No admissible trajectory can accumulate more risk than the initial budget permits. This provides **deterministic termination guarantees** for cognitive systems.

---

## 5. Relationship to Coh

Coh (Coherence) is the **enforcement mechanism** of ATS:

| Coh Property | ATS Manifestation |
|--------------|-------------------|
| Risk Monotonicity | V(x_{k+1}) ≤ V(x_k) + κ·B_k |
| Budget Boundedness | Σ(ΔV)^+ ≤ B₀ / κ |
| Deterministic Verification | RV is a pure function |

---

## 6. References

- [Project Identity](./project_identity.md)
- [Coh Kernel Scope](./coh_kernel_scope.md)
- [State Space Definition](../10_mathematical_core/state_space.md)
- [Risk Functional V](../10_mathematical_core/risk_functional_V.md)
- [Budget Law](../10_mathematical_core/budget_law.md)
