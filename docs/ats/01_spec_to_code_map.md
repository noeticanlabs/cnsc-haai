# Spec to Code Map

**Version**: 1.0.0
**Last Updated**: 2026-02-20

---

## Purpose

This document maps ATS/Coh specification pages to their corresponding code modules. It ensures that spec authors and implementers can trace requirements to implementation and vice versa.

---

## Mapping Tables

### 10 Mathematical Core

| Spec File | Code Module | Status |
|-----------|-------------|--------|
| `state_space.md` | `src/cnsc/haai/ats/types.py` | ✅ Implemented |
| `budget_law.md` | `src/cnsc/haai/ats/budget.py` | ✅ Implemented |
| `risk_functional_V.md` | `src/cnsc/haai/ats/risk.py` | ✅ Implemented |
| `admissibility_predicate.md` | `src/cnsc/haai/ats/rv.py` | ✅ Implemented |
| `continuous_manifold_flow.md` | N/A | 🔲 Pending |

---

### 20 Coh Kernel

| Spec File | Code Module | Status |
|-----------|-------------|--------|
| `chain_hash_rule.md` | DEPRECATED | ⚠️ Use `chain_hash_universal.md` |
| `chain_hash_universal.md` | `src/cnsc_haai/consensus/chain.py` | 🔲 Pending |
| `canonical_serialization.md` | DEPRECATED | ⚠️ Use JCS (RFC8785) |
| `coh.merkle.v1.md` | `src/cnsc_haai/consensus/merkle.py` | 🔲 Pending |
| `receipt_schema.md` | `schemas/receipt.ats.v2.schema.json` | ⚠️ v3 pending |
| `deterministic_numeric_domain.md` | `src/cnsc/haai/ats/numeric.py` | ✅ Implemented |
| `receipt_identity.md` | `src/cnsc/haai/ats/types.py` | ✅ Implemented |
| `rv_step_spec.md` | `src/cnsc/haai/ats/rv.py` | ✅ Implemented |

---

### 30 ATS Runtime

| Spec File | Code Module | Status |
|-----------|-------------|--------|
| `budget_transition_spec.md` | `src/cnsc/haai/ats/budget.py` | ✅ Implemented |
| `action_emission_contract.md` | `src/cnsc/haai/tgs/proposal.py` | ✅ Implemented |
| `slab_compression_rules.md` | `src/cnsc_haai/consensus/slab.py` | 🔲 Pending |
| `replay_verification.md` | `src/cnsc/haai/gml/replay.py` | ✅ Implemented |
| `risk_witness_generation.md` | `src/cnsc/haai/ats/risk.py` | ✅ Implemented |
| `state_digest_model.md` | `src/cnsc/haai/ats/types.py` | ✅ Implemented |

---

### 40 NSC Integration

| Spec File | Code Module | Status |
|-----------|-------------|--------|
| `nsc_vm_to_ats_bridge.md` | `src/cnsc/haai/ats/bridge.py` | ✅ Implemented |
| `gate_to_receipt_translation.md` | `src/cnsc/haai/ats/bridge.py` | ✅ Implemented |
| `cognitive_system_embedding.md` | `src/cnsc/haai/ghll/`, `src/cnsc/haai/nsc/` | ✅ Implemented |
| `policy_layer_constraints.md` | `src/cnsc/haai/tgs/rails.py` | ✅ Implemented |

---

### 50 Security Model

| Spec File | Code Module | Status |
|-----------|-------------|--------|
| `adversary_model.md` | Documentation only | ✅ Documented |
| `deterministic_replay_requirements.md` | `src/cnsc/haai/gml/replay.py` | ✅ Implemented |
| `float_prohibition.md` | `src/cnsc/haai/ats/numeric.py` | ✅ Implemented |
| `timestamp_nonconsensus_rule.md` | `src/cnsc/haai/tgs/clock.py` | ✅ Implemented |
| `rejection_reason_codes.md` | `src/cnsc/haai/ats/errors.py` | ✅ Implemented |

---

## Code Directory Structure

```
src/
├── cnsc/
│   └── haai/
│       ├── ats/                    # ATS Kernel
│       │   ├── __init__.py
│       │   ├── bridge.py           # NSC-ATS bridge
│       │   ├── budget.py           # Budget transitions
│       │   ├── errors.py           # Error codes
│       │   ├── numeric.py          # QFixed arithmetic
│       │   ├── risk.py             # Risk functional V
│       │   ├── rv.py               # Receipt verification
│       │   └── types.py            # Core types
│       ├── ghll/                   # GHLL (High-Level Language)
│       ├── glll/                   # GLLL (Low-Level Language)
│       ├── gml/                    # GML (Governance Metadata)
│       ├── nsc/                    # NSC (Neural State Controller)
│       └── tgs/                    # TGS (Time Governor System)
│
├── cnsc_haai/
│   └── consensus/                   # NEW: Consensus utilities
│       ├── __init__.py
│       ├── chain.py                # Chain hashing
│       ├── hash.py                 # SHA256 utilities
│       ├── jcs.py                  # RFC8785 JCS
│       ├── merkle.py               # Merkle trees
│       └── slab.py                 # Slab compression
│
├── cnhaai/
│   └── core/
│       ├── abstraction.py          # Abstraction layer
│       ├── coherence.py            # ⚠️ UI ONLY - NOT for ATS
│       ├── gates.py                # Gate system
│       ├── phases.py               # Phase management
│       └── receipts.py             # Receipt system
│
└── npe/
    ├── api/                        # NPE API server
    ├── core/                       # NPE core
    ├── proposers/                  # GR Proposers
    ├── retrieval/                  # Retrieval system
    └── scoring/                    # Scoring system
```

---

## Critical: Coherence Module Distinction

> **WARNING**: There are TWO coherence implementations:

| Module | Purpose | Use For |
|--------|---------|---------|
| `src/cnhaai/core/coherence.py` | UI display only | NOTHING ATS-related |
| `src/cnsc/haai/ats/risk.py` | Deterministic | ATS verification |
| `src/cnsc/haai/ats/numeric.py` | QFixed math | All numeric ops |

**Do NOT import `cnhaai.core.coherence` in any `cnsc.haai.ats.*` module.**

---

## Undocumented Directories

These directories exist but need documentation:

| Directory | Purpose | Priority |
|-----------|---------|----------|
| `cnsc-haai/` | Root-level project | MEDIUM |
| `npe_assets/` | Codebooks, corpus, receipts | HIGH |
| `tools/` | Utility scripts | LOW |
| `plans/` | Implementation plans | LOW |

---

## Schema Files

| Schema | Purpose | Version |
|--------|---------|---------|
| `receipt.ats.v2.schema.json` | Receipt format | v2 (frozen) |
| `receipt.schema.json` | Generic receipt | Legacy |
| `coh.policy.retention.v1.schema.json` | Retention policy | v1 (pending) |
| `coh.receipt.slab.v1.schema.json` | Slab receipt | v1 (pending) |
| `coh.receipt.fraudproof.v1.schema.json` | Fraud proof | v1 (pending) |
| `coh.receipt.finalize.v1.schema.json` | Finalize | v1 (pending) |

---

## Test Locations

| Test Type | Location |
|-----------|----------|
| Unit tests | `tests/test_*.py` |
| Compliance tests | `compliance_tests/*/` |
| Integration tests | `tests/integration/` |

---

## Related Documents

- [Spec Governance Policy](00_identity/spec_governance.md)
- [Coh Kernel Scope](00_identity/coh_kernel_scope.md)
- [Roadmap](90_roadmap/)
