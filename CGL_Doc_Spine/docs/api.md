# APIs

CGL exposes APIs for submitting workloads, querying decisions, and managing governance artifacts. This doc provides a concrete REST shape (gRPC maps cleanly).

## Principles
- every request has an idempotency key
- every response includes `decision_id` and `policy_bundle_hash`
- long-running workloads are asynchronous (job model)
- errors are structured (reason codes)

## REST endpoints (core)

### Submit a workload
`POST /v1/workloads`

Request body:
- `operation` (string)
- `target_runtime` (string)
- `parameters` (object)
- `inputs_ref` (object)

Response:
- `workload_id`
- `decision_id`
- `effect`
- `constraints`
- `policy_bundle_hash`

### Get workload status
`GET /v1/workloads/{workload_id}`

Response:
- state: `queued|running|completed|failed|quarantined` (example: `running`)
- timestamps
- enforcement_receipt_id
- output_refs (if released)

### Query a decision
`GET /v1/decisions/{decision_id}`

Response:
- decision object + explanation + matched rule IDs

### List audit events
`GET /v1/audit/events?runtime_id=sim-runtime-prod-3&from=2026-01-31T00:00:00Z&to=2026-02-01T00:00:00Z&type=cgl.runtime.quarantined`

Response:
- paginated events (metadata + hashes)
- payload expansion optional (by access rights)

## Governance endpoints

### Propose a policy bundle
`POST /v1/policy/bundles:propose`

- creates a Change Request (CR)
- runs automated tests (async)
- returns CR id and proposed bundle hash

### Approve a change request
`POST /v1/change-requests/{cr_id}:approve`

- requires appropriate role
- records signature and evidence

### Activate a policy bundle
`POST /v1/policy/bundles/{bundle_hash}:activate`

- requires operator + signatures satisfied
- supports canary parameters:
  - runtimes subset
  - percentage rollout
  - time window

## Error model
Errors return:
- `code` (HTTP + internal)
- `reason` (stable reason code)
- `message` (human readable)
- `decision_id` (if a decision existed)
- `policy_bundle_hash` (if evaluated)

## Provenance headers
Every workload response should include:
- `X-CGL-Decision-Id`
- `X-CGL-Policy-Bundle-Hash`
- `X-CGL-Request-Id`
- `X-CGL-Audit-Chain-Head` (optional)

These headers make downstream systems provable.

