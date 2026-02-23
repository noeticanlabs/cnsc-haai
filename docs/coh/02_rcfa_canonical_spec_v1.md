# RCFA Canonical Specification

**Recursive Coherence Formal Analysis - Hybrid Viability Engine**

| Field | Value |
|-------|-------|
| **Document** | rcfa.canonical |
| **Version** | 1.0.0 |
| **Status** | ACTIVE |
| **Layer** | L2 (Engine) |
| **Depends On** | [Coh Canonical Spec](00_coh_canonical_spec_v1.md) |

---

## 1. Overview

RCFA (Recursive Coherence Formal Analysis) is the **hybrid viability engine** for Coh systems. It provides:

- **Renormalization**: Bounding coherence drift
- **Unfolding**: Extending coherent traces
- **Finite Precision Bounds**: Guaranteed computational limits
- **Budget Absorption**: Handling resource constraints

RCFA operates on top of the Coh algebra, providing the runtime engine that ensures coherent states remain viable.

---

## 2. Mathematical Framework

### 2.1 Renormalization Operator

The renormalization operator R: X → X bounds coherence drift:

```
R(x) = Π_K(x)
```

Where Π_K is projection onto the admissible set K.

### 2.2 Renorm Bound

For any state x, the renorm satisfies:

```
‖x - R(x)‖ ≤ ε_max
```

Where ε_max is the maximum allowed deviation.

### 2.3 Scale-Free Statistics

RCFA tracks renormalization events to detect scale-free behavior:

```
P(event_size > s) ∝ s^(-α)
```

Where α is the critical exponent (typically α ≈ 1.0 for SOC systems).

---

## 3. Unfolding

### 3.1 Unfold Definition

Unfolding extends a coherent trace by one step:

```
unfold(τ): X → X × Receipt
```

Given current state x ∈ X, produce next state x' and receipt.

### 3.2 Unfold Conditions

An:

```
1 unfold is valid iff. x' = f(x) for some f ∈ Mor(X, X)  (morphism)
2. V(x') ≤ V(x)                       (coherence non-increasing)
3. B(x') ≥ 0                           (budget not exhausted)
4. x' ∈ K                              (admissible)
```

### 3.3 Unfold Failure Modes

| Mode | Condition | Action |
|------|-----------|--------|
| COHERENCE_EXHAUSTED | V(x') > V(x) | Reject transition |
| BUDGET_EXHAUSTED | B(x') < 0 | Halt execution |
| VIABILITY_LOST | x' ∉ K | Trigger renormalization |

---

## 4. Finite Precision Bounds

### 4.1 QFixed Representation

All numerical values use QFixed(18):

```
QFixed = ℤ / 10^18
```

No floating-point in consensus-critical paths.

### 4.2 Precision Drift Bound

After n unfold steps:

```
|true_value - QFixed(approximated_value)| ≤ n × δ
```

Where δ is the per-step drift (typically δ ≤ 10^-12).

### 4.3 Overflow Protection

Maximum values bounded:

```
|V(x)| ≤ V_MAX = 10^60
|RV(x)| ≤ B_MAX = 10^60
```

---

## 5. Budget Absorption

### 5.1 Budget Model

Budget B: X → QFixed(18) tracks resources:

```
B(x) = κ - RV(x)
```

Where κ is initial budget constant.

### 5.2 Absorption Events

When B approaches zero, absorption events occur:

```
If B(x) < B_CRITICAL:
  Trigger renormalization
  Attempt budget recovery
```

### 5.3 Recovery Mechanisms

| Mechanism | Condition | Budget Effect |
|-----------|-----------|---------------|
| IDLE_RECOVERY | No step for τ seconds | +α × τ |
| COHERENCE_SPIKE | V increases | +(V_new - V_old) |
| GARBAGE_COLLECTION | Memory freed | +β × freed |

---

## 6. RCFA State Machine

### 6.1 States

```
enum RCFAState:
    COHERENT      // Normal operation
    RENORMING     // Applying renormalization
    ABSORBING     // Handling budget event
    HALTED        // Cannot proceed
```

### 6.2 Transitions

```
COHERENT → RENORMING:  when ‖x - Π_K(x)‖ > ε_max
COHERENT → ABSORBING: when B(x) < B_CRITICAL
RENORMING → COHERENT: when ‖x - Π_K(x)‖ ≤ ε_max
ABSORBING → COHERENT: when budget recovered
ANY → HALTED:         when budget ≤ 0 and recovery failed
```

### 6.3 State Invariants

```
COHERENT:  V(x) ≤ V_MAX ∧ B(x) ≥ 0 ∧ x ∈ K
RENORMING: ‖x - Π_K(x)‖ decreasing
ABSORBING: B(x) bounded below by B_MIN
HALTED:    ¬∃valid_unfold(x)
```

---

## 7. Verification API

### 7.1 Core Functions

```python
def rcfa_step(x: CohState) -> (CohState, Receipt, RCFAState):
    """
    Execute one RCFA step.
    Returns: (next_state, receipt, new_state)
    """
    
def rcfa_verify(trace: Trace) -> VerificationResult:
    """
    Verify a complete trace.
    Returns: (is_valid, error_details)
    """
    
def renormalize(x: CohState) -> CohState:
    """
    Apply renormalization operator.
    Returns: renormalized state
    """
```

### 7.2 Verification Conditions

A trace is RCFA-valid iff:

```
∀step ∈ trace:
  1. step.state ∈ K                 (admissible)
  2. V(step.state) ≤ V_MAX          (coherence bounded)
  3. B(step.state) ≥ 0              (budget non-negative)
  4. |renorm_error| ≤ ε_max         (precision bound)
```

---

## 8. Receipt Integration

### 8.1 RCFA Receipt Fields

```json
{
  "rcfa_state": "COHERENT",
  "renorm_applied": false,
  "budget_before": "1000000000000000000",
  "budget_after": "900000000000000000",
  "renorm_error": "0",
  "event_type": "UNFOLD"
}
```

### 8.2 Event Types

| Event | Description |
|-------|-------------|
| UNFOLD | Normal state transition |
| RENORM | Renormalization applied |
| ABSORB | Budget absorption event |
| HALT | Execution halted |

---

## 9. Integration with Coh Algebra

### 9.1 Functoriality

RCFA is a **functor** from Coh to RCFA:

```
F: Coh → RCFA

F(X) = (X, K, ε_max)
F(f: X → Y) = rcfa_step(f)
```

### 9.2 Natural Transformations

Budget and coherence map naturally:

```
B_RCFA = B ∘ F^(-1)
V_RCFA = V ∘ F^(-1)
```

---

## 10. RCFA as Coh Object

This section formally maps RCFA to the Coh object structure (X, V, RV) as defined in [Coh Canonical Spec](00_coh_canonical_spec_v1.md).

### 10.1 State Space (X)

RCFA state space is defined as:

```
X_RCFA = (S, E, R, M)
```

Where:
- `S` = belief state (QFixed vector)
- `E` = evidence trace (list of witnessed events)
- `R` = renormalization history (list of renormalization events)
- `M` = memory allocation (QFixed)

This maps to Coh's X as the computational state.

### 10.2 Coherence Functional (V)

RCFA coherence functional maps to Coh's V:

```
V_RCFA(x) = α * Φ_coherence(s) + β * Ψ_budget(b) + γ * Ω_memory(m)
```

Where:
- `Φ_coherence(s)` = coherence measure of belief state
- `Ψ_budget(b)` = budget depletion penalty
- `Ω_memory(m)` = memory efficiency penalty
- `α, β, γ` = policy weights

### 10.3 Risk Value (RV)

RCFA receipt verifier maps to Coh's RV:

```
RV_RCFA(x) = risk_witness(x) + verification_cost(x)
```

Where:
- `risk_witness(x)` = cryptographic proof of coherence bound
- `verification_cost(x)` = computational cost of verification

### 10.4 Morphisms

RCFA unfold operations are Coh morphisms:

```
unfold: X_RCFA → X_RCFA × Receipt

Properties:
1. V_RCFA(x') ≤ V_RCFA(x)  (coherence non-increasing)
2. RV_RCFA(x') ≥ RV_RCFA(x) + Δ  (budget accounting)
3. det(unfold) = true  (deterministic)
```

---

## 11. References

- [Coh Canonical Spec](00_coh_canonical_spec_v1.md)
- [Module Interface Contract](01_coh_module_interface_contract_v1.md)
- [SOC Attractor Conditions](../soc/01_soc_attractor_necessary_conditions.md)
- [Scale-Free Renorm Theorem](../soc/02_scale_free_renorm_theorem_program.md)
- [Runtime Trigger Spec](../soc/03_runtime_trigger_spec.md)

---

## 11. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.1 | 2026-02-23 | Added "RCFA as Coh Object" section (Section 10) |
| 1.0.0 | 2026-02-23 | Initial RCFA canonical form |
