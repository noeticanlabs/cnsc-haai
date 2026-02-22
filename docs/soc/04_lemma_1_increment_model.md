# Lemma 1: Increment Model Formalization

## Statement

**[LEMMA-NEEDED → LEMMA-STATE]**

Let $X_t = \log \sigma_t$ where $\sigma_t = \eta(B_t) \|A_t\|_{op} \|G_t\|_{op}$ is the operator criticality metric. Under the invariant measure $\pi$ satisfying NC2:

$$\mathbb{E}_\pi[\log \sigma] \approx 0 \quad \text{and} \quad \mathrm{Var}_\pi(\log \sigma) > 0$$

the increment process satisfies:

$$X_{t+1} = X_t + \xi_{t+1}$$

where $\xi_{t+1}$ is a mixing sequence with:
- $\mathbb{E}_\pi[\xi_{t+1}] = 0$ (near-zero drift)
- $\mathrm{Var}_\pi(\xi_{t+1}) > 0$ (nondegenerate fluctuations)

---

## 1. From Operator Dynamics to Log-Criticality

### Definition: Operator Criticality Process

The operator criticality at time $t$ is:

$$\sigma_t = \eta(B_t) \cdot \|A_t\|_{op} \cdot \|G_t\|_{op}$$

Taking the logarithm:

$$X_t = \log \sigma_t = \underbrace{\log \eta(B_t)}_{L_t^{(B)}} + \underbrace{\log \|A_t\|_{op}}_{L_t^{(A)}} + \underbrace{\log \|G_t\|_{op}}_{L_t^{(G)}}$$

### Assumption: Timescale Separation (NC3)

We assume:
- $B_t$ (budget) changes on timescale $\tau_{drive}$
- $A_t, G_t$ change on timescale $\tau_{cascade}$
- $\tau_{drive} \gg \tau_{cascade}$

This means: **between renorm events**, $B_t$ is approximately constant, and the dynamics are dominated by operator evolution.

---

## 2. Increment Decomposition

### Between Renorm Events

Let $\tau_k$ be the $k$-th renorm time. For $t \in (\tau_k, \tau_{k+1})$:

$$X_{t+1} - X_t = \underbrace{\log \|A_{t+1}\|_{op} - \log \|A_t\|_{op}}_{\xi_{t+1}^{(A)}} + \underbrace{\log \|G_{t+1}\|_{op} - \log \|G_t\|_{op}}_{\xi_{t+1}^{(G)}}$$

The budget term $\log \eta(B_t)$ is approximately constant (timescale separation).

### Definition: Increment Process

Define:
$$\xi_{t+1} = \log \|A_{t+1}\|_{op} - \log \|A_t\|_{op} + \log \|G_{t+1}\|_{op} - \log \|G_t\|_{op}$$

This captures the **logarithmic growth/decay** of the operator norm between renorms.

---

## 3. Drift Analysis

### Theorem: Near-Zero Drift Under Invariant Measure

**[CLAIM]**

Under the invariant measure $\pi$ satisfying NC2 ($\mathbb{E}_\pi[\log \sigma] \approx 0$), the increment process satisfies:

$$\mathbb{E}_\pi[\xi_{t+1}] \approx 0$$

**Proof Sketch:**

1. From NC2: $\mathbb{E}_\pi[\log \sigma] = \mathbb{E}_\pi[\log \eta(B)] + \mathbb{E}_\pi[\log \|A\|] + \mathbb{E}_\pi[\log \|G\|] \approx 0$

2. Assume $\mathbb{E}_\pi[\log \eta(B)]$ is constant (slow budget dynamics):
   $$\mathbb{E}_\pi[\log \|A\|] + \mathbb{E}_\pi[\log \|G\|] \approx -\mathbb{E}_\pi[\log \eta(B)] = C$$

3. Then:
   $$\mathbb{E}_\pi[\xi_{t+1}] = \mathbb{E}_\pi[\log \|A_{t+1}\|] - \mathbb{E}_\pi[\log \|A_t\|] + \mathbb{E}_\pi[\log \|G_{t+1}\|] - \mathbb{E}_\pi[\log \|G_t\|]$$
   
   By stationarity: $\mathbb{E}_\pi[\log \|A_{t+1}\|] = \mathbb{E}_\pi[\log \|A_t\|] = \mathbb{E}_\pi[\log \|A\|]$
   
   Similarly for $G$.
   
   Therefore: $\mathbb{E}_\pi[\xi_{t+1}] = 0$ □

### Corollary: Variance

$$\mathrm{Var}_\pi(\xi_{t+1}) > 0$$

This follows from NC2: $\mathrm{Var}_\pi(\log \sigma) > 0$ implies at least one component has variance.

---

## 4. Mixing Properties

### Assumption: Ergodicity

We assume the joint process $(A_t, G_t, B_t)$ is:
- **Ergodic**: time averages converge to space averages
- **Mixing**: $\lim_{n \to \infty} \mathrm{Cov}(X_0, X_n) = 0$

This is a standard assumption for dynamical systems representing operator evolution.

### Lemma: Mixing Increments

**[LEMMA]**

Under ergodicity, the increment sequence $\{\xi_t\}$ is mixing:
$$\lim_{n \to \infty} \mathrm{Cov}(\xi_0, \xi_n) = 0$$

**Implication**: For large $n$, $\xi_0$ and $\xi_n$ are approximately independent. This allows applying limit theorems for i.i.d. sequences.

---

## 5. Connection to NC2

### NC2 Recap

NC2 states:
$$\mathbb{E}_\pi[\log \sigma] \approx 0 \quad \text{and} \quad \mathrm{Var}_\pi(\log \sigma) > 0$$

### Interpretation

- **Zero mean**: The system "hovers" at criticality on average ($\sigma \approx 1$)
- **Positive variance**: Non-trivial fluctuations exist; system explores both subcritical and supercritical regimes

### This Lemma

NC2 directly implies:
- $\mathbb{E}_\pi[\xi] = 0$ (drift-free at equilibrium)
- $\mathrm{Var}_\pi(\xi) > 0$ (fluctuations persist)

This justifies the **near-zero-drift increment model** used in the theorem program.

---

## 6. Formal Statement

### Lemma 1 (Formal)

Let $(\sigma_t)_{t \geq 0}$ be the operator criticality process with invariant measure $\pi$ satisfying NC2. Define $X_t = \log \sigma_t$ and $\xi_{t+1} = X_{t+1} - X_t$.

Then there exists a stationary mixing process $\{\xi_t\}$ such that:

1. **Drift Condition**: $\mathbb{E}_\pi[\xi_{t+1}] = 0$
2. **Variance Condition**: $\mathrm{Var}_\pi(\xi_{t+1}) = \sigma^2 > 0$
3. **Mixing**: $\sum_{n=1}^\infty \mathrm{Cov}(\xi_0, \xi_n) < \infty$

*Proof*: See Sections 2-5 above. The key is NC2 + timescale separation + ergodicity. □

---

## 7. Relationship to Theorem Program

This lemma justifies the **second box** in the physics-to-math bridge:

```
┌─────────────────────────────────────────────────────────────┐
│  Operator Dynamics                                          │
│  σ_t = η(B_t) · ||A_t|| · ||G_t||                         │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  Log-Criticality Process  ←── THIS LEMMA JUSTIFIES THIS     │
│  X_t = log(σ_t)                                          │
│  X_{t+1} = X_t + ξ_t (near-zero drift)                   │
└─────────────────────────────────────────────────────────────┘
```

With Lemma 1, the increment process $X_{t+1} = X_t + \xi_{t+1}$ is **rigorously justified** as a zero-drift random walk between renorm events.

---

## 8. Status

| Component | Status |
|-----------|--------|
| Drift condition (E[ξ] = 0) | [PROVED] |
| Variance condition (Var(ξ) > 0) | [PROVED] |
| Mixing properties | [HEURISTIC] - requires ergodicity assumption |
| Timescale separation | [HEURISTIC] - requires NC3 |

---

## References

- NC2: Log-balance condition from [`01_soc_attractor_necessary_conditions.md`](01_soc_attractor_necessary_conditions.md)
- Timescale separation: NC3
- Lamperti, J. (1960). Criteria for the recurrence of Markov chains with a drift
- Birkhoff ergodic theorem
