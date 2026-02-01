# Governance process

This is the human layer of CGL: how changes happen without turning into chaos theater.

## Change classes
Classify changes by impact:

- **Class A (High):** changes that relax envelopes, raise budgets, disable enforcement, or affect production integrity.
- **Class B (Medium):** changes that add new operations, adjust clamps conservatively, or affect staging.
- **Class C (Low):** documentation, non-functional metadata, low-risk policy additions.

Required approvals:
- Class A: author + peer + safety + operator
- Class B: author + peer (safety optional depending on scope)
- Class C: author (peer optional)

## Change request (CR) required fields
- description of change and motivation
- affected runtimes/environments
- risk analysis (what could go wrong?)
- test evidence (policy tests + replay results)
- rollback plan (bundle hash)
- approval list and signatures

## Release strategy
- stage first
- canary in production
- monitor metrics and envelope breaches
- ramp gradually
- document the final activation with evidence links

## Emergency changes
Emergency path exists but is constrained:

- must create CR (even minimal) before activation
- require break-glass approval (dual control if possible)
- set expiry time on the emergency policy
- schedule post-hoc review within 24–72 hours

## Governance anti-patterns
- “temporary” waivers with no expiry
- policy changes without replay evidence
- relying on tribal knowledge for envelopes
- approvals by the same person in multiple required roles
- disabling telemetry to “get the run done”

## Culture note
Governance isn’t there to block discovery; it’s there to make discovery **repeatable** and **defensible**.

