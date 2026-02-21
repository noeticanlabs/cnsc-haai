# Formal Definitions

## State, levels, and updates

* **State** \(x\): whatever is updated (fields, parameters, symbolic claims, plans).
* **Optional levels** \(z_\ell\): hierarchical partitions of state for multiscale systems.

## Residuals

* **Residual vector** \(\mathbf r(x)\): measurable constraint defects (conservation, consistency, reconstruction, tool mismatch, contradiction).
* Each residual must be defined with an **observable measurement** and a **normalization**.

## Coherence debt

Define the debt functional as:

\[
\mathfrak C(x)=\sum_i w_i r_i(x)^2 + \sum_j v_j p_j(x)
\]

where \(p_j\) are explicit penalties (thrash, ungrounded steps, excessive branching).

## Gates, rails, and receipts

* **Hard gates:** binary safety checks that must pass (e.g., NaN/Inf, forbidden state).
* **Soft gates:** policy thresholds on residuals or debt budget.
* **Hysteresis:** separate enter/exit thresholds to prevent chatter.
* **Rails:** bounded corrective actions (e.g., reduce step size, projection/repair, evidence fetch).
* **Receipts:** structured logs of residuals, debt decomposition, gates, rails, and decisions.

### Gate policy notation

Let \(G = (G_h, G_s, H)\) where:

* \(G_h\) is the set of hard predicates \(g_h(x) \in \{\text{pass},\text{fail}\}\).
* \(G_s\) are soft thresholds \(\tau_i^{\text{warn}}, \tau_i^{\text{fail}}\) for residuals \(r_i\).
* \(H\) are hysteresis parameters \((\tau_i^{\text{enter}}, \tau_i^{\text{exit}})\).

### Rail notation

Each rail is a bounded operator \(\rho_k\) with a declared bound \(\beta_k\):

\[
\rho_k: x \mapsto x' \quad \text{such that} \quad \|x' - x\| \leq \beta_k
\]

### Receipt structure (minimal formalization)

A receipt is a tuple:

\[
R = (s, \mathbf r, \mathfrak C, D, G, A, \text{policy\_id}, h_{\text{parent}}, h)
\]

where \(s\) is a state summary, \(D\) is the debt decomposition, \(A\) are actions/rails, and hashes support replay.

## Accepted step

An **accepted step** is one where:

1. **All hard gates pass**, and
2. **Soft policy holds** (within thresholds, including hysteresis), and
3. **Receipt is emitted** with a decision and rationale.
