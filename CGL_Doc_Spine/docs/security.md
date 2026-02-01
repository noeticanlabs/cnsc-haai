# Security & threat model

Coherence systems add unusual attack surfaces: the “payload” is often a parameter set that can drive unstable dynamics.

## Assets
- policy bundle integrity (signatures, hashes)
- audit chain integrity (tamper-evidence)
- runtime safety (prevent unsafe resonance / runaway)
- output provenance (prevent forged results)
- identity integrity (prevent impersonation)

## Adversaries
- curious insider (non-malicious but reckless)
- malicious insider (exfiltration or sabotage)
- external attacker (credential theft)
- supply-chain attacker (policy injection, dependency compromise)

## Attack vectors and mitigations

### 1) Policy injection
Vector:
- attacker inserts a permissive policy bundle or modifies registry content
Mitigations:
- signed bundles, content-addressed pulls
- immutable registry entries
- multi-party approval required for activation
- audit notarization and monitoring for unexpected bundle hashes

### 2) Telemetry spoofing
Vector:
- attacker feeds fake “GREEN” telemetry to allow unsafe operations
Mitigations:
- authenticated telemetry channels (mTLS)
- telemetry source attestation (agent identity)
- plausibility checks (signal physics constraints, rate-of-change limits)
- fail-safe to BLACK when telemetry integrity uncertain

### 3) Glyph / parameter injection
Vector:
- adversarial boundary conditions or glyphs that trigger instability or hidden behavior
Mitigations:
- input schema validation
- safe templates (deny arbitrary functions)
- sandbox execution for untrusted workloads
- envelope monitoring + quarantine
- static analysis / lint for glyph constructs

### 4) Output forgery
Vector:
- attacker publishes outputs without provenance or with altered metadata
Mitigations:
- require provenance headers with decision_id and bundle hash
- store outputs with hash references and signed manifests
- deny exports unless decision allows and outputs pass release policy

### 5) Credential abuse
Vector:
- stolen tokens or over-privileged service accounts
Mitigations:
- short-lived tokens, least privilege, just-in-time grants
- step-up auth for high-impact ops
- anomaly detection on actor behavior
- mandatory audit logs and alerting

## Threat model notes
The most dangerous failures are **integrity failures that look like success**:
- “everything is GREEN” because your telemetry is lying
- “allow” decisions based on unsigned policy
- outputs released without provenance

CGL’s design should assume adversaries target *governance* before physics.

