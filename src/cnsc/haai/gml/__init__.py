"""
GML (Governance Metadata Language) Module

This module provides:
- Trace: Reasoning trace representation
- PhaseLoom: PhaseLoom thread management
- Receipts: Receipt chain management
- Replay: Deterministic replay and verification
"""

from cnsc.haai.gml.trace import (
    TraceEvent,
    TraceThread,
    TraceManager,
    TraceLevel,
    TraceQuery,
)

from cnsc.haai.gml.phaseloom import (
    PhaseLoom,
    ThreadCoupling,
    CouplingPolicy,
    ThreadState,
)

from cnsc.haai.gml.receipts import (
    Receipt,
    ReceiptStepType,
    ReceiptDecision,
    ReceiptSignature,
    ReceiptContent,
    ReceiptProvenance,
    HashChain,
    ChainValidator,
    ReceiptSystem,
)

from cnsc.haai.gml.replay import (
    Checkpoint,
    ReplayEngine,
    Verifier,
    ReplayResult,
)

__all__ = [
    # Trace
    "TraceEvent",
    "TraceThread",
    "TraceManager",
    "TraceLevel",
    "TraceQuery",
    # PhaseLoom
    "PhaseLoom",
    "ThreadCoupling",
    "CouplingPolicy",
    "ThreadState",
    # Receipts
    "Receipt",
    "ReceiptStepType",
    "ReceiptDecision",
    "ReceiptSignature",
    "ReceiptContent",
    "ReceiptProvenance",
    "ReceiptChain",
    "HashChain",
    "ChainValidator",
    "ReceiptSystem",
    # Replay
    "Checkpoint",
    "ReplayEngine",
    "Verifier",
    "ReplayResult",
]
