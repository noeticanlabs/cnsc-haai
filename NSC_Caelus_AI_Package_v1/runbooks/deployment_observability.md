# Deployment + Observability Runbook (v1)

This runbook assumes Caelus is deployed as a tool-using orchestration service with:
- NSC tag routing
- gate/rail enforcement
- Aeonic Memory Bank (tiered retention)
- Receipt Ledger (audit trail)

## Service Objectives
Primary SLO: tool-use success rate >= 0.85 over 7 days
Guardrails:
- hallucination rate <= 0.03
- p95 latency <= 1.8s
- safety incident rate (P0/P1) == 0

## Required Dashboards
1) Quality
- tool_use_success_rate (overall + by domain tag)
- refusal_rate (block/defer decisions)
- hallucination_rate (measured via rubric + replay checks)
- gate_outcome_distribution (allow/warn/block/reroute/defer)

2) Performance
- p50/p95/p99 latency (end-to-end + per tool call)
- tool_call_count per request
- cache hit rate (retrieval + spectral cache if enabled)

3) Safety / Governance
- no_future_leak violations (should be 0)
- privacy gate violations (should be 0)
- human_review queue depth + SLA
- audit log completeness (missing receipt ratio)

## Alerts (minimum)
- tool_use_success_rate < 0.83 for 2 hours (page)
- hallucination_rate > 0.03 for 1 hour (page)
- no_future_leak violation detected (page immediately)
- audit log completeness < 99.5% for 30 minutes (page)
- p95 latency > 1.8s for 2 hours (ticket)

## Incident Response (P0/P1)
1) Contain
- switch to "safe mode": restrict tool set, raise gating thresholds, force human_review for high-risk domains
- disable memory writes to L2/L3 if corruption suspected

2) Diagnose
- pull receipts for affected window
- replay with deterministic decoding
- identify failure cluster tags (e.g., safety:privacy or safety:causality)

3) Correct
- patch prompt/tool routing policy OR rollback to prior known-good model_id
- add targeted tests to TOOLUSE_V1 or SAFETY_V1 suites

4) Postmortem (within 72 hours)
- failure mode summary
- guardrail breached? why it escaped detection
- preventive controls (tests + gates + monitoring)
