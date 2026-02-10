# TGS Build and Integration Plan

**Temporal Governance System Implementation**

---

## Executive Summary

This plan details the implementation of the Temporal Governance System (TGS) as the authoritative control layer for cognitive state transitions. TGS will integrate with existing components (NSC, GML, Coherence Framework) to enforce temporal governance, coherence rails, and deterministic receipt emission.

---

## Phase 1: Foundation Layer

### 1.1 Create TGS Module Structure

**File:** `src/cnsc/haai/tgs/__init__.py`
**File:** `src/cnsc/haai/tgs/clock.py`
**File:** `src/cnsc/haai/tgs/governor.py`
**File:** `src/cnsc/haai/tgs/snapshot.py`
**File:** `src/cnsc/haai/tgs/receipt.py`
**File:** `src/cnsc/haai/tgs/exceptions.py`

**Dependencies:**
- `src/cnsc/haai/nsc/gates.py` (GateManager, GateResult)
- `src/cnsc/haai/gml/receipts.py` (Receipt system)
- `src/cnhaai/core/abstraction.py` (Cognitive state abstraction)

### 1.2 Clock Arbitration System

**File:** `src/cnsc/haai/tgs/clock.py`

```python
# Clock implementations required:
class ConsistencyClock:
    """Measures contradiction risk introduced by delta."""
    def compute_dt(proposal, state) -> float

class CommitmentClock:
    """Measures obligation load and intent instability."""
    def compute_dt(proposal, state) -> float

class CausalityClock:
    """Enforces temporal ordering and evidence availability."""
    def compute_dt(proposal, state) -> float

class ResourceClock:
    """Limits based on remaining budgets."""
    def compute_dt(proposal, state) -> float

class TaintClock:
    """Penalizes untrusted or weakly-provenanced input."""
    def compute_dt(proposal, state) -> float

class DriftClock:
    """Measures coherence drift from prior state."""
    def compute_dt(proposal, state) -> float

class ClockRegistry:
    """Manages all clock instances and dt arbitration."""
    def register_clock(clock: BaseClock) -> None
    def compute_dt(proposal, state) -> Tuple[float, ClockID]
```

---

## Phase 2: Core Governance Engine

### 2.1 Snapshot and Staging Protocol

**File:** `src/cnsc/haai/tgs/snapshot.py`

```python
class SnapshotManager:
    """Manages CNSC state snapshots for TGS operations."""
    def begin_attempt_snapshot() -> Snapshot:
        """Create immutable snapshot of current state."""
    def rollback(snapshot: Snapshot) -> None:
        """Restore bitwise-identical state."""
    def commit(snapshot: Snapshot, staged: StagedState) -> StateHash:
        """Persist staged changes and return new state hash."""

@dataclass
class StagedState:
    """Mutable staging area for proposal evaluation."""
    memory: Dict[str, Any]
    tags: Dict[str, Any]
    policies: Dict[str, Any]
    resources: Dict[str, Any]
    auxiliary: Dict[str, Any]
```

### 2.2 Temporal Governance Engine

**File:** `src/cnsc/haai/tgs/governor.py`

```python
class TemporalGovernanceEngine:
    """Core TGS engine for temporal governance."""
    def __init__(
        self,
        clock_registry: ClockRegistry,
        snapshot_manager: SnapshotManager,
        gate_manager: GateManager,
        receipt_emitter: ReceiptEmitter
    ):
        """Initialize TGS with required dependencies."""

    def process_proposal(
        self,
        proposal: Proposal,
        current_state_hash: StateHash,
        logical_time: int
    ) -> GovernanceResult:
        """
        Process proposal through TGS pipeline:
        1. Snapshot current state
        2. Stage proposal deltas
        3. Compute dt via clock arbitration
        4. Evaluate coherence rails
        5. Apply corrections if needed
        6. Commit or rollback
        7. Emit receipt
        """

    def _snapshot_state(self, state_hash: StateHash) -> Snapshot:
        """Create snapshot of current CNSC state."""

    def _stage_deltas(self, proposal: Proposal, snapshot: Snapshot) -> StagedState:
        """Apply proposal deltas to staged state."""

    def _arbitrate_dt(self, proposal: Proposal, staged: StagedState) -> DTResult:
        """Compute dt via clock arbitration."""

    def _evaluate_rails(self, proposal: Proposal, staged: StagedState) -> GateResult:
        """Evaluate all coherence rails via GateManager."""

    def _apply_corrections(self, result: GateResult) -> List[Correction]:
        """Apply deterministic corrections if needed."""

    def _resolve_commitment(self, result: GateResult, snapshot: Snapshot, staged: StagedState) -> Resolution:
        """Commit or rollback based on gate evaluation."""

    def _emit_receipt(self, resolution: Resolution) -> Receipt:
        """Emit immutable governance receipt."""
```

### 2.3 Proposal Intake Contract

**File:** `src/cnsc/haai/tgs/proposal.py`

```python
@dataclass
class Proposal:
    """Structured proposal from NPE."""
    proposal_id: UUID
    logical_time: int
    delta_ops: List[DeltaOp]
    evidence_refs: List[EvidenceID]
    confidence: float
    cost_estimate: ResourceVector
    claims: List[InvariantClaim]
    taint_class: TaintClass

@dataclass
class DeltaOp:
    """Allowed delta operation."""
    operation: DeltaOperationType  # add_belief, revise_belief, attach_evidence, etc.
    target: str
    payload: Dict[str, Any]
    provenance: Optional[str] = None

class TaintClass(Enum):
    """Taint classification for proposals."""
    TRUSTED = auto()
    UNTRUSTED = auto()
    EXTERNAL = auto()
    SPECULATIVE = auto()
```

---

## Phase 3: Receipt System Integration

### 3.1 TGS Receipt Schema

**File:** `src/cnsc/haai/tgs/receipt.py`

```python
@dataclass
class TGSReceipt:
    """TGS governance receipt."""
    attempt_id: UUID
    parent_state_hash: StateHash
    proposal_id: UUID
    dt: float
    dt_components: Dict[ClockID, float]
    gate_margins: Dict[RailID, float]
    reasons: List[ReasonCode]
    corrections_applied: List[Correction]
    accepted: bool
    new_state_hash: Optional[StateHash]
    diff_digest: str
    timestamp: datetime
    logical_time: int

class ReceiptEmitter:
    """Handles receipt emission and ledger management."""
    def emit(self, receipt: TGSReceipt) -> str:
        """Emit receipt to ledger and return receipt ID."""
    def verify(self, receipt_id: str) -> bool:
        """Verify receipt integrity."""
    def replay(self, from_ledger_index: int) -> List[TGSReceipt]:
        """Replay receipts from index for verification."""
```

### 3.2 Ledger Integration

**File:** `src/cnsc/haai/tgs/ledger.py`

```python
class GovernanceLedger:
    """Append-only ledger for TGS receipts."""
    def __init__(self, storage_path: str):
        """Initialize ledger with storage."""
    def append(self, receipt: TGSReceipt) -> int:
        """Append receipt and return ledger index."""
    def get(self, index: int) -> Optional[TGSReceipt]:
        """Retrieve receipt by ledger index."""
    def get_latest(self) -> Optional[TGSReceipt]:
        """Get most recent receipt."""
    def verify_chain(self, from_index: int) -> bool:
        """Verify hash chain integrity from index."""
```

---

## Phase 4: Gate System Extension

### 4.1 Extend Existing GateManager

**File:** `src/cnsc/haai/tgs/rails.py`

```python
# Extend GateManager with TGS-specific rails
class CoherenceRails:
    """Mandatory coherence rails for TGS."""

    def __init__(self, gate_manager: GateManager):
        """Initialize rails with gate manager."""

    def evaluate_consistency_rail(
        self,
        staged: StagedState,
        proposal: Proposal
    ) -> RailResult:
        """Evaluate consistency rail."""

    def evaluate_commitment_rail(
        self,
        staged: StagedState,
        proposal: Proposal
    ) -> RailResult:
        """Evaluate commitment rail."""

    def evaluate_causality_rail(
        self,
        staged: StagedState,
        proposal: Proposal
    ) -> RailResult:
        """Evaluate causality rail."""

    def evaluate_resource_rail(
        self,
        staged: StagedState,
        proposal: Proposal
    ) -> RailResult:
        """Evaluate resource rail."""

    def evaluate_taint_rail(
        self,
        staged: StagedState,
        proposal: Proposal
    ) -> RailResult:
        """Evaluate taint rail."""

    def evaluate_all(self, staged: StagedState, proposal: Proposal) -> CompositeRailResult:
        """Evaluate all rails and return composite result."""
```

### 4.2 Correction System

**File:** `src/cnsc/haai/tgs/corrections.py`

```python
class CorrectionEngine:
    """Deterministic correction application."""
    def apply(
        self,
        rail_results: List[RailResult],
        staged: StagedState
    ) -> Tuple[StagedState, List[Correction]]:
        """Apply corrections to staged state."""

class AllowedCorrections(Enum):
    """TGS-allowed corrections."""
    QUARANTINE_CLAIM = auto()
    CLAMP_CONFIDENCE = auto()
    DROP_LOW_PROVENANCE_EDGE = auto()
    ENFORCE_SPECULATIVE_TAG = auto()
    RESTRICT_ACTION_SCOPE = auto()
```

---

## Phase 5: Integration Points

### 5.1 NPE Integration

**File:** `src/npe/api/tgs_integration.py`

```python
class NPEToTGSGateway:
    """NPE sends proposals to TGS via this gateway."""
    def __init__(self, tgs_engine: TemporalGovernanceEngine):
        """Initialize gateway with TGS engine."""
    def submit_proposal(self, proposal: Proposal) -> TGSResponse:
        """Submit proposal to TGS and return response."""
```

### 5.2 CNSC Integration

**File:** `src/cnsc/haai/cnsc/tgs_interface.py`

```python
class CNSCToTGSInterface:
    """CNSC exposes state to TGS via this interface."""
    def __init__(self, state_store: StateStore):
        """Initialize interface with state store."""
    def get_state_hash(self) -> StateHash:
        """Get current authoritative state hash."""
    def get_state(self, hash: StateHash) -> CognitiveState:
        """Retrieve state by hash."""
    def apply_state(self, state: CognitiveState) -> None:
        """Persist committed state."""
```

### 5.3 CLI Integration

**File:** `src/cnsc/haai/cli/commands.py` (extend)

```python
@tgs_command.group()
def tgs():
    """TGS administrative commands."""
    pass

@tgs.command()
def status():
    """Show TGS system status."""
    pass

@tgs.command()
def ledger():
    """Show TGS receipt ledger."""
    pass

@tgs.command()
def clock_status():
    """Show clock status and dt computation."""
    pass
```

---

## Phase 6: Testing and Verification

### 6.1 Unit Tests

**Files:** `tests/tgs/test_clock.py`
**Files:** `tests/tgs/test_governor.py`
**Files:** `tests/tgs/test_snapshot.py`
**Files:** `tests/tgs/test_receipt.py`
**Files:** `tests/tgs/test_rails.py`

### 6.2 Integration Tests

**Files:** `tests/tgs/test_npe_integration.py`
**Files:** `tests/tgs/test_cnsc_integration.py`
**Files:** `tests/tgs/test_determinism.py`

### 6.3 Compliance Tests

**Files:** `tests/tgs/test_rollback_purity.py`
**Files:** `tests/tgs/test_single_writer.py`
**Files:** `tests/tgs/test_receipt_replay.py`

---

## Phase 7: Documentation

### 7.1 API Documentation

**File:** `docs/tgs/api.md`
- Module documentation
- Class documentation
- Method documentation
- Type annotations

### 7.2 Architecture Documentation

**File:** `docs/tgs/architecture.md`
- System overview
- Component diagram
- Data flow diagrams
- Integration points

### 7.3 Usage Guide

**File:** `docs/tgs/usage.md`
- Quick start
- Configuration
- Examples
- Troubleshooting

---

## Implementation Order

```
Phase 1: Foundation Layer
  ├── Create tgs module structure
  └── Implement clock arbitration system

Phase 2: Core Governance Engine
  ├── Implement snapshot and staging protocol
  ├── Implement temporal governance engine
  └── Implement proposal intake contract

Phase 3: Receipt System Integration
  ├── Implement TGS receipt schema
  └── Implement ledger integration

Phase 4: Gate System Extension
  ├── Extend gate manager with coherence rails
  └── Implement correction system

Phase 5: Integration Points
  ├── NPE integration
  ├── CNSC integration
  └── CLI integration

Phase 6: Testing and Verification
  ├── Unit tests
  ├── Integration tests
  └── Compliance tests

Phase 7: Documentation
  ├── API documentation
  ├── Architecture documentation
  └── Usage guide
```

---

## Backward Compatibility

- All existing APIs remain unchanged
- TGS operates as new layer above existing components
- No breaking changes to GateManager, ReceiptChain, or StateStore interfaces

---

## Success Criteria

1. Clock arbitration produces deterministic dt values
2. Snapshot and rollback restore bitwise-identical state
3. All 5 coherence rails evaluate correctly
4. Receipt emission follows fixed schema
5. Determinism guarantees hold under replay
6. No regressions in existing functionality
7. All 6 compliance tests pass
