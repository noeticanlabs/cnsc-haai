# Policy model

Policies in CGL answer: **“Under what conditions can this actor request this operation on this runtime?”**

The policy model is intentionally declarative. Physics systems drift; governance needs stable semantics.

## Policy layers
CGL composes policies from layers, from most general to most specific:

1. **Global safety policies**  
   Hard constraints that always apply (e.g., never allow operations that disable telemetry, never allow unsigned policy activation).

2. **Runtime-class policies**  
   Constraints for categories of runtimes (simulation, glyph compiler, lab hardware driver).

3. **Runtime-instance policies**  
   Constraints tuned to a specific runtime (calibrated envelopes, known hazards).

4. **Workload policies**  
   Constraints for specific workload types (training run, field solve, exploratory scan).

5. **Emergency policies**  
   Rules for incident mode, outage mode, or containment.

Composition rule:
- Evaluate all applicable policies and take the **most restrictive** outcome unless an explicit, signed exception exists.

## Decision outcomes
A policy evaluation returns one of:

- **deny**  
  The request is not permitted. Provide a reason code and minimal explanation.

- **allow**  
  The request is permitted with default constraints.

- **allow_with_constraints**  
  The request is permitted but must run with explicit constraints (budgets, envelopes, throttles, quarantine rules).

## Policy inputs
Policies can only depend on:
- request fields (operation, parameters, input references)
- actor claims (roles, attributes, auth strength)
- runtime attributes (type, environment, classification)
- risk snapshot (signals, risk level, telemetry freshness)
- active policy bundle version/hash

No hidden “magic” data dependencies. If you need more context, add it to the request or snapshot explicitly.

## Risk-aware policy
CGL makes risk a first-class input. Example rule:

- If `risk_level` is **YELLOW**, allow low-risk operations; require constraints for high-energy operations.
- If `risk_level` is **RED** or **BLACK**, deny high-impact ops and only allow containment actions.

## Policy constraints types

### 1) Coherence budgets
A numeric allowance for instability risk.

Example semantics:
- budget units are runtime-defined but must be monotonically “more budget = more allowed risk”
- consumption is tracked per workload
- exceeding budget triggers quarantine or termination

### 2) Signal envelopes
Bounds on signals during execution.

Example:
- 𝒞 must remain ≥ 0.90 after warmup
- p99 gradient norm ≤ threshold
- energy injection ≤ threshold

### 3) Operation clamps
Hard caps on runtime parameters:
- max amplitude
- max solver step / CFL condition
- max iterations
- boundary condition templates only (no arbitrary functions)

### 4) Output controls
- quarantined outputs by default
- manual release required for RED/YELLOW runs
- watermark or provenance headers always

## Exceptions and waivers
Exceptions are allowed only if:
- they are explicit objects with scope and expiry
- signed by required roles
- logged and reviewed post-hoc

Policy bundles should prefer “principled constraints” to waivers.

