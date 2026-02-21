# CNSC-HAAI Issues Fix Plan

**Generated**: 2026-02-21  
**Purpose**: Address P0/P1/P2 issues from full-repo review

---

## Executive Summary

This plan addresses critical correctness and architectural issues identified in the repository review. The issues are organized by priority, with clear actionable steps and dependencies.

### Priority Overview

| Priority | Issue | Effort | Risk if Deferred |
|----------|-------|--------|------------------|
| P0 | NSC VM float encoding broken + non-deterministic | Medium | Runtime crashes |
| P0 | GML receipt chain not consensus-tight | High | Consensus failures |
| P0 | ATS QFixed overflow semantics conflict with spec | Medium | Invalid trajectories accepted |
| P1 | ATS state_hash canonical bytes use concatenation | Medium | Non-injective hashing |
| P1 | Floats appear in language frontend | High | Boundary violations |
| P2 | License/doc hygiene issues | Low | Friction, confusion |

---

## Phase 1: Critical P0 Fixes (Week 1-2)

### 1.1 Fix NSC VM Float Encoding/Decoding

**Problem**: [`src/cnsc/haai/nsc/vm.py:251`](src/cnsc/haai/nsc/vm.py:251) calls `float.to_bytes()` and [`src/cnsc/haai/nsc/vm.py:447`](src/cnsc/haai/nsc/vm.py:447) calls `float.from_bytes()` which don't exist in Python.

**Decision Required**: 
- Option A: Remove float operands entirely from bytecode (recommended - aligns with "no floats in consensus")
- Option B: Implement IEEE-754 packing via `struct.pack('>d', x)` / `struct.unpack('>d', x)`

**Recommended Action**: Choose Option A — ban float operands entirely.

**Steps**:
1. [ ] Remove `emit_float` method from `BytecodeEmitter`
2. [ ] Remove float decoding branch in `VM._decode_operands()`
3. [ ] Remove `NSCOpcode.FLOAT` enum value if present
4. [ ] Add gate in GHLL parser to reject float literals at compile-time: `"Float literals not permitted in NSC bytecode; use QFixed from rational representation"`
5. [ ] Add test: verify parsing `let x: float = 3.14;` produces compile error
6. [ ] Update [`docs/ats/20_coh_kernel/deterministic_numeric_domain.md`](docs/ats/20_coh_kernel/deterministic_numeric_domain.md) to explicitly ban float types in NSC

**File to edit**: 
- [`src/cnsc/haai/nsc/vm.py`](src/cnsc/haai/nsc/vm.py)
- [`src/cnsc/haai/ghll/parser.py`](src/cnsc/haai/ghll/parser.py) (add compile-time rejection)

---

### 1.2 Define and Enforce Consensus Boundary

**Problem**: No clear separation between consensus-critical code and telemetry/code. Risk of floats/timestamps/uuid flowing into consensus paths.

**Decision Required**: Define what "consensus" means in this system.

**Recommended Action**: Create a formal boundary document.

**Steps**:
1. [ ] Create new spec document: [`docs/ats/00_identity/consensus_boundary.md`](docs/ats/00_identity/consensus_boundary.md)

   Contents:
   ```
   ## Consensus Boundary

   ### Consensus-Critical (MUST use QFixed, JCS, no timestamps)
   - `src/cnsc_haai/consensus/*` - all modules
   - `src/cnsc/haai/ats/*` - verifier, numeric, types (StateCore)
   - Receipts with `version: "2.0.0"` or higher

   ### Non-Consensus / Telemetry (MAY use floats, timestamps, UUIDs)
   - `src/cnsc/haai/gml/*` - trace, receipts (telemetry variant)
   - `src/cnsc/haai/tgs/*` - debug/telemetry
   - `src/cnhaai/*` - UI heuristics (explicitly non-consensus)
   - Receipts with `version: "1.x.x"`

   ### Boundary Enforcement
   - Import guards: consensus modules MUST NOT import from non-consensus
   - Type markers: all consensus receipts MUST have `version: "2.0.0"` or higher
   - No float/QFixed mixing in receipt content fields
   ```

2. [ ] Add import guard in [`src/cnsc_haai/consensus/__init__.py`](src/cnsc_haai/consensus/__init__.py):
   ```python
   # CONSENSUS BOUNDARY GUARD
   # This module is consensus-critical. DO NOT import from:
   #   - src/cnsc/haai/gml/*
   #   - src/cnsc/haai/tgs/*
   #   - src/cnhaai/*
   # Doing so may introduce non-determinism (floats, timestamps, UUIDs).
   ```

3. [ ] Add same guard to [`src/cnsc/haai/ats/__init__.py`](src/cnsc/haai/ats/__init__.py)

4. [ ] Update README.md to reference the boundary document

---

### 1.3 Align ATS QFixed Overflow Semantics with Spec

**Problem**: Docs say "REJECT on overflow" but [`src/cnsc/haai/ats/numeric.py:166`](src/cnsc/haai/ats/numeric.py:166) silently caps.

**Recommended Action**: Change implementation to match docs (reject on overflow).

**Steps**:
1. [ ] Update `QFixed.__add__()` to raise `QFixedOverflow` instead of capping:
   ```python
   def __add__(self, other: QFixed) -> QFixed:
       if not isinstance(other, QFixed):
           return NotImplemented
       result = self.value + other.value
       if result > MAX_VALUE:
           raise QFixedOverflow(f"Overflow: {self} + {other}")
       return QFixed(result)
   ```

2. [ ] Apply same change to `__mul__()`, `__truediv__()`

3. [ ] Update `BudgetManager` to catch `QFixedOverflow` and treat as step rejection

4. [ ] Update docs to clarify: "overflow causes step REJECTION, not saturation"

5. [ ] Verify `MAX_VALUE` matches spec range — currently 10000 but spec says 10^18-1

6. [ ] Run existing ATS tests to ensure no regressions

**Files to edit**:
- [`src/cnsc/haai/ats/numeric.py`](src/cnsc/haai/ats/numeric.py)
- [`src/cnsc/haai/ats/budget.py`](src/cnsc/haai/ats/budget.py)
- [`docs/ats/20_coh_kernel/deterministic_numeric_domain.md`](docs/ats/20_coh_kernel/deterministic_numeric_domain.md)

---

### 1.4 Unify GML Receipt Chain Hashing (Or Explicitly Deprecate)

**Problem**: GML receipts use non-deterministic genesis (timestamp + UUID) and custom hash spec, conflicting with consensus chain hash.

**Decision Required**: 
- Option A: Refactor GML to reuse consensus chain hashing (breaking change)
- Option B: Explicitly mark GML receipts as telemetry-only, never used for consensus

**Recommended Action**: Choose Option B — GML is telemetry, ATS is consensus.

**Steps**:
1. [ ] Add version field check in `ReceiptVerifier`:
   ```python
   def verify_step(self, ...):
       # Reject v1 receipts in consensus path
       if receipt.version.startswith("1."):
           raise ATSError(RejectionCode.INVALID_RECEIPT_VERSION, 
                        "v1 receipts are telemetry-only, use v2+ for consensus")
   ```

2. [ ] Update GML receipt creation to always use `version = "1.0.0"` (telemetry)

3. [ ] Update ATS bridge to convert GML → ATS v2 before verification

4. [ ] Add compliance test: verify v1 receipts are rejected in consensus path

5. [ ] Update docs: "GML receipts are for debugging/telemetry; ATS receipts for consensus"

**Files to edit**:
- [`src/cnsc/haai/ats/rv.py`](src/cnsc/haai/ats/rv.py)
- [`src/cnsc/haai/gml/receipts.py`](src/cnsc/haai/gml/receipts.py)
- [`src/cnsc/haai/ats/bridge.py`](src/cnsc/haai/ats/bridge.py)

---

## Phase 2: P1 Correctness Fixes (Week 2-3)

### 2.1 Fix ATS State Canonical Bytes (Injection Safety)

**Problem**: `StateCore.canonical_bytes()` concatenates five JSON blobs without framing — collision risk.

**Recommended Action**: Wrap in single JCS object with explicit field names.

**Steps**:
1. [ ] Refactor [`src/cnsc/haai/ats/types.py:199`](src/cnsc/haai/ats/types.py:199):
   ```python
   def canonical_bytes(self) -> bytes:
       # Wrap in single JCS object to prevent concatenation collisions
       from cnsc_haai.consensus.jcs import jcs_canonical_bytes
       obj = {
           "belief": self.belief.to_canonical_dict(),
           "memory": self.memory.to_canonical_dict(),
           "plan": self.plan.to_canonical_dict(),
           "policy": self.policy.to_canonical_dict(),
           "io": self.io.to_canonical_dict(),
       }
       return jcs_canonical_bytes(obj)
   ```

2. [ ] Add `to_canonical_dict()` methods to each StateComponent class

3. [ ] Run existing state-hash tests to verify no regression

4. [ ] Add collision test: verify different component orders produce different hashes

---

### 2.2 Audit and Remove Floats from Consensus-Adjacent Code

**Problem**: Floats appear in GHLL parser output and NSC VM state.

**Recommended Action**: Audit all paths from GHLL → NSC → GML receipts and ensure floats don't influence receipt content.

**Steps**:
1. [ ] Search all receipt content fields for float types:
   ```bash
   grep -rn "float" src/cnsc/haai/gml/receipts.py | grep "content\|hash"
   ```

2. [ ] For each float field in receipt content:
   - Convert to QFixed if consensus-adjacent
   - Move to metadata if non-consensus

3. [ ] Update GHLL parser: reject float literals with helpful message

4. [ ] Add compliance test: verify float literals rejected at parse time

---

### 2.3 Align Chain Hash Spec with Implementation

**Problem**: Docs mark chain_hash_rule.md and canonical_serialization.md as deprecated but don't point to replacement clearly.

**Recommended Action**: Update deprecation headers with clear migration path.

**Steps**:
1. [ ] Update [`docs/ats/20_coh_kernel/chain_hash_rule.md`](docs/ats/20_coh_kernel/chain_hash_rule.md) header:
   ```markdown
   > **DEPRECATED**: See [../30_ats_runtime/replay_verification.md](../30_ats_runtime/replay_verification.md)
   > and [../../spec/seam/04_Frontier_Definition_and_Coverage.md](../../spec/seam/04_Frontier_Definition_and_Coverage.md)
   > for current chain hashing spec.
   ```

2. [ ] Add "Migration Guide" section to deprecated docs pointing to new location

3. [ ] Ensure [`src/cnsc_haai/consensus/chain.py`](src/cnsc_haai/consensus/chain.py) is referenced in docs

---

## Phase 3: P2 Hygiene Fixes (Week 3)

### 3.1 Fix License Mismatch

**Problem**: [`pyproject.toml`](pyproject.toml:10) says PRL-1.1 but [`LICENSE`](LICENSE:1) is PRL-1.2.

**Steps**:
1. [ ] Update pyproject.toml line 10: `"CNSC-HAAI Protective Research License (PRL-1.2)"`

---

### 3.2 Fix Requirements.txt vs pyproject.toml Drift

**Problem**: [`requirements.txt`](requirements.txt:1) missing runtime deps declared in pyproject.toml.

**Steps**:
1. [ ] Regenerate requirements.txt from pyproject.toml:
   ```bash
   pip-compile pyproject.toml --output-file requirements.txt
   ```
   OR manually add missing runtime deps:
   ```
   requests>=2.28.0
   jsonschema>=4.17.0
   aiohttp>=3.9.0
   ```

---

### 3.3 Fix Makefile Test Target

**Problem**: [`Makefile:8`](Makefile:8) runs pytest without PYTHONPATH.

**Steps**:
1. [ ] Update test target:
   ```makefile
   test:
   	PYTHONPATH=./src pytest -q
   ```

---

## Phase 4: Testing & Validation (Week 4)

### 4.1 Add Consensus Boundary Tests

**Steps**:
1. [ ] Add test: verify consensus modules cannot import from non-consensus
2. [ ] Add test: verify v1 receipts rejected in consensus path
3. [ ] Add test: verify float literals rejected at GHLL parse time

### 4.2 Run Full Compliance Suite

**Steps**:
1. [ ] Run all compliance tests:
   ```bash
   PYTHONPATH=./src pytest compliance_tests/ -v
   ```

2. [ ] Run integration tests:
   ```bash
   PYTHONPATH=./src pytest tests/integration/ -v
   ```

3. [ ] Verify no regressions in existing 922 tests

---

## Dependencies & Ordering

```
Phase 1 (Critical)
├── 1.1 Fix NSC VM floats ──────► 1.2 (use same branch)
├── 1.2 Define boundary ─────────► 1.4 (depends on boundary)
└── 1.3 Align QFixed ───────────► 1.4 (depends on boundary)

Phase 2 (Correctness)
├── 2.1 Fix state canonical ─────┐
├── 2.2 Audit floats ───────────┤► After Phase 1
└── 2.3 Update deprecated docs ─┘

Phase 3 (Hygiene)
└── All independent, can parallelize

Phase 4 (Validation)
└── After all previous phases
```

---

## Success Criteria

- [ ] No float operands in NSC bytecode (compile-time rejection works)
- [ ] Consensus boundary documented and enforced via import guards
- [ ] QFixed overflow raises exception (not silent cap)
- [ ] GML receipts explicitly marked telemetry-only
- [ ] State canonical bytes use JCS wrapping (not raw concat)
- [ ] License text aligned (PRL-1.2)
- [ ] Makefile test target works without PYTHONPATH errors
- [ ] All 922+ tests pass

---

## Open Questions (Requires Team Input)

1. **QFixed MAX_VALUE mismatch**: Spec says 10^18-1 but code uses 10000. Which is correct?

2. **GML receipt versioning**: Should we bump GML to v2 with consensus-safe hashing, or keep v1 as telemetry only?

3. **Risk functional weights**: Currently hardcoded to 0.2 each. Should these be configurable per-deployment?

4. **Slab compression**: Docs say non-consensus until CRT implemented. Should we add a feature flag to disable slab features in consensus mode?

---

## Appendix: Files to Edit Summary

| File | Changes |
|------|---------|
| `src/cnsc/haai/nsc/vm.py` | Remove float emit/decode |
| `src/cnsc/haai/ghll/parser.py` | Reject float literals |
| `src/cnsc_haai/ats/numeric.py` | Overflow rejection, MAX_VALUE align |
| `src/cnsc/haai/ats/budget.py` | Catch overflow |
| `src/cnsc/haai/ats/types.py` | Canonical bytes JCS wrap |
| `src/cnsc/haai/ats/rv.py` | Reject v1 receipts |
| `src/cnsc/haai/gml/receipts.py` | Set v1 = telemetry |
| `src/cnsc/haai/ats/bridge.py` | Convert GML→ATSv2 |
| `src/cnsc_haai/consensus/__init__.py` | Import guard |
| `src/cnsc/haai/ats/__init__.py` | Import guard |
| `pyproject.toml` | License fix |
| `requirements.txt` | Add runtime deps |
| `Makefile` | PYTHONPATH fix |
| `docs/ats/00_identity/consensus_boundary.md` | New doc |
| `docs/ats/20_coh_kernel/*.md` | Update deprecation headers |
