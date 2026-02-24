# TODO Tracker

**Last Updated:** 2026-02-23  
**Total Items:** 8 | Pending: 0 | In Progress: 0 | Completed: 6 | Deprecated: 2

---

## Priority: Critical

| ID | Status | Item | Owner | Created | Updated |
|----|--------|------|-------|---------|---------|
| TODO-001 | [x] | Implement full GML tracing with coherence tracking | - | 2026-02-21 | 2026-02-21 |

**Details:** Implemented in `src/cnsc/haai/cli/commands.py:644` - Full GML tracing with coherence tracking now includes GHLL parsing, coherence analysis of AST nodes, and receipt generation with coherence state.

---

## Priority: High

| ID | Status | Item | Owner | Created | Updated |
|----|--------|------|-------|---------|---------|
| TODO-002 | [x] | Get corpus snapshot hash from corpus store | - | 2026-02-21 | 2026-02-21 |

**Details:** Fixed in `src/npe/api/routes.py:181-191` - Now correctly retrieves corpus_snapshot_hash from index dictionary

| TODO-005 | [x] | JCS RFC8785 Implementation | - | 2026-02-23 | 2026-02-23 |

**Details:** Implemented in `src/cnsc_haai/consensus/jcs.py` - RFC 8785 compliant JSON canonicalization with float rejection for consensus safety.

| TODO-006 | [x] | Add snapshot hashing functions | - | 2026-02-23 | 2026-02-23 |

**Details:** Added `hash_corpus_snapshot()` and `hash_receipts_snapshot()` in `src/npe/core/hashing.py`.

| TODO-007 | [x] | Fix GR repair proposer budget enforcement | - | 2026-02-23 | 2026-02-23 |

**Details:** Fixed `src/npe/proposers/gr/repair_from_gate_reasons.py` to properly enforce max_candidates budget limit.

| TODO-008 | [x] | Fix golden test vectors | - | 2026-02-23 | 2026-02-23 |

**Details:** Updated TV1 and TV2 expected hashes in `tests/vectors/npe/v1_0_1/` to match canonical serialization.

---

## Priority: Medium

*No active items*

---

## Priority: Low

*No items*

---

## Deprecated

| ID | Status | Item | Owner | Deprecated |
|----|--------|------|-------|-----------|
| TODO-003 | [~] | Execute TODO Organization Plan (Phases 1-4) | - | 2026-02-21 |
| TODO-004 | [~] | Execute Documentation Reorganization Plan | - | 2026-02-21 |

**Reason:** These structural tasks have been superseded by modular updates to individual components. Focus has shifted to targeted fixes and feature implementation.

---

## Completed (Archive)

| ID | Status | Item | Owner | Completed |
|----|--------|------|-------|-----------|
| TODO-000 | [x] | Create TODO Organization Plan | - | 2026-02-21 |

---

## How to Use This Tracker

1. **Add new items**: Create new row with next sequential ID, set status to `[ ]`
2. **Update items**: Move from Pending → In Progress → Completed as work advances
3. **Reference in code**: Add comment like `# TODO: See TODO-001 in plans/TODO.md`
4. **Weekly review**: Update status, resolve blocked items, add new items

### Status Legend
- `[ ]` - Pending (not started)
- `[-]` - In Progress (actively working)
- `[x]` - Completed
- `[!]` - Blocked (waiting on external dependency)

### Priority Levels
- **Critical** - Blocker, security issue, or fundamental breakage
- **High** - Important feature or fix needed soon
- **Medium** - Normal development work
- **Low** - Nice to have, can be deferred indefinitely

---

## Related Plans

- [`TODO_Organization_Plan.md`](TODO_Organization_Plan.md) - Full implementation plan
- [`README.md`](README.md) - Index of all project plans
