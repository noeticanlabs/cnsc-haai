# TODO Organization Plan

**Created:** 2026-02-21  
**Status:** 📋 PROPOSED  
**Purpose:** Create a professional todo/tracker system for the cnsc-haai project

---

## Executive Summary

This plan establishes a unified system for tracking todos, work items, and technical debt across the cnsc-haai project. It addresses three areas:
1. **Plan files** in `/plans/` - 12 existing files needing categorization and standardization
2. **Inline TODOs** in source code - 3 items requiring tracking
3. **New centralized tracker** - A master TODO.md file with standardized format

---

## Current State Analysis

### Plan Files (in `/plans/`)

| # | Filename | Purpose | Recommended Category |
|---|----------|---------|----------------------|
| 1 | ATS_Kernel_Fix_Plan.md | ATS kernel code fixes | `kernel/` |
| 2 | CNHAAI_Doc_Spine_Reorganization.md | Documentation restructuring | `docs/` |
| 3 | CNHAAI_Issue_Fix_Plan.md | General issue fixes | `general/` |
| 4 | cnsc_haai_fix_plan.md | General CNSC fixes | `general/` |
| 5 | COH_AGI_Migration_Completion_Plan.md | COH-AGI migration | `migration/` |
| 6 | coherence_framework_implementation_plan.md | Coherence framework | `core/` |
| 7 | GML_Graph_Native_Migration_Plan.md | GML graph migration | `migration/` |
| 8 | GML_Graph_Native_Migration_Results.md | Migration results | `migration/` |
| 9 | NPE_Implementation_Plan.md | NPE service integration | `integration/` |
| 10 | TGS_Build_Integration_Plan.md | TGS build integration | `integration/` |
| 11 | Token_to_Graph_Conversion_Plan.md | Token/graph conversion | `core/` |
| 12 | *NEW* TODO_Organization_Plan.md | This plan | `general/` |

### Inline TODOs in Source Code

| # | File | Line | Description |
|---|------|------|-------------|
| 1 | `src/cnsc/haai/cli/commands.py` | 660 | Implement full GML tracing with coherence tracking |
| 2 | `src/npe/api/routes.py` | 189 | Get corpus snapshot hash from corpus |
| 3 | `src/cnsc/haai/nsc/proposer_client.py` | 380 | (This appears to be an error message, not a TODO) |

---

## Proposed Directory Structure

```
plans/
├── README.md                          # Index of all plans
├── TODO.md                            # Master todo tracker (NEW)
├── general/
│   ├── CNHAAI_Issue_Fix_Plan.md
│   ├── cnsc_haai_fix_plan.md
│   └── TODO_Organization_Plan.md      # This plan
├── kernel/
│   └── ATS_Kernel_Fix_Plan.md
├── docs/
│   └── CNHAAI_Doc_Spine_Reorganization.md
├── core/
│   ├── coherence_framework_implementation_plan.md
│   └── Token_to_Graph_Conversion_Plan.md
├── migration/
│   ├── COH_AGI_Migration_Completion_Plan.md
│   ├── GML_Graph_Native_Migration_Plan.md
│   └── GML_Graph_Native_Migration_Results.md
└── integration/
    ├── NPE_Implementation_Plan.md
    └── TGS_Build_Integration_Plan.md
```

---

## TODO.md Standard Format

```markdown
# TODO Tracker

**Last Updated:** YYYY-MM-DD
**Total Items:** X | Pending: X | In Progress: X | Completed: X

---

## Priority: Critical

| ID | Status | Item | Owner | Created | Updated |
|----|--------|------|-------|---------|---------|
| TODO-001 | [ ] | ... | ... | YYYY-MM-DD | YYYY-MM-DD |

## Priority: High

...

## Priority: Medium

...

## Priority: Low

...

---

## Completed (Archive)

| ID | Status | Item | Owner | Completed |
|----|--------|------|-------|-----------|
| TODO-XXX | [x] | ... | ... | YYYY-MM-DD |
```

### Status Labels
- `[ ]` - Pending
- `[-]` - In Progress
- `[x]` - Completed
- `[!]` - Blocked

### Priority Levels
- **Critical** - Blocker, security, or fundamental breakage
- **High** - Important feature or fix
- **Medium** - Normal development work
- **Low** - Nice to have, can be deferred

---

## Implementation Tasks

### Phase 1: Create Infrastructure

- [ ] 1.1 Create `plans/README.md` - Index of all plans with descriptions
- [ ] 1.2 Create `plans/TODO.md` - Master todo tracker with standardized format
- [ ] 1.3 Add status metadata header to each existing plan file

### Phase 2: Reorganize Plans Directory

- [ ] 2.1 Create category subdirectories: `general/`, `kernel/`, `docs/`, `core/`, `migration/`, `integration/`
- [ ] 2.2 Move plan files into appropriate category directories
- [ ] 2.3 Update all internal links in moved files

### Phase 3: Migrate Inline TODOs

- [ ] 3.1 Add TODO items from `src/cnsc/haai/cli/commands.py` to `TODO.md`
- [ ] 3.2 Add TODO items from `src/npe/api/routes.py` to `TODO.md`
- [ ] 3.3 Convert TODO comments to trackable format or remove if duplicate

### Phase 4: Documentation & Workflow

- [ ] 4.1 Create `docs/workflow/TODO_WORKFLOW.md` - Guidelines for using the tracker
- [ ] 4.2 Add a pre-commit hook or script to validate TODO format
- [ ] 4.3 Document the versioning scheme for plan files

### Phase 5: Documentation Reorganization (See Separate Plan)

- [ ] **See:** [`Documentation_Reorganization_Plan.md`](Documentation_Reorganization_Plan.md)
- [ ] 5.1 Create section READMEs in cnhaai/docs/
- [ ] 5.2 Consolidate docs/ and spec/ into cnhaai/docs/
- [ ] 5.3 Move legacy specs to cnhaai/docs/legacy/
- [ ] 5.4 Standardize naming conventions

---

## Migration Examples

### Before (Inline TODO)
```python
# TODO: Implement full GML tracing with coherence tracking
```

### After (Tracked + Comment)
```python
# TODO: See TODO-001 in plans/TODO.md - Implement full GML tracing with coherence tracking
```

---

## Benefits

1. **Single source of truth** - All work items in one place
2. **Searchable** - Easy to find by ID, priority, or keyword
3. **Trackable** - Status and ownership clearly visible
4. **Prioritized** - Critical items surface to top
5. **Auditable** - History of when items were created/completed

---

## Notes

- Plan files remain as detailed documentation; TODO.md serves as the executive summary
- Category directories use lowercase names for consistency
- TODO IDs should be zero-padded (TODO-001, TODO-002, etc.)
- Review TODO.md in every planning/review meeting
