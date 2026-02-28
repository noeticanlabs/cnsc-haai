# GMI v1.6 Runtime Integration Plan

**Created:** 2026-02-28  
**Status:** Draft  
**Purpose:** Wire NPE → TGS → Consensus into a complete metabolic AI loop

---

## Problem Statement

GMI v1.5 implements a deterministic **governed metabolic substrate kernel** but lacks the full **metabolic AI loop** that connects:

1. **Predictor/Proposer** (NPE - generates candidate actions)
2. **Gate/Governance** (TGS - evaluates and filters proposals)
3. **Commit/Ledger** (Consensus - deterministic state updates with receipts)

Without this integration, "GMI" is only a kernel, not an AI system.

---

## Phase 1: Receipted ProposalSet

### 1.1 Extend Receipt Schema

Add proposal tracking to the receipt bundle:

| Field | Type | Description |
|-------|------|-------------|
| `proposalset_root` | bytes | Merkle root of proposal pool |
| `proposalset_slab_id` | str | Slab ID for proposal retrieval |
| `selected_proposal_id` | str | Index/ID of chosen proposal |
| `proposal_membership_proof` | bytes | Merkle proof of selection |

**Files:**
- `schemas/gmi/receipt.schema.json` - Add new fields
- `src/cnsc_haai/gmi/types.py` - Add ProposalSetReceipt type

### 1.2 Use Existing Merkle Module

**REUSE:** `src/cnsc_haai/consensus/merkle.py` - Already has deterministic Merkle

Existing API to leverage:
```python
class MerkleTree:
    def __init__(self, leaves: List[bytes])
    def root(self) -> bytes
    def get_proof(self, index: int) -> List[bytes]
    
def verify_inclusion_proof(leaf_bytes, proof, root) -> bool
```

---

## Phase 2: GMI Runtime Engine

### 2.1 Runtime Entry Point

Create `src/cnsc_haai/gmi/runtime.py` with the main tick function:

```python
def gmi_tick(
    state: GMIState,
    observation: bytes,
    policy: GatePolicy,
    ctx: dict,
    chain_prev: bytes,
) -> Tuple[GMIState, GMIRuntimeReceipt]:
    """
    Single tick of the GMI metabolic AI loop.
    
    1. NPE.predict() → generate candidate proposals
    2. TGS.gate() → evaluate against policy/gates
    3. Execute → apply selected proposal
    4. Consensus.commit() → deterministic state update + receipt
    
    Uses existing modules:
    - cnsc_haai.consensus.chain for chain hashing
    - cnsc_haai.consensus.merkle for proposal Merkle
    - cnsc.haai.nsc.gates for gate evaluation
    """
```

### 2.2 Receipt Types

**Files:**
- `src/cnsc_haai/gmi/runtime.py` - Main runtime
- `src/cnsc_haai/gmi/types.py` - Add GMIRuntimeReceipt

**GMIRuntimeReceipt fields:**
- `step_receipt` - Core GMI step receipt
- `proposal_set_root` - Merkle root of proposals
- `gate_decisions` - Per-gate results
- `execution_cost` - Work units spent
- `witness_data` - Evidence used

### 2.3 Integration with Existing Modules

Wire to existing CNSC-HAAI components (REUSE, don't rewrite):

| Component | Module | Integration Point |
|-----------|--------|------------------|
| NPE | `cnsc.haai.nsc.proposer_client` | `ProposerClient.predict()` |
| Gates | `cnsc.haai.nsc.gates` | `GateManager.evaluate_all()` |
| Chain | `cnsc_haai.consensus.chain` | `chain_hash_sequence()` |
| Merkle | `cnsc_haai.consensus.merkle` | `MerkleTree` |

---

## Phase 3: Metabolic Budget System

### 3.1 Work-Unit Budget Tracking

Replace constant budget spend with measurable work:

**Files:**
- `src/cnsc_haai/gmi/budget.py` - Metabolic budget tracker

**Budget Components:**
```python
@dataclass(frozen=True)
class WorkUnits:
    proposal_generation_cost: int  # NPE compute
    witness_acquisition_cost: int  # Evidence gathering
    gate_evaluation_cost: int      # Policy checks
    execution_cost: int            # State update
    memory_write_cost: int         # Receipt storage
    repair_cost: int              # Corrections applied
```

### 3.2 Budget Enforcement

- Total cost = sum of work units
- Budget decreases by total cost per tick
- Gates can reject based on insufficient budget

---

## Phase 4: Compliance Tests

### 4.1 Runtime Tests

Create `compliance_tests/gmi/test_runtime_*.py`:

| Test File | Coverage |
|-----------|----------|
| `test_runtime_integration.py` | Full NPE→TGS→consensus loop |
| `test_proposal_receipts.py` | Merkle proof generation/verification |
| `test_metabolic_budget.py` | Work-unit budget enforcement |
| `test_gate_decisions.py` | Gate evaluation reproducibility |

### 4.2 Golden Vectors

Add runtime test vectors:
- `compliance_tests/gmi/vectors/runtime_case01.json` - Full loop with proposals
- `compliance_tests/gmi/vectors/runtime_case02.json` - Gate rejection scenario

---

## Phase 5: Documentation

### 5.1 Update GMI Spec

**Files:**
- `docs/gmi/03_predictor_layer.md` - Clarify nondeterminism rule
- `docs/gmi/08_receipt_bundle.md` - Add proposal receipt fields

### 5.2 Runtime API Docs

**Files:**
- `docs/gmi/19_runtime_api.md` - Complete runtime documentation

---

## Execution Order

```
Phase 1 (Week 1)
├── 1.1 Extend receipt schema
└── 1.2 Merkle integration

Phase 2 (Week 2)
├── 2.1 Runtime entry point
├── 2.2 Receipt types
└── 2.3 Integration wiring

Phase 3 (Week 3)
├── 3.1 Work-unit tracking
└── 3.2 Budget enforcement

Phase 4 (Week 4)
├── 4.1 Runtime tests
└── 4.2 Golden vectors

Phase 5 (Week 5)
├── 5.1 Spec updates
└── 5.2 API docs
```

---

## Success Criteria

| Metric | Target |
|--------|--------|
| Runtime tests pass | 20+ new tests |
| Determinism | Full loop deterministic |
| Proposal receipts | Merkle root in every receipt |
| Budget enforcement | Work-unit tracking active |
| CI integration | `pytest compliance_tests/gmi -q` includes runtime |

---

## Existing Architecture (Verified)

### Current Integration Points

| Component | Module | Purpose |
|-----------|--------|---------|
| **Proposer** | `src/cnsc/haai/nsc/proposer_client.py` | NPE client for proposals |
| **Gates** | `src/cnsc/haai/nsc/gates.py` | Gate evaluation |
| **Rails** | `src/cnsc/haai/tgs/rails.py` | Constraint enforcement |
| **Consensus** | `src/cnsc_haai/consensus/finalize.py` | State finalization |
| **Chain** | `src/cnsc_haai/consensus/chain.py` | Chain hashing |
| **Merkle** | `src/cnsc_haai/consensus/merkle.py` | Merkle tree operations |
| **Slab** | `src/cnsc_haai/consensus/slab.py` | Receipt storage |

### Key Decision: Runtime Should Be Thin Wrapper

The runtime should NOT duplicate consensus logic. Instead, it should:
1. Use existing `consensus.chain` for chain hashing
2. Use existing `consensus.merkle` for proposal Merkle
3. Use existing `nsc/gates` for gate evaluation
4. Create GMI-specific types for the loop

---

## Key Design Decisions

### Decision 1: Predictor Nondeterminism

**Rule:** Predictor MAY be nondeterministic IF AND ONLY IF:
- ProposalSet is stored in retrievable slab
- Merkle root of ProposalSet is in receipt
- Membership proof verifies selected proposal

This maintains consensus while allowing exploration.

### Decision 2: Gate Determinism

Gates MUST be deterministic given:
- Same policy
- Same proposal set
- Same state

Gate evaluation is fully reproducible.

### Decision 3: Budget as Metabolic Currency

Budget is not just "time" - it tracks actual work:
- Proposal generation (compute-bound)
- Witness acquisition (I/O-bound)
- Gate evaluation (decision-bound)
- Execution (state-bound)

### Decision 4: Reuse Existing Consensus

The runtime should reuse existing modules:
- `cnsc_haai.consensus.chain` for chain hashing
- `cnsc_haai.consensus.merkle` for Merkle proofs
- `cnsc_haai.consensus.slab` for proposal storage
- `cnsc.haai.nsc.gates` for gate evaluation

---

## Files to Create/Modify

### New Files
- `src/cnsc_haai/gmi/runtime.py` - Main runtime engine (thin wrapper)
- `src/cnsc_haai/gmi/budget.py` - Metabolic budget tracking
- `compliance_tests/gmi/test_runtime_integration.py`
- `compliance_tests/gmi/test_proposal_receipts.py`
- `compliance_tests/gmi/test_metabolic_budget.py`
- `compliance_tests/gmi/vectors/runtime_case01.json`
- `compliance_tests/gmi/vectors/runtime_case02.json`
- `docs/gmi/19_runtime_api.md`

### Modified Files
- `src/cnsc_haai/gmi/types.py` - Add new receipt types
- `schemas/gmi/receipt.schema.json` - Add proposal fields
- `docs/gmi/03_predictor_layer.md` - Clarify nondeterminism rule
- `docs/gmi/08_receipt_bundle.md` - Document proposal receipts
- `.github/workflows/ci.yml` - Add runtime tests to CI

### Existing Files to Reference (DO NOT MODIFY)
- `src/cnsc_haai/consensus/chain.py` - Chain hashing
- `src/cnsc_haai/consensus/merkle.py` - Merkle operations
- `src/cnsc_haai/consensus/slab.py` - Receipt storage
- `src/cnsc/haai/nsc/gates.py` - Gate evaluation

---

## Notes

- This plan builds on GMI v1.5 kernel (already implemented)
- Focus on **integration** rather than new theory
- All runtime components must be deterministic for consensus
- Proposal nondeterminism is acceptable with proper receipting
