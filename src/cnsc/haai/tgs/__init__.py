"""
Temporal Governance System (TGS)

TGS is the authoritative control layer for cognitive state transitions.
It integrates with NSC, GML, and Coherence Framework to enforce:
- Temporal governance
- Coherence rails
- Deterministic receipt emission

This module provides:
- Clock arbitration system for dt computation
- Snapshot and staging protocol for proposal evaluation
- Temporal governance engine for processing proposals
- Receipt emission and ledger management
- Coherence rail evaluation and correction
"""

from cnsc.haai.tgs.clock import (
    BaseClock,
    ConsistencyClock,
    CommitmentClock,
    CausalityClock,
    ResourceClock,
    TaintClock,
    DriftClock,
    ClockRegistry,
    ClockID,
    ClockResult,
)
from cnsc.haai.tgs.snapshot import (
    SnapshotManager,
    Snapshot,
    StagedState,
    StateHash,
)
from cnsc.haai.tgs.proposal import (
    Proposal,
    DeltaOp,
    DeltaOperationType,
    TaintClass,
)
from cnsc.haai.tgs.governor import (
    TemporalGovernanceEngine,
    GovernanceResult,
)
from cnsc.haai.tgs.receipt import (
    TGSReceipt,
    ReceiptEmitter,
    ReasonCode,
    Correction,
)
from cnsc.haai.tgs.ledger import (
    GovernanceLedger,
)
from cnsc.haai.tgs.rails import (
    CoherenceRails,
    RailResult,
    RailDecision,
    CompositeRailResult,
)
from cnsc.haai.tgs.corrections import (
    CorrectionEngine,
    Correction,
    CorrectionType,
)
from cnsc.haai.tgs.exceptions import (
    TGSError,
    ClockError,
    SnapshotError,
    GovernanceError,
    ReceiptError,
)

__all__ = [
    # Clock system
    "BaseClock",
    "ConsistencyClock",
    "CommitmentClock",
    "CausalityClock",
    "ResourceClock",
    "TaintClock",
    "DriftClock",
    "ClockRegistry",
    "ClockID",
    "ClockResult",
    # Snapshot system
    "SnapshotManager",
    "Snapshot",
    "StagedState",
    "StateHash",
    # Proposal system
    "Proposal",
    "DeltaOp",
    "DeltaOperationType",
    "TaintClass",
    # Governance engine
    "TemporalGovernanceEngine",
    "GovernanceResult",
    # Receipt system
    "TGSReceipt",
    "ReceiptEmitter",
    "ReasonCode",
    "Correction",
    # Ledger
    "GovernanceLedger",
    # Rails
    "CoherenceRails",
    "RailResult",
    "RailDecision",
    "CompositeRailResult",
    # Corrections
    "CorrectionEngine",
    "Correction",
    "CorrectionType",
    # Exceptions
    "TGSError",
    "ClockError",
    "SnapshotError",
    "GovernanceError",
    "ReceiptError",
]
