# Incident response

CGL is both a governance tool and an early-warning system. When coherence systems go unstable, you want rapid containment with strong forensics.

## Incident triggers
Create an incident automatically when:
- risk level transitions to **RED** for longer than threshold
- telemetry becomes **BLACK** in production
- signature verification fails (policy bundle, config, or audit digest)
- repeated envelope breaches occur in a short window
- emergency override invoked

## Incident lifecycle
1. **Detect** (risk monitor emits incident candidate)
2. **Declare** (incident created, severity assigned)
3. **Contain** (quarantine runtimes/workloads, freeze policy changes)
4. **Eradicate** (remove unsafe workloads, rollback policy/config)
5. **Recover** (validate stable signals, restore normal operations)
6. **Review** (postmortem, corrective actions, policy updates)

## Containment actions
- stop active workloads safely
- quarantine outputs
- reduce allowed operation set (policy “incident mode”)
- pin policy bundles to last known good
- isolate runtime instance or network segment
- increase logging and sampling rates

## Severity model (example)
- **SEV-1:** sustained RED in production or integrity failure
- **SEV-2:** repeated ORANGE in production, or RED in staging
- **SEV-3:** YELLOW anomalies or isolated ORANGE in staging
- **SEV-4:** informational / false positive

## Break-glass override
If containment requires override:
- require strong auth
- require dual control where possible
- record override reason and incident link
- trigger immediate review

## Postmortem evidence checklist
- decision IDs for all related workloads
- policy bundle hash and activation events
- enforcement receipts and runtime config hashes
- telemetry time series around breach
- actor identities for any overrides
- timeline reconstruction from audit chain

Incidents are where governance earns its keep.

