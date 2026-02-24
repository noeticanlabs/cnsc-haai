# Documentation Spine Classification

> **Status**: Active  
> **Created**: 2026-02-24

This document declares the canonical status of each documentation directory in the CNHAAI project. Without explicit classification, documentation drift can cause inconsistencies between spec and implementation.

---

## Classification Legend

| Status | Meaning |
|--------|---------|
| **Normative** | Source of truth for protocol definitions. Code must conform. |
| **Informative** | Explanatory content. May deviate from implementation without breaking anything. |
| **Legacy** | Deprecated. Do not add new content. Migration in progress. |

---

## Normative (Protocol Truth - Source of Truth)

These documents define bytes, hashes, schemas, and core invariants. **Code must conform to these.**

| Directory | Description |
|-----------|-------------|
| `docs/ats/10_mathematical_core/` | Core mathematics (state space, action algebra, risk functional V, budget law) |
| `docs/ats/20_coh_kernel/` | Kernel primitives (receipt identity, chain hash rule, deterministic numeric domain, canonical serialization) |
| `docs/spec/` | System overview, ledger truth contract |
| `src/npe/schemas/` | JSON schemas (machine-readable truth) |
| `src/cnsc_haai/consensus/` | Consensus kernel implementation |

### Key Normative Documents

| Primitive | Canonical Definition Location |
|-----------|------------------------------|
| `receipt_id` | `docs/ats/20_coh_kernel/receipt_identity.md` |
| `chain_digest` | `docs/ats/20_coh_kernel/chain_hash_rule.md` |
| `state_hash` | `docs/ats/20_coh_kernel/deterministic_numeric_domain.md` |
| `slab_id` | `docs/ats/20_coh_kernel/receipt_schema.md` |
| `budget_transition` | `docs/ats/30_ats_runtime/budget_transition_spec.md` |
| `admissibility` | `docs/ats/10_mathematical_core/admissibility_predicate.md` |

---

## Informative (Explanatory)

These documents explain and contextualize but are **not protocol truth**. They may contain examples, tutorials, or high-level architecture discussions.

| Directory | Description |
|-----------|-------------|
| `docs/coh-agi/` | Conceptual system layer, AGI summary |
| `docs/guides/` | How-to guides |
| `docs/architecture/` | High-level architecture diagrams |
| `docs/gmi/` | General mathematical ideas (unless made normative Legacy (Deprecated - Do Not Edit)

) |

---

##These directories are in maintenance mode. **Do not add new content.**

| Directory | Status | Notes |
|-----------|--------|-------|
| `docs/spine/` | DEPRECATED | Superseded by `docs/ats/` |
| `docs/cnhaai/` | DEPRECATED | Content migrated to `docs/ats/` |
| `docs/Coherence_Spec_v1_0/` | DEPRECATED | Old spec version |

---

## Primitive Definition Registry

To prevent drift, each primitive should have **exactly one** canonical definition:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ PRIMITIVE DEFINITION REGISTRY                                               │
├──────────────────────────┬──────────────────────────────────────────────────┤
│ Primitive                │ Canonical Location                               │
├──────────────────────────┼──────────────────────────────────────────────────┤
│ receipt_id               │ docs/ats/20_coh_kernel/receipt_identity.md      │
│ chain_digest             │ docs/ats/20_coh_kernel/chain_hash_rule.md      │
│ state_hash               │ docs/ats/20_coh_kernel/deterministic_numeric.. │
│ slab_id                  │ docs/ats/20_coh_kernel/receipt_schema.md        │
│ risk_functional_V       │ docs/ats/10_mathematical_core/risk_functional_V │
│ budget_law              │ docs/ats/10_mathematical_core/budget_law.md     │
│ action_algebra          │ docs/ats/10_mathematical_core/action_algebra   │
│ admissibility_predicate │ docs/ats/10_mathematical_core/admissibility_... │
└──────────────────────────┴──────────────────────────────────────────────────┘
```

---

## Rule: How to Avoid Drift

1. **When editing a primitive**, find its canonical location in the registry above.
2. **When writing new code**, reference the normative docs. If a primitive is not documented normatively, **create the doc first**.
3. **When adding docs**, check the classification:
   - Protocol/bytes/hashes → Normative (`docs/ats/`)
   - Tutorial/explanation → Informative (`docs/guides/`)
4. **When renaming primitives**, update both the code AND all normative docs simultaneously.

---

## Enforcement (Future)

To prevent drift, consider adding CI checks:

- [ ] Schema checksums match committed specs
- [ ] Key code files reference correct spec IDs
- [ ] No duplicate primitive definitions across normative docs

---

## Quick Reference

| Need to... | Go to... |
|------------|----------|
| Define a new hash primitive | `docs/ats/20_coh_kernel/` |
| Write a how-to guide | `docs/guides/` |
| Understand the math | `docs/ats/10_mathematical_core/` |
| Find the old docs | `docs/legacy/` (or they're gone) |
