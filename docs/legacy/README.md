# Legacy Documentation Archive

> **This directory contains archived documentation.**

---

## What Was Moved Here

| Original Location | Description | Date Moved |
|-------------------|-------------|------------|
| `Coherence_Spec_v1_0/` | Original Coherence specification bundle | 2026-02-20 |

---

## Why These Are Archived

These documents represent an earlier version of the Coherence specification. They have been superseded by the canonical ATS/Coh documentation in `docs/ats/`.

### Content That Survived

The following concepts from these legacy docs were incorporated into the new ATS spine:

1. **Coherence Principle** → `docs/ats/10_mathematical_core/`
2. **Gate/Rail Contracts** → `docs/ats/30_ats_runtime/`
3. **Receipt System** → `docs/ats/20_coh_kernel/receipt_schema.md`
4. **Formal Definitions** → `docs/ats/10_mathematical_core/`

### Content That Was Replaced

1. **Chain Hash Rules** → Replaced by `docs/ats/20_coh_kernel/chain_hash_universal.md`
2. **Canonical Serialization** → Replaced by RFC8785 JCS specification

---

## Migration Status

| Legacy Doc | Status | New Location |
|------------|--------|---------------|
| 01_Coherence_Principle.md | Superseded | docs/ats/10_mathematical_core/ |
| 02_Formal_Definitions.md | Superseded | docs/ats/10_mathematical_core/ |
| 06_Gates_Rails_and_Affordability.md | Superseded | docs/ats/30_ats_runtime/ |
| 09_Receipts_Ledgers_and_Certificates.md | Superseded | docs/ats/20_coh_kernel/ |

---

## For More Information

- [Canonical Documentation](../ats/)
- [Spec Governance Policy](../ats/00_identity/spec_governance.md)
- [Migration Guide](../ats/01_spec_to_code_map.md)
