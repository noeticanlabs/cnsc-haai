"""
GML (Glyph Memory Language) Module

GML is the Memory/Time axis of Triaxis — a declarative append-only language
recording irreversible system evolution, including time, causality, coherence
receipts, and outcomes.

GML answers: "What *actually happened*, when, and why it was permitted?"

This module provides traceability and forensics by recording what happened:
- Trace: Reasoning trace representation and event recording
- PhaseLoom: PhaseLoom thread management for temporal coupling
- Receipts: Receipt chain management for causality and coherence verification
- Replay: Deterministic replay and verification for audit purposes
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
    "HashChain",
    "ChainValidator",
    "ReceiptSystem",
    # Replay
    "Checkpoint",
    "ReplayEngine",
    "Verifier",
    "ReplayResult",
]
