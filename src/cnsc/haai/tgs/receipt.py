"""
TGS Receipt System

Defines the TGS governance receipt schema and receipt emitter.
Receipts provide immutable evidence of governance decisions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


class ReasonCode(Enum):
    """Reason codes for governance decisions."""

    CONSISTENCY_CHECK = auto()
    COMMITMENT_CHECK = auto()
    CAUSALITY_CHECK = auto()
    RESOURCE_CHECK = auto()
    TAINT_CHECK = auto()
    DRIFT_CHECK = auto()
    COHERENCE_RAIL = auto()
    CORRECTION_APPLIED = auto()
    PHASE_TRANSITION = auto()
    REPLAY_VERIFICATION = auto()


@dataclass
class Correction:
    """Correction applied during governance."""

    correction_type: str
    target: str
    reason: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TGSReceipt:
    """
    TGS governance receipt.

    A receipt provides immutable evidence of a governance decision,
    including the proposal evaluated, dt computation, rail margins,
    and the final decision.

    Attributes:
        attempt_id: Unique identifier for this governance attempt
        parent_state_hash: Hash of state before this attempt
        proposal_id: ID of the proposal evaluated
        dt: Total dt from clock arbitration
        dt_components: Per-clock dt contributions
        gate_margins: Per-rail margin values
        reasons: Reason codes for the decision
        corrections_applied: Corrections applied, if any
        accepted: Whether the proposal was accepted
        new_state_hash: Hash of new state (if accepted)
        diff_digest: Digest of state changes
        timestamp: Wall clock timestamp
        logical_time: Logical timestamp
        metadata: Additional receipt metadata
    """

    attempt_id: UUID = field(default_factory=uuid4)
    parent_state_hash: str = ""
    proposal_id: UUID = field(default_factory=uuid4)
    dt: float = 0.0
    dt_components: Dict[str, float] = field(default_factory=dict)
    gate_margins: Dict[str, float] = field(default_factory=dict)
    reasons: List[ReasonCode] = field(default_factory=list)
    corrections_applied: List[Correction] = field(default_factory=list)
    accepted: bool = False
    new_state_hash: Optional[str] = None
    diff_digest: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    logical_time: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert receipt to dictionary."""
        return {
            "attempt_id": str(self.attempt_id),
            "parent_state_hash": self.parent_state_hash,
            "proposal_id": str(self.proposal_id),
            "dt": self.dt,
            "dt_components": self.dt_components,
            "gate_margins": self.gate_margins,
            "reasons": [r.name for r in self.reasons],
            "corrections_applied": [
                {
                    "correction_type": c.correction_type,
                    "target": c.target,
                    "reason": c.reason,
                    "details": c.details,
                }
                for c in self.corrections_applied
            ],
            "accepted": self.accepted,
            "new_state_hash": self.new_state_hash,
            "diff_digest": self.diff_digest,
            "timestamp": self.timestamp.isoformat(),
            "logical_time": self.logical_time,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TGSReceipt":
        """Create receipt from dictionary."""
        return cls(
            attempt_id=UUID(data["attempt_id"]),
            parent_state_hash=data["parent_state_hash"],
            proposal_id=UUID(data["proposal_id"]),
            dt=data["dt"],
            dt_components=data["dt_components"],
            gate_margins=data["gate_margins"],
            reasons=[ReasonCode[r] for r in data.get("reasons", [])],
            corrections_applied=[
                Correction(
                    correction_type=c["correction_type"],
                    target=c["target"],
                    reason=c["reason"],
                    details=c.get("details", {}),
                )
                for c in data.get("corrections_applied", [])
            ],
            accepted=data["accepted"],
            new_state_hash=data.get("new_state_hash"),
            diff_digest=data.get("diff_digest", ""),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            logical_time=data["logical_time"],
            metadata=data.get("metadata", {}),
        )

    def to_json(self) -> str:
        """Serialize receipt to JSON string."""
        import json

        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "TGSReceipt":
        """Deserialize receipt from JSON string."""
        import json

        return cls.from_dict(json.loads(json_str))


class ReceiptEmitter:
    """
    Handles receipt emission and ledger management.

    The receipt emitter:
    1. Creates receipts for governance decisions
    2. Emits receipts to the ledger
    3. Verifies receipt integrity
    4. Supports replay for verification
    """

    def __init__(self, ledger: "GovernanceLedger"):
        """
        Initialize receipt emitter.

        Args:
            ledger: Ledger to emit receipts to
        """
        self._ledger = ledger

    def emit(self, receipt: TGSReceipt) -> str:
        """
        Emit receipt to ledger and return receipt ID.

        Args:
            receipt: Receipt to emit

        Returns:
            Receipt ID (hex string)
        """
        return self._ledger.append(receipt)

    def verify(self, receipt_id: str) -> bool:
        """
        Verify receipt integrity.

        Args:
            receipt_id: Receipt ID to verify

        Returns:
            True if receipt is valid, False otherwise
        """
        try:
            receipt = self._ledger.get_by_id(receipt_id)
            if receipt is None:
                return False

            # Verify receipt structure
            if not receipt.parent_state_hash:
                return False

            if not 0.0 <= receipt.dt <= 1.0:
                return False

            return True
        except Exception:
            return False

    def replay(self, from_ledger_index: int = 0) -> List[TGSReceipt]:
        """
        Replay receipts from index for verification.

        Args:
            from_ledger_index: Starting ledger index

        Returns:
            List of receipts for replay
        """
        receipts = []

        for i in range(from_ledger_index, self._ledger.get_length()):
            receipt = self._ledger.get(i)
            if receipt:
                receipts.append(receipt)

        return receipts

    def create_receipt(
        self,
        parent_state_hash: str,
        proposal_id: UUID,
        dt: float,
        dt_components: Dict[str, float],
        gate_margins: Dict[str, float],
        reasons: List[ReasonCode],
        corrections: List[Correction],
        accepted: bool,
        new_state_hash: Optional[str],
        diff_digest: str,
        logical_time: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TGSReceipt:
        """
        Create a TGSReceipt from governance results.

        Args:
            parent_state_hash: Hash of state before governance
            proposal_id: ID of proposal evaluated
            dt: Total dt from arbitration
            dt_components: Per-clock dt values
            gate_margins: Per-rail margins
            reasons: Reason codes for decision
            corrections: Corrections applied
            accepted: Whether proposal was accepted
            new_state_hash: New state hash (if accepted)
            diff_digest: Digest of state changes
            logical_time: Logical timestamp
            metadata: Additional metadata

        Returns:
            Created TGSReceipt
        """
        return TGSReceipt(
            parent_state_hash=parent_state_hash,
            proposal_id=proposal_id,
            dt=dt,
            dt_components=dt_components,
            gate_margins=gate_margins,
            reasons=reasons,
            corrections_applied=corrections,
            accepted=accepted,
            new_state_hash=new_state_hash,
            diff_digest=diff_digest,
            logical_time=logical_time,
            metadata=metadata or {},
        )


# Import GovernanceLedger for type hints
from cnsc.haai.tgs.ledger import GovernanceLedger
