# Policy language (CPL)

CGL uses **CPL** (Coherence Policy Language): a small, auditable DSL designed for governance, not cleverness.

You can implement CPL directly or compile it to an engine like OPA/Rego, Cedar, or your own evaluator. The key is **deterministic evaluation** and **clear explanations**.

## Design goals
- readable by humans
- deterministic and side-effect free
- versionable and testable
- produces structured explanations

## CPL overview

A CPL file contains:
- `package` (namespace)
- `defaults` (global defaults)
- `rules` (allow/deny/constraints)
- `envelopes` (named signal envelope sets)
- `budgets` (named budget profiles)

### Example policy (complete)

```cpl
package cgl.runtime.simulation

defaults:
  effect: deny
  reason: "default_deny"

envelopes:
  stable_v1:
    C_min: 0.92
    grad_p99_max: 3.0
    spr_max: 20
    dE_dt_max: 0.10
    telemetry_max_age_sec: 10

budgets:
  exploratory:
    coherence_budget: 1.0
    max_runtime_sec: 600
  production:
    coherence_budget: 0.3
    max_runtime_sec: 300

rules:
  - id: allow_low_risk_ops
    when:
      operation in ["runtime.execute_simulation", "runtime.export_results"]
      actor.role in ["researcher", "engineer"]
      risk.level == "GREEN"
    then:
      effect: allow_with_constraints
      reason: "green_ok_with_envelope"
      constraints:
        envelope: stable_v1
        budget: exploratory
        clamps:
          max_amplitude: 0.7
          max_iterations: 200000

  - id: deny_on_black
    when:
      risk.level == "BLACK"
    then:
      effect: deny
      reason: "telemetry_or_integrity_unknown"

  - id: quarantine_on_orange
    when:
      risk.level == "ORANGE"
      operation == "runtime.execute_simulation"
    then:
      effect: allow_with_constraints
      reason: "orange_quarantine"
      constraints:
        envelope: stable_v1
        budget: production
        quarantine: true
        clamps:
          max_amplitude: 0.4
          max_iterations: 80000
```

## Semantics

### Evaluation order
1. Load active policy bundle (signed).
2. Determine applicable packages by runtime type and operation namespace.
3. Evaluate rules top-to-bottom within a package.
4. If multiple rules match, take the most restrictive effect:
   - `deny` > `allow_with_constraints` > `allow`
5. Merge constraints by intersection:
   - lower budgets win
   - tighter envelopes win
   - stricter clamps win

### Conditions
Supported operators:
- `==`, `!=`, `in`, `not in`
- numeric comparisons: `<`, `<=`, `>`, `>=`
- boolean logic: implicit AND between lines inside `when`

CPL intentionally avoids arbitrary function calls. If you need derived values, compute them into the risk snapshot.

### Explanation model
Each decision must include:
- matched rule IDs
- reason codes
- the final constraints object
- policy bundle hash

This is how humans debug governance.

## Authoring conventions

### Reason codes
Use stable reason codes for metrics and incident analysis:
- `default_deny`
- `green_ok_with_envelope`
- `telemetry_or_integrity_unknown`
- `orange_quarantine`
- `role_not_permitted`
- `operation_disallowed`
- `budget_exceeded`

### Don’t hide danger in “allow”
If it’s allowed only because you clamp it, make it `allow_with_constraints`, not `allow`.

## CPL JSON representation
Policy bundles store CPL policies as normalized JSON to make hashing deterministic.
See `schemas/cgl.policy.bundle.v1.json`.

