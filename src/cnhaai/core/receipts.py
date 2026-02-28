"""
Receipt System for CNHAAI

This module provides the receipt infrastructure for auditability:
- Receipt: Cryptographic record of a reasoning step
- ReceiptSystem: Emits and stores receipts
- HMAC signing for integrity verification (simplified for prototype)
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import uuid4
import hashlib
import hmac
import base64
import json


class ReceiptStepType(Enum):
    """Types of steps that can generate receipts."""

    GATE_VALIDATION = auto()
    PHASE_TRANSITION = auto()
    RECOVERY_ACTION = auto()
    MANUAL_ANNOTATION = auto()
    ABSTRACTION_CREATION = auto()
    EPISODE_START = auto()
    EPISODE_END = auto()


class ReceiptDecision(Enum):
    """Possible decisions recorded in receipts."""

    PASS = auto()
    FAIL = auto()
    WARN = auto()
    SKIP = auto()


@dataclass
class ReceiptSignature:
    """Signature component of a receipt."""

    algorithm: str = "HMAC-SHA256"
    signer: str = "system"
    signature: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {"algorithm": self.algorithm, "signer": self.signer, "signature": self.signature}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReceiptSignature":
        """Create from dictionary."""
        return cls(
            algorithm=data.get("algorithm", "HMAC-SHA256"),
            signer=data.get("signer", "system"),
            signature=data.get("signature", ""),
        )


@dataclass
class ReceiptContent:
    """Content component of a receipt."""

    step_type: ReceiptStepType
    input_state: str = ""
    output_state: str = ""
    decision: ReceiptDecision = ReceiptDecision.PASS
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "step_type": self.step_type.name,
            "input_state": self.input_state,
            "output_state": self.output_state,
            "decision": self.decision.name,
            "details": self.details,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReceiptContent":
        """Create from dictionary."""
        step_type = ReceiptStepType[data.get("step_type", "GATE_VALIDATION")]
        decision = ReceiptDecision[data.get("decision", "PASS")]
        return cls(
            step_type=step_type,
            input_state=data.get("input_state", ""),
            output_state=data.get("output_state", ""),
            decision=decision,
            details=data.get("details", {}),
        )


@dataclass
class ReceiptProvenance:
    """Provenance component of a receipt."""

    parent_receipts: List[str] = field(default_factory=list)
    evidence_references: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "parent_receipts": self.parent_receipts,
            "evidence_references": self.evidence_references,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReceiptProvenance":
        """Create from dictionary."""
        return cls(
            parent_receipts=data.get("parent_receipts", []),
            evidence_references=data.get("evidence_references", []),
        )


@dataclass
class Receipt:
    """
    A cryptographic record of a reasoning step.

    Receipts enable auditability, verification, and state reconstruction
    by capturing the complete context of each reasoning step.

    Attributes:
        version: Receipt schema version
        receipt_id: Unique identifier
        timestamp: ISO 8601 timestamp of creation
        episode_id: ID of the reasoning episode
        content: Step-specific content
        provenance: Parent receipts and evidence references
        signature: Cryptographic signature
    """

    version: str = "1.0.0"
    receipt_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    episode_id: str = ""
    content: ReceiptContent = field(
        default_factory=lambda: ReceiptContent(ReceiptStepType.GATE_VALIDATION)
    )
    provenance: ReceiptProvenance = field(default_factory=ReceiptProvenance)
    signature: ReceiptSignature = field(default_factory=ReceiptSignature)

    def to_dict(self) -> Dict[str, Any]:
        """Convert receipt to dictionary representation."""
        return {
            "version": self.version,
            "receipt_id": self.receipt_id,
            "timestamp": self.timestamp.isoformat(),
            "episode_id": self.episode_id,
            "content": self.content.to_dict(),
            "provenance": self.provenance.to_dict(),
            "signature": self.signature.to_dict(),
        }

    def to_json(self) -> str:
        """Convert receipt to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Receipt":
        """Create receipt from dictionary representation."""
        timestamp = (
            datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.utcnow()
        )
        content = ReceiptContent.from_dict(data.get("content", {}))
        provenance = ReceiptProvenance.from_dict(data.get("provenance", {}))
        signature = ReceiptSignature.from_dict(data.get("signature", {}))

        return cls(
            version=data.get("version", "1.0.0"),
            receipt_id=data.get("receipt_id", str(uuid4())),
            timestamp=timestamp,
            episode_id=data.get("episode_id", ""),
            content=content,
            provenance=provenance,
            signature=signature,
        )

    @classmethod
    def from_json(cls, json_str: str) -> "Receipt":
        """Create receipt from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def compute_hash(self) -> str:
        """Compute hash of receipt content for signing."""
        content_dict = {
            "version": self.version,
            "receipt_id": self.receipt_id,
            "timestamp": self.timestamp.isoformat(),
            "episode_id": self.episode_id,
            "content": self.content.to_dict(),
            "provenance": self.provenance.to_dict(),
        }
        content_json = json.dumps(content_dict, sort_keys=True)
        return hashlib.sha256(content_json.encode()).hexdigest()


class ReceiptSystem:
    """
    System for emitting and storing receipts.

    The receipt system provides:
    - Receipt creation and signing
    - Storage and retrieval
    - Chain verification
    - Audit capabilities
    """

    def __init__(
        self,
        signing_key: str = "cnhaai-prototype-key",
        storage_type: str = "in_memory",
        retention: str = "session",
    ):
        """
        Initialize the receipt system.

        Args:
            signing_key: Key for HMAC signing
            storage_type: Type of storage ("in_memory", "file")
            retention: Retention policy ("session", "persistent")
        """
        self.signing_key = signing_key
        self.storage_type = storage_type
        self.retention = retention
        self.receipts: Dict[str, Receipt] = {}
        self.receipts_by_episode: Dict[str, List[str]] = {}
        self.receipt_chain: List[str] = []  # Ordered list of receipt IDs
        self._counter = 0

    def emit_receipt(
        self,
        episode_id: str,
        step_type: ReceiptStepType,
        input_state: str = "",
        output_state: str = "",
        decision: ReceiptDecision = ReceiptDecision.PASS,
        details: Optional[Dict[str, Any]] = None,
        parent_receipts: Optional[List[str]] = None,
        evidence_references: Optional[List[str]] = None,
        signer: str = "system",
    ) -> Receipt:
        """
        Create and emit a new receipt.

        Args:
            episode_id: ID of the reasoning episode
            step_type: Type of step being recorded
            input_state: Hash of input state
            output_state: Hash of output state
            decision: Decision made
            details: Step-specific details
            parent_receipts: Parent receipt IDs
            evidence_references: Evidence URIs
            signer: Signer identifier

        Returns:
            The created and signed receipt
        """
        self._counter += 1

        content = ReceiptContent(
            step_type=step_type,
            input_state=input_state,
            output_state=output_state,
            decision=decision,
            details=details or {},
        )

        provenance = ReceiptProvenance(
            parent_receipts=parent_receipts or [], evidence_references=evidence_references or []
        )

        receipt = Receipt(episode_id=episode_id, content=content, provenance=provenance)

        # Sign the receipt
        self._sign_receipt(receipt, signer)

        # Store the receipt
        self._store_receipt(receipt)

        # Add to chain
        self.receipt_chain.append(receipt.receipt_id)

        return receipt

    def _sign_receipt(self, receipt: Receipt, signer: str) -> None:
        """Sign a receipt using HMAC."""
        content_hash = receipt.compute_hash()

        # Create signature data
        signature_data = f"{receipt.receipt_id}:{content_hash}"
        hmac_signature = hmac.new(
            self.signing_key.encode(), signature_data.encode(), hashlib.sha256
        ).digest()

        receipt.signature = ReceiptSignature(
            algorithm="HMAC-SHA256",
            signer=signer,
            signature=base64.b64encode(hmac_signature).decode(),
        )

    def verify_receipt(self, receipt: Receipt) -> bool:
        """
        Verify a receipt's signature.

        Args:
            receipt: The receipt to verify

        Returns:
            True if signature is valid
        """
        # Compute expected signature
        content_hash = receipt.compute_hash()
        signature_data = f"{receipt.receipt_id}:{content_hash}"
        expected_signature = hmac.new(
            self.signing_key.encode(), signature_data.encode(), hashlib.sha256
        ).digest()
        expected_b64 = base64.b64encode(expected_signature).decode()

        # Compare
        return hmac.compare_digest(receipt.signature.signature, expected_b64)

    def _store_receipt(self, receipt: Receipt) -> None:
        """Store a receipt in the appropriate storage."""
        self.receipts[receipt.receipt_id] = receipt

        # Index by episode
        if receipt.episode_id not in self.receipts_by_episode:
            self.receipts_by_episode[receipt.episode_id] = []
        self.receipts_by_episode[receipt.episode_id].append(receipt.receipt_id)

    def get_receipt(self, receipt_id: str) -> Optional[Receipt]:
        """Get a receipt by ID."""
        return self.receipts.get(receipt_id)

    def get_episode_receipts(self, episode_id: str) -> List[Receipt]:
        """Get all receipts for an episode."""
        ids = self.receipts_by_episode.get(episode_id, [])
        return [self.receipts[id_] for id_ in ids if id_ in self.receipts]

    def get_receipt_chain(self, episode_id: str) -> List[Receipt]:
        """Get the complete receipt chain for an episode."""
        receipts = self.get_episode_receipts(episode_id)
        # Sort by timestamp
        return sorted(receipts, key=lambda r: r.timestamp)

    def verify_episode_chain(self, episode_id: str) -> bool:
        """
        Verify the integrity of an episode's receipt chain.

        Args:
            episode_id: The episode to verify

        Returns:
            True if chain is valid
        """
        receipts = self.get_episode_receipts(episode_id)
        if not receipts:
            return True

        # Verify each receipt
        for receipt in receipts:
            if not self.verify_receipt(receipt):
                return False

        # Verify chain order (timestamps should be increasing)
        sorted_receipts = sorted(receipts, key=lambda r: r.timestamp)
        for i in range(1, len(sorted_receipts)):
            if sorted_receipts[i].timestamp < sorted_receipts[i - 1].timestamp:
                return False

        return True

    def create_gate_receipt(
        self,
        episode_id: str,
        gate_name: str,
        decision: ReceiptDecision,
        details: Dict[str, Any],
        parent_receipts: Optional[List[str]] = None,
    ) -> Receipt:
        """Create a receipt for a gate validation."""
        return self.emit_receipt(
            episode_id=episode_id,
            step_type=ReceiptStepType.GATE_VALIDATION,
            input_state=details.get("input_state", ""),
            output_state=details.get("output_state", ""),
            decision=decision,
            details={"gate_name": gate_name, **details},
            parent_receipts=parent_receipts,
        )

    def create_phase_receipt(
        self,
        episode_id: str,
        from_phase: str,
        to_phase: str,
        duration_ms: int,
        steps_completed: int,
        parent_receipts: Optional[List[str]] = None,
    ) -> Receipt:
        """Create a receipt for a phase transition."""
        return self.emit_receipt(
            episode_id=episode_id,
            step_type=ReceiptStepType.PHASE_TRANSITION,
            decision=ReceiptDecision.PASS,
            details={
                "from_phase": from_phase,
                "to_phase": to_phase,
                "duration_ms": duration_ms,
                "steps_completed": steps_completed,
            },
            parent_receipts=parent_receipts,
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get receipt system statistics."""
        return {
            "total_receipts": len(self.receipts),
            "episodes_with_receipts": len(self.receipts_by_episode),
            "chain_length": len(self.receipt_chain),
            "storage_type": self.storage_type,
            "retention": self.retention,
        }

    def clear(self) -> None:
        """Clear all receipts (for session reset)."""
        self.receipts.clear()
        self.receipts_by_episode.clear()
        self.receipt_chain.clear()
        self._counter = 0
