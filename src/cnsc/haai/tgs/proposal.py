"""
Proposal Intake Contract

Defines the structured proposal format received from NPE and processed by TGS.
This module provides the data classes for proposals, delta operations, and
taint classification.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


class DeltaOperationType(Enum):
    """Allowed delta operation types."""

    ADD_BELIEF = auto()
    REVISE_BELIEF = auto()
    RETRACT_BELIEF = auto()
    ADD_EVIDENCE = auto()
    ATTACH_EVIDENCE = auto()
    ADD_TAG = auto()
    REMOVE_TAG = auto()
    UPDATE_TAG = auto()
    ADD_OBLIGATION = auto()
    FULFILL_OBLIGATION = auto()
    ADD_INTENT = auto()
    REVISE_INTENT = auto()
    DROP_INTENT = auto()
    PHASE_TRANSITION = auto()
    ALLOCATE_RESOURCE = auto()
    DEALLOCATE_RESOURCE = auto()
    SET_ATTRIBUTE = auto()
    DELETE_ATTRIBUTE = auto()
    CUSTOM = auto()


class TaintClass(Enum):
    """Taint classification for proposals."""

    TRUSTED = auto()
    UNTRUSTED = auto()
    EXTERNAL = auto()
    SPECULATIVE = auto()


@dataclass
class ResourceVector:
    """
    Resource cost estimate for a proposal.

    Attributes:
        budget: Budget type (e.g., "compute", "memory", "tokens")
        amount: Estimated resource amount
    """

    budget: str
    amount: float

    def __getitem__(self, key: str) -> Any:
        """Allow dict-like access."""
        if key == "budget":
            return self.budget
        elif key == "amount":
            return self.amount
        raise KeyError(key)

    def get(self, key: str, default: Any = None) -> Any:
        """Get value with default."""
        try:
            return self[key]
        except KeyError:
            return default


@dataclass
class InvariantClaim:
    """
    Claim about an invariant that this proposal preserves.

    Attributes:
        invariant_id: Identifier of the invariant
        claim_type: Type of claim (preserves, strengthens, weakens)
        evidence: Evidence supporting the claim
    """

    invariant_id: str
    claim_type: str  # "preserves", "strengthens", "weakens"
    evidence: Optional[Dict[str, Any]] = None


@dataclass
class DeltaOp:
    """
    A single delta operation within a proposal.

    Attributes:
        operation: Type of delta operation
        target: Target of the operation (e.g., belief ID, tag name)
        payload: Operation payload data
        provenance: Optional provenance chain string
        prerequisites: Optional list of prerequisite event IDs
        conditions: Optional conditions for this delta
    """

    operation: DeltaOperationType
    target: str
    payload: Dict[str, Any] = field(default_factory=dict)
    provenance: Optional[str] = None
    prerequisites: List[str] = field(default_factory=list)
    conditions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Proposal:
    """
    Structured proposal from NPE.

    A proposal represents a set of state changes that NPE suggests
    applying to the cognitive state.

    Attributes:
        proposal_id: Unique identifier for this proposal
        logical_time: Logical timestamp for this proposal
        delta_ops: List of delta operations to apply
        evidence_refs: List of evidence IDs referenced
        confidence: Confidence score (0.0 to 1.0)
        cost_estimate: Estimated resource costs
        claims: Invariant claims made by NPE
        taint_class: Taint classification of the proposal
        metadata: Additional proposal metadata
    """

    proposal_id: UUID = field(default_factory=uuid4)
    logical_time: int = 0
    delta_ops: List[DeltaOp] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)
    confidence: float = 1.0
    cost_estimate: Optional[Dict[str, float]] = None
    claims: List[InvariantClaim] = field(default_factory=list)
    taint_class: TaintClass = TaintClass.TRUSTED
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Proposal":
        """Create Proposal from dictionary."""
        proposal_id = data.get("proposal_id", str(uuid4()))
        if isinstance(proposal_id, str):
            proposal_id = UUID(proposal_id)

        delta_ops = [
            DeltaOp(
                operation=DeltaOperationType[op["operation"]],
                target=op["target"],
                payload=op.get("payload", {}),
                provenance=op.get("provenance"),
                prerequisites=op.get("prerequisites", []),
                conditions=op.get("conditions", {}),
            )
            for op in data.get("delta_ops", [])
        ]

        evidence_refs = data.get("evidence_refs", [])
        confidence = data.get("confidence", 1.0)
        cost_estimate = data.get("cost_estimate")
        taint_class = TaintClass[data.get("taint_class", "TRUSTED")]
        metadata = data.get("metadata", {})

        return cls(
            proposal_id=proposal_id,
            logical_time=data.get("logical_time", 0),
            delta_ops=delta_ops,
            evidence_refs=evidence_refs,
            confidence=confidence,
            cost_estimate=cost_estimate,
            claims=[],
            taint_class=taint_class,
            metadata=metadata,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert Proposal to dictionary."""
        return {
            "proposal_id": str(self.proposal_id),
            "logical_time": self.logical_time,
            "delta_ops": [
                {
                    "operation": op.operation.name,
                    "target": op.target,
                    "payload": op.payload,
                    "provenance": op.provenance,
                    "prerequisites": op.prerequisites,
                    "conditions": op.conditions,
                }
                for op in self.delta_ops
            ],
            "evidence_refs": self.evidence_refs,
            "confidence": self.confidence,
            "cost_estimate": self.cost_estimate,
            "claims": [
                {
                    "invariant_id": claim.invariant_id,
                    "claim_type": claim.claim_type,
                    "evidence": claim.evidence,
                }
                for claim in self.claims
            ],
            "taint_class": self.taint_class.name,
            "metadata": self.metadata,
        }

    def validate(self) -> bool:
        """
        Validate proposal structure.

        Returns:
            True if proposal is valid, False otherwise
        """
        if not self.delta_ops:
            return False

        for delta in self.delta_ops:
            if not delta.target:
                return False

        if not 0.0 <= self.confidence <= 1.0:
            return False

        return True
