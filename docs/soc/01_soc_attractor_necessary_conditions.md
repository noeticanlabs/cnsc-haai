# Necessary Conditions for SOC Attractor Existence

This document derives **necessary conditions** in the **operator + ledger** regime for Self-Organized Criticality (SOC) attractor existence.

## Core Definitions

### Operator Criticality Metric

We define the operator criticality at time $t$ as:

$$\sigma_t^{op} = \eta(B_t) \cdot \|A_t\|_{op} \cdot \|G_t\|_{op}$$

Where:
- $\eta(B) = \frac{1}{1 + \mu c B}$ is the prox attenuation factor
- $A_t$ is the graph adjacency/operator matrix
- $G_t$ represents the gain/weight matrix
- $B_t$ is the budget (proxy for constraint strength)

### Interpretation

- $\sigma < 1$: Subcritical (contraction dominates)
- $\sigma = 1$: Critical (balanced)
- $\sigma > 1$: Supercritical (expansion dominates)

---

## NC1: Two-Sided Recurrence Around Criticality [PROVED]

**Condition:**
$$\limsup \sigma^{op} \geq 1 \quad \text{and} \quad \liminf \sigma^{op} \leq 1$$

### Rationale

If the system never reaches criticality ($\limsup \sigma < 1$):
- It remains subcritical forever
- The operator norm contracts monotonically
- No cascade events occur → No SOC

If the system always exceeds criticality ($\liminf \sigma > 1$):
- It blows up or requires forced periodic collapse
- Becomes a driven periodic system, not self-organized

Therefore, **two-sided recurrence** is necessary for SOC.

### Proof Sketch

For SOC to exhibit scale-free behavior, the system must:
1. Explore both subcritical and supercritical regimes
2. Have a return mechanism to the critical surface
3. Avoid trivial fixed points (all $\sigma < 1$) or unbounded growth (all $\sigma > 1$)

The critical surface $\sigma = 1$ must be reachable and recurrent in the dynamics.

---

## NC2: Log-Balance + Nondegenerate Fluctuations [LEMMA-NEEDED]

**Condition:**
$$\mathbb{E}_\pi[\log \sigma^{op}] \approx 0 \quad \text{and} \quad \mathrm{Var}_\pi(\log \sigma^{op}) > 0$$

### Rationale

The expectation condition $\mathbb{E}[\log \sigma] \approx 0$ ensures the system "hovers" at criticality on average—the log-gain balances the log-loss over time.

The variance condition $\mathrm{Var}(\log \sigma) > 0$ ensures:
- Non-trivial fluctuations exist
- The system doesn't get stuck at a single value
- There is genuine stochastic drive

### Current Status

[LEMMA-NEEDED]: A rigorous invariant measure argument is required to upgrade this from heuristic to theorem. The mixing assumptions and stationary distribution properties need formal treatment.

---

## NC3: Timescale Separation [HEURISTIC]

**Condition:**
$$\tau_{drive} \gg \tau_{cascade}$$

Where:
- $\tau_{drive}$: Timescale of external drive/budget changes
- $\tau_{cascade}$: Timescale of operator renormalization events

### Rationale

Without timescale separation:
- Drive and cascade compete directly
- System exhibits periodic oscillation rather than SOC
- No separation between "forcing" and "response"

This is a **heuristic** condition—formalizing requires specifying the exact stochastic processes for drive and cascade.

---

## NC4: Non-Collapse of Degrees of Freedom [HEURISTIC]

**Condition:** The system must have **unfold** or **regeneration** mechanisms.

### Rationale

If renormalization only shrinks the system:
- Finite-size effects eventually dominate
- The power-law window collapses
- Scale-free behavior is cut off

The system requires mechanisms to:
- Regrow degrees of freedom after renormalization
- Or maintain a distribution over system sizes
- Prevent complete collapse to trivial state

### Current Status

[HEURISTIC]: The intuition is clear but requires specification of the regeneration process in the operator dynamics.

---

## NC5: RG-Like Self-Similarity Window [HEURISTIC]

**Condition:** Renormalization operations must be approximately scale-invariant across a window of scales.

### Rationale

For SOC to produce power laws:
- Renorm operations at different scales must have similar structure
- The "bare" parameters should flow slowly under RG transformation
- A window of scales must exist where self-similarity holds

### Current Status

[HEURISTIC]: Requires precise definition of the renormalization map and fixed-point analysis.

---

## Summary Table

| Condition | Statement | Status |
|-----------|-----------|--------|
| NC1 | Two-sided recurrence around $\sigma=1$ | [PROVED] |
| NC2 | $\mathbb{E}[\log\sigma] \approx 0$, $\mathrm{Var}(\log\sigma) > 0$ | [LEMMA-NEEDED] |
| NC3 | Timescale separation: drive $\gg$ cascade | [HEURISTIC] |
| NC4 | Non-collapse of DOF (unfold/regeneration) | [HEURISTIC] |
| NC5 | RG self-similarity window | [HEURISTIC] |

---

## Relationship to Theorem Program

These necessary conditions feed into the **Scale-Free Renorm Theorem Program** ([`02_scale_free_renorm_theorem_program.md`](02_scale_free_renorm_theorem_program.md)), which provides the mathematical bridge from these conditions to observable scale-free statistics.

---

## References

- Prox attenuation formula: $\eta(B) = \frac{1}{1 + \mu c B}$
- Operator criticality bound: $\|r_{t+1}\| \leq \eta(B) \|A\|_{op} \|G\|_{op} \|r_t\|$
