# Hashing Primitives Refactor Plan

**Create single source of truth for all consensus-critical hashing**

## Executive Summary

The codebase currently has **51 direct uses** of `hashlib.sha256(...)` scattered across multiple modules. This creates:
- Inconsistent domain separation
- Double-hashing bugs
- Unenforcible numeric domain (floats) 

**Goal**: Create one canonical primitives module and migrate all consensus-critical code to use it.

---

## Current State Analysis

### Existing: `src/cnsc_haai/consensus/hash_primitives.py`

Already implements:
- ✅ Domain separators (DOMAIN_RECEIPT_ID, DOMAIN_CHAIN, DOMAIN_MERKLE_LEAF, DOMAIN_MERKLE_INTERNAL)
- ✅ `sha256()` / `sha256_hex()` / `sha256_prefixed()`
- ✅ `receipt_id()` - content hash (no prev)
- ✅ `chain_digest()` - actual chain (with prev)
- ✅ `decode_sha256_prefixed()`
- ✅ Merkle hashes

### Missing from primitives.py

| Function | Status |
|----------|--------|
| `jcs_bytes(obj)` | ❌ (imports from jcs.py) |
| `receipt_core(receipt)` | ❌ (needs to be added) |
| `merkle_leaf_hash(leaf_bytes)` | ✅ Exists |
| `merkle_node_hash(left, right)` | ✅ Exists |

### Direct hashlib.sha256 Uses by Module

**CRITICAL (consensus - must migrate):**
| Module | Count | Purpose |
|--------|-------|---------|
| `src/cnsc_haai/consensus/hash.py` | 2 | Duplicate implementation |
| `src/cnsc_haai/consensus/compat.py` | 3 | Legacy compatibility |
| `src/cnsc_haai/consensus/slab.py` | ? | Slab construction |
| `src/cnsc_haai/consensus/topology.py` | ? | Topology hashing |
| `src/cnsc_haai/consensus/finalize.py` | ? | Finalization |
| `src/cnsc_haai/consensus/fraudproof.py` | ? | Fraud proofs |
| `src/cnsc_haai/consensus/retention.py` | ? | Retention policies |

**NON-CRITICAL (not consensus, can keep custom):**
- `src/cnhaai/core/receipts.py` - Application layer
- `src/npe/...` - NPE layer
- `src/cnsc/haai/...` - Legacy modules

---

## Implementation Plan

### Phase 1: Extend Primitives Module

**File**: `src/cnsc_haai/consensus/hash_primitives.py`

Add these functions:

```python
def jcs_bytes(obj: Any) -> bytes:
    """
    Compute JCS canonical bytes for any JSON-serializable object.
    STRICT: Rejects floats (QFixed only).
    """
    from .jcs import jcs_canonical_bytes
    return jcs_canonical_bytes(obj)

def receipt_core(receipt: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract receipt core - strip derived fields.
    Keeps: content, metadata
    Removes: receipt_id, chain_digest, signatures
    """
    # Implementation needed

def receipt_core_bytes(receipt: Dict[str, Any]) -> bytes:
    """
    Get canonical bytes for receipt core.
    """
    return jcs_bytes(receipt_core(receipt))
```

### Phase 2: Consolidate Duplicate hash.py

The `hash.py` module duplicates `hash_primitives.py`. Options:

1. **Deprecate hash.py** - redirect to hash_primitives
2. **Merge** - move remaining unique functions to hash_primitives

**Recommended**: Option 1 - Deprecate and redirect.

```python
# hash.py - DEPRECATED
import warnings
def sha256(data):
    warnings.warn("Use hash_primitives.sha256() instead", DeprecationWarning)
    from .hash_primitives import sha256
    return sha256(data)
```

### Phase 3: Migrate Consensus Modules

Migrate in this order (dependencies first):

1. **chain.py** - Already mostly uses hash_primitives ✅
2. **merkle.py** - Already mostly uses hash_primitives ✅
3. **jcs.py** - Ensure strict float rejection
4. **slab.py** - Fix B_end semantic + slab_id
5. **topology.py** - Migrate to primitives
6. **finalize.py** - Migrate to primitives
7. **fraudproof.py** - Fix proof direction encoding
8. **retention.py** - Migrate to primitives

### Phase 4: Fix Specific Bugs

#### Bug #1: Slab B_end
```python
# WRONG
B_end = max(budgets)

# RIGHT  
B_end = final_budget  # Last budget value
```

#### Bug #2: Fraud Proof Direction
```python
# WRONG
direction = "left"  # or "right"

# RIGHT
direction = "L"  # or "R"  (canonical)
```

#### Bug #3: Double Hashing
```python
# WRONG
slab_id = sha256(sha256(leaf_bytes))

# RIGHT
slab_id = receipt_id(slab_receipt_core)  # Single hash
```

### Phase 5: CI Gates

Add `tests/test_hash_hygiene.py`:

```python
def test_no_direct_hashlib_usage():
    """Fail build if hashlib.sha256 used outside primitives."""
    # Grep for 'hashlib.sha256' in src/cnsc_haai/consensus/
    # Should only appear in hash_primitives.py
    
def test_no_floats_in_consensus():
    """Fail if JCS accepts floats."""
    with pytest.raises(TypeError):
        jcs_bytes({"value": 1.5})

def test_receipt_id_determinism():
    """Golden vector test."""
    # Known test vectors
    
def test_chain_digest_linkage():
    """Verify prev dependency works."""
    # Test chain broken if prev changes
```

---

## Migration Checklist

| Task | Status |
|------|--------|
| Extend hash_primitives.py with jcs_bytes, receipt_core | [ ] |
| Add deprecation warnings to hash.py | [ ] |
| Migrate slab.py to primitives | [ ] |
| Migrate topology.py to primitives | [ ] |
| Migrate finalize.py to primitives | [ ] |
| Migrate fraudproof.py to primitives | [ ] |
| Migrate retention.py to primitives | [ ] |
| Fix B_end semantic | [ ] |
| Fix proof direction encoding | [ ] |
| Add CI hygiene tests | [ ] |
| Run full test suite | [ ] |

---

## Acceptance Criteria

1. **Single Source**: `hashlib.sha256` appears ONLY in `hash_primitives.py` (consensus)
2. **No Double-Hash**: No module computes `sha256(sha256(...))` 
3. **Float Rejection**: JCS hard-rejects floats in consensus paths
4. **Deterministic**: Golden vectors pass for receipt_id, chain_digest, merkle_root
5. **Proof Direction**: All fraud proofs use canonical "L"/"R"
6. **B_end Correct**: Slab summary.B_end = final budget, not max

---

## Files to Modify

```
src/cnsc_haai/consensus/hash_primitives.py  # Extend
src/cnsc_haai/consensus/hash.py              # Deprecate
src/cnsc_haai/consensus/slab.py             # Migrate + fix B_end
src/cnsc_haai/consensus/topology.py          # Migrate
src/cnsc_haai/consensus/finalize.py          # Migrate
src/cnsc_haai/consensus/fraudproof.py        # Migrate + fix direction
src/cnsc_haai/consensus/retention.py         # Migrate
tests/test_hash_hygiene.py                   # NEW - CI gate
```

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Breaking existing tests | Run full suite after each migration |
| Circular imports | Use lazy imports in hash_primitives |
| Performance regression | Benchmark before/after |
| Backward compatibility | Keep hash.py as redirect with warnings |
