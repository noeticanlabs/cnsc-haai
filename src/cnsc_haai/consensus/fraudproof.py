"""
Fraud Proof Module

Provides fraud proof verification for ATS slabs.
Per docs/ats/20_coh_kernel/fraud_proof_rules.md

A fraud proof demonstrates that a slab contains an invalid micro receipt,
allowing anyone to challenge the slab during the dispute window.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from cnsc_haai.consensus.jcs import jcs_canonical_bytes
from cnsc_haai.consensus.hash import sha256, sha256_prefixed, decode_sha256_prefixed
from cnsc_haai.consensus.merkle import verify_inclusion_proof


class ViolationType(Enum):
    """Types of violations a fraud proof can demonstrate."""
    V_MAX_UNDERREPORTED = "V_MAX_UNDERREPORTED"  # Max risk was higher than claimed
    M_MAX_UNDERREPORTED = "M_MAX_UNDERREPORTED"  # Max memory was higher than claimed
    BUDGET_UNDERREPORTED = "BUDGET_UNDERREPORTED"  # Budget end was wrong
    INVALID_STATE_TRANSITION = "INVALID_STATE_TRANSITION"  # State transition invalid
    INVALID_RECEIPT = "INVALID_RECEIPT"  # Receipt itself is invalid


@dataclass
class DirectedPathStep:
    """
    A single step in a directed Merkle proof path.
    
    Each step indicates whether the hash being verified is the left or right
    child at that level of the tree.
    """
    side: str  # "L" for left, "R" for right
    hash: str  # sha256: prefixed hash of the sibling
    
    def to_dict(self) -> Dict[str, Any]:
        return {"side": self.side, "hash": self.hash}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DirectedPathStep':
        return cls(side=data["side"], hash=data["hash"])


@dataclass
class FraudProof:
    """
    A fraud proof demonstrating an invalid micro receipt in a slab.
    """
    version: str = "1.0.0"
    fraud_proof_id: str = ""
    slab_chain_hash: str = ""  # Chain hash of the disputed slab
    micro_receipt_index: int = 0  # Index of the disputed receipt in slab
    micro_receipt: Dict[str, Any] = {}  # The disputed receipt
    violation_type: str = ""  # Type of violation
    violation_details: Dict[str, Any] = {}  # Details of the violation
    directed_path: List[Dict[str, Any]] = field(default_factory=list)  # Merkle proof
    merkle_root: str = ""  # Expected merkle root
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "fraud_proof_id": self.fraud_proof_id,
            "slab_chain_hash": self.slab_chain_hash,
            "micro_receipt_index": self.micro_receipt_index,
            "micro_receipt": self.micro_receipt,
            "violation_type": self.violation_type,
            "violation_details": self.violation_details,
            "directed_path": self.directed_path,
            "merkle_root": self.merkle_root,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FraudProof':
        return cls(
            version=data.get("version", "1.0.0"),
            fraud_proof_id=data.get("fraud_proof_id", ""),
            slab_chain_hash=data.get("slab_chain_hash", ""),
            micro_receipt_index=data.get("micro_receipt_index", 0),
            micro_receipt=data.get("micro_receipt", {}),
            violation_type=data.get("violation_type", ""),
            violation_details=data.get("violation_details", {}),
            directed_path=data.get("directed_path", []),
            merkle_root=data.get("merkle_root", ""),
        )


def verify_fraud_proof(
    fraud_proof: FraudProof,
    slab_merkle_root: str,
) -> Tuple[bool, Optional[str]]:
    """
    Verify a fraud proof.
    
    Checks:
    1. Merkle proof is valid (directed path to root)
    2. Violation is correctly identified
    
    Args:
        fraud_proof: The fraud proof to verify
        slab_merkle_root: The merkle root of the disputed slab
        
    Returns:
        (is_valid, error_message)
    """
    # 1. Verify Merkle proof
    # Compute leaf hash from the disputed micro receipt
    receipt_bytes = jcs_canonical_bytes(fraud_proof.micro_receipt)
    leaf_hash = sha256(receipt_bytes)
    
    # Build path for verification
    path = []
    for step_dict in fraud_proof.directed_path:
        step = DirectedPathStep.from_dict(step_dict)
        sibling_hash = decode_sha256_prefixed(step.hash)
        path.append((step.side, sibling_hash))
    
    # Verify the proof
    root_bytes = decode_sha256_prefixed(slab_merkle_root)
    if not verify_inclusion_proof(leaf_hash, path, root_bytes):
        return False, "INVALID_MERKLE_PROOF: Leaf not in tree"
    
    # 2. Verify violation type
    violation_valid, violation_msg = _verify_violation(
        fraud_proof.violation_type,
        fraud_proof.violation_details,
        fraud_proof.micro_receipt,
    )
    
    if not violation_valid:
        return False, f"INVALID_VIOLATION: {violation_msg}"
    
    return True, None


def _verify_violation(
    violation_type: str,
    violation_details: Dict[str, Any],
    micro_receipt: Dict[str, Any],
) -> Tuple[bool, Optional[str]]:
    """
    Verify the violation details.
    
    Args:
        violation_type: Type of violation
        violation_details: Details of the violation
        micro_receipt: The disputed micro receipt
        
    Returns:
        (is_valid, error_message)
    """
    if violation_type == ViolationType.V_MAX_UNDERREPORTED.value:
        # Check that risk was higher than claimed
        claimed_max = violation_details.get("claimed_V_max_q", 0)
        actual_risk = micro_receipt.get("risk_after_q", 0)
        if actual_risk <= claimed_max:
            return False, f"V_max not underreported: {actual_risk} <= {claimed_max}"
    
    elif violation_type == ViolationType.M_MAX_UNDERREPORTED.value:
        # Check that memory was higher than claimed
        claimed_max = violation_details.get("claimed_M_max_int", 0)
        actual_memory = micro_receipt.get("memory_used", 0)
        if actual_memory <= claimed_max:
            return False, f"M_max not underreported: {actual_memory} <= {claimed_max}"
    
    elif violation_type == ViolationType.BUDGET_UNDERREPORTED.value:
        # Check that budget end was wrong
        claimed_end = violation_details.get("claimed_B_end_q", 0)
        actual_end = micro_receipt.get("budget_after_q", 0)
        if actual_end <= claimed_end:
            return False, f"Budget not underreported: {actual_end} <= {claimed_end}"
    
    elif violation_type == ViolationType.INVALID_STATE_TRANSITION.value:
        # Verify state transition is invalid
        # This requires recomputing the state hash
        state_before = micro_receipt.get("state_hash_before", "")
        state_after = micro_receipt.get("state_hash_after", "")
        
        # Check if the transition makes sense
        # (This is a simplified check - real verification would recompute)
        if not state_before or not state_after:
            return False, "Missing state hashes"
    
    elif violation_type == ViolationType.INVALID_RECEIPT.value:
        # Receipt itself is malformed
        # Check required fields
        required = ["receipt_id", "state_hash_before", "state_hash_after", "action"]
        for field in required:
            if field not in micro_receipt:
                return False, f"Missing required field: {field}"
    
    else:
        return False, f"Unknown violation type: {violation_type}"
    
    return True, None


def create_fraud_proof(
    slab_chain_hash: str,
    micro_receipt_index: int,
    micro_receipt: Dict[str, Any],
    violation_type: ViolationType,
    violation_details: Dict[str, Any],
    directed_path: List[DirectedPathStep],
    merkle_root: str,
) -> FraudProof:
    """
    Create a fraud proof.
    
    Args:
        slab_chain_hash: Chain hash of the disputed slab
        micro_receipt_index: Index of the disputed receipt
        micro_receipt: The disputed micro receipt
        violation_type: Type of violation
        violation_details: Details of the violation
        directed_path: Directed Merkle proof path
        merkle_root: Expected merkle root
        
    Returns:
        FraudProof
    """
    fraud_proof = FraudProof(
        version="1.0.0",
        slab_chain_hash=slab_chain_hash,
        micro_receipt_index=micro_receipt_index,
        micro_receipt=micro_receipt,
        violation_type=violation_type.value,
        violation_details=violation_details,
        directed_path=[step.to_dict() for step in directed_path],
        merkle_root=merkle_root,
    )
    
    # Compute fraud proof ID (single hash, no double-hash)
    proof_bytes = jcs_canonical_bytes(fraud_proof.to_dict())
    proof_id = sha256_prefixed(proof_bytes)
    fraud_proof.fraud_proof_id = proof_id
    
    return fraud_proof


# Dispute registry for tracking disputed slabs
class DisputeRegistry:
    """
    Registry for tracking disputed slabs.
    """
    
    def __init__(self):
        self._disputes: Dict[str, Dict[str, Any]] = {}
    
    def register_dispute(
        self,
        slab_chain_hash: str,
        fraud_proof: FraudProof,
        winning_chain_hash: str,
    ) -> None:
        """
        Register a dispute.
        
        Args:
            slab_chain_hash: Chain hash of the disputed slab
            fraud_proof: The fraud proof
            winning_chain_hash: Chain hash of the winning (disputed) proof
        """
        self._disputes[slab_chain_hash] = {
            "fraud_proof": fraud_proof,
            "winning_chain_hash": winning_chain_hash,
            "disputed": True,
        }
    
    def is_disputed(self, slab_chain_hash: str) -> bool:
        """Check if a slab is disputed."""
        dispute = self._disputes.get(slab_chain_hash)
        return dispute is not None and dispute.get("disputed", False)
    
    def get_dispute(self, slab_chain_hash: str) -> Optional[Dict[str, Any]]:
        """Get dispute info."""
        return self._disputes.get(slab_chain_hash)
    
    def reject_already_disputed(
        self,
        slab_chain_hash: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if a slab is already disputed and reject if so.
        
        Args:
            slab_chain_hash: Chain hash of the slab
            
        Returns:
            (is_allowed, error_message)
        """
        if self.is_disputed(slab_chain_hash):
            return False, "REJECT_ALREADY_DISPUTED"
        return True, None


# Global dispute registry
_dispute_registry = DisputeRegistry()


def get_dispute_registry() -> DisputeRegistry:
    """Get the global dispute registry."""
    return _dispute_registry
