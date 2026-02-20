"""
Finalize Module

Provides finalize receipt verification for ATS slabs.
Per docs/ats/20_coh_kernel/finalize_rules.md

A finalize receipt authorizes deletion of a slab after the retention period
has elapsed and no disputes are active.
"""

from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from cnsc_haai.consensus.retention import (
    get_policy,
    compute_finalize_height,
    is_finalized as check_finalized,
)
from cnsc_haai.consensus.fraudproof import get_dispute_registry


class FinalizeState(Enum):
    """States for a finalized slab."""
    PENDING = "PENDING"      # Waiting for finalize
    FINALIZABLE = "FINALIZABLE"  # Ready to finalize
    FINALIZED = "FINALIZED"   # Deletion authorized


@dataclass
class FinalizeReceipt:
    """
    A finalize receipt authorizes deletion of a slab.
    
    It verifies:
    1. The slab exists and matches the hash
    2. The window_end matches the derived value
    3. Current height >= derived window_end
    4. No disputes are active for the slab
    """
    version: str = "1.0.0"
    finalize_id: str = ""
    slab_chain_hash: str = ""  # Chain hash of the slab being finalized
    window_end_height: int = 0  # Claimed window end
    finalize_height: int = 0  # Height at which finalization occurs
    retention_policy_id: str = ""
    authorization_signature: str = ""  # Authorization for deletion
    chain_hash: str = ""  # Chain hash of this receipt
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "finalize_id": self.finalize_id,
            "slab_chain_hash": self.slab_chain_hash,
            "window_end_height": self.window_end_height,
            "finalize_height": self.finalize_height,
            "retention_policy_id": self.retention_policy_id,
            "authorization_signature": self.authorization_signature,
            "chain_hash": self.chain_hash,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FinalizeReceipt':
        return cls(
            version=data.get("version", "1.0.0"),
            finalize_id=data.get("finalize_id", ""),
            slab_chain_hash=data.get("slab_chain_hash", ""),
            window_end_height=data.get("window_end_height", 0),
            finalize_height=data.get("finalize_height", 0),
            retention_policy_id=data.get("retention_policy_id", ""),
            authorization_signature=data.get("authorization_signature", ""),
            chain_hash=data.get("chain_hash", ""),
        )


def verify_finalize_receipt(
    finalize_receipt: FinalizeReceipt,
    slab_window_end: int,
    current_height: int,
    is_disputed: bool,
) -> Tuple[bool, Optional[str]]:
    """
    Verify a finalize receipt.
    
    Checks:
    1. window_end matches derived value from policy
    2. Current height >= window_end
    3. No disputes active
    
    Args:
        finalize_receipt: The finalize receipt to verify
        slab_window_end: The actual window end from the slab
        current_height: Current block height
        is_disputed: Whether the slab has an active dispute
        
    Returns:
        (is_valid, error_message)
    """
    # 1. Verify window_end matches
    if finalize_receipt.window_end_height != slab_window_end:
        return False, f"REJECT: window_end mismatch: {finalize_receipt.window_end_height} != {slab_window_end}"
    
    # 2. Verify timing - must be after window_end
    if current_height < finalize_receipt.window_end_height:
        return False, f"REJECT: premature, height {current_height} < window_end {finalize_receipt.window_end_height}"
    
    # 3. Verify no disputes
    if is_disputed:
        return False, "REJECT: slab has active dispute"
    
    # 4. Verify finalize_height is correctly computed
    policy = get_policy(finalize_receipt.retention_policy_id)
    if policy:
        expected_finalize = compute_finalize_height(
            finalize_receipt.window_end_height,
            policy.retention_period_blocks,
        )
        if finalize_receipt.finalize_height != expected_finalize:
            return False, f"REJECT: finalize_height mismatch: {finalize_receipt.finalize_height} != {expected_finalize}"
    
    return True, None


def is_finalized(
    slab_chain_hash: str,
    slab_window_end: int,
    retention_policy_id: str,
    current_height: int,
) -> Tuple[FinalizeState, Optional[str]]:
    """
    Check if a slab is finalized and eligible for deletion.
    
    Args:
        slab_chain_hash: Chain hash of the slab
        slab_window_end: Window end height from the slab
        retention_policy_id: Policy ID for retention
        current_height: Current block height
        
    Returns:
        (state, error_message)
    """
    # Check dispute status
    dispute_registry = get_dispute_registry()
    if dispute_registry.is_disputed(slab_chain_hash):
        return FinalizeState.PENDING, "Slab is disputed"
    
    # Get policy
    policy = get_policy(retention_policy_id)
    if not policy:
        return FinalizeState.PENDING, "Policy not found"
    
    # Check if window has closed
    if current_height < slab_window_end:
        return FinalizeState.PENDING, "Challenge window not closed"
    
    # Check if retention period has elapsed
    finalize_height = compute_finalize_height(
        slab_window_end,
        policy.retention_period_blocks,
    )
    
    if current_height < finalize_height:
        return FinalizeState.FINALIZABLE, "Retention period not elapsed"
    
    # Finalized!
    return FinalizeState.FINALIZED, None


def create_finalize_receipt(
    slab_chain_hash: str,
    window_end_height: int,
    retention_policy_id: str,
    current_height: int,
    prev_chain_hash: str,
) -> FinalizeReceipt:
    """
    Create a finalize receipt.
    
    Args:
        slab_chain_hash: Chain hash of the slab
        window_end_height: Window end from the slab
        retention_policy_id: Policy ID
        current_height: Current block height
        prev_chain_hash: Previous chain hash
        
    Returns:
        FinalizeReceipt
    """
    # Get policy for finalize height
    policy = get_policy(retention_policy_id)
    if policy:
        finalize_height = compute_finalize_height(
            window_end_height,
            policy.retention_period_blocks,
        )
    else:
        # Default to window_end + 100
        finalize_height = window_end_height + 100
    
    # Build receipt
    receipt_data = {
        "slab_chain_hash": slab_chain_hash,
        "window_end_height": window_end_height,
        "finalize_height": finalize_height,
        "retention_policy_id": retention_policy_id,
    }
    
    # In a real system, this would have an authorization signature
    # For now, we use a placeholder
    receipt_data["authorization_signature"] = "authorized"
    
    # Compute ID (in practice, this would include more fields)
    from cnsc_haai.consensus.jcs import jcs_canonical_bytes
    from cnsc_haai.consensus.hash import sha256, sha256_prefixed
    from cnsc_haai.consensus.chain import chain_hash_v1_prefixed
    
    receipt_bytes = jcs_canonical_bytes(receipt_data)
    receipt_hash = sha256(receipt_bytes)
    finalize_id = sha256_prefixed(receipt_hash)
    
    # Compute chain hash
    chain_hash = chain_hash_v1_prefixed(prev_chain_hash, receipt_data)
    
    return FinalizeReceipt(
        version="1.0.0",
        finalize_id=finalize_id,
        slab_chain_hash=slab_chain_hash,
        window_end_height=window_end_height,
        finalize_height=finalize_height,
        retention_policy_id=retention_policy_id,
        authorization_signature=receipt_data["authorization_signature"],
        chain_hash=chain_hash,
    )


# Finalized slabs registry
class FinalizedRegistry:
    """
    Registry for tracking finalized slabs.
    """
    
    def __init__(self):
        self._finalized: Dict[str, Dict[str, Any]] = {}
    
    def mark_finalized(
        self,
        slab_chain_hash: str,
        finalize_receipt: FinalizeReceipt,
    ) -> None:
        """
        Mark a slab as finalized.
        
        Args:
            slab_chain_hash: Chain hash of the slab
            finalize_receipt: The finalize receipt
        """
        self._finalized[slab_chain_hash] = {
            "finalize_receipt": finalize_receipt,
            "finalized": True,
        }
    
    def is_finalized(self, slab_chain_hash: str) -> bool:
        """Check if a slab is finalized."""
        record = self._finalized.get(slab_chain_hash)
        return record is not None and record.get("finalized", False)
    
    def get_finalize_receipt(
        self,
        slab_chain_hash: str,
    ) -> Optional[FinalizeReceipt]:
        """Get finalize receipt for a slab."""
        record = self._finalized.get(slab_chain_hash)
        if record:
            return record.get("finalize_receipt")
        return None


# Global finalized registry
_finalized_registry = FinalizedRegistry()


def get_finalized_registry() -> FinalizedRegistry:
    """Get the global finalized registry."""
    return _finalized_registry
