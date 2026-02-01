# Testing & validation

Governance needs tests the same way physics needs calibration. You don’t “feel” your way into safe envelopes.

## Policy tests
Every policy bundle must ship with:
- unit tests for rules (allow/deny under specific conditions)
- regression tests against known incidents (“never allow this again”)
- property tests for monotonicity (tightening envelopes should not increase allows)

## Replay simulations
Maintain a library of recorded workloads:
- baseline stable runs
- known risky runs (edge of LoC)
- known failure runs (breach, divergence, NaN storms)

For each candidate bundle:
1. replay library in staging
2. compare decisions to expected outcomes
3. run with enforcement plugins enabled
4. verify envelope breach behaviors trigger quarantine as designed

## Signal calibration
For each runtime version:
- capture distributions of 𝒞, gradients, spectral metrics
- establish baseline envelopes per workload class
- document the dataset used for envelope selection
- store calibration hashes in evidence

## Integrity tests
- verify policy bundle signatures
- verify audit hash chains
- verify notarization signatures
- chaos test telemetry partitions (ensure fail-safe)

## Operational drills
At least quarterly:
- simulate telemetry outage (BLACK mode)
- simulate policy injection attempt
- simulate envelope breach storm
- practice rollback to known-good bundle

## Acceptance criteria (recommended)
A bundle may be activated to production only if:
- all tests pass
- replay library shows no unexpected allows
- audit chain verification passes end-to-end
- canary shows stable signal behavior and acceptable deny rate deltas

