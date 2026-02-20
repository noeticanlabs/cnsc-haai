# Verification and Test Plan

## Unit tests

* Schema validation for receipts, gate policies, and certificates.
* Hash chaining correctness.
* Hysteresis behavior (enter/exit thresholds respected).
* Policy identity consistency (policy id/hash referenced in receipts and certificates).

## Integration tests

* Recovery: rails fire within bounds and reduce debt in controlled scenarios.
* Determinism: same seed/config yields identical final hash (within tolerances).

## System tests

* Stress tests for long-run stability and bounded debt.
* Failure injection (invalid states, tool mismatch).

## Pass/fail thresholds for coherence compliance

* **Debt budget**: \(\max \mathfrak C \leq B\) during accepted steps.
* **Residual budget**: each normalized residual \(r_i \leq 1.0\) on acceptance.
* **Determinism**: identical final hash for repeated runs (within tolerance).
* **Recovery**: rails reduce debt in controlled scenarios and do not exceed declared bounds.
