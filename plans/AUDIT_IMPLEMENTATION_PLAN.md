# Comprehensive Audit Implementation Plan

**Based on:** Codebase Audit Analysis  
**Status:** Planning  
**Priority:** P0 (Critical) → P1 (High) → P2 (Hardening)

---

## Executive Summary

This plan addresses the critical issues identified in the codebase audit. The audit revealed:

1. **Determinism violations** in compliance tests (timestamps, floats in SOC)
2. **Namespace fragmentation** across three parallel implementations
3. **Weak test coverage** that doesn't verify contract guarantees
4. **Build hygiene issues** (pycache artifacts)
5. **Framework inconsistency** (mixed pytest/unittest)

The plan is organized into three priority tiers following the audit's recommendations.

---

## Current State Analysis

### Namespace Structure (Verified)
```
src/
├── cnhaai/           # Legacy namespace (phase/gates/abstraction)
├── cnsc/haai/       # Primary active namespace (ATS, GHLL, GMLL, NSC, TGS)
├── cnsc_haai/       # Consensus namespace (chain, merkle, slab)
├── npe/              # NPE proposal engine
└── soc/             # SOC spine simulation
```

### Critical Issues Found

| Issue | Location | Impact |
|-------|----------|--------|
| `datetime.utcnow()` in receipts | `compliance_tests/gml/test_receipt_chain_hash.py:32` | Nondeterministic chain hashes |
| Float accumulation in norm bounds | `src/soc/norm_bounds.py:43-50` | Violates Q18 fixed-point contract |
| `compute_eta` uses float math | `src/soc/norm_bounds.py:204-218` | Non-reproducible verifier output |
| Mixed unittest/pytest | `tests/`, `compliance_tests/` | Inconsistent fixtures |

---

## P0: Must Fix Soon

### P0-1: Remove __pycache__ / .pyc Artifacts

**Issue:** The repo contains compiled artifacts that will pollute diffs/releases.

**Current State:** `.gitignore` correctly excludes these, but the extracted zip contains them.

**Action:**
1. Remove all `__pycache__` directories recursively
2. Remove all `.pyc` files
3. Verify `.gitignore` is comprehensive
4. Document clean extraction procedure

**Files Affected:**
- `src/**/__pycache__/`
- `tests/**/__pycache__/`
- `compliance_tests/**/__pycache__/`

**Verification:** Run `find . -type d -name __pycache__` should return empty.

---

### P0-2: Freeze Time in Compliance Tests

**Issue:** [`test_receipt_chain_hash.py:32`](compliance_tests/gml/test_receipt_chain_hash.py:32) uses `datetime.utcnow()` inside receipts, causing nondeterministic chain hashes.

**Current Code:**
```python
provenance = ReceiptProvenance(
    source="test",
    timestamp=datetime.utcnow()  # NONDETERMINISTIC
)
```

**Required Fix Options:**

**Option A (Preferred):** Exclude timestamp from canonical hash preimage
- Modify receipt canonicalization to skip/zero timestamp field
- Hash computed on deterministic fields only

**Option B:** Inject frozen timestamp in tests
- Add optional `timestamp` parameter to test helper
- Use fixed epoch timestamp for all test receipts

**Implementation Steps:**
1. Identify all receipt creation points in compliance tests
2. Add timestamp parameter with default `None` → use fixed value
3. Update canonical serialization to handle timestamp field
4. Add deterministic hash verification test

**Files to Modify:**
- `compliance_tests/gml/test_receipt_chain_hash.py`
- `src/cnsc/haai/gml/receipts.py` (Receipt, ReceiptProvenance classes)

---

### P0-3: Remove Floats from SOC Verifier-Critical Computations

**Issue:** [`src/soc/norm_bounds.py`](src/soc/norm_bounds.py) claims Q18 fixed-point but uses float accumulation, violating deterministic verification contract.

**KEY FINDING:** A proper Q18 library already exists at [`src/npe/core/qfixed18.py`](src/npe/core/qfixed18.py) with:
- `q18_mul()`, `q18_div()` - deterministic multiplication/division
- `q18_add()`, `q18_sub()` - with overflow checking  
- Proper rounding modes (UP/DOWN)
- Q18_SCALE = 2^18 = 262144

**The SOC code MUST use this existing library instead of floats.**

**Current Problematic Code:**

```python
# Lines 43-50: Float accumulation (WRONG)
max_row_sum = 0.0
for row in A:
    row_sum = sum(abs(val) for val in row)  # Float intermediate
    if row_sum > max_row_sum:
        max_row_sum = row_sum
return int(max_row_sum * Q18)  # Late conversion to int

# Lines 204-218: Float in compute_eta (WRONG)
def compute_eta(mu: float, c: float, B: int) -> int:
    denominator = 1.0 + mu * c * float(B)  # Float arithmetic
    eta_float = 1.0 / denominator
    return int(eta_float * Q18)
```

**Required Fix:** Rewrite using existing Q18 library:

```python
from npe.core.qfixed18 import q18_mul, q18_div, q18_add, Q18_SCALE

def mat_inf_norm_q18(A: List[List[int]]) -> int:
    """Pure Q18 integer norm - use existing Q18 library."""
    max_row_sum = 0
    for row in A:
        row_sum = sum(abs(val) for val in row)
        if row_sum > max_row_sum:
            max_row_sum = row_sum
    return max_row_sum * Q18_SCALE  # Direct Q18 scaling

def compute_eta_q18(mu_q18: int, c_q18: int, B: int) -> int:
    """Pure Q18: eta = 1 / (1 + mu * c * B)"""
    # Use q18_mul for deterministic computation
    mu_c = q18_mul(mu_q18, c_q18)  # mu * c in Q18
    mu_c_B = q18_mul(mu_c, B)       # mu * c * B in Q18
    denominator = q18_add(Q18_SCALE, mu_c_B)  # 1 + mu*c*B
    return q18_div(Q18_SCALE, denominator)     # 1 / denominator
```

**Breaking Change Note:** Function signatures change from `float` to `int` for Q18 values.

**Files to Modify:**
- `src/soc/norm_bounds.py` - replace float math with Q18 library calls

**Verification:**
- All functions use `npe.core.qfixed18` functions
- No `float()` conversions in verifier path
- Tests use integer matrices only

---

## P1: Next Priority

### P1-1: Unify Namespace Layout

**Issue:** Three parallel namespaces cause confusion and import drift:
- `src/cnhaai/` - legacy
- `src/cnsc/haai/` - primary active
- `src/cnsc_haai/` - consensus

**Recommended Action:** Adopt `cnsc.haai` as canonical, create thin compatibility shims for others.

**Migration Strategy:**

```
cnsc.haai (TARGET)
├── ats/          # From cnsc/haai/ats
├── ghll/         # From cnsc/haai/ghll
├── glll/         # From cnsc/haai/glll
├── gml/          # From cnsc/haai/gml
├── graphgml/     # From cnsc/haai/graphgml
├── nsc/          # From cnsc/haai/nsc
├── tgs/          # From cnsc/haai/tgs
├── cli/          # From cnsc/haai/cli

cnsc_haai (COMPATIBILITY)
├── consensus/   # Keep as-is
└── ats/          # Import from cnsc.haai.ats

cnhaai (DEPRECATED)
└── compatibility shim → import cnsc.haai
```

**Implementation:**
1. Keep `cnsc/haai/` as the canonical location (already primary)
2. Add `__init__.py` re-exports in `cnsc_haai/` pointing to `cnsc.haai`
3. Add deprecation warnings in `cnhaai/`
4. Update all internal imports to use `cnsc.haai`

**Files to Modify:**
- `src/cnsc_haai/*/__init__.py` - add re-exports
- `src/cnhaai/*/__init__.py` - add deprecation warnings
- All import statements across codebase

---

### P1-2: Upgrade Shape Tests to Contract Tests

**Issue:** Tests like [`test_receipt_hash_property`](compliance_tests/gml/test_receipt_chain_hash.py:47) only check attribute existence, not contract guarantees.

**Current Weak Test:**
```python
def test_receipt_hash_property(self):
    receipt = self._create_receipt("receipt_001")
    # Only checks attribute exists, not hash integrity
    assert hasattr(receipt, 'chain_hash') or receipt.previous_receipt_hash is not None
```

**Required Contract Tests:**

1. **Hash Determinism Test**
   ```python
   def test_receipt_chain_hash_deterministic(self):
       """Same receipt must produce identical hash across runs."""
       receipt = create_receipt(fixed_timestamp())
       
       hash1 = compute_hash(receipt)
       hash2 = compute_hash(receipt)
       assert hash1 == hash2  # Byte-identical
   ```

2. **Chain Integrity Test**
   ```python
   def test_receipt_chain_integrity(self):
       """Chain hash must include previous hash."""
       receipt1 = create_receipt("r1", previous=None)
       receipt2 = create_receipt("r2", previous=receipt1.chain_hash)
       
       assert receipt2.previous_receipt_hash == receipt1.chain_hash
       assert verify_chain([receipt1, receipt2])  # Full chain validation
   ```

3. **Canonical Serialization Test**
   ```python
   def test_canonical_serialization_stability(self):
       """Two independent serializations must produce identical bytes."""
       receipt = create_receipt(fixed_timestamp())
       
       bytes1 = canonical_serialize(receipt)
       bytes2 = canonical_serialize(receipt)
       
       assert bytes1 == bytes2  # Byte-identical
       assert hashlib.sha256(bytes1).hexdigest() == EXPECTED_HASH
   ```

**Files to Create/Modify:**
- `compliance_tests/gml/test_receipt_chain_hash.py` - add contract tests
- Add new test files as needed

---

### P1-3: Standardize Testing Framework

**Issue:** Mixed pytest and unittest produce inconsistent fixtures and reporting.

**Decision:** Adopt pytest as primary framework.

**Migration Steps:**
1. Convert all `unittest.TestCase` classes to pytest classes
2. Remove `unittest` imports where not needed
3. Standardize fixtures using `@pytest.fixture`
4. Add `conftest.py` for shared fixtures
5. Use pytest markers for test categorization

**Example Conversion:**
```python
# Before (unittest)
class TestReceipt(unittest.TestCase):
    def test_creation(self):
        receipt = create_receipt()
        self.assertEqual(receipt.id, "test")

# After (pytest)
class TestReceipt:
    def test_creation(self):
        receipt = create_receipt()
        assert receipt.id == "test"
```

**Files to Modify:**
- `compliance_tests/*/test_*.py` - convert to pytest
- `tests/` - convert to pytest

---

## P2: Hardening

### P2-1: Add Adversarial Mutation Tests

**Issue:** Architecture is adversary-aware but tests don't verify resilience.

**Required Tests:**

1. **Tamper Detection**
   ```python
   def test_receipt_tamper_detected(self):
       """Modifying any field must invalidate chain."""
       receipt = create_receipt()
       original_hash = receipt.chain_hash
       
       # Tamper with field
       receipt.content.output_hash = "tampered"
       
       assert verify_chain([receipt]) == False
   ```

2. **Reorder Resistance**
   ```python
   def test_chain_reorder_detected(self):
       """Reordering receipts must break chain."""
       chain = create_chain(length=5)
       
       # Reorder
       shuffled = chain[::-1]
       
       assert verify_chain(shuffled) == False
   ```

3. **Budget Smuggling Prevention**
   ```python
   def test_budget_smuggling_blocked(self):
       """Attempting to exceed budget must fail verification."""
       action = create_action(budget_exceeds_limit=True)
       
       result = verify_action(action)
       assert result.valid == False
       assert "budget_exceeded" in result.reason
   ```

**Files to Create:**
- `compliance_tests/adversarial/test_tamper_detection.py`
- `compliance_tests/adversarial/test_reorder_resistance.py`
- `compliance_tests/adversarial/test_budget_smuggling.py`

---

### P2-2: Add CI Gate for Determinism Failures

**Issue:** No automated enforcement of determinism requirements.

**Implementation:**

1. Create determinism test marker
   ```python
   # conftest.py
   def pytest_configure(config):
       config.addinivalue_line("markers", "determinism: determinism requirement")
   ```

2. Mark determinism tests
   ```python
   @pytest.mark.determinism
   def test_receipt_hash_deterministic():
       ...
   ```

3. Add CI configuration
   ```yaml
   # .github/workflows/test.yml
   - name: Run Determinism Tests
     run: pytest -m determinism -v
   
   - name: Fail on Determinism Violations
     run: |
       pytest -m determinism --tb=short || exit 1
   ```

**Files to Create/Modify:**
- `compliance_tests/conftest.py` - add markers
- `.github/workflows/test.yml` - add determinism gate

---

### P2-3: Add Two-Run Reproducibility Tests

**Issue:** No standard test for cross-run reproducibility.

**Implementation:**
```python
@pytest.mark.determinism
def test_pipeline_reproducibility():
    """Full pipeline must produce identical results on two runs."""
    # Run 1
    result1 = run_pipeline(input_data)
    
    # Run 2 (fresh instance)
    result2 = run_pipeline(input_data)
    
    # Compare
    assert result1.canonical_bytes == result2.canonical_bytes
    assert result1.receipt_chain_hash == result2.receipt_chain_hash
    assert result1.final_state_hash == result2.final_state_hash
```

**Files to Create:**
- `compliance_tests/determinism/test_pipeline_reproducibility.py`

---

## Implementation Order

```
P0 (Immediate)
├── P0-1: Clean pycache artifacts
├── P0-2: Fix timestamp nondeterminism  
└── P0-3: Remove floats from SOC

P1 (After P0)
├── P1-1: Unify namespace layout
├── P1-2: Upgrade to contract tests
└── P1-3: Standardize pytest

P2 (After P1)
├── P2-1: Adversarial mutation tests
├── P2-2: CI determinism gate
└── P2-3: Two-run reproducibility
```

---

## Hardened Requirements (Post-Review)

### P0-2: Timestamp - STRONGER REQUIREMENT

**Original:** Option A (exclude from preimage) or Option B (freeze in tests)

**Hardened Position:** Timestamp MUST NEVER be part of canonical serialization or hash preimage.

> Timestamp is provenance metadata ONLY. It must be excluded from deterministic hash computation entirely.

**Updated Implementation:**
1. Modify receipt canonicalization to explicitly exclude timestamp field
2. Timestamp stored separately as metadata, never influencing chain hash
3. Tests verify timestamp is NOT in serialized preimage

### P0-3: SOC Float - REQUIRES SPEC DOCUMENT

**Original:** Implement pure Q18 integer arithmetic

**Hardened Requirement:** Must include formal Numeric Domain Contract

**New Deliverable:** Create `docs/cnsc/deterministic_numeric_domain.md` specifying:
- All verifier-critical paths MUST use Q18 integers
- Floats allowed ONLY in dev/simulation paths
- Rounding mode: truncation toward zero (explicit)
- Overflow policy: raise OverflowError on bounds violation
- Maximum bounds: mu, c, B must fit in 64-bit Q54 intermediate
- Scaling derivation: explicit math in comments

**Overflow Guard:**
```python
def _mul_q18_safe(a: int, b: int) -> int:
    """Multiply two Q18 values with overflow checking."""
    MAX_Q18 = (1 << 63) - 1
    result = a * b
    if result > MAX_Q18 or result < -MAX_Q18:
        raise OverflowError(f"Q18 multiplication overflow: {a} * {b}")
    return result
```

### P0-1: Add CI Hygiene Gate

**Addition:** Add CI step that fails if `__pycache__` exists

```yaml
# .github/workflows/ hygiene check
- name: Check for pycache artifacts
  run: |
    if find . -type d -name __pycache__ | grep -q .; then
      echo "ERROR: __pycache__ directories found"
      find . -type d -name __pycache__
      exit 1
    fi
```

---

## Risk Assessment

| Item | Risk Level | Mitigation |
|------|------------|------------|
| P0-1: pycache cleanup | Low | Reversible, plus CI enforcement |
| P0-2: Timestamp fix | Medium | Exclude from hash preimage entirely |
| P0-3: SOC float removal | High | Breaking API + requires spec document |
| P1-1: Namespace unification | High | Gradual migration with re-exports |
| P1-2: Contract tests | Medium | Requires understanding current behavior |
| P1-3: Framework migration | Medium | Large-scale test refactoring |

---

## Dependencies

- P0-2 depends on: Understanding receipt canonicalization
- P0-3 depends on: Creating Numeric Domain Contract spec
- P1-1 depends on: P0 completion (clearer picture of what to unify)
- P1-2 depends on: P0-2 (deterministic timestamps)
- P2-1 depends on: P1-2 (contract tests exist)
- P2-2 depends on: P1-2 (determinism tests exist)
- P2-3 depends on: P0-2, P0-3 (determinism guarantees)

---

## Success Criteria

- [ ] No `__pycache__` or `.pyc` in clean checkout
- [ ] All compliance tests produce identical results across runs
- [ ] SOC norm functions accept only Q18 integers
- [ ] Single canonical namespace (`cnsc.haai`)
- [ ] All tests use pytest
- [ ] Contract tests verify hash equality, chain integrity
- [ ] Adversarial tests pass (tamper/reorder/smuggle detected)
- [ ] CI fails on determinism violations
- [ ] Two-run reproducibility verified for full pipeline
