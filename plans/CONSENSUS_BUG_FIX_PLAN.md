# Consensus-Breaking Bugs Implementation Fix Plan

**Generated:** 2026-02-23  
**Context:** Hostile referee review from cnsc-haai-main(12).zip  
**Updated:** 2026-02-23 (Added strategic architecture decision)

**Objective:** Fix consensus-breaking bugs + resolve spec design issues to achieve protocol coherence

---

## Strategic Architecture Decision (CRITICAL)

Per review analysis, the following protocol decision is REQUIRED before implementation:

### Split: receipt_id vs chain_digest

| Concept | Purpose | Includes prev_hash? |
|---------|---------|---------------------|
| **`receipt_id`** | Content addressable ID for this receipt | NO - it's a stable ID |
| **`chain_digest`** | Order-binding, tamper-evident history | YES - depends on prior |

### Selected Protocol: Option A (Real Chain)

```
receipt_id = SHA256(DOMAIN || JCS(receipt_core))        # Content hash only
chain_digest_next = SHA256(DOMAIN || chain_digest_prev || receipt_id)  # Actual chain
```

This matches the Coh Module Interface Contract's intent.

---

## Immediate Actions Required

---

## Executive Summary

The specification layer is mathematically sound, but the implementation has critical bugs that break consensus. The docs/spec are ahead of code by ~1 integration pass. This plan fixes the issues in priority order.

---

## Phase 1: Protocol Architecture (MUST DO FIRST)

### 1.1 Define Hashing Primitives Module

Create canonical primitives in [`src/cnsc_haai/consensus/hash_primitives.py`](src/cnsc_haai/consensus/hash_primitives.py):

```python
# Domain constants
DOMAIN_RECEIPT_ID = b"COH_RECEIPT_ID_V1\n"
DOMAIN_CHAIN = b"COH_CHAIN_DIGEST_V1\n"
DOMAIN_MERKLE_LEAF = bytes([0x00])
DOMAIN_MERKLE_INTERNAL = bytes([0x01])

def receipt_id(receipt_core: dict) -> bytes32:
    """Content hash - stable ID for this receipt's content (no prev)."""
    core_bytes = jcs_canonical_bytes(receipt_core)
    return sha256(DOMAIN_RECEIPT_ID + core_bytes)

def chain_digest(prev_digest: bytes32, receipt_id: bytes32) -> bytes32:
    """Actual chain digest - depends on prior digest."""
    return sha256(DOMAIN_CHAIN + prev_digest + receipt_id)

def merkle_leaf_hash(leaf_bytes: bytes) -> bytes32:
    """Leaf hash with domain separation."""
    return sha256(DOMAIN_MERKLE_LEAF + leaf_bytes)

def merkle_internal_hash(left: bytes32, right: bytes32) -> bytes32:
    """Internal node hash with domain separation."""
    return sha256(DOMAIN_MERKLE_INTERNAL + left + right)
```

### 1.2 Update chain_hash_universal.md Spec

Rewrite the spec to match Option A:
- `receipt_id` = content hash (no prev)
- `chain_digest` = actual chain with prev

---

## Phase 2: Implementation Fixes (After Architecture)

### Issue #1: Chain Hash Doesn't Link (CRITICAL - Consensus Breaker)

**File:** [`src/cnsc_haai/consensus/chain.py`](src/cnsc_haai/consensus/chain.py:21)

**Current Behavior:**
- Function accepts `prev_chain_hash` but doesn't use it
- This is now understood as implementing `receipt_id` semantics (content hash)

**Protocol Decision Applied:** We need BOTH:
- Keep `receipt_id` computation (current behavior for content hash)
- Add new `chain_digest` that includes prev

**Fix Required:**
```python
def receipt_id_v1(receipt_core: dict) -> bytes:
    """Content hash - stable ID (no prev)."""
    serialized = jcs_canonical_bytes(receipt_core)
    return sha256(DOMAIN_RECEIPT_ID + serialized)

def chain_digest_v1(prev_chain_digest: bytes, receipt_id: bytes) -> bytes:
    """Actual chain digest - depends on prior digest."""
    if len(prev_chain_digest) != 32:
        raise ValueError(...)
    return sha256(DOMAIN_CHAIN + prev_chain_digest + receipt_id)
```

---

## Phase 3: Refactoring (After Primitives Defined)

### Issue #2: Merkle Prefix + Proof Format Mismatch (CRITICAL - Consensus Breaker)

**Files:** 
- [`src/cnsc_haai/consensus/merkle.py`](src/cnsc_haai/consensus/merkle.py:17)
- [`src/cnsc_haai/consensus/fraudproof.py`](src/cnsc_haai/consensus/fraudproof.py:37)

**Use primitives from Phase 1:**
- Import `DOMAIN_MERKLE_LEAF`, `DOMAIN_MERKLE_INTERNAL` 
- Use `merkle_leaf_hash()` and `merkle_internal_hash()` from hash_primitives

### Part 2a: Identical Prefix for Leaf and Internal

**Current:**
```python
LEAF_PREFIX = bytes([0x01])      # Line 17
INTERNAL_PREFIX = bytes([0x01])  # Line 18 - SAME!
```

**Fix:** Use standard domain separation (recommended):
```python
LEAF_PREFIX = bytes([0x00])  # Import from hash_primitives
INTERNAL_PREFIX = bytes([0x01])  # Import from hash_primitives
```

### Part 2b: Proof Direction Mismatch

**Merkle emits:** `"left"` / `"right"` (lines 168, 171, 174)  
**FraudProof expects:** `"L"` / `"R"` (line 37)

**Fix:** Standardize on `"L"/"R"` to match fraudproof.py

---

## Phase 4: Individual Fixes

### Issue #3: JCS Accepts Floats (Consensus - Numeric Domain Violation)

**File:** [`src/cnsc_haai/consensus/jcs.py`](src/cnsc_haai/consensus/jcs.py:40)

**Fix:** Hard-reject floats at encoder boundary:
```python
elif isinstance(value, int):
    return _encode_number(value)
elif isinstance(value, float):
    raise TypeError(f"Floats not allowed in consensus - use QFixed int")
```

---

### Issue #4: Slab Micro-Leaf Hashing + B_end Logic

**File:** [`src/cnsc_haai/consensus/slab.py`](src/cnsc_haai/consensus/slab.py:104)

**Use primitives from Phase 1:**
- Import `encode_micro_leaf()` from codec
- Import `merkle_leaf_hash()` from hash_primitives (not raw sha256)

**Fix B_end:**
```python
# B_end = final budget, not max
if micro_receipts:
    B_end_q = int(micro_receipts[-1].get("budget_after_q", 0))
```

---

### Issue #5: ContinuousTrajectory State Management Bug

**File:** [`src/cnsc_haai/consensus/continuous.py`](src/cnsc_haai/consensus/continuous.py:77)

**Fix:** Split state variables:
```python
self._x_state = initial_state      # Cognitive state dict
self._traj_state = TrajectoryState.IDLE  # Trajectory enum
```

---

### Issue #6: Budgets Import Error

**File:** [`src/npe/core/budgets.py`](src/npe/core/budgets.py)

**Fix:** Re-export Budgets for backwards compatibility:
```python
# At end of budgets.py:
from .types import Budgets
```

---

## Phase 5: Double-Hash Refactoring

### Issue #7: Eliminate Double-Hashing Inconsistencies

Refactor these files to use single hash from primitives:

| File | Current Pattern | Fix |
|------|-----------------|-----|
| slab.py:139 | `sha256_prefixed(sha256(...))` | Use `receipt_id()` |
| topology.py:272 | `sha256_prefixed(sha256(...))` | Use `receipt_id()` |
| finalize.py:219 | `sha256_prefixed(sha256(...))` | Use `receipt_id()` |
| fraudproof.py:238 | `sha256_prefixed(sha256(...))` | Use `receipt_id()` |
| retention.py:47-48 | Double-hash | Use single hash |

---

## Implementation Order (Revised)

| Phase | Priority | Issue | Files to Modify |
|-------|----------|-------|-----------------|
| 1 | 0 | Define hashing primitives | NEW FILE |
| 1 | 0 | Update chain_hash_universal.md | SPEC FILE |
| 2 | 1 | Chain hash (receipt_id + chain_digest) | chain.py |
| 3 | 2 | Merkle prefixes + proof format | merkle.py, fraudproof.py |
| 4 | 3 | JCS float rejection | jcs.py |
| 4 | 4 | Slab leaf hashing + B_end | slab.py |
| 4 | 5 | ContinuousTrajectory state | continuous.py |
| 4 | 6 | Budgets import | budgets.py |
| 5 | 7 | Double-hash cleanup | slab.py, topology.py, finalize.py, fraudproof.py, retention.py |

---

## Verification Plan

After all fixes, run:

```bash
# 1. Check imports work
python -c "from npe.core.budgets import Budgets; print('OK')"

# 2. Run compliance tests
pytest compliance_tests/ -v

# 3. Verify receipt_id vs chain_digest distinction works
# 4. Verify merkle proof format matches fraudproof
# 5. Verify no double-hash regression
```

---

## Related Specification Documents

- [`docs/h_kernel/chainats/20_co_hash_rule.md`](docs/ats/20_coh_kernel/chain_hash_rule.md) - Chain hash spec (DEPRECATED)
- [`docs/ats/20_coh_kernel/chain_hash_universal.md`](docs/ats/20_coh_kernel/chain_hash_universal.md) - NEW chain hash spec (ACTIVE)
- [`docs/ats/20_coh_kernel/coh.merkle.v1.md`](docs/ats/20_coh_kernel/coh.merkle.v1.md) - Merkle spec
- [`docs/ats/20_coh_kernel/deterministic_numeric_domain.md`](docs/ats/20_coh_kernel/deterministic_numeric_domain.md) - QFixed domain
- [`docs/ats/30_ats_runtime/slab_compression_rules.md`](docs/ats/30_ats_runtime/slab_compression_rules.md) - Slab spec

---

## ADDENDUM: Additional Issues Found During Deep Analysis

### Issue #7: Double-Hashing Inconsistencies (Consistency Issue)

Multiple files use inconsistent double-hashing patterns:

| File | Line | Current Code | Issue |
|------|------|--------------|-------|
| [`slab.py`](src/cnsc_haai/consensus/slab.py:139) | 139 | `sha256_prefixed(sha256(core_bytes))` | Double-hash |
| [`topology.py`](src/cnsc_haai/consensus/topology.py:272) | 272 | `sha256_prefixed(sha256(receipt_bytes))` | Double-hash |
| [`finalize.py`](src/cnsc_haai/consensus/finalize.py:219) | 219 | `sha256_prefixed(receipt_hash)` where `receipt_hash = sha256(...)` | Double-hash |
| [`fraudproof.py`](src/cnsc_haai/consensus/fraudproof.py:238) | 238 | `sha256_prefixed(sha256(proof_bytes))` | Double-hash |
| [`retention.py`](src/cnsc_haai/consensus/retention.py:47) | 47-48 | `sha256_prefixed(policy_hash)` where `policy_hash = sha256(...)` | Double-hash |

**Correct pattern should be:**
```python
# Single hash - hash once, prefix the result
id = sha256_prefixed(data_bytes)
```

**NOT:**
```python
# Double-hash - wrong!
id = sha256_prefixed(sha256(data_bytes))  # Hashes twice!
```

### Issue #8: Chain Hash Universal Spec Doesn't Include prev_hash (SPEC DESIGN BUG)

**Finding:** The ACTIVE spec in [`chain_hash_universal.md`](docs/ats/20_coh_kernel/chain_hash_universal.md:32) defines:
```
chain_hash(prev_chain_hash_raw32, receipt_core) -> bytes32:
    1. Serialize receipt_core using JCS
    2. Prepend domain separator
    3. Double-hash: SHA256(SHA256(domain || serialized))
    4. Return raw 32 bytes
```

This does NOT include `prev_chain_hash` in the computation - it's validated but never used.

**The DEPRECATED spec** (chain_hash_rule.md) correctly includes linkage:
```
chain_hash(k) = sha256(previous_receipt_id(k) || receipt_id(k))
```

**Analysis:**
- Current code matches the NEW (broken) spec
- For true consensus, you NEED actual chain linkage
- Either fix the spec to include prev_hash, or acknowledge this is a "deterministic receipt ID system" not a "chain"

### Issue #9: Slab ID Uses Double-Hash

In [`slab.py:139`](src/cnsc_haai/consensus/slab.py:139):
```python
slab_id = sha256_prefixed(sha256(core_bytes))  # Double-hash
```
Should be:
```python
slab_id = sha256_prefixed(core_bytes)  # Single hash
```

---

## Summary of All Issues

| # | Issue | Severity | Type | Files |
|---|-------|----------|------|-------|
| 1 | Chain hash doesn't link | CRITICAL | Implementation | chain.py |
| 2 | Merkle prefix mismatch | CRITICAL | Implementation | merkle.py, fraudproof.py |
| 3 | JCS accepts floats | HIGH | Implementation | jcs.py |
| 4 | Slab leaf hashing + B_end | CRITICAL | Implementation | slab.py |
| 5 | ContinuousTrajectory state bug | MEDIUM | Implementation | continuous.py |
| 6 | Budgets import error | LOW | Import | budgets.py + 6 files |
| 7 | Double-hashing inconsistencies | MEDIUM | Consistency | slab.py, topology.py, finalize.py, fraudproof.py, retention.py |
| 8 | Chain spec doesn't link | CRITICAL | SPEC DESIGN | chain_hash_universal.md |
| 9 | Slab ID double-hash | LOW | Implementation | slab.py |
