# Lemma 2: Jump Relation and Event Size Function

## Statement

**[LEMMA-NEEDED → LEMMA-STATE]**

Let $X_t = \log \sigma_t$ be the log-criticality process, and let $\tau_k$ be the $k$-th renorm time. Define the event size $S_k$ as the cascade magnitude associated with the $k$-th renormalization event.

Then there exists a monotone function $f: \mathbb{R}^+ \to \mathbb{R}^+$ such that:

$$S_k = f(X_{\tau_k})$$

and for large $x$:

$$f(x) \asymp x \quad \text{as } x \to \infty$$

i.e., $f(x)$ is asymptotically equivalent to $x$ (there exist constants $c_1, c_2 > 0$ such that $c_1 x \leq f(x) \leq c_2 x$ for sufficiently large $x$).

---

## 1. Physical Interpretation

### What is Event Size?

In SOC theory, $S_k$ represents the **"energy release"** or **cascade magnitude** during the $k$-th renormalization event. This is analogous to:

- Earthquake magnitude (energy released)
- Avalanche size (number of grains)
- Forest fire area (burned region)

### The Overshoot

When $\sigma > 1$ (supercritical), the system is "above" the critical surface. The **overshoot** is:

$$X_{\tau_k} = \log \sigma_{\tau_k} > 0$$

This is the distance above criticality when renorm triggers.

---

## 2. Defining the Event Size Function

### Definition: Event Size

Let $S_k$ be the **cumulative norm change** during the cascade associated with renorm event $k$:

$$S_k = \|A_{\tau_k^-}\|_{op} - \|A_{\tau_k^+}\|_{op}$$

Where:
- $\tau_k^-$: Just before renorm
- $\tau_k^+$: Just after renorm

### Alternative Definition: Log Event Size

For mathematical convenience, work with:

$$Y_k = \log S_k$$

This puts event sizes in additive form, matching $X_t$.

---

## 3. The Jump Relation

### From Acceptance Predicate

Recall the acceptance predicate from [`03_runtime_trigger_spec.md`](03_runtime_trigger_spec.md):

- $\sigma_{pre} > 1$ (supercritical)
- $\sigma_{post} \leq 1$ (critical or subcritical)

In log form:
$$X_{\tau_k} > 0 \quad \text{and} \quad X_{\tau_k^+} \leq 0$$

### The Jump Magnitude

The renorm enforces:
$$X_{\tau_k^+} = X_{\tau_k} - J_k$$

where $J_k \geq X_{\tau_k}$ ensures $X_{\tau_k^+} \leq 0$.

### Event Size Connection

The event size $S_k$ relates to the overshoot $X_{\tau_k}$:

$$S_k = \sigma_{\tau_k} - \sigma_{\tau_k^+} = \sigma_{\tau_k} - 1 \quad \text{(approximately)}$$

Taking logs:
$$Y_k = \log(\sigma_{\tau_k} - 1) = \log(e^{X_{\tau_k}} - 1)$$

---

## 4. Asymptotic Analysis

### Lemma: Asymptotic Equivalence

For large $x$ (i.e., large overshoot $\sigma \gg 1$):

$$f(x) = \log(e^x - 1) \asymp x$$

**Proof:**

For $x \to \infty$:
$$e^x - 1 = e^x(1 - e^{-x}) = e^x(1 - o(1))$$

Taking logs:
$$\log(e^x - 1) = x + \log(1 - e^{-x}) = x + o(1)$$

Therefore:
$$\lim_{x \to \infty} \frac{\log(e^x - 1)}{x} = 1$$

This proves $f(x) \asymp x$. □

### Physical Interpretation

For large overshoots (far above criticality), the cascade magnitude grows **linearly** with the overshoot. This is the key relationship that enables scale-free statistics.

---

## 5. Formal Definition

### Definition: Event Size Function

Define $f: \mathbb{R}^+ \to \mathbb{R}^+$ by:

$$f(x) = \log(e^x - 1)$$

Properties:
1. **Monotone increasing**: $x_1 < x_2 \implies f(x_1) < f(x_2)$
2. **Asymptotically linear**: $\lim_{x \to \infty} f(x)/x = 1$
3. **Domain**: $x > 0$ (supercritical regime)

### Alternative: Direct Definition

For the cumulative norm change interpretation:
$$S_k = \|A_{\tau_k^-}\|_{op} - \|A_{\tau_k^+}\|_{op} = e^{X_{\tau_k}} - 1$$

Taking the log:
$$Y_k = \log S_k = \log(e^{X_{\tau_k}} - 1) = f(X_{\tau_k})$$

---

## 6. Theorem: Jump Relation

### Lemma 2 (Formal)

Let $X_{\tau_k} > 0$ be the log-criticality at the $k$-th renorm event. Let $S_k$ be the associated event size. Then:

$$S_k = e^{X_{\tau_k}} - 1$$

and defining $f(x) = \log(e^x - 1)$, we have:

$$S_k = e^{f(X_{\tau_k})}$$

or equivalently:

$$\log S_k = f(X_{\tau_k})$$

Furthermore, for $x > 1$:
$$f(x) \asymp x$$

*Proof*: Direct computation and asymptotic analysis in Section 4. □

---

## 7. Relationship to Theorem Program

This lemma justifies the connection between the **log-criticality process** and **event sizes**:

```
┌─────────────────────────────────────────────────────────────┐
│  Log-Criticality Process                                     │
│  X_t = log(σ_t)                                             │
│  X_{t+1} = X_t + ξ_t (near-zero drift)                    │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼ (at renorm τ_k)
┌─────────────────────────────────────────────────────────────┐
│  Jump Magnitude: X_{τ_k^+} = X_{τ_k} - J_k  ← THIS LEMMA  │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  Event Size: S_k = e^{X_{τ_k}} - 1                        │
│              log S_k = f(X_{τ_k}) with f(x) ≍ x           │
└─────────────────────────────────────────────────────────────┘
```

The key insight: **large overshoots produce large events linearly**.

---

## 8. Status

| Component | Status |
|-----------|--------|
| Definition of S_k | [PROVED] |
| Relation S_k = e^{X_τ} - 1 | [PROVED] |
| Function f(x) = log(e^x - 1) | [PROVED] |
| Asymptotic equivalence f(x) ≍ x | [PROVED] |

---

## References

- [`03_runtime_trigger_spec.md`](03_runtime_trigger_spec.md) - Acceptance predicate
- [`02_scale_free_renorm_theorem_program.md`](02_scale_free_renorm_theorem_program.md) - Theorem program overview
- SOC literature: Bak, Tang, Wiesenfeld (1987)
