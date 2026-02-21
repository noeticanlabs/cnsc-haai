# Legacy Documentation Archive

> **This directory contains archived documentation.**

These documents represent earlier versions or superseded specifications that have been moved here to keep the main documentation clean and focused.

---

## Archive Contents

### 1. Coherence_Spec_v1_0/
Original Coherence specification bundle (moved: 2026-02-20)

| File | Description | Superseded By |
|------|-------------|---------------|
| docs/01_Coherence_Principle.md | Original coherence principle | `docs/ats/10_mathematical_core/` |
| docs/02_Formal_Definitions.md | Formal definitions | `docs/ats/10_mathematical_core/` |
| docs/06_Gates_Rails_and_Affordability.md | Gate/rail contracts | `docs/ats/30_ats_runtime/` |
| docs/09_Receipts_Ledgers_and_Certificates.md | Receipt system | `docs/ats/20_coh_kernel/` |
| docs/10_Verification_and_Test_Plan.md | Test plans | Various ATS docs |
| docs/11_Failure_Modes_and_Recovery.md | Failure modes | `docs/spine/24-failure-modes-and-recovery.md` |

**Why Archived:** These docs represent an earlier version of the Coherence specification that has been superseded by the canonical ATS/Coh documentation in `docs/ats/`.

### 2. spec/
Technical specification documents for GHLL, GLLL, GML, GraphGML, NSC, and Seam (moved: 2026-02-21)

| Directory | Description | Superseded By |
|-----------|-------------|---------------|
| ghll/ | GHLL design specifications | `docs/ats/`, `docs/spine/` |
| glll/ | GLLL specifications | `docs/ats/`, `docs/spine/` |
| gml/ | GML trace model specs | `docs/ats/`, `docs/spine/` |
| graphgml/ | GraphGML specs | `docs/ats/`, `docs/spine/` |
| nsc/ | NSC specifications | `docs/ats/40_nsc_integration/` |
| seam/ | Seam contracts | `docs/ats/` |

**Why Archived:** These technical specifications were scattered across multiple directories. The content has been consolidated into the canonical ATS documentation in `docs/ats/` and the spine in `docs/spine/`.

---

## Migration Status

| Legacy Doc | Status | New Location |
|------------|--------|---------------|
| Coherence_Spec_v1_0/* | Superseded | docs/ats/ |
| spec/ghll/* | Superseded | docs/ats/ |
| spec/glll/* | Superseded | docs/ats/ |
| spec/gml/* | Superseded | docs/ats/ |
| spec/graphgml/* | Superseded | docs/ats/ |
| spec/nsc/* | Superseded | docs/ats/40_nsc_integration/ |
| spec/seam/* | Superseded | docs/ats/ |

---

## What Survived

The following concepts from these legacy docs were incorporated into the current canonical documentation:

1. **Coherence Principle** → `docs/ats/10_mathematical_core/`
2. **Gate/Rail Contracts** → `docs/ats/30_ats_runtime/`
3. **Receipt System** → `docs/ats/20_coh_kernel/receipt_schema.md`
4. **Formal Definitions** → `docs/ats/10_mathematical_core/`
5. **Chain Hash Rules** → `docs/ats/20_coh_kernel/chain_hash_universal.md`
6. **Canonical Serialization** → RFC8785 JCS specification

---

## For More Information

- [Canonical Documentation](../ats/) - Current ATS specifications
- [Spine Documentation](../spine/) - Core abstraction theory
- [Spec Governance Policy](../ats/00_identity/spec_governance.md)
- [Migration Guide](../ats/01_spec_to_code_map.md)

---

*Archived: 2026-02-21*
