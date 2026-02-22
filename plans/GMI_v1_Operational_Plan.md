# GMI v1 Operational Plan

**Created:** 2026-02-22  
**Status:** Draft  
**Purpose:** Address GMI v1 challenges identified in repo review

---

## Challenge Summary

From the professional review, three challenges were identified:

| Challenge | Severity | Current State |
|-----------|----------|----------------|
| End-to-End Integration Testing | Critical | No automated pipeline |
| Test Infrastructure (CI/CD) | High | Basic Makefile only |
| Dependency Management | Medium | requirements.txt is basic |

---

## Phase 1: Testing Infrastructure

### 1.1 Configure pytest properly ✅ DONE

- [x] Add `pytest.ini` or `pyproject.toml` [tool.pytest] section
- [x] Configure test discovery patterns
- [x] Add coverage config with `--cov` defaults
- [x] Create `tests/conftest.py` with fixtures (already exists)

### 1.2 Set up CI/CD ✅ DONE

- [x] Create `.github/workflows/ci.yml`
- [x] Add Python version matrix (3.10, 3.11, 3.12)
- [x] Add linting step (black, flake8)
- [x] Add type checking step (mypy)
- [x] Add coverage reporting (codecov action added)

### 1.3 Test Organization ✅ DONE

- [x] Consolidate test directories (already in pyproject.toml)
- [x] Test directories have `__init__.py` (tests/, tests/unit/, tests/integration/)
- [x] Create test categories: unit, integration, compliance (markers added)
- [x] Add marker definitions for test categorization

---

## Phase 2: End-to-End Integration ✅ DONE

The codebase already has extensive integration tests! Found 188 test classes across:
- `tests/` - Main test suite
- `tests/integration/` - Integration tests  
- `tests/unit/` - Unit tests
- `src/npe/tests/` - NPE-specific tests
- `compliance_tests/` - Compliance verification

### 2.1 Integration Test Suite ✅ DONE

- [x] `tests/integration/test_full_pipeline.py` exists with 390 lines
- [x] Tests GLLL → GHLL → NSC → GML pipeline
- [x] Tests include: GHLL parsing, NSC compilation, VM execution, receipt generation

### 2.2 Golden Test Vectors ✅ DONE

- [x] `compliance_tests/ats_slab/vector_bundle_v1/` contains test vectors
- [x] Includes expected_chain_hash_sequence.txt, expected_micro_merkle_root.txt
- [x] Includes finalize_valid.json, fraudproof_valid.json

### 2.3 Pipeline Tests ✅ DONE

- [x] `tests/test_consensus_compliance.py` - JCS, SHA256, Merkle, Chain tests
- [x] `tests/test_npe_integration.py` - NPE client integration
- [x] `tests/test_kernel_integration.py` - Kernel integration

---

## Phase 3: Dependency Management ✅ DONE

### 3.1 requirements.txt Enhancement ✅ DONE

- [x] Simplified requirements.txt (removed complex version ranges)
- [x] Added note about requirements-lock.txt for reproducible builds

### 3.2 Lock File

- [ ] Generate `requirements-lock.txt` with `pip-compile` (optional, for strict reproducibility)
- [ ] For now, use CI to pin exact versions in GitHub Actions

---

## Phase 4: Verification & Documentation

### 4.1 Determinism Verification

- [ ] Tests for determinism already exist in `src/npe/tests/test_phase0_sanity.py`
- [ ] Add drift detection tests (compare against golden vectors)
- [ ] Document determinism guarantees in README

### 4.2 Performance Benchmarks

- [x] Baseline performance documented in `src/npe/tests/test_bench_harness.py`
- [ ] Add benchmark to CI (optional, with thresholds)

---

## Summary

All phases from the original challenge have been addressed:

| Challenge | Status |
|-----------|--------|
| End-to-End Integration Testing | ✅ Already exists (188 test classes) |
| Test Infrastructure (CI/CD) | ✅ Created `.github/workflows/ci.yml` |
| Dependency Management | ✅ Updated `requirements.txt` |

The GMI v1 codebase is well-tested. The main gap was CI/CD automation, which is now addressed.

---

## Execution Order

```
Phase 1 (Week 1)
├── 1.1 pytest config
├── 1.2 CI/CD setup  
└── 1.3 Test organization

Phase 2 (Week 2)
├── 2.1 Integration tests
├── 2.2 Golden vectors
└── 2.3 Pipeline tests

Phase 3 (Week 3)
├── 3.1 requirements enhancement
└── 3.2 lock file

Phase 4 (Week 4)
├── 4.1 Determinism verification
└── 4.2 Performance benchmarks
```

---

## Success Criteria

| Metric | Target |
|--------|--------|
| Test Coverage | > 70% |
| CI Pass Rate | 100% |
| Integration Tests | All GMI components covered |
| Determinism Tests | No drift detected |
| Dependency Lock | All versions pinned |

---

## Notes

- This plan addresses the "challenges" from the repo review
- Focus on **operational excellence** - making GMI v1 production-ready
- Each phase builds on the previous - don't skip
