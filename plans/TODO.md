# TODO Tracker

**Last Updated:** 2026-02-21  
**Total Items:** 5 | Pending: 4 | In Progress: 0 | Completed: 1

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
| TODO-002 | [ ] | Get corpus snapshot hash from corpus store | TBD | 2026-02-21 | 2026-02-21 |

**Details:** See `src/npe/api/routes.py:189` - Currently returning empty string

---

## Priority: Medium

| ID | Status | Item | Owner | Created | Updated |
|----|--------|------|-------|---------|---------|
| TODO-003 | [ ] | Execute TODO Organization Plan (Phases 1-4) | TBD | 2026-02-21 | 2026-02-21 |
| TODO-004 | [ ] | Execute Documentation Reorganization Plan | TBD | 2026-02-21 | 2026-02-21 |

**Details:** See [`plans/TODO_Organization_Plan.md`](plans/TODO_Organization_Plan.md) and [`plans/Documentation_Reorganization_Plan.md`](plans/Documentation_Reorganization_Plan.md)

**Details:** See `plans/TODO_Organization_Plan.md` for full implementation plan

---

## Priority: Low

*No items*

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
