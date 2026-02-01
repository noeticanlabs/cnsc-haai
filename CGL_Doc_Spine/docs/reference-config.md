# Reference configuration

This is a working reference config for a baseline CGL deployment. Adapt it, but keep the invariants: signed bundles, deterministic policy, and tamper-evident audit.

## Components
- Gateway: stateless, horizontally scaled
- Policy engine: stateless evaluators with verified bundle cache
- Risk monitor: stream processor that computes risk snapshots
- Audit store: append-only with hash chaining + periodic signatures
- Bundle registry: immutable storage with signature verification
- Enforcement: runtime sidecar/plugin + scheduler hooks

## Suggested defaults

### Telemetry
- sampling: 10 Hz (or runtime-appropriate)
- max telemetry age for GREEN/YELLOW decisions: 10 seconds
- missing telemetry → BLACK risk

### Audit
- hash chain per runtime instance
- notarize every 5 minutes (batch digest signature)
- replicate audit storage across at least 2 failure domains

### Policy
- default deny
- allow only `allow_with_constraints` for execution operations in production
- require quarantine-on-breach for ORANGE and above
- require manual output release for YELLOW/ORANGE/RED runs

## Example environment classification
- `sandbox`: exploratory, less strict, still auditable
- `staging`: mirrors prod policies, used for replay tests
- `production`: strict, requires signed bundles and strong auth

## Example clamps (simulation runtime)
- max amplitude: 0.7 (sandbox), 0.4 (production)
- max iterations: 200k (sandbox), 80k (production)
- max dÊ/dt: 0.10 (sandbox), 0.05 (production)
- min coherence 𝒞: 0.92 (production), 0.90 (sandbox)

## Logging
- structured logs everywhere
- include decision_id and bundle hash in every log line
- redact sensitive inputs; reference by hash

## Backup/DR
- policy registry snapshot daily + on activation
- audit digest keys in HSM with documented recovery
- periodic restore tests

