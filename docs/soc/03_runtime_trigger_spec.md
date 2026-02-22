# Runtime Trigger Specification

This document defines the **runtime quantities** and **exact acceptance predicate** for renormalization criticality triggers.

---

## 1. Core Runtime Quantities

### Operator Criticality Metric

The operator criticality is computed as:
$$\sigma = \eta(B) \cdot \|A\|_{bound} \cdot g$$

Where:
- $\eta(B)$: Prox contractivity factor
- $\|A\|_{bound}$: Safe upper bound on operator norm
- $g$: NPE gain factor

### Prox Contractivity Factor

$$\eta(B) = \frac{1}{1 + \mu c B}$$

**Properties:**
- Decreases with budget $B$ (more budget → stronger contraction)
- $\eta(B) \in (0, 1]$ for $B \geq 0$
- At $B = 0$: $\eta(0) = 1$ (no prox, no contraction from regularization)
- As $B \to \infty$: $\eta(B) \to 0$ (strong prox forces contraction)

### Safe Norm Bound

Two options for $\|A\|_{bound}$:

#### Option A: Symmetric Case
For symmetric operators $A = A^T$:
$$\|A\|_{bound} = \|A\|_2 \leq \|A\|_F \leq \|A\|_\infty$$

Can safely use $\|A\| \cdot 2$ as an upper bound, but verifier can rely on $\|A\|_\infty$.

#### Option B: General Case (Default)
For general (non-symmetric) operators:
$$\|A\|_{bound} = \|A\|_\infty = \max_i \sum_j |A_{ij}|$$

This is the **deterministic, verifier-safe upper bound**.

---

## 2. Acceptance Predicate

A renormalization event is accepted **iff all** of the following conditions hold:

### Condition 1: Norm Decrease
$$\text{norm}_{post} < \text{norm}_{pre}$$

The renormalization must actually reduce the operator norm.

### Condition 2: Pre-Criticality (Supercritical)
$$\eta \cdot \text{norm}_{pre} \cdot g > 1$$

The system must be **supercritical** before renormalization (above critical surface).

### Condition 3: Post-Criticality (Subcritical)
$$\eta \cdot \text{norm}_{post} \cdot g \leq 1$$

After renormalization, the system must return to **critical or subcritical** state.

### Formal Predicate

```
ACCEPT if and only if:
  norm_post < norm_pre
  AND eta * norm_pre * g > 1
  AND eta * norm_post * g <= 1
```

---

## 3. Physical Interpretation

### Pre-Condition: $\sigma_{pre} > 1$

When $\sigma_{pre} > 1$:
- The operator is expanding
- The system is **supercritical**
- Cascade events can grow uncontrolled

This represents the system "piling up" at the critical boundary.

### Post-Condition: $\sigma_{post} \leq 1$

After renormalization:
- The operator is contracting or neutral
- The system returns to **critical or subcritical** state
- Scale-free cascade completes

This is the **barrier-crossing correction** that returns the system to the critical surface.

### Norm Decrease

The renormalization must physically reduce the graph norm—this is the actual "coarsening" or "pruning" operation.

---

## 4. Implementation Notes

### Fixed-Point Arithmetic

All quantities use Q18 fixed-point arithmetic:
- $\eta$: Q18 (e.g., $0.5 = 2^{18} \cdot 0.5 = 131072$)
- norms: Q18
- $g$: Q18

### Verifier Decision

The verifier performs **exact inequality checks**:
- No floating-point ambiguity
- Deterministic acceptance
- Reproducible across runs

### Ledger Integration

The acceptance predicate is recorded in the **renorm criticality receipt** (see [`schemas/coh.renorm_criticality_receipt.v1.json`](../schemas/coh.renorm_criticality_receipt.v1.json)).

---

## 5. Example Computation

```python
# Given:
B = 1000        # budget
mu = 1.0        # prox parameter
c = 1.0         # constant
norm_pre = 2.0  # pre-renorm norm (Q18)
norm_post = 1.5 # post-renorm norm (Q18)
g = 1.2         # NPE gain (Q18)

# Compute:
eta = 1 / (1 + mu * c * B)
   = 1 / (1 + 1000)
   = 1 / 1001
   ≈ 0.001

sigma_pre = eta * norm_pre * g
          = 0.001 * 2.0 * 1.2
          = 0.0024

sigma_post = eta * norm_post * g
           = 0.001 * 1.5 * 1.2
           = 0.0018

# Check predicate:
norm_post < norm_pre:   True  (1.5 < 2.0)
sigma_pre > 1:          False (0.0024 ≤ 1)
sigma_post <= 1:        True  (0.0018 ≤ 1)

# Result: REJECT (not supercritical before renorm)
```

---

## 6. Diagnostic: Power Iteration Witness

For diagnostic purposes (not required for verification), a **power iteration** can estimate the true spectral radius:

```python
def power_iteration_witness(A, iterations=10, seed=42):
    """Estimate spectral radius via power iteration."""
    # Deterministic seed for reproducibility
    v = seeded_random_vector(seed, A.shape[1])
    v = v / norm(v)
    
    for _ in range(iterations):
        v = A @ v
        v = v / norm(v)
    
    # Rayleigh quotient as witness
    witness = (v @ A @ v) / (v @ v)
    return witness
```

**Important:** The verifier is **not required to trust** this witness. It is for diagnostic/analysis only.

---

## 7. Relationship to Theorem Program

The acceptance predicate directly implements the **barrier-crossing** in the theorem program:

- $\sigma_{pre} > 1$: $X_{\tau_k} > 0$ (above critical surface in log-space)
- $\sigma_{post} \leq 1$: $X_{\tau_k^+} \leq 0$ (at or below critical surface)
- $J_k = X_{\tau_k} - X_{\tau_k^+}$: Jump magnitude that enforces return

This connects the runtime trigger to the mathematical framework in [`02_scale_free_renorm_theorem_program.md`](02_scale_free_renorm_theorem_program.md).

---

## 8. Summary

| Quantity | Formula | Purpose |
|----------|---------|---------|
| $\eta(B)$ | $1/(1 + \mu c B)$ | Prox contractivity |
| $\|A\|_{bound}$ | $\max_i \sum_j \|A_{ij}\|$ (or $\|A\|_2$ for symmetric) | Safe norm bound |
| $g$ | NPE gain | Amplification factor |
| $\sigma$ | $\eta \cdot \|A\|_{bound} \cdot g$ | Operator criticality |

**Acceptance requires:**
1. Actual norm reduction
2. Pre-renorm supercriticality ($\sigma > 1$)
3. Post-renorm critical/subcriticality ($\sigma \leq 1$)
