"""
Slab FSM and Verifier State

Provides the certified forgetting FSM for slab receipts:
- On STEP_SLAB: record slab_accept_height
- On STEP_FRAUD_PROOF: set DISPUTED flag
- On STEP_FINALIZE: verify window_end, verify !disputed, authorize deletion
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, List
from datetime import datetime


class SlabState(Enum):
    """Slab lifecycle states."""
    PENDING = "PENDING"        # Created, waiting for window
    ACTIVE = "ACTIVE"          # Within retention window
    DISPUTED = "DISPUTED"      # Fraud proof raised
    FINALIZABLE = "FINALIZABLE" # Retention period complete, can finalize
    FINALIZED = "FINALIZED"    # Deletion authorized
    DELETED = "DELETED"        # Actually deleted


class DisputeStatus(Enum):
    """Dispute status for a slab."""
    CLEAN = "CLEAN"            # No disputes
    DISPUTED = "DISPUTED"      # Active dispute
    RESOLVED = "RESOLVED"      # Dispute resolved


@dataclass
class SlabVerifierState:
    """
    Verifier state for a slab receipt.
    
    Tracks the complete lifecycle of a slab including:
    - Slab acceptance height
    - Dispute status
    - Finalization authorization
    
    State Machine:
        PENDING → ACTIVE → DISPUTED (on fraud proof)
                   ACTIVE → FINALIZABLE (after retention)
                   FINALIZABLE → FINALIZED (after verify)
                   FINALIZED → DELETED (after deletion)
    """
    
    # Identity
    slab_receipt_hash: str  # sha256: prefixed
    slab_id: str
    
    # Timing
    slab_accept_height: int = 0
    window_start: int = 0
    window_end: int = 0
    
    # State
    state: SlabState = SlabState.PENDING
    dispute_status: DisputeStatus = DisputeStatus.CLEAN
    
    # Dispute tracking
    fraudproof_chain_hash: Optional[str] = None
    fraudproof_height: Optional[int] = None
    
    # Finalization
    finalize_height: Optional[int] = None
    deletion_authorized: bool = False
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def step_slab(self, window_start: int, window_end: int, current_height: int) -> bool:
        """
        Handle STEP_SLAB: Record slab acceptance.
        
        Args:
            window_start: Starting block height
            window_end: Ending block height
            current_height: Current block height
            
        Returns:
            True if successful
        """
        self.window_start = window_start
        self.window_end = window_end
        self.slab_accept_height = current_height
        
        if current_height >= window_start:
            self.state = SlabState.ACTIVE
        else:
            self.state = SlabState.PENDING
        
        self.updated_at = datetime.utcnow()
        return True
    
    def step_fraud_proof(self, fraudproof_chain_hash: str, current_height: int) -> bool:
        """
        Handle STEP_FRAUD_PROOF: Set disputed flag.
        
        Args:
            fraudproof_chain_hash: Chain hash of fraud proof receipt
            current_height: Current block height
            
        Returns:
            True if successful
        """
        if self.state in (SlabState.FINALIZED, SlabState.DELETED):
            return False  # Cannot dispute finalized/deleted slab
        
        self.dispute_status = DisputeStatus.DISPUTED
        self.state = SlabState.DISPUTED
        self.fraudproof_chain_hash = fraudproof_chain_hash
        self.fraudproof_height = current_height
        self.updated_at = datetime.utcnow()
        return True
    
    def check_finalizable(self, current_height: int, retention_period: int) -> bool:
        """
        Check if slab is eligible for finalization.
        
        Args:
            current_height: Current block height
            retention_period: Required retention period in blocks
            
        Returns:
            True if finalizable
        """
        if self.dispute_status == DisputeStatus.DISPUTED:
            return False
        
        if self.state in (SlabState.FINALIZED, SlabState.DELETED):
            return False
        
        # Check retention period elapsed
        if current_height < self.window_end + retention_period:
            return False
        
        self.state = SlabState.FINALIZABLE
        return True
    
    def step_finalize(
        self,
        claimed_window_end: int,
        current_height: int,
        min_budget: int,
        current_budget: int
    ) -> tuple[bool, str]:
        """
        Handle STEP_FINALIZE: Authorize deletion.
        
        Args:
            claimed_window_end: Window end height from finalize receipt
            current_height: Current block height
            min_budget: Minimum required budget
            current_budget: Current budget
            
        Returns:
            (authorized, reason)
        """
        # Check window end matches
        if claimed_window_end != self.window_end:
            return False, f"REJECT: window_end mismatch: {claimed_window_end} != {self.window_end}"
        
        # Check for disputes
        if self.dispute_status == DisputeStatus.DISPUTED:
            return False, "REJECT: slab has active dispute"
        
        # Check budget
        if current_budget < min_budget:
            return False, f"REJECT: budget {current_budget} < min {min_budget}"
        
        # Check timing
        if current_height < self.window_end:
            return False, f"REJECT: premature, height {current_height} < window_end {self.window_end}"
        
        # Authorize deletion
        self.state = SlabState.FINALIZED
        self.finalize_height = current_height
        self.deletion_authorized = True
        self.updated_at = datetime.utcnow()
        
        return True, "AUTHORIZED"
    
    def can_delete(self) -> bool:
        """Check if slab can be deleted."""
        return (
            self.state == SlabState.FINALIZED and
            self.deletion_authorized and
            self.dispute_status != DisputeStatus.DISPUTED
        )
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "slab_receipt_hash": self.slab_receipt_hash,
            "slab_id": self.slab_id,
            "slab_accept_height": self.slab_accept_height,
            "window_start": self.window_start,
            "window_end": self.window_end,
            "state": self.state.value,
            "dispute_status": self.dispute_status.value,
            "fraudproof_chain_hash": self.fraudproof_chain_hash,
            "finalize_height": self.finalize_height,
            "deletion_authorized": self.deletion_authorized,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class SlabRegistry:
    """
    Registry for tracking all slab states.
    
    Maps slab_receipt_hash -> SlabVerifierState
    """
    
    def __init__(self):
        """Initialize the slab registry."""
        self._slabs: Dict[str, SlabVerifierState] = {}
    
    def register_slab(
        self,
        slab_receipt_hash: str,
        slab_id: str,
        window_start: int,
        window_end: int,
        current_height: int
    ) -> SlabVerifierState:
        """
        Register a new slab.
        
        Args:
            slab_receipt_hash: Hash of slab receipt
            slab_id: Slab identifier
            window_start: Starting block height
            window_end: Ending block height
            current_height: Current block height
            
        Returns:
            Created SlabVerifierState
        """
        state = SlabVerifierState(
            slab_receipt_hash=slab_receipt_hash,
            slab_id=slab_id,
        )
        state.step_slab(window_start, window_end, current_height)
        self._slabs[slab_receipt_hash] = state
        return state
    
    def get(self, slab_receipt_hash: str) -> Optional[SlabVerifierState]:
        """Get slab state by hash."""
        return self._slabs.get(slab_receipt_hash)
    
    def get_by_id(self, slab_id: str) -> Optional[SlabVerifierState]:
        """Get slab state by ID."""
        for state in self._slabs.values():
            if state.slab_id == slab_id:
                return state
        return None
    
    def all_slab_hashes(self) -> List[str]:
        """Get all registered slab hashes."""
        return list(self._slabs.keys())
    
    def get_deletable(self) -> List[SlabVerifierState]:
        """Get all slabs eligible for deletion."""
        return [s for s in self._slabs.values() if s.can_delete()]
    
    def get_disputed(self) -> List[SlabVerifierState]:
        """Get all disputed slabs."""
        return [s for s in self._slabs.values() if s.dispute_status == DisputeStatus.DISPUTED]
    
    def count(self) -> int:
        """Get total slab count."""
        return len(self._slabs)
