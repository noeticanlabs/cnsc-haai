# CNSC-HAAI Upgrade Plan - Integrated (Doc Review + ATS Coh Stack)

**Generated**: 2026-02-20
**Based on**: Documentation Review Findings + ATS/Coh Stack Upgrade

---

## CRITICAL DISCREPANCIES FROM DOC REVIEW (Must Be Addressed)

### 🔴 Critical Issues Found

| # | Issue | Impact | Priority |
|---|-------|--------|----------|
| 1 | `cnhaai/core/coherence.py` is **UI-only**, NOT for ATS kernel | Fork risk - wrong coherence used | CRITICAL |
| 2 | Only 1/7 guides exist (00-quick-start) | Incomplete documentation | HIGH |
| 3 | Spec files skeletal (2-10 lines) vs 1000+ LOC code | No consensus spec | HIGH |
| 4 | `examples/end_to_end/` referenced but missing | Can't verify end-to-end | MEDIUM |
| 5 | CLI entry may not work (`python -m cnsc.haai`) | Can't run system | MEDIUM |
| 6 | Mixed digest formats (`sha256:` vs bare hex) | Your schema issue | HIGH |

---

## INTEGRATED PHASE 0 — Safety Rail + Doc Cleanup

### 0.1 Create Safety Branch
```bash
git checkout -b v0.4.0-pre-coh-ats-upgrade
```

### 0.2 Add Spec Governance
Create [`docs/ats/00_identity/spec_governance.md`](docs/ats/00_identity/spec_governance.md):
- Root `/docs/ats/` is canonical
- Changes require version bump + new test vectors
- DEPRECATED status for legacy doc stacks

### 0.3 INTEGRATE DOC REVIEW FIXES:

#### 0.3.1 Fix Coherence Misunderstanding (CRITICAL)
- Create docs clarifying:
  - **UI Coherence**: `src/cnhaai/core/coherence.py` (heuristic, display only)
  - **ATS Kernel Coherence**: `src/cnsc/haai/ats/risk.py`, `src/cnsc/haai/ats/numeric.py` (deterministic)
- Add to [`docs/ats/00_identity/coh_kernel_scope.md`](docs/ats/00_identity/coh_kernel_scope.md):
  ```
  ## Coherence Module Distinction
  
  WARNING: Do NOT use cnhaai.core.coherence for verification.
  Use cnsc.haai.ats.risk for deterministic coherence.
  ```

#### 0.3.2 Document Directory Structure Fix
Update [`docs/ats/01_spec_to_code_map.md`](docs/ats/01_spec_to_code_map.md):
- `src/cnsc/haai/` - Main implementation (Triaxis, NSC, TGS)
- `src/cnhaai/` - Coherence kernel documentation + minimal kernel
- `src/npe/` - Neural Planning Engine
- `compliance_tests/` - Consensus test vectors

---

## PHASE 1 — Canonicalize Documentation Authority

### 1.1 Keep Root `/docs/ats/` as Single Source

### 1.2 Deprecate Legacy Doc Stacks

| Legacy Path | Action | New Location |
|-------------|--------|--------------|
| `cnhaai/docs/` | Add DEPRECATION notice | Link to `docs/ats/` |
| `Coherence_Spec_v1_0/` | Move to archive | `docs/legacy/Coherence_Spec_v1_0/` |

**Execute:**
```bash
mkdir -p docs/legacy
mv Coherence_Spec_v1_0 docs/legacy/
# Add deprecation notice to cnhaai/docs/SPINE.md
```

### 1.3 INTEGRATE DOC REVIEW FIXES:

#### 1.3.1 Add Missing Guides (HIGH PRIORITY)
Create the 6 missing guides:
- [ ] `docs/guides/01-creating-abstraction-ladders.md`
- [ ] `docs/guides/02-developing-gates.md`
- [ ] `docs/guides/03-developing-rails.md`
- [ ] `docs/guides/04-implementing-receipts.md`
- [ ] `docs/guides/05-analyzing-coherence.md`
- [ ] `docs/guides/06-troubleshooting.md`

#### 1.3.2 Fix CLI Entry Point
Update [`docs/cli-reference.md`](docs/cli-reference.md):
- Document PYTHONPATH requirement
- Or create proper setup.py/pyproject.toml entry points

---

## PHASE 2 — Add Continuous Manifold Flow

### 2.1 Add Spec Page
Create [`docs/ats/10_mathematical_core/continuous_manifold_flow.md`](docs/ats/10_mathematical_core/continuous_manifold_flow.md)

### 2.2 Update Mathematical Core Index
Update [`docs/ats/10_mathematical_core/README.md`](docs/ats/10_mathematical_core/README.md)

---

## PHASE 3 — Replace Consensus Kernel Specs

### 3.1 Add New Crypto Specs

| New Spec | Purpose |
|----------|---------|
| `docs/ats/20_coh_kernel/coh.merkle.v1.md` | Merkle tree rules |
| `docs/ats/20_coh_kernel/chain_hash_universal.md` | Universal chain hashing (JCS + domain sep) |
| `docs/ats/20_coh_kernel/slab_compression_rules.md` | Slab compression |

### 3.2 Deprecate Outdated Kernel Docs

| Old Doc | Action | New Pointer |
|---------|--------|-------------|
| `chain_hash_rule.md` | DEPRECATE | → `chain_hash_universal.md` |
| `canonical_serialization.md` | DEPRECATE | → RFC8785 JCS rule |

### 3.3 INTEGRATE DOC REVIEW FIXES:

#### 3.3.1 Expand Spec Files (HIGH PRIORITY)
Your current spec files are 2-10 lines. Must expand:

| Spec File | Current | Target | Action |
|-----------|---------|--------|--------|
| `ghll/00_GHLL_Design_Principles.md` | 2 lines | ~500 lines | Expand or DEPRECATE |
| `glll/00_GLLL_Purpose...md` | Few lines | ~500 lines | Expand or DEPRECATE |
| `nsc/00_NSC_Goals...md` | 10 lines | ~500 lines | Expand or DEPRECATE |

**RECOMMENDATION**: Add "IMPLEMENTED" markers:
```markdown
## Implementation Status

- [x] Rewrite-graph execution
- [x] Deterministic receipts
- [ ] <incomplete items>
```

---

## PHASE 4 — Schema Unification + Slab Retention

### 4.1 Create New Schema Files

Add to `schemas/`:
- [ ] `coh.policy.retention.v1.schema.json`
- [ ] `coh.receipt.slab.v1.schema.json`
- [ ] `coh.receipt.fraudproof.v1.schema.json`
- [ ] `coh.receipt.finalize.v1.schema.json`

### 4.2 Normalize Digest Format (CRITICAL FIX)

**Decision**: Use `sha256:` prefix everywhere in JSON

| Schema | Current | Fix |
|--------|---------|-----|
| `receipt.ats.v2.schema.json` | bare hex | FREEZE v2 |
| `receipt.ats.v3.schema.json` | NEW | Use `sha256:` prefix |

### 4.3 INTEGRATE DOC REVIEW FIXES:

#### 4.3.1 Add Examples Directory
Create [`examples/end_to_end/`](examples/end_to_end/):
- `00_glll_encode_decode.md`
- `01_ghll_parse_rewrite.md`
- `02_nsc_cfa_run.md`
- `03_gml_trace_audit.md`

---

## PHASE 5 — Implementation Upgrade

### 5.1 Add Consensus Utility Module

Create `src/cnsc_haai/consensus/`:
```
consensus/
├── __init__.py
├── jcs.py          # RFC8785 canonical serialization
├── hash.py         # SHA256 with domain separation
├── merkle.py       # Merkle tree construction
└── chain.py        # Universal chain hashing
```

### 5.2 Add Slab Registry + Dispute Flags

Create `src/cnsc_haai/ats/verifier_state.py`:
- `slab_accept_height` tracking
- `disputed_flag` for fraud proofs
- `finalize` authorization

### 5.3 INTEGRATE DOC REVIEW FIXES:

#### 5.3.1 Fix Coherence Import Restrictions
Ensure `cnhaai.core.coherence` is NOT imported in ATS kernel:
```python
# In src/cnsc/haai/ats/__init__.py add:
"""
WARNING: Do NOT import cnhaai.core.coherence here.
Use cnsc.haai.ats.risk for deterministic coherence.
"""
```

---

## PHASE 6 — Compliance Tests

### 6.1 Add Consensus Test Vectors

Create `compliance_tests/ats_slab/`:
- `vectors_policy.json`
- `vectors_micro_receipts.jsonl`
- `expected_merkle_root.txt`
- `expected_chain_hashes.jsonl`
- etc.

### 6.2 Add Test Runners
- `tests/test_consensus_merkle.py`
- `tests/test_consensus_chainhash.py`
- `tests/test_slab_fsm.py`

### 6.3 INTEGRATE DOC REVIEW FIXES:

#### 6.3.1 Fix Outdated Tests Import
Update test imports to use correct coherence module:
```python
# WRONG:
from cnhaai.core.coherence import CoherenceBudget

# CORRECT:
from cnsc.haai.ats.risk import CoherenceRisk
```

---

## PHASE 7 — Integration Wiring

### 7.1 Add Spec-to-Code Map
Create [`docs/ats/01_spec_to_code_map.md`](docs/ats/01_spec_to_code_map.md)

### 7.2 Add Compliance Checklist
Create [`docs/ats/90_roadmap/consensus_upgrade_checklist.md`](docs/ats/90_roadmap/consensus_upgrade_checklist.md)

### 7.3 INTEGRATE DOC REVIEW FIXES:

#### 7.3.1 Update Undocumented Directories
Document these in the spec:
- `cnsc-haai/` - Purpose unclear
- `npe_assets/` - Codebooks, corpus, receipts
- `tools/` - Utility scripts
- `plans/` - Implementation plans

---

## EXECUTION CHECKLIST

| Phase | Task | Status |
|-------|------|--------|
| 0 | Safety branch + governance | [ ] |
| 0 | Fix coherence module distinction docs | [ ] |
| 1 | Deprecate cnhaai/docs | [ ] |
| 1 | Add 6 missing guides | [ ] |
| 2 | Add continuous_manifold_flow.md | [ ] |
| 3 | Add new kernel specs | [ ] |
| 3 | Deprecate old kernel specs | [ ] |
| 3 | Expand skeletal spec files | [ ] |
| 4 | Add 4 new schemas | [ ] |
| 4 | Create v3 receipt schema | [ ] |
| 4 | Add examples/end_to_end/ | [ ] |
| 5 | Add consensus/ module | [ ] |
| 5 | Add verifier_state.py | [ ] |
| 6 | Add compliance test vectors | [ ] |
| 7 | Add spec-to-code map | [ ] |
| 7 | Document undocumented dirs | [ ] |

---

## PRIORITY MATRIX

| Priority | Items |
|----------|-------|
| **CRITICAL** | Fix coherence module distinction, Schema digest format |
| **HIGH** | Add 6 missing guides, Expand spec files, Deprecate legacy docs |
| **MEDIUM** | Add examples/, Fix CLI entry, Document directories |
| **LOW** | Add continuous_manifold_flow, Add spec-to-code map |
