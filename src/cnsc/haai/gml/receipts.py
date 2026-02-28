"""
GML Receipt Chain

Receipt chain management for the Coherence Framework.

This module provides:
- Receipt: Cryptographic receipt record
- ReceiptChain: Linked receipt list
- HashChain: Cryptographic hash chain
- ChainValidator: Receipt verification
- ReceiptSystem: Receipt emission and storage
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Callable
from datetime import datetime
from uuid import uuid4
import hashlib
import hmac
import base64
import json

# GraphGML import for dual-write support
try:
    from cnsc.haai.graphgml import types, builder, core

    GRAPHGML_AVAILABLE = True
except ImportError:
    GRAPHGML_AVAILABLE = False


class ReceiptStepType(Enum):
    """Types of steps that generate receipts."""

    PARSE = auto()
    TYPE_CHECK = auto()
    GATE_EVAL = auto()
    PHASE_TRANSITION = auto()
    VM_EXECUTION = auto()
    COHERENCE_CHECK = auto()
    TRACE_EVENT = auto()
    CHECKPOINT = auto()
    REPLAY = auto()
    CUSTOM = auto()


class ReceiptDecision(Enum):
    """Possible decisions in receipts."""

    PASS = auto()
    FAIL = auto()
    WARN = auto()
    SKIP = auto()
    PENDING = auto()


class NPEResponseStatus(Enum):
    """NPE response status codes."""

    SUCCESS = "success"
    PARTIAL = "partial"  # Some candidates returned, others failed
    ERROR = "error"  # Request failed entirely
    TIMEOUT = "timeout"  # Request exceeded budget
    INVALID = "invalid"  # Request was invalid


# =============================================================================
# NPE-Specific Receipt Extensions
# =============================================================================


@dataclass
class NPEProposalRequest:
    """
    Tracks proposal requests sent to NPE.

    Attributes:
        request_id: Unique identifier for the NPE request
        domain: NPE domain (e.g., "gr" for governance/repair)
        candidate_type: Type of candidates requested
        seed: Deterministic seed for reproducibility
        budgets: Budget constraints used
        inputs: Input data sent to NPE
    """

    request_id: str
    domain: str = "gr"
    candidate_type: str = "repair"
    seed: int = 0
    budgets: Dict[str, Any] = field(default_factory=dict)
    inputs: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "request_id": self.request_id,
            "domain": self.domain,
            "candidate_type": self.candidate_type,
            "seed": self.seed,
            "budgets": self.budgets,
            "inputs": self.inputs,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NPEProposalRequest":
        """Create from dictionary."""
        return cls(
            request_id=data.get("request_id", ""),
            domain=data.get("domain", "gr"),
            candidate_type=data.get("candidate_type", "repair"),
            seed=data.get("seed", 0),
            budgets=data.get("budgets", {}),
            inputs=data.get("inputs", {}),
        )


@dataclass
class NPERepairProposal:
    """
    Tracks repair proposals received from NPE.

    Attributes:
        proposal_id: Unique identifier for this proposal
        candidate: The proposed candidate solution
        score: Confidence or quality score
        evidence: Supporting evidence items
        explanation: Human-readable explanation of the proposal
        provenance: Provenance data from NPE
    """

    proposal_id: str
    candidate: Dict[str, Any] = field(default_factory=dict)
    score: Optional[float] = None
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    explanation: Optional[str] = None
    provenance: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "proposal_id": self.proposal_id,
            "candidate": self.candidate,
            "score": self.score,
            "evidence": self.evidence,
            "explanation": self.explanation,
            "provenance": self.provenance,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NPERepairProposal":
        """Create from dictionary."""
        return cls(
            proposal_id=data.get("proposal_id", ""),
            candidate=data.get("candidate", {}),
            score=data.get("score"),
            evidence=data.get("evidence", []),
            explanation=data.get("explanation"),
            provenance=data.get("provenance", {}),
        )


@dataclass
class NPEProposalMetadata:
    """
    Metadata for NPE proposals.

    Attributes:
        request_timestamp: When the request was sent
        response_timestamp: When the response was received
        response_status: Status of the NPE response
        total_candidates: Total candidates returned
        budget_used: Actual budget consumed
        npe_version: Version of NPE that processed the request
    """

    request_timestamp: str = ""
    response_timestamp: str = ""
    response_status: str = NPEResponseStatus.SUCCESS.value
    total_candidates: int = 0
    budget_used: Dict[str, Any] = field(default_factory=dict)
    npe_version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "request_timestamp": self.request_timestamp,
            "response_timestamp": self.response_timestamp,
            "response_status": self.response_status,
            "total_candidates": self.total_candidates,
            "budget_used": self.budget_used,
            "npe_version": self.npe_version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NPEProposalMetadata":
        """Create from dictionary."""
        return cls(
            request_timestamp=data.get("request_timestamp", ""),
            response_timestamp=data.get("response_timestamp", ""),
            response_status=data.get("response_status", NPEResponseStatus.SUCCESS.value),
            total_candidates=data.get("total_candidates", 0),
            budget_used=data.get("budget_used", {}),
            npe_version=data.get("npe_version", "1.0.0"),
        )


@dataclass
class NPEProvenance:
    """
    NPE-specific provenance data.

    Attributes:
        source: Original source ("npe")
        episode_id: Episode identifier
        phase: Phase when NPE was invoked
        npe_request_id: Reference to NPE request ID
        npe_response_id: Reference to NPE response ID
    """

    source: str = "npe"
    episode_id: Optional[str] = None
    phase: Optional[str] = None
    npe_request_id: Optional[str] = None
    npe_response_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "source": self.source,
            "episode_id": self.episode_id,
            "phase": self.phase,
            "npe_request_id": self.npe_request_id,
            "npe_response_id": self.npe_response_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NPEProvenance":
        """Create from dictionary."""
        return cls(
            source=data.get("source", "npe"),
            episode_id=data.get("episode_id"),
            phase=data.get("phase"),
            npe_request_id=data.get("npe_request_id"),
            npe_response_id=data.get("npe_response_id"),
        )


@dataclass
class ReceiptSignature:
    """Signature component of receipt."""

    algorithm: str = "HMAC-SHA256"
    signer: str = "system"
    signature: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "algorithm": self.algorithm,
            "signer": self.signer,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReceiptSignature":
        """Create from dictionary."""
        return cls(
            algorithm=data.get("algorithm", "HMAC-SHA256"),
            signer=data.get("signer", "system"),
            signature=data.get("signature", ""),
        )

    def sign(self, data: str, key: str) -> None:
        """Sign data."""
        self.signature = hmac.new(
            key.encode("utf-8"), data.encode("utf-8"), hashlib.sha256
        ).hexdigest()

    def verify(self, data: str, key: str) -> bool:
        """Verify signature."""
        expected = hmac.new(key.encode("utf-8"), data.encode("utf-8"), hashlib.sha256).hexdigest()
        return hmac.compare_digest(self.signature, expected)


@dataclass
class ReceiptContent:
    """Content component of receipt."""

    step_type: ReceiptStepType
    input_hash: str = ""
    output_hash: str = ""
    decision: ReceiptDecision = ReceiptDecision.PASS
    details: Dict[str, Any] = field(default_factory=dict)
    coherence_before: Optional[float] = None
    coherence_after: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "step_type": self.step_type.name,
            "input_hash": self.input_hash,
            "output_hash": self.output_hash,
            "decision": self.decision.name,
            "details": self.details,
            "coherence_before": self.coherence_before,
            "coherence_after": self.coherence_after,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReceiptContent":
        """Create from dictionary."""
        return cls(
            step_type=(
                ReceiptStepType[data["step_type"]]
                if isinstance(data["step_type"], str)
                else ReceiptStepType(data["step_type"])
            ),
            input_hash=data.get("input_hash", ""),
            output_hash=data.get("output_hash", ""),
            decision=(
                ReceiptDecision[data["decision"]]
                if isinstance(data["decision"], str)
                else ReceiptDecision(data["decision"])
            ),
            details=data.get("details", {}),
            coherence_before=data.get("coherence_before"),
            coherence_after=data.get("coherence_after"),
        )

    def compute_hash(self) -> str:
        """Compute content hash."""
        data = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(data.encode("utf-8")).hexdigest()


@dataclass
class ReceiptProvenance:
    """Provenance component of receipt."""

    source: str
    episode_id: Optional[str] = None
    phase: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    span: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "source": self.source,
            "episode_id": self.episode_id,
            "phase": self.phase,
            "timestamp": self.timestamp.isoformat(),
            "span": self.span,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReceiptProvenance":
        """Create from dictionary."""
        return cls(
            source=data["source"],
            episode_id=data.get("episode_id"),
            phase=data.get("phase"),
            timestamp=(
                datetime.fromisoformat(data["timestamp"])
                if "timestamp" in data
                else datetime.utcnow()
            ),
            span=data.get("span"),
        )


@dataclass
class Receipt:
    """
    Receipt.

    Cryptographic record of a reasoning step.

    Version: 1.0.0 - See schemas/receipt.schema.json for canonical spec.
    """

    # Core fields (required, no defaults)
    receipt_id: str
    content: ReceiptContent
    signature: ReceiptSignature
    provenance: ReceiptProvenance

    # Version field (required for schema compatibility)
    version: str = "1.0.0"

    # Chain links
    previous_receipt_id: Optional[str] = None
    previous_receipt_hash: Optional[str] = None
    chain_hash: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Graph integration
    graph_commit_id: Optional[str] = None

    # NPE-specific fields (optional, backward compatible)
    npe_request_id: Optional[str] = None
    npe_response_status: Optional[str] = None
    npe_proposals: List[Dict[str, Any]] = field(default_factory=list)
    npe_provenance: Optional[Dict[str, Any]] = None

    # Artifact hashes for replay safety (E1)
    registry_hash: Optional[str] = None
    corpus_snapshot_hash: Optional[str] = None
    schema_bundle_hash: Optional[str] = None

    # Taint/provenance enforcement (E2)
    # "observed", "inferred", "proposed", "external", "user_claim"
    taint_class: str = "observed"
    provenance_chain_id: Optional[str] = None
    gate_approval_required: bool = False
    gate_approved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "version": self.version,
            "receipt_id": self.receipt_id,
            "content": self.content.to_dict(),
            "signature": self.signature.to_dict(),
            "provenance": self.provenance.to_dict(),
            "previous_receipt_id": self.previous_receipt_id,
            "previous_receipt_hash": self.previous_receipt_hash,
            "chain_hash": self.chain_hash,
            "metadata": self.metadata,
        }
        # Only include NPE fields if they are set (backward compatibility)
        if self.npe_request_id is not None:
            result["npe_request_id"] = self.npe_request_id
        if self.npe_response_status is not None:
            result["npe_response_status"] = self.npe_response_status
        if self.npe_proposals:
            result["npe_proposals"] = self.npe_proposals
        if self.npe_provenance is not None:
            result["npe_provenance"] = self.npe_provenance
        # Artifact hashes for replay safety (E1)
        if self.registry_hash is not None:
            result["registry_hash"] = self.registry_hash
        if self.corpus_snapshot_hash is not None:
            result["corpus_snapshot_hash"] = self.corpus_snapshot_hash
        if self.schema_bundle_hash is not None:
            result["schema_bundle_hash"] = self.schema_bundle_hash
        # Taint/provenance enforcement (E2)
        if self.taint_class != "observed":
            result["taint_class"] = self.taint_class
        if self.provenance_chain_id is not None:
            result["provenance_chain_id"] = self.provenance_chain_id
        if self.gate_approval_required:
            result["gate_approval_required"] = True
        if self.gate_approved:
            result["gate_approved"] = True
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Receipt":
        """Create from dictionary."""
        return cls(
            version=data.get("version", "1.0.0"),
            receipt_id=data["receipt_id"],
            content=ReceiptContent.from_dict(data["content"]),
            signature=ReceiptSignature.from_dict(data["signature"]),
            provenance=ReceiptProvenance.from_dict(data["provenance"]),
            previous_receipt_id=data.get("previous_receipt_id"),
            previous_receipt_hash=data.get("previous_receipt_hash"),
            chain_hash=data.get("chain_hash"),
            metadata=data.get("metadata", {}),
            npe_request_id=data.get("npe_request_id"),
            npe_response_status=data.get("npe_response_status"),
            npe_proposals=data.get("npe_proposals", []),
            npe_provenance=data.get("npe_provenance"),
            # Artifact hashes for replay safety (E1)
            registry_hash=data.get("registry_hash"),
            corpus_snapshot_hash=data.get("corpus_snapshot_hash"),
            schema_bundle_hash=data.get("schema_bundle_hash"),
            # Taint/provenance enforcement (E2)
            taint_class=data.get("taint_class", "observed"),
            provenance_chain_id=data.get("provenance_chain_id"),
            gate_approval_required=data.get("gate_approval_required", False),
            gate_approved=data.get("gate_approved", False),
        )

    def compute_hash(self) -> str:
        """Compute receipt hash for chain."""
        data = json.dumps(
            {
                "receipt_id": self.receipt_id,
                "content": self.content.to_dict(),
                "previous_receipt_hash": self.previous_receipt_hash,
            },
            sort_keys=True,
        )
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    def compute_chain_hash(self, previous_chain_hash: Optional[str] = None) -> str:
        """Compute chain hash."""
        receipt_hash = self.compute_hash()
        if previous_chain_hash:
            data = json.dumps(
                {
                    "previous": previous_chain_hash,
                    "current": receipt_hash,
                },
                sort_keys=True,
            )
        else:
            data = receipt_hash
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    def to_graph_commit(self) -> Optional[types.CommitNode]:
        """Convert Receipt to GraphGML CommitNode."""
        if not GRAPHGML_AVAILABLE:
            return None
        return types.CommitNode(
            commit_id=self.graph_commit_id or f"commit_{self.receipt_id}",
            operation=self.content.step_type.name,
            properties={
                "receipt_id": self.receipt_id,
                "version": self.version,
                "content": self.content.to_dict(),
                "signature": self.signature.to_dict(),
                "provenance": self.provenance.to_dict(),
                "previous_receipt_id": self.previous_receipt_id,
                "previous_receipt_hash": self.previous_receipt_hash,
                "chain_hash": self.chain_hash,
                "metadata": self.metadata,
            },
            metadata={"source": "receipt"},
        )

    # -------------------------------------------------------------------------
    # NPE Helper Methods
    # -------------------------------------------------------------------------

    def record_npe_request(
        self,
        request_id: str,
        domain: str,
        candidate_type: str,
        seed: int = 0,
        budgets: Optional[Dict[str, Any]] = None,
        inputs: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record NPE request information on this receipt.

        Args:
            request_id: Unique identifier for the NPE request
            domain: NPE domain (e.g., "gr" for governance/repair)
            candidate_type: Type of candidates requested
            seed: Deterministic seed for reproducibility
            budgets: Budget constraints used
            inputs: Input data sent to NPE
        """
        self.npe_request_id = request_id
        # Store request details in metadata for provenance
        npe_request_data = {
            "domain": domain,
            "candidate_type": candidate_type,
            "seed": seed,
            "budgets": budgets or {},
            "inputs": inputs or {},
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.metadata["npe_request"] = npe_request_data

    def record_npe_response(
        self,
        status: str,
        proposals: Optional[List[Dict[str, Any]]] = None,
        budget_used: Optional[Dict[str, Any]] = None,
        npe_version: str = "1.0.0",
    ) -> None:
        """
        Record NPE response information on this receipt.

        Args:
            status: Response status (success, partial, error, timeout, invalid)
            proposals: List of proposals received from NPE
            budget_used: Actual budget consumed
            npe_version: Version of NPE that processed the request
        """
        self.npe_response_status = status
        self.npe_proposals = proposals or []
        # Store response metadata
        response_data = {
            "status": status,
            "proposal_count": len(self.npe_proposals),
            "budget_used": budget_used or {},
            "npe_version": npe_version,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.metadata["npe_response"] = response_data

    def record_npe_provenance(
        self,
        episode_id: Optional[str] = None,
        phase: Optional[str] = None,
        npe_request_id: Optional[str] = None,
        npe_response_id: Optional[str] = None,
    ) -> None:
        """
        Record NPE-specific provenance data.

        Args:
            episode_id: Episode identifier
            phase: Phase when NPE was invoked
            npe_request_id: Reference to NPE request ID
            npe_response_id: Reference to NPE response ID
        """
        self.npe_provenance = {
            "source": "npe",
            "episode_id": episode_id,
            "phase": phase,
            "npe_request_id": npe_request_id or self.npe_request_id,
            "npe_response_id": npe_response_id,
        }
        # Update provenance if not already set
        if episode_id and not self.provenance.episode_id:
            self.provenance.episode_id = episode_id
        if phase and not self.provenance.phase:
            self.provenance.phase = phase

    def get_npe_metadata(self) -> Dict[str, Any]:
        """
        Get NPE-related metadata from this receipt.

        Returns:
            Dictionary containing all NPE-related data
        """
        return {
            "has_npe_data": self.npe_request_id is not None or self.npe_proposals,
            "request_id": self.npe_request_id,
            "response_status": self.npe_response_status,
            "proposal_count": len(self.npe_proposals),
            "proposals": self.npe_proposals,
            "provenance": self.npe_provenance,
            "request_details": self.metadata.get("npe_request", {}),
            "response_details": self.metadata.get("npe_response", {}),
        }

    def has_npe_data(self) -> bool:
        """
        Check if this receipt contains NPE data.

        Returns:
            True if NPE data is present
        """
        return self.npe_request_id is not None or bool(self.npe_proposals)

    # -------------------------------------------------------------------------
    # Taint/Provenance Enforcement (E2)
    # -------------------------------------------------------------------------

    def set_taint_class(self, taint: str) -> None:
        """
        Set the taint class for this receipt.

        Args:
            taint: Taint class ("observed", "inferred", "proposed", "external", "user_claim")

        Raises:
            ValueError: If taint class is not recognized
        """
        valid_taints = {"observed", "inferred", "proposed", "external", "user_claim"}
        if taint not in valid_taints:
            raise ValueError(f"Invalid taint class: {taint}. Valid: {valid_taints}")
        self.taint_class = taint

    def requires_gate_approval(self) -> bool:
        """
        Check if this receipt requires gate approval before mutating memory.

        Returns:
            True if gate approval is required
        """
        return self.gate_approval_required

    def set_gate_approval(self, approved: bool) -> None:
        """
        Set gate approval status.

        Args:
            approved: Whether gate approved this receipt
        """
        self.gate_approved = approved

    def can_mutate_memory(self) -> bool:
        """
        Check if this receipt can mutate memory.
        Memory mutation requires: no taint, or gate approval.

        Returns:
            True if memory mutation is allowed
        """
        # "observed" is the default (safe) taint class
        # Other taint classes require gate approval
        if self.taint_class == "observed":
            return True
        return self.gate_approved

    def set_provenance_chain(self, chain_id: str) -> None:
        """
        Set the provenance chain ID.

        Args:
            chain_id: Unique provenance chain identifier
        """
        self.provenance_chain_id = chain_id

    def record_artifact_hashes(
        self,
        registry_hash: Optional[str] = None,
        corpus_snapshot_hash: Optional[str] = None,
        schema_bundle_hash: Optional[str] = None,
    ) -> None:
        """
        Record artifact hashes for replay safety (E1).

        Args:
            registry_hash: Hash of the registry manifest
            corpus_snapshot_hash: Hash of the corpus snapshot
            schema_bundle_hash: Hash of the schema bundle
        """
        if registry_hash:
            self.registry_hash = registry_hash
        if corpus_snapshot_hash:
            self.corpus_snapshot_hash = corpus_snapshot_hash
        if schema_bundle_hash:
            self.schema_bundle_hash = schema_bundle_hash

    def verify_artifact_hashes(
        self,
        expected_registry_hash: Optional[str] = None,
        expected_corpus_hash: Optional[str] = None,
        expected_schema_hash: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Verify artifact hashes match expected values.
        Used for replay safety - fail-fast if hashes differ.

        Args:
            expected_registry_hash: Expected registry hash
            expected_corpus_hash: Expected corpus snapshot hash
            expected_schema_hash: Expected schema bundle hash

        Returns:
            Tuple of (match, message)
        """
        if expected_registry_hash and self.registry_hash:
            if self.registry_hash != expected_registry_hash:
                return (
                    False,
                    f"Registry hash mismatch: expected {expected_registry_hash[:16]}..., got {self.registry_hash[:16]}...",
                )

        if expected_corpus_hash and self.corpus_snapshot_hash:
            if self.corpus_snapshot_hash != expected_corpus_hash:
                return (
                    False,
                    f"Corpus hash mismatch: expected {expected_corpus_hash[:16]}..., got {self.corpus_snapshot_hash[:16]}...",
                )

        if expected_schema_hash and self.schema_bundle_hash:
            if self.schema_bundle_hash != expected_schema_hash:
                return (
                    False,
                    f"Schema hash mismatch: expected {expected_schema_hash[:16]}..., got {self.schema_bundle_hash[:16]}...",
                )

        return True, "All artifact hashes match"


class NPEReceipt(Receipt):
    """
    Receipt with explicit NPE tracking.

    This subclass provides a convenient way to create receipts that
    are known to contain NPE-related data. It provides enhanced
    type hints and convenience methods for NPE workflows.

    Note: The base Receipt class already supports all NPE fields,
    so this is primarily a convenience class for documentation
    and type checking purposes.
    """

    # NPE-specific fields with type hints
    npe_request_id: str
    npe_response_status: str
    npe_proposals: List[Dict[str, Any]]
    npe_provenance: Dict[str, Any]

    @classmethod
    def create_npe_receipt(
        cls,
        receipt_id: str,
        request_id: str,
        domain: str,
        candidate_type: str,
        proposals: List[Dict[str, Any]],
        response_status: str = NPEResponseStatus.SUCCESS.value,
        content: Optional[ReceiptContent] = None,
        signature: Optional[ReceiptSignature] = None,
        provenance: Optional[ReceiptProvenance] = None,
        **kwargs,
    ) -> "NPEReceipt":
        """
        Factory method to create an NPE receipt.

        Args:
            receipt_id: Unique receipt identifier
            request_id: NPE request ID
            domain: NPE domain
            candidate_type: Type of candidates
            proposals: List of proposals from NPE
            response_status: NPE response status
            content: Receipt content (auto-created if None)
            signature: Receipt signature (auto-created if None)
            provenance: Receipt provenance (auto-created if None)
            **kwargs: Additional receipt arguments

        Returns:
            Configured NPEReceipt instance
        """
        # Create default content if not provided
        if content is None:
            content = ReceiptContent(
                step_type=ReceiptStepType.CUSTOM,
                decision=ReceiptDecision.PASS,
                details={
                    "npe_domain": domain,
                    "npe_candidate_type": candidate_type,
                },
            )

        # Create default signature if not provided
        if signature is None:
            signature = ReceiptSignature(signer="npe")

        # Create default provenance if not provided
        if provenance is None:
            provenance = ReceiptProvenance(source="npe")

        # Create the receipt
        receipt = cls(
            receipt_id=receipt_id,
            content=content,
            signature=signature,
            provenance=provenance,
            npe_request_id=request_id,
            npe_response_status=response_status,
            npe_proposals=proposals,
            npe_provenance={
                "source": "npe",
                "npe_request_id": request_id,
            },
            **kwargs,
        )

        return receipt


class HashChain:
    """
    Hash Chain.

    Cryptographic hash chain for receipts.
    """

    def __init__(self, genesis_hash: Optional[str] = None):
        self.genesis_hash = genesis_hash or self._generate_genesis()
        self.chain: List[Tuple[str, datetime]] = [(self.genesis_hash, datetime.utcnow())]
        self.hash_to_index: Dict[str, int] = {self.genesis_hash: 0}

    def _generate_genesis(self) -> str:
        """Generate genesis hash."""
        data = json.dumps(
            {
                "type": "genesis",
                "timestamp": datetime.utcnow().isoformat(),
                "random": uuid4().hex,
            },
            sort_keys=True,
        )
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    def append(self, receipt: Receipt) -> int:
        """Append receipt to chain. Returns index."""
        previous_hash = self.chain[-1][0] if self.chain else None
        chain_hash = receipt.compute_chain_hash(previous_hash)

        self.chain.append((chain_hash, datetime.utcnow()))
        self.hash_to_index[chain_hash] = len(self.chain) - 1

        return len(self.chain) - 1

    def verify(self, index: int, chain_hash: str) -> bool:
        """Verify chain hash at index."""
        if 0 <= index < len(self.chain):
            return self.chain[index][0] == chain_hash
        return False

    def get_hash(self, index: int) -> Optional[str]:
        """Get hash at index."""
        if 0 <= index < len(self.chain):
            return self.chain[index][0]
        return None

    def get_length(self) -> int:
        """Get chain length (excluding genesis entry)."""
        # Subtract 1 to exclude the genesis entry
        return max(0, len(self.chain) - 1)

    def get_root(self) -> str:
        """Get chain root (genesis)."""
        return self.genesis_hash

    def get_tip(self) -> str:
        """Get chain tip (latest hash)."""
        return self.chain[-1][0] if self.chain else self.genesis_hash

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "genesis_hash": self.genesis_hash,
            "length": len(self.chain),
            "tip": self.get_tip(),
        }

    def to_graph_proof_bundle(self) -> Optional[types.ProofBundleNode]:
        """Convert HashChain to GraphGML ProofBundleNode."""
        if not GRAPHGML_AVAILABLE:
            return None
        return types.ProofBundleNode(
            bundle_id=f"proof_{self.genesis_hash[:8]}",
            proof_type="hash_chain",
            properties={
                "genesis_hash": self.genesis_hash,
                "length": len(self.chain),
                "tip": self.get_tip(),
            },
            metadata={"source": "hash_chain"},
        )


class ChainValidator:
    """
    Chain Validator.

    Validates receipt chains for integrity.
    """

    def __init__(self, signing_key: str = "default-key"):
        self.signing_key = signing_key

    def validate_receipt(self, receipt: Receipt) -> Tuple[bool, str]:
        """
        Validate single receipt.

        Returns:
            Tuple of (valid, message)
        """
        # Verify signature
        content_hash = receipt.content.compute_hash()
        if not receipt.signature.verify(content_hash, self.signing_key):
            return False, "Invalid signature"

        # Verify chain hash
        computed_chain_hash = receipt.compute_chain_hash(receipt.previous_receipt_hash)
        if receipt.chain_hash != computed_chain_hash:
            return False, "Chain hash mismatch"

        return True, "Receipt valid"

    def validate_chain(
        self,
        receipts: List[Receipt],
        expected_root: Optional[str] = None,
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validate receipt chain.

        Returns:
            Tuple of (valid, message, details)
        """
        if not receipts:
            return False, "Empty chain", {}

        details = {
            "length": len(receipts),
            "valid_count": 0,
            "invalid_count": 0,
            "chain_breaks": 0,
        }

        previous_hash = None
        for i, receipt in enumerate(receipts):
            # Validate single receipt
            valid, message = self.validate_receipt(receipt)
            if valid:
                details["valid_count"] += 1
            else:
                details["invalid_count"] += 1
                return False, f"Invalid receipt at index {i}: {message}", details

            # Check chain continuity
            if previous_hash is not None:
                if receipt.previous_receipt_hash != previous_hash:
                    details["chain_breaks"] += 1
                    return False, f"Chain break at index {i}", details

            previous_hash = receipt.chain_hash

        # Check root if provided
        if expected_root and receipts[0].previous_receipt_hash != expected_root:
            return False, "Genesis mismatch", details

        return True, "Chain valid", details

    def verify_replay(
        self,
        original: Receipt,
        replay: Receipt,
    ) -> Tuple[bool, str]:
        """
        Verify replay receipt matches original.

        Returns:
            Tuple of (match, message)
        """
        # Check step type
        if original.content.step_type != replay.content.step_type:
            return (
                False,
                f"Step type mismatch: {original.content.step_type} vs {replay.content.step_type}",
            )

        # Check decision
        if original.content.decision != replay.content.decision:
            return (
                False,
                f"Decision mismatch: {original.content.decision} vs {replay.content.decision}",
            )

        # Check output hash (should match for deterministic replay)
        if original.content.output_hash != replay.content.output_hash:
            return False, "Output hash mismatch"

        return True, "Replay matches original"


class ReceiptSystem:
    """
    Receipt System.

    Manages receipt emission and storage.
    """

    def __init__(self, signing_key: str = "default-key"):
        self.signing_key = signing_key
        self.chain = HashChain()
        self.receipts: Dict[str, Receipt] = {}
        self.receipts_by_episode: Dict[str, List[str]] = {}
        self.receipts_by_type: Dict[str, List[str]] = {}

    def emit_receipt(
        self,
        step_type: ReceiptStepType,
        source: str,
        input_data: Any,
        output_data: Any,
        decision: ReceiptDecision = ReceiptDecision.PASS,
        episode_id: Optional[str] = None,
        phase: Optional[str] = None,
        **kwargs,
    ) -> Receipt:
        """Emit new receipt."""
        # Create content
        content = ReceiptContent(
            step_type=step_type,
            input_hash=hashlib.sha256(str(input_data).encode("utf-8")).hexdigest(),
            output_hash=hashlib.sha256(str(output_data).encode("utf-8")).hexdigest(),
            decision=decision,
            **kwargs,
        )

        # Create provenance
        provenance = ReceiptProvenance(
            source=source,
            episode_id=episode_id,
            phase=phase,
        )

        # Create signature
        signature = ReceiptSignature(signer="system")
        content_hash = content.compute_hash()
        signature.sign(content_hash, self.signing_key)

        # Get previous receipt for chain
        previous_receipt = self._get_latest_receipt()
        previous_id = previous_receipt.receipt_id if previous_receipt else None
        previous_hash = previous_receipt.chain_hash if previous_receipt else None

        # Create receipt
        receipt = Receipt(
            receipt_id=str(uuid4())[:8],
            content=content,
            signature=signature,
            provenance=provenance,
            previous_receipt_id=previous_id,
            previous_receipt_hash=previous_hash,
        )

        # Compute chain hash
        receipt.chain_hash = receipt.compute_chain_hash(previous_hash)

        # Add to chain
        self.chain.append(receipt)

        # Store receipt
        self.receipts[receipt.receipt_id] = receipt

        # Index by episode
        if episode_id:
            if episode_id not in self.receipts_by_episode:
                self.receipts_by_episode[episode_id] = []
            self.receipts_by_episode[episode_id].append(receipt.receipt_id)

        # Index by type
        step_key = step_type.name
        if step_key not in self.receipts_by_type:
            self.receipts_by_type[step_key] = []
        self.receipts_by_type[step_key].append(receipt.receipt_id)

        return receipt

    def _get_latest_receipt(self) -> Optional[Receipt]:
        """Get latest receipt."""
        if self.receipts:
            latest_id = self.chain.get_tip()
            for receipt in self.receipts.values():
                if receipt.chain_hash == latest_id:
                    return receipt
        return None

    def get_receipt(self, receipt_id: str) -> Optional[Receipt]:
        """Get receipt by ID."""
        return self.receipts.get(receipt_id)

    def get_episode_receipts(self, episode_id: str) -> List[Receipt]:
        """Get all receipts for episode."""
        receipt_ids = self.receipts_by_episode.get(episode_id, [])
        return [self.receipts[rid] for rid in receipt_ids if rid in self.receipts]

    def get_receipt_chain(self, episode_id: str) -> List[Receipt]:
        """Get receipt chain for episode in order."""
        receipts = self.get_episode_receipts(episode_id)
        # Sort by chain hash to get order
        return sorted(receipts, key=lambda r: self.chain.hash_to_index.get(r.chain_hash, 0))

    def verify_episode_chain(self, episode_id: str) -> Tuple[bool, str]:
        """Verify receipt chain for episode."""
        receipts = self.get_episode_receipts(episode_id)
        if not receipts:
            return False, "No receipts for episode"

        valid, message, _ = self.validate_chain(receipts)
        return valid, message

    def validate_chain(self, receipts: List[Receipt]) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate receipt chain."""
        validator = ChainValidator(self.signing_key)
        return validator.validate_chain(receipts)

    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics."""
        return {
            "total_receipts": len(self.receipts),
            "chain_length": self.chain.get_length(),
            "episode_count": len(self.receipts_by_episode),
            "type_counts": {k: len(v) for k, v in self.receipts_by_type.items()},
        }

    def clear(self) -> None:
        """Clear all receipts."""
        self.chain = HashChain()
        self.receipts.clear()
        self.receipts_by_episode.clear()
        self.receipts_by_type.clear()

    def to_graph(self) -> Optional[core.GraphGML]:
        """Convert ReceiptSystem to GraphGML representation."""
        if not GRAPHGML_AVAILABLE:
            return None

        graph = core.GraphGML()
        commit_nodes = {}

        # First pass: create all commit nodes
        for receipt_id, receipt in self.receipts.items():
            commit_node = receipt.to_graph_commit()
            if commit_node:
                graph.add_node(commit_node)
                receipt.graph_commit_id = commit_node.node_id
                commit_nodes[receipt_id] = commit_node

        # Second pass: create requires_proof edges
        for receipt_id, receipt in self.receipts.items():
            if receipt.previous_receipt_id and receipt_id in commit_nodes:
                prev_commit_id = f"commit_{receipt.previous_receipt_id}"
                graph.add_edge(prev_commit_id, "requires_proof", commit_nodes[receipt_id].node_id)

        # Add proof bundle if exists
        proof_bundle = self.chain.to_graph_proof_bundle()
        if proof_bundle:
            graph.add_node(proof_bundle)
            for receipt_id, commit_node in commit_nodes.items():
                graph.add_edge(commit_node.node_id, "requires_proof", proof_bundle.node_id)

        return graph

    def validate_graph_invariants(self) -> List[str]:
        """Validate graph invariants for the receipt ledger."""
        issues = []
        graph = self.to_graph()
        if graph:
            issues.extend(graph.validate_invariants())

        # Additional receipt-specific validations
        for receipt_id, receipt in self.receipts.items():
            if receipt.previous_receipt_id and receipt.previous_receipt_id not in self.receipts:
                issues.append(
                    f"Receipt {receipt_id} references non-existent previous_receipt_id {receipt.previous_receipt_id}"
                )

        return issues


def create_receipt_system(signing_key: str = "default-key") -> ReceiptSystem:
    """Create new receipt system."""
    return ReceiptSystem(signing_key=signing_key)
