# Audit & evidence

CGL’s audit design aims for: **tamper-evident, queryable, privacy-aware evidence**.

## Audit principles
- append-only
- immutable storage (WORM preferred)
- cryptographic hash chaining
- periodic notarization (sign batch digests)
- minimal sensitive content; reference large blobs by hash

## Event hashing
Each event stores:
- `prev_hash` (hash of previous event in the chain/partition)
- `event_hash` = H(event_payload + prev_hash)

This makes tampering detectable.

## Partitions
You can maintain multiple chains:
- per runtime
- per environment (prod/stage)
- per tenant

Each chain can be notarized independently.

## Evidence capture
Record:
- request received (normalized)
- policy bundle hash and signatures
- policy decision and explanation
- constraints actually applied
- runtime start/stop and status
- telemetry references and envelope evaluations
- output release decisions and quarantines
- override invocations
- change requests and approvals

## Retention and privacy
- keep hashes and metadata long-term
- store sensitive payloads in a restricted evidence store
- implement data minimization and redaction policies
- define retention by data class (e.g., 90 days full telemetry, 7 years audit digests)

## Audit queries (examples)
- “Show all RED runs in production last 30 days”
- “Which policy bundle was active during decision X?”
- “Who approved envelope change that raised dÊ/dt cap?”
- “List workloads executed under emergency override”

## Verifying an audit chain
Verification steps:
1. fetch event range and recompute hashes
2. confirm prev_hash links
3. confirm periodic digest signatures
4. confirm policy bundle hashes match registry content
5. confirm signer identities and key validity at signing time

If verification fails → automatic incident.

