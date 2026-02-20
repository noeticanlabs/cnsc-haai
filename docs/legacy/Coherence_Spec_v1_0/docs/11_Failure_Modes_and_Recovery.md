# Failure Modes and Recovery

## Failure mode taxonomy

* **Time freeze:** gates too strict; retries collapse \(dt\).
* **Coherence leak:** gates too loose; drift accumulates.
* **Residual dominance:** missing normalization causes one residual to swamp others.
* **Thrash loops:** repeated retries without convergence.

## Symptoms and recovery policies

* **Too-strict gates → dt collapse (“time freeze”)**
  * Symptom: repeated retries; \(dt\) hits floor.
  * Remedy: widen hysteresis; staged rails with bounded easing.

* **Too-loose gates → drift (“coherence leak”)**
  * Symptom: debt rises across accepted steps.
  * Remedy: tighten budgets; add residuals or penalties.

* **Missing normalization → residual dominance**
  * Symptom: one residual dominates \(\mathfrak C\) despite governance intent.
  * Remedy: normalize to unit budget boundary; reweight.

* **Thrash loops**
  * Symptom: oscillation between accept/retry.
  * Remedy: add thrash penalty, branching cap, and checkpoint backtrack.
