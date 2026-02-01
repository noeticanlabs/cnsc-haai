# Coherence Governance Layer (CGL) — Doc Spine (v1.0)

This zip contains a complete documentation spine for the **Coherence Governance Layer (CGL)** — the control-plane that governs, audits, and enforces safety/policy constraints over a coherence-first runtime.

## What this is
CGL is designed to sit *between*:
- a **Coherence Runtime** (simulators, field solvers, glyph-manifold engines, coherence computing stacks), and
- **applications / users / automation** that request operations from that runtime.

CGL’s job is to make coherence systems governable:
- **Policy-as-code** for coherence limits and allowed operations
- **Identity & approvals** for changes
- **Auditability & attestation** for every decision
- **Runtime enforcement** that fails safe and degrades gracefully

## How to read
Start at:
- `docs/index.md` (overview + navigation)
- `docs/system-context.md` (what CGL touches)
- `docs/architecture.md` (components + data flow)

## How to publish
This spine is **MkDocs**-ready:
- Edit `mkdocs.yml`
- Run: `mkdocs serve`

## Contents
- `docs/` — narrative documentation
- `schemas/` — JSON Schemas for events, bundles, and change objects
- `examples/` — policy examples and reference configurations

**Build date:** February 1, 2026
