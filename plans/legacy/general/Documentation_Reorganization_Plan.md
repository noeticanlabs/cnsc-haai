# Documentation Reorganization Plan

**Created:** 2026-02-21  
**Status:** 📋 PROPOSED  
**Purpose:** Consolidate all specs into `cnhaai/docs/` and create clear taxonomy

---

## Executive Summary

This plan reorganizes scattered documentation into a unified structure under `cnhaai/docs/`, eliminating duplicates and creating clear pathways for users and developers.

---

## Current State Analysis

### Documentation Locations (Before)

| Location | Content | Status |
|----------|---------|--------|
| `cnhaai/docs/` | Primary docs (spine, ats, gmi, coh-agi, guides, appendices) | Active |
| `docs/` | Architecture specs, legacy v1.0 specs | Mixed |
| `spec/` | System overview, compiler contracts, glossaries | Legacy |
| `Coherence_Spec_v1_0/` | Old v1.0 specification | Legacy |
| `cnhaai/implementation/` | Minimal kernel spec | Single file |

### Issues Identified

1. **Scattered specs** - No single entry point for specifications
2. **Legacy duplication** - v1.0 specs in multiple locations
3. **Schema isolation** - Schemas in root `schemas/`, not near specs that use them
4. **Unclear hierarchy** - No master index linking everything
5. **Naming inconsistency** - Some use `00_`, others use `00-`

---

## Proposed Structure

```
cnhaai/docs/
├── README.md                    # Master index (NEW)
├── SPINE.md                     # Core abstraction theory
├── spine/                       # Theory & conceptual (24 files)
│   └── README.md
├── ats/                         # ATS specifications (well organized)
│   ├── README.md
│   ├── 00_identity/
│   ├── 10_mathematical_core/
│   ├── 20_coh_kernel/
│   ├── 30_ats_runtime/
│   ├── 40_nsc_integration/
│   ├── 50_security_model/
│   ├── 60_test_vectors/
│   └── 90_roadmap/
├── gmi/                         # GMI specifications
│   ├── README.md
│   └── appendices/
├── coh-agi/                     # COH-AGI overview
│   ├── README.md
│   └── 10_engineering_mapping/
├── guides/                      # User/developer guides
│   └── README.md
├── appendices/                  # Reference material
│   └── README.md
└── legacy/                      # v1.0 specs (moved from root)
    ├── README.md
    └── Coherence_Spec_v1_0/
```

```
docs/  →  cnhaai/docs/guides/    # Migration: guides
spec/  →  cnhaai/docs/legacy/   # Migration: legacy specs
Coherence_Spec_v1_0/  →  cnhaai/docs/legacy/Coherence_Spec_v1_0/
```

```
schemas/  →  cnhaai/docs/appendices/schemas/  (or keep in root if actively used)
```

---

## Migration Tasks

### Phase 1: Create Infrastructure

- [ ] 1.1 Create `cnhaai/docs/README.md` - Master index with navigation
- [ ] 1.2 Create `cnhaai/docs/ats/README.md` - ATS section index
- [ ] 1.3 Create `cnhaai/docs/spine/README.md` - Spine section index
- [ ] 1.4 Create `cnhaai/docs/gmi/README.md` - GMI section index
- [ ] 1.5 Create `cnhaai/docs/coh-agi/README.md` - COH-AGI section index
- [ ] 1.6 Create `cnhaai/docs/guides/README.md` - Guides section index
- [ ] 1.7 Create `cnhaai/docs/appendices/README.md` - Appendices section index
- [ ] 1.8 Create `cnhaai/docs/legacy/README.md` - Legacy section index

### Phase 2: Consolidate Documentation

- [ ] 2.1 Move `docs/architecture/` → `cnhaai/docs/guides/`
- [ ] 2.2 Move `spec/` → `cnhaai/docs/legacy/spec/`
- [ ] 2.3 Move `Coherence_Spec_v1_0/` → `cnhaai/docs/legacy/Coherence_Spec_v1_0/`
- [ ] 2.4 Move `cnhaai/implementation/` → `cnhaai/docs/appendices/implementation/`
- [ ] 2.5 Move `docs/legacy/` content to appropriate locations

### Phase 3: Add Schema Co-location

- [ ] 3.1 Copy key schemas to `cnhaai/docs/appendices/schemas/`
- [ ] 3.2 Update schema references in markdown files
- [ ] 3.3 OR keep schemas in root `schemas/` and document in README

### Phase 4: Fix Naming & Cross-references

- [ ] 4.1 Standardize numbering: `00_identity/` not `00_identity/` (keep dashes)
- [ ] 4.2 Add cross-links between related documents
- [ ] 4.3 Fix broken internal links after moves
- [ ] 4.4 Add "See Also" sections to related documents

### Phase 5: Cleanup

- [ ] 5.1 Remove empty directories after migration
- [ ] 5.2 Update any external references (README files, etc.)
- [ ] 5.3 Verify all files accessible from new locations

---

## New README.md Template

```markdown
# CNSC-HAAI Documentation

**Version:** 1.0  
**Last Updated:** YYYY-MM-DD

Welcome to the CNSC-HAAI documentation. This is the authoritative source for all project specifications, guides, and references.

## Quick Links

| Section | Description |
|---------|-------------|
| [Spine](spine/) | Core abstraction theory |
| [ATS](ats/) | Autonomic Transaction System specifications |
| [GMI](gmi/) | Global Memory Infrastructure |
| [COH-AGI](coh-agi/) | Coherent AGI architecture |
| [Guides](guides/) | User and developer guides |
| [Appendices](appendices/) | Reference material, schemas, glossary |
| [Legacy](legacy/) | Historical specifications (v1.0) |

## Getting Started

1. **New to CNSC-HAAI?** Start with [Spine](spine/00-project-overview.md)
2. **Understanding ATS?** See [ATS Summary](ats/00_identity/ats_definition.md)
3. **Want to build?** Check out the [Guides](guides/)

## Project Structure

- [`src/`](src/) - Implementation source code
- [`schemas/`](schemas/) - JSON schemas
- [`plans/`](plans/) - Project plans and trackers
- [`tests/`](tests/) - Test suite
```

---

## File Naming Convention

Use consistent naming across all documentation:

| Type | Convention | Example |
|------|------------|---------|
| Sections | `NN_name/` | `00_identity/` |
| Documents | `NN-name.md` | `00-identity.md` |
| Multi-part | `NN-name-part-N.md` | `01-intro-part-1.md` |

---

## Cross-Reference Format

```markdown
## See Also

- [Document Title](path/to/document.md) - Brief description
- [ATS Kernel](../ats/20_coh_kernel/chain_hash_rule.md) - Related spec
```

---

## Backward Compatibility

- Create redirects if old URLs are externally referenced
- Document old paths in `cnhaai/docs/legacy/migration_notes.md`
- Update any CI/CD that references old paths

---

## Benefits

1. **Single source of truth** - All docs in one place
2. **Clear hierarchy** - Easy to find what you need
3. **Professional organization** - Matches industry standards
4. **Easy onboarding** - Clear entry points for new users
5. **Maintainable** - Clear ownership of each section
