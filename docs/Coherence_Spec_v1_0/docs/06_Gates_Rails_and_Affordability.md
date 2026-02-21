# Gates, Rails, and Affordability

## Hard vs soft gates

* **Hard gates:** NaN/Inf detection, invalid invariants, forbidden states.
* **Soft gates:** residual thresholds and total debt budget.

## Hysteresis design

Use **enter/exit thresholds** to prevent chatter. Example: enter when \(r > 1.0\), exit when \(r < 0.8\).

## Rails list and bounds

Rails are bounded corrective actions, such as:

* Reduce \(dt\) (step size) within a declared floor.
* Increase damping within a declared ceiling.
* Projection/repair onto constraints with bounded magnitude.
* Evidence fetch or tool cross-check within bounded depth.
* Backtrack to last checkpoint (bounded by retry limit).

## Acceptance semantics

**Operational time advances only on acceptance.** Retries do not advance time; they apply rails and re-evaluate gates.
