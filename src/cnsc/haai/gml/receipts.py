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
    def from_dict(cls, data: Dict[str, Any]) -> 'ReceiptSignature':
        """Create from dictionary."""
        return cls(
            algorithm=data.get("algorithm", "HMAC-SHA256"),
            signer=data.get("signer", "system"),
            signature=data.get("signature", ""),
        )
    
    def sign(self, data: str, key: str) -> None:
        """Sign data."""
        self.signature = hmac.new(
            key.encode('utf-8'),
            data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def verify(self, data: str, key: str) -> bool:
        """Verify signature."""
        expected = hmac.new(
            key.encode('utf-8'),
            data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
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
    def from_dict(cls, data: Dict[str, Any]) -> 'ReceiptContent':
        """Create from dictionary."""
        return cls(
            step_type=ReceiptStepType[data["step_type"]] if isinstance(data["step_type"], str) else ReceiptStepType(data["step_type"]),
            input_hash=data.get("input_hash", ""),
            output_hash=data.get("output_hash", ""),
            decision=ReceiptDecision[data["decision"]] if isinstance(data["decision"], str) else ReceiptDecision(data["decision"]),
            details=data.get("details", {}),
            coherence_before=data.get("coherence_before"),
            coherence_after=data.get("coherence_after"),
        )
    
    def compute_hash(self) -> str:
        """Compute content hash."""
        data = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(data.encode('utf-8')).hexdigest()


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
    def from_dict(cls, data: Dict[str, Any]) -> 'ReceiptProvenance':
        """Create from dictionary."""
        return cls(
            source=data["source"],
            episode_id=data.get("episode_id"),
            phase=data.get("phase"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.utcnow(),
            span=data.get("span"),
        )


@dataclass
class Receipt:
    """
    Receipt.
    
    Cryptographic record of a reasoning step.
    
    Version: 1.0.0 - See schemas/receipt.schema.json for canonical spec.
    """
    # Version field (required for schema compatibility)
    version: str = "1.0.0"
    
    # Core fields
    receipt_id: str
    content: ReceiptContent
    signature: ReceiptSignature
    provenance: ReceiptProvenance
    
    # Chain links
    previous_receipt_id: Optional[str] = None
    previous_receipt_hash: Optional[str] = None
    chain_hash: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
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
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Receipt':
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
        )
    
    def compute_hash(self) -> str:
        """Compute receipt hash for chain."""
        data = json.dumps({
            "receipt_id": self.receipt_id,
            "content": self.content.to_dict(),
            "previous_receipt_hash": self.previous_receipt_hash,
        }, sort_keys=True)
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    
    def compute_chain_hash(self, previous_chain_hash: Optional[str] = None) -> str:
        """Compute chain hash."""
        receipt_hash = self.compute_hash()
        if previous_chain_hash:
            data = json.dumps({
                "previous": previous_chain_hash,
                "current": receipt_hash,
            }, sort_keys=True)
        else:
            data = receipt_hash
        return hashlib.sha256(data.encode('utf-8')).hexdigest()


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
        data = json.dumps({
            "type": "genesis",
            "timestamp": datetime.utcnow().isoformat(),
            "random": uuid4().hex,
        }, sort_keys=True)
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    
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
        """Get chain length."""
        return len(self.chain)
    
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
            return False, f"Step type mismatch: {original.content.step_type} vs {replay.content.step_type}"
        
        # Check decision
        if original.content.decision != replay.content.decision:
            return False, f"Decision mismatch: {original.content.decision} vs {replay.content.decision}"
        
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
            input_hash=hashlib.sha256(str(input_data).encode('utf-8')).hexdigest(),
            output_hash=hashlib.sha256(str(output_data).encode('utf-8')).hexdigest(),
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


def create_receipt_system(signing_key: str = "default-key") -> ReceiptSystem:
    """Create new receipt system."""
    return ReceiptSystem(signing_key=signing_key)
