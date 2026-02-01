# Operations runbook

This runbook covers day-2 operations: deployments, rollouts, monitoring, and common failure scenarios.

## Health checks
CGL should expose:
- gateway liveness and readiness
- policy engine bundle verification status
- risk monitor ingestion lag
- audit write success and notarization status
- enforcement point connectivity

## Monitoring dashboards (minimum)
- request rate by operation and environment
- allow/deny rates and top reason codes
- risk level distribution by runtime
- envelope breach counts
- audit chain notarization success
- policy bundle activation timeline

## Rollout procedure (recommended)
1. deploy new CGL components to staging
2. replay recorded workloads in staging with mirrored policy
3. canary in production (subset of runtimes or operations)
4. monitor allow/deny deltas and breach rates
5. ramp to full
6. finalize evidence artifacts

## On-call playbook: common problems

### A) Telemetry stale (BLACK risk)
Symptoms:
- risk monitor shows missing data
Actions:
- deny high-impact ops automatically
- verify telemetry pipeline (agents, broker, network)
- check runtime health
- if production: declare SEV-1/2 depending on impact

### B) Policy bundle signature failure
Symptoms:
- policy engine refuses bundle
Actions:
- freeze activations
- rollback to last known-good bundle hash
- investigate registry integrity and signing keys
- declare incident if production

### C) Sudden spike in denies
Symptoms:
- deny rate jumps, new reason codes appear
Actions:
- check recent policy activation
- compare decision explanations
- validate IAM changes and token issuers
- consider rollback if user-impacting

### D) Envelope breach storm
Symptoms:
- ORANGE/RED events surge
Actions:
- quarantine new workloads
- stop risky operations
- isolate runtime instance(s)
- capture telemetry and configs for forensics

## Backup and disaster recovery
- replicate policy registry and audit store across regions
- keep policy caches on policy engines (verified)
- ensure audit chain notarization keys are recoverable in HSM/KMS procedures

## Key rotation
- rotate signing keys on a schedule
- support overlapping validity windows
- store key IDs in signatures
- include “key status at signing time” in evidence

