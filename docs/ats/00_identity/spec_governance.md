# Spec Governance Policy

**Version**: 1.0.0
**Effective Date**: 2026-02-20

---

## 1. Purpose

This document establishes the governance policy for the ATS/Coh specification documents under `docs/ats/`. The goal is to prevent drift between documentation and implementation, and ensure consensus-tight specifications.

---

## 2. Canonical Specification Authority

### 2.1 Single Source of Truth

All specifications under `docs/ats/` are the **canonical source of truth** for the ATS/Coh stack implementation.

```
docs/ats/           ← CANONICAL (this is the truth)
cnhaai/docs/        ← DEPRECATED (legacy)
Coherence_Spec_v1_0/ ← DEPRECATED (archive)
```

### 2.2 Directory Structure

| Path | Purpose |
|------|---------|
| `docs/ats/00_identity/` | Core identity, scope, governance |
| `docs/ats/10_mathematical_core/` | Mathematical foundations |
| `docs/ats/20_coh_kernel/` | Consensus kernel specs |
| `docs/ats/30_ats_runtime/` | Runtime specifications |
| `docs/ats/40_nsc_integration/` | NSC integration |
| `docs/ats/50_security_model/` | Security requirements |
| `docs/ats/60_test_vectors/` | Test vectors |
| `docs/ats/90_roadmap/` | Future plans |

---

## 3. Versioning Rules

### 3.1 Version Bump Requirements

A version bump is REQUIRED when:

1. Adding new spec pages
2. Changing existing spec behavior
3. Adding new test vectors
4. Deprecating old specs

### 3.2 Version Format

```
MAJOR.MINOR.PATCH
- MAJOR: Breaking changes to spec behavior
- MINOR: New features (backward compatible)
- PATCH: Clarifications, fixes (no behavior change)
```

### 3.3 Version Locations

Each spec file must have:

```markdown
| Field | Value |
|-------|-------|
| **Version** | X.Y.Z |
| **Status** | ACTIVE | DEPRECATED | FROZEN |
```

---

## 4. Deprecation Policy

### 4.1 How to Deprecate

When deprecating a spec:

1. Change status to `DEPRECATED`
2. Add deprecation notice at top:
   ```markdown
   > **DEPRECATED**: Use [new_spec.md] instead. This spec will be removed in vX.Y.0.
   ```
3. Add redirect/note at bottom:
   ```markdown
   ## Migration
   Migrate to [new_spec.md] by [date].
   ```

### 4.2 Legacy Locations

Deprecated specs move to:
- `docs/legacy/` - Deprecated documentation
- Archives remain read-only

---

## 5. Test Vector Requirements

### 5.1 When Vectors Are Required

New specs MUST include test vectors if they define:
- Hashing algorithms
- Serialization formats
- Chain rules
- Receipt schemas

### 5.2 Vector Format

Vectors go in `compliance_tests/`:
- JSON or JSONL format
- Include input + expected output
- Document deterministic properties

---

## 6. Change Control

### 6.1 Proposal Process

1. Create PR with changes
2. Include updated version in spec
3. Add test vectors for new behavior
4. Update `spec_to_code_map.md` if applicable

### 6.2 Review Criteria

- Spec is self-consistent
- Implementation is feasible
- Test vectors are deterministic
- No ambiguity in key words (RFC 2119)

---

## 7. Key Words (RFC 2119)

Use these keywords precisely:

| Keyword | Meaning |
|---------|---------|
| MUST | Absolute requirement |
| MUST NOT | Absolute prohibition |
| SHOULD | Recommended, but not required |
| SHOULD NOT | Not recommended, but permitted |
| MAY | Optional |

---

## 8. Enforcement

### 8.1 Compliance Checks

- All specs MUST have version field
- All new crypto specs MUST have test vectors
- Deprecated specs MUST have migration notes

### 8.2 Violations

| Violation | Action |
|-----------|--------|
| Missing version | Block merge |
| No test vectors for crypto | Block merge |
| Deprecated without notice | Warning |

---

## 9. Related Documents

- [Spec to Code Map](01_spec_to_code_map.md)
- [Coh Kernel Scope](coh_kernel_scope.md)
- [Receipt Schema](20_coh_kernel/receipt_schema.md)
