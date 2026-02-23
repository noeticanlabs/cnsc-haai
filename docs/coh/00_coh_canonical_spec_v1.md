# Coh Canonical Specification

**Mathematical Foundation for Coherent Autonomous Systems**

| Field | Value |
|-------|-------|
| **Document** | coh.canonical |
| **Version** | 1.0.0 |
| **Status** | ACTIVE |
| **Layer** | L1 (Constitutional) |

---

## 1. Overview

This document defines the **Coh algebra** — the mathematical foundation upon which all coherent autonomous systems are built. It provides:

- **Object definition**: The canonical form of a coherent state
- **Morphism preservation**: How states evolve while preserving coherence
- **Trace closure**: How reasoning chains maintain integrity
- **Determinism canon**: Ensuring reproducible computation
- **PhaseLoom extension**: Integration with the PhaseLoom categorical framework

---

## 2. Object Definition

### 2.1 Canonical Object Structure

A Coh object is a tuple:

```
CohObject = (X, V, RV)
```

Where:

| Component | Type | Description |
|-----------|------|-------------|
| **X** | StateSpace | The computational state (belief, memory, plan, policy, I/O) |
| **V** | CoherenceFunctional | V: X → ℝ∪{+∞} — measures coherence of state |
| **RV** | RiskValue | RV: X → QFixed(18) — quantifies risk/cost |

### 2.2 Axioms

The canonical object MUST satisfy:

1. **Properness**: V(x) ≥ 0 for all x ∈ X, V(x) = +∞ outside domain
2. **Lower Semicontinuity**: liminf V(xₙ) ≥ V(x) when xₙ → x
3. **Convexity**: V(λx + (1-λ)y) ≤ λV(x) + (1-λ)V(y) for λ ∈ [0,1]
4. **Boundedness**: RV(x) ≤ B_max for all x (budget constraint)

---

## 3. Morphisms

### 3.1 Morphism Definition

A Coh morphism f: X → Y is a function that preserves coherence:

```
f ∈ Mor(X, Y) ⟺:
  1. ∀x ∈ X: V_Y(f(x)) ≤ V_X(x)  (coherence non-increasing)
  2. RV_Y(f(x)) ≥ RV_X(x) + Δ    (budget accounts for transition)
  3. det(f) = deterministic        (same input → same output)
```

### 3.2 Composition

Morphism composition preserves coherence:

```
f: X → Y, g: Y → Z
(g ∘ f): X → Z

V_Z(g(f(x))) ≤ V_Y(f(x)) ≤ V_X(x)
```

### 3.3 Identity Morphism

The identity morphism id_X: X → X satisfies:

```
id_X(x) = x
V_X(id_X(x)) = V_X(x)
RV_X(id_X(x)) = RV_X(x)
```

---

## 4. Trace Closure

### 4.1 Trace Definition

A **trace** is a finite sequence of morphisms:

```
τ = (f₁: X₀ → X₁, f₂: X₁ → X₂, ..., fₙ: Xₙ₋₁ → Xₙ)
```

### 4.2 Trace Coherence

A trace is coherent if:

```
∀i ∈ [1, n]: fᵢ ∈ Mor(Xᵢ₋₁, Xᵢ)
```

### 4.3 Trace Closure Property

The set of all coherent traces is **closed under concatenation**:

```
If τ₁ = (f₁, ..., fₖ) and τ₂ = (g₁, ..., gₘ) are coherent
Then τ = (f₁, ..., fₖ, g₁, ..., gₘ) is also coherent
```

### 4.4 Trace Integrity (Chain Hash)

Each trace generates a canonical hash:

```
chain_digest(τ) = H(chain_digest(τ[:-1]), receipt_id(fₙ))
```

Where `receipt_id` is the canonical content hash of the morphism fₙ.

---

## 5. Determinism Canon

### 5.1 Determinism Requirement

All morphisms MUST be deterministic:

```
∀x ∈ X: f(x) = unique_output
```

### 5.2 Canonical Serialization

To ensure determinism, every object is serialized using **JCS** (RFC 8785):

```
canonical_bytes(x) = JCS.encode(x)
hash(x) = SHA256(domain + canonical_bytes(x))
```

### 5.3 Domain Separation

| Context | Domain Separator |
|---------|-----------------|
| Receipt ID | `COH_RECEIPT_ID_V1\n` |
| Chain Digest | `COH_CHAIN_DIGEST_V1\n` |
| State Hash | `COH_STATE_HASH_V1\n` |
| Risk Value | `COH_RISK_VALUE_V1\n` |

---

## 6. PhaseLoom Extension

### 6.1 Category Structure

Coh objects form a **category** with:

- **Objects**: CohObject = (X, V, RV)
- **Morphisms**: coherent state transitions
- **Composition**: trace concatenation
- **Identity**: identity morphism

### 6.2 Functoriality

The budget law acts as a **functor** from Coh to ℝ:

```
B: Coh → ℝ
B(f: X → Y) = V_Y(f(x)) - V_X(x)  (budget consumption)
```

### 6.3 Natural Transformations

RiskWitness is a natural transformation:

```
RV: Id_Coh → ℝ
```

---

## 7. Budget Law Integration

### 7.1 Budget Functional

The budget B: X → QFixed(18) is defined:

```
B(x) = κ - RV(x)
```

Where κ is the initial budget (constant).

### 7.2 Budget Conservation

For any morphism f: X → Y:

```
B(Y) = B(X) - ΔV + R

Where:
  ΔV = V(Y) - V(X)  (coherence consumed)
  R ≥ 0              (recovery term)
```

### 7.3 Lyapunov Property

V(x) serves as a Lyapunov function:

```
dV/dt ≤ 0  along coherent trajectories
```

---

## 8. Verification Contract

### 8.1 Receipt Requirements

Every morphism f MUST produce a receipt containing:

```json
{
  "receipt_id": "sha256:...",      // Content hash
  "chain_digest": "sha256:...",    // History hash  
  "content": {
    "V_before": "QFixed",
    "V_after": "QFixed",
    "RV_before": "QFixed",
    "RV_after": "QFixed"
  }
}
```

### 8.2 Verification Conditions

A receipt is valid iff:

```
1. receipt_id = hash(content)
2. chain_digest = hash(prev_chain_digest, receipt_id)
3. V_after ≤ V_before
4. B_after = B_before - (V_before - V_after) + R
```

---

## 9. References

- [Module Interface Contract](01_coh_module_interface_contract_v1.md)
- [State Space](../ats/10_mathematical_core/state_space.md)
- [Risk Functional V](../ats/10_mathematical_core/risk_functional_V.md)
- [Budget Law](../ats/10_mathematical_core/budget_law.md)
- [Chain Hash Universal](../ats/20_coh_kernel/chain_hash_universal.md)
- [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785) - JCS

---

## 10. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-02-23 | Initial canonical form |
