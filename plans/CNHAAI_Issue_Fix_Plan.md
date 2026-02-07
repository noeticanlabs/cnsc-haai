# CNHAAI Issue Fix Plan

**Created:** 2026-02-07  
**Status:** Draft - Pending User Approval  
**Author:** Architect Mode

---

## Executive Summary

This plan addresses all identified issues in the CNHAAI project, prioritizing critical issues that prevent end-to-end usability. The plan is organized into 3 phases with clear dependencies and success criteria.

---

## Issue Summary

| Severity | Count | Description |
|----------|-------|-------------|
| CRITICAL | 2 | Receipt schema incompatibility, empty end-to-end examples |
| MAJOR | 4 | Under-specified seam contracts, legacy docs, dual doc structure |
| MINOR | 3 | Missing CLI/API docs, no cross-reference index |

---

## Phase 1: Critical Fixes (Foundation)

### Issue 1.1: Receipt Schema Unification

**Problem:** 3 incompatible receipt implementations:
- [`schemas/receipt.schema.json`](schemas/receipt.schema.json) - minimal (receipt_id, parent, hash, payload, phase)
- [`cnhaai/docs/appendices/appendix-c-receipt-schema.md`](cnhaai/docs/appendices/appendix-c-receipt-schema.md) - full (version, receipt_id, timestamp, content, signature)
- [`src/cnsc/haai/gml/receipts.py`](src/cnsc/haai/gml/receipts.py:25) - enums (ReceiptStepType, ReceiptDecision, ReceiptSignature)

**Root Cause:** Parallel development without schema governance

#### Actions Required

| # | File | Change |
|---|------|--------|
| 1.1.1 | `schemas/receipt.schema.json` | Upgrade to v1.0.0 full schema with version, timestamp, content, provenance, signature |
| 1.1.2 | `src/cnsc/haai/gml/receipts.py` | Add version field, update dataclasses to match full schema |
| 1.1.3 | `cnhaai/docs/appendices/appendix-c-receipt-schema.md` | Align with code implementation, add migration notes |
| 1.1.4 | `cnhaai/docs/spine/21-receipt-system.md` | Update theory documentation to match schema |
| 1.1.5 | `cnhaai/docs/spine/22-receipt-implementation.md` | Update implementation notes |
| 1.1.6 | `spec/gml/03_Receipt_Spec_and_Hash_Chains.md` | Expand from 2 bullets to complete spec |
| 1.1.7 | `Coherence_Spec_v1_0/schemas/coherence_receipt.schema.json` | Deprecate or align with unified schema |
| 1.1.8 | All receipt examples in `Coherence_Spec_v1_0/examples/` | Update to use unified schema |

**Dependencies:** None (foundation work)  
**Success Criteria:**
- [ ] Single source of truth for receipt schema
- [ ] All code, docs, and examples use unified schema v1.0.0
- [ ] All receipt-related tests pass

---

### Issue 1.2: Complete End-to-End Examples

**Problem:** All 4 files in [`examples/end_to_end/`](examples/end_to_end) are empty stubs:
- [`00_glll_encode_decode.md`](examples/end_to_end/00_glll_encode_decode.md)
- [`01_ghll_parse_rewrite.md`](examples/end_to_end/01_ghll_parse_rewrite.md)
- [`02_nsc_cfa_run.md`](examples/end_to_end/02_nsc_cfa_run.md)
- [`03_gml_trace_audit.md`](examples/end_to_end/03_gml_trace_audit.md)

**Root Cause:** Documentation deferred during implementation

#### Actions Required

| # | File | Change |
|---|------|--------|
| 1.2.1 | `examples/end_to_end/00_glll_encode_decode.md` | Add: codebook creation → glyph encoding → packetization → transmission → depacketization → decoding |
| 1.2.2 | `examples/end_to_end/01_ghll_parse_rewrite.md` | Add: GHLL source → lexicon parsing → AST → type checking → rewrite rules → NSC IR |
| 1.2.3 | `examples/end_to_end/02_nsc_cfa_run.md` | Add: NSC bytecode → VM execution → CFA analysis → gate evaluation → receipt emission |
| 1.2.4 | `examples/end_to_end/03_gml_trace_audit.md` | Add: Trace collection → receipt chain verification → replay → audit query |

**Dependencies:** Issue 1.1 (receipt schema) must complete first  
**Success Criteria:**
- [ ] Each example is a complete, runnable walkthrough
- [ ] All examples produce verifiable receipts
- [ ] Examples can be executed end-to-end

---

## Phase 2: Major Fixes (Architecture Clarity)

### Issue 2.1: Seam Contracts Formalization

**Problem:** [`spec/seam/`](spec/seam) files are 2-5 bullets each, missing:
- Formal pre/post conditions
- Error codes and handling
- Example wire formats
- Version compatibility rules

**Current State (2-5 bullets per file):**
```
spec/seam/00_Seam_Principles.md - 2 bullets
spec/seam/01_GLLL_to_GHLL_Binding.md - 2 bullets
spec/seam/02_GHLL_to_NSC_Lowering_Contract.md - 2 bullets
spec/seam/03_NSC_to_GML_Receipt_Emission_Contract.md - 2 bullets
spec/seam/04_Frontier_Definition_and_Coverage.md - 5 bullets
spec/seam/05_Replay_Verifier_Interface.md - 2 bullets
```

#### Actions Required

| # | File | Change |
|---|------|--------|
| 2.1.1 | `spec/seam/00_Seam_Principles.md` | Expand to: principles, invariants, determinism guarantees |
| 2.1.2 | `spec/seam/01_GLLL_to_GHLL_Binding.md` | Add: binding rules, error codes, wire format example |
| 2.1.3 | `spec/seam/02_GHLL_to_NSC_Lowering_Contract.md` | Add: preconditions, postconditions, error handling |
| 2.1.4 | `spec/seam/03_NSC_to_GML_Receipt_Emission_Contract.md` | Add: receipt format, timing, failure modes |
| 2.1.5 | `spec/seam/04_Frontier_Definition_and_Coverage.md` | Add: formal definition, coverage metrics |
| 2.1.6 | `spec/seam/05_Replay_Verifier_Interface.md` | Add: API contract, input/output formats |
| 2.1.7 | Create `spec/seam/06_Version_Compatibility.md` | Add: version rules, migration paths |

**Dependencies:** Phase 1 complete  
**Success Criteria:**
- [ ] Each seam contract is actionable (can implement from spec)
- [ ] All error conditions documented
- [ ] Wire format examples included

---

### Issue 2.2: Legacy Documentation Cleanup

**Problem:** [`Coherence_Spec_v1_0/`](Coherence_Spec_v1_0) exists alongside [`spec/`](spec) and [`cnhaai/docs/`](cnhaai/docs) without clear relationship

#### Actions Required

| # | Action | Change |
|---|--------|--------|
| 2.2.1 | Create deprecation notice | Add `DEPRECATED.md` to Coherence_Spec_v1_0/ |
| 2.2.2 | Document migration path | Add migration guide from v1.0 to current |
| 2.2.3 | Create cross-reference | Link v1.0 docs to current spec equivalents |
| 2.2.4 | Archive or remove | Decide: archive in `/archive` or remove (post Phase 2) |

**Dependencies:** Phase 1 complete  
**Success Criteria:**
- [ ] Clear deprecation status visible
- [ ] Migration path documented
- [ ] No confusion about which docs are current

---

### Issue 2.3: Documentation Structure Rationalization

**Problem:** Dual structure without clear relationship:
- `spec/` - Technical specifications
- `cnhaai/docs/spine/` - Theory/documentation
- `docs/` - Additional docs (overlaps with above)
- `examples/` - Examples

#### Actions Required

| # | Action | Change |
|---|--------|--------|
| 2.3.1 | Document architecture | Create `docs/ARCHITECTURE.md` explaining doc structure |
| 2.3.2 | Clarify `spec/` vs `docs/` | Add mapping table in `spec/README.md` |
| 2.3.3 | Clarify `cnhaai/docs/spine/` | Add relationship to `spec/` in `cnhaai/README.md` |
| 2.3.4 | Remove duplicates | Identify and consolidate duplicate content |
| 2.3.5 | Add navigation | Create `docs/INDEX.md` with cross-references |

**Dependencies:** Issue 2.1 (seam contracts) partially complete  
**Success Criteria:**
- [ ] Clear hierarchy: spec = implementation, docs = theory, spine = learning path
- [ ] No duplicate content
- [ ] New contributors can navigate docs easily

---

### Issue 2.4: Minimal Kernel Documentation Alignment

**Problem:** Two minimal kernel specs exist:
- [`cnhaai/implementation/kernel/minimal-kernel-spec.md`](cnhaai/implementation/kernel/minimal-kernel-spec.md)
- [`spec/nsc/00_NSC_Goals_and_Invariants.md`](spec/nsc/00_NSC_Goals_and_Invariants.md)

#### Actions Required

| # | File | Change |
|---|------|--------|
| 2.4.1 | `cnhaai/implementation/kernel/minimal-kernel-spec.md` | Add reference to `spec/nsc/00_NSC_Goals_and_Invariants.md` |
| 2.4.2 | `spec/nsc/00_NSC_Goals_and_Invariants.md` | Add reference to minimal kernel spec |
| 2.4.3 | Merge if identical | Consolidate if content is redundant |

**Dependencies:** Phase 1 complete  
**Success Criteria:**
- [ ] Clear relationship between kernel and NSC specs
- [ ] No conflicting information

---

## Phase 3: Minor Fixes (Polish)

### Issue 3.1: CLI Reference Documentation

**Problem:** No CLI reference docs, though [`src/cnsc/haai/cli/commands.py`](src/cnsc/haai/cli/commands.py:14) has 10+ subcommands

**Current CLI Subcommands:**
- `parse` - Parse GHLL source
- `compile` - Compile to NSC bytecode
- `run` - Execute bytecode
- `trace` - Run with GML tracing
- `verify` - Verify receipts
- `replay` - Replay execution
- `encode` - GLLL encode
- `decode` - GLLL decode
- `lexicon` - Lexicon management
- `gate` - Gate policy management

#### Actions Required

| # | File | Change |
|---|------|--------|
| 3.1.1 | `docs/cli-reference.md` | Create comprehensive CLI reference |
| 3.1.2 | `spec/nsc/09_CLI_and_Tooling.md` | Expand from 8 lines to complete spec |
| 3.1.3 | `cnhaai/docs/guides/cli-guide.md` | Add getting-started guide |

**Dependencies:** Phase 1 complete  
**Success Criteria:**
- [ ] Every CLI command documented
- [ ] Examples for each command
- [ ] Error codes documented

---

### Issue 3.2: API Documentation

**Problem:** No API documentation for Python modules

#### Actions Required

| # | File | Change |
|---|------|--------|
| 3.2.1 | `docs/api/cnhaai/` | Create API docs directory |
| 3.2.2 | `docs/api/cnsc/` | Create API docs directory |
| 3.2.3 | Generate docstrings | Ensure all public APIs have docstrings |
| 3.2.4 | Create `docs/api/README.md` | API overview and navigation |

**Dependencies:** Phase 1 complete  
**Success Criteria:**
- [ ] All public classes/functions documented
- [ ] Usage examples in docstrings
- [ ] Type hints complete

---

### Issue 3.3: Cross-Reference Index

**Problem:** No index linking specs to code

#### Actions Required

| # | File | Change |
|---|------|--------|
| 3.3.1 | `docs/cross-reference.md` | Create master index |
| 3.3.2 | Add code comments | Link specs to code with `SPEC: spec/xx_xxx.md` |
| 3.3.3 | Add doc links | Link code to docs with `DOCS: cnhaai/docs/spine/xx_xxx.md` |

**Dependencies:** Phase 2 complete  
**Success Criteria:**
- [ ] Every spec section links to relevant code
- [ ] Every major code module links to relevant specs
- [ ] Navigable from code to docs and vice versa

---

## Dependencies Graph

```
Phase 1 (Critical)
├── 1.1 Receipt Schema Unification
│   └── Blocks: All other receipt-related work
└── 1.2 Complete E2E Examples
    └── Blocks: Phase 2, Phase 3

Phase 2 (Major)
├── 2.1 Seam Contracts (depends on 1.1, 1.2)
├── 2.2 Legacy Docs Cleanup (depends on 2.1)
├── 2.3 Doc Structure Rationalization (depends on 2.1, 2.2)
└── 2.4 Kernel Alignment (depends on 1.1)

Phase 3 (Minor)
├── 3.1 CLI Reference (depends on 1.1)
├── 3.2 API Documentation (depends on 1.1)
└── 3.3 Cross-Reference Index (depends on 2.1, 2.3)
```

---

## Execution Timeline

```
Month 1:
├── Week 1: Receipt Schema Design & Approval
├── Week 2: Schema Implementation (code + JSON Schema)
├── Week 3: Documentation Updates
└── Week 4: E2E Example 1 (GLLL Encode/Decode)

Month 2:
├── Week 1: E2E Examples 2-4 (GHLL, NSC, GML)
├── Week 2: Seam Contracts 1-3 (GLLL→GHLL→NSC)
├── Week 3: Seam Contracts 4-6 + Version Compatibility
└── Week 4: Legacy Doc Cleanup + Migration Guide

Month 3:
├── Week 1: Doc Structure Rationalization
├── Week 2: CLI Reference Documentation
├── Week 3: API Documentation
└── Week 4: Cross-Reference Index + Final Polish
```

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Schema changes break existing code | High | Version the schema, provide migration path |
| Doc cleanup causes confusion | Medium | Deprecate gradually, maintain redirects |
| E2E examples reveal implementation gaps | Medium | Focus on working paths, document gaps |
| Cross-reference maintenance burden | Low | Automate generation where possible |

---

## Success Metrics

| Phase | Metric | Target |
|-------|--------|--------|
| Phase 1 | Schema consistency | 100% of receipts use v1.0.0 |
| Phase 1 | E2E examples | 4/4 runnable end-to-end |
| Phase 2 | Seam completeness | All 6 seams have full specs |
| Phase 2 | Doc clarity | New contributor navigation test passes |
| Phase 3 | CLI docs | 100% of commands documented |
| Phase 3 | API docs | 100% public APIs documented |
| All | Test coverage | No regression in test pass rate |

---

## Recommendations

1. **Start with Issue 1.1** - Everything depends on unified receipt schema
2. **Create receipt schema review** - Have team approve schema before implementation
3. **Write E2E examples first** - Use to validate schema and identify implementation gaps
4. **Automate doc generation** - Use docstrings → documentation where possible
5. **Establish governance** - New schemas must go through review process

---

## Next Steps

1. Review and approve this plan
2. Begin Phase 1, Issue 1.1 (Receipt Schema Design)
3. Schedule weekly check-ins for progress tracking

---

*Plan created in Architect mode. Ready for user approval to proceed to Code mode for implementation.*
