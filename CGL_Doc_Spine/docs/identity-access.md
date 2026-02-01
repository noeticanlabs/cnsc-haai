# Identity & access

Coherence systems are “sharp knives.” CGL needs a clean authorization model.

## Authentication
Recommended:
- mTLS for service-to-service
- OIDC for humans (SSO)
- short-lived tokens (no long-lived API keys)

High-impact operations require **step-up auth**:
- hardware-backed MFA
- re-auth within a short window

## Authorization: RBAC + ABAC
RBAC gives clarity; ABAC gives nuance.

### Roles (example)
- `viewer`: read-only access to results and audit logs
- `researcher`: submit low/medium risk workloads
- `engineer`: manage runtime configs within policy
- `safety_reviewer`: approve envelope/budget changes
- `operator`: activate bundles, manage incidents, invoke containment
- `admin`: manage IAM mappings (ideally very small group)

### Attributes (examples)
- `actor.clearance`: `public|internal|restricted`
- `actor.team`: research group identifier
- `actor.auth_strength`: `weak|strong`
- `runtime.classification`: `sandbox|staging|production`
- `request.risk_class`: `low|medium|high`

Policies can say: “researchers can run high-risk workloads only in sandbox with strong auth.”

## Separation of duties
CGL should enforce:
- policy author cannot self-approve high-impact policy
- activation requires a distinct operator role
- emergency override requires post-hoc review by safety reviewer

## Least privilege
- default deny
- minimal role grants
- time-bound elevated access (just-in-time)

## Service identities
Automation identities must:
- be scoped to specific operations
- use dedicated credentials
- be rate limited
- have mandatory logging

## Identity evidence
Audit logs should record:
- actor id and display name
- auth method + strength
- token issuer and token id (or mTLS cert serial)
- IP / device posture where available

This turns “who did what” from an argument into a fact.

