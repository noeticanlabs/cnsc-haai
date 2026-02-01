# Event contracts

CGL is event-driven. The audit store and observability pipelines consume a consistent set of events.

All canonical schemas live in `/schemas`.

## Event envelope
All events share a common envelope:

- `event_id`
- `type`
- `created_at`
- `actor_id` (optional for system events)
- `request_id` / `decision_id` (when applicable)
- `policy_bundle_hash` (when applicable)
- `payload` (type-specific)
- `prev_hash` and `event_hash` (audit chain)

## Canonical event types

### cgl.request.received
Emitted by gateway on request intake.

### cgl.decision.made
Emitted after policy evaluation, includes matched rules and constraints.

### cgl.enforcement.applied
Emitted by enforcement point, includes actual clamps and runtime config hash.

### cgl.runtime.telemetry
Emitted periodically, includes signal summaries + envelope eval.

### cgl.runtime.completed
Emitted at end, includes outcome and output refs.

### cgl.runtime.quarantined
Emitted when quarantine is triggered.

### cgl.policy.bundle.activated
Emitted on activation; includes signer set and rollout scope.

### cgl.override.invoked
Emitted on break-glass operations; must link to incident id.

## Schema discipline
- schemas are versioned: ``cgl.runtime.telemetry.v1``, `cgl.runtime.telemetry.v2`
- breaking changes require new version
- policy bundles specify minimum supported schema versions

## Event-driven policy hooks
Policies can reference *risk state* derived from telemetry, but not raw event streams directly. The risk monitor is the “derivation boundary.”

That keeps policy deterministic.

