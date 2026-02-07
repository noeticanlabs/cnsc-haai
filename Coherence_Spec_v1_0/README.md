# Coherence Spec v1.0 (Canonical Constraint)

> **DEPRECATED**: This specification has been superseded by the current CNHAAI spec at `spec/` and `cnhaai/docs/`.
> 
> For current documentation, see:
> - **Specs**: [`spec/`](spec/)
> - **Theory**: [`cnhaai/docs/spine/`](cnhaai/docs/spine/)
> - **Examples**: [`examples/`](examples/)

This package defines **Coherence** as an **operational, measurable, and auditable governance budget** for system evolution. Coherence is not a metaphysical claim; it is a discipline for deciding whether a proposed step is affordable under declared constraints and logged corrections.

## What “Coherence” means here

**Coherence** is a governance-measurable integrity budget consisting of:

* A **scalar debt** \(\mathfrak C\) computed from residuals and penalties.
* A **residual vector** \(\mathbf r\) of measurable defects (constraint violations, reconstruction error, tool mismatch, contradiction, thrash).
* **Gates, rails, and receipts** that enforce safe evolution and auditable correction.

A system is **coherence-compliant** only if it produces replayable receipts and enforces bounded correction. Coherence is therefore the **affordability condition** for making claims or taking steps; it is not “truth.”

## What it is not

* **Not** a metaphysical theory of reality.
* **Not** a claim about physics unless explicitly labeled **BRIDGE/UNVERIFIED** in `docs/13_Bridge_Notes_Time_GR_PDE_AI.md`.
* **Not** a performance guarantee beyond the declared gates, rails, and residual design.

## Navigation

> **DEPRECATED**: This directory is archived. Use current docs instead.

For current documentation:
- **Specs**: [`spec/`](spec/) - Technical specifications
- **Theory**: [`cnhaai/docs/spine/`](cnhaai/docs/spine/) - Learning path
- **Examples**: [`examples/`](examples/) - End-to-end examples
- **Schemas**: [`schemas/`](schemas/) - JSON schemas

### Migration Guide

| Old Path | New Path |
|----------|----------|
| `docs/01_Coherence_Principle.md` | [`cnhaai/docs/spine/12-coherence-principles.md`](cnhaai/docs/spine/12-coherence-principles.md) |
| `docs/02_Formal_Definitions.md` | [`cnhaai/docs/spine/`](cnhaai/docs/spine/) |
| `schemas/coherence_receipt.schema.json` | [`schemas/receipt.schema.json`](schemas/receipt.schema.json) |
| `examples/receipt.example.json` | [`cnhaai/docs/appendices/appendix-c-receipt-schema.md`](cnhaai/docs/appendices/appendix-c-receipt-schema.md) |

## Compliance checklist (minimum requirements)

A system may claim **Coherence-compliant** only if all items below are satisfied:

1. **Residual vector defined** with measurable defects and normalization so 1.0 means “budget boundary.”
2. **Debt functional \(\mathfrak C\)** computed each step with a logged decomposition.
3. **Gate policy** with hard/soft gates and hysteresis, plus bounded rails.
4. **Accept/retry/abort decision** emitted each step with reasons.
5. **Receipts** emitted with hash chaining and decision rationale; replay determinism within tolerances.
6. **Policy identity** (policy id/hash) recorded so gates/rails are auditable.
7. **Bounded correction** (rails) enforced; corrections logged with before/after and bounds.
8. **Verification plan** covering schema, determinism, recovery, and stress tests.
