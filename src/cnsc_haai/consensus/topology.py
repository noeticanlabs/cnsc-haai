"""
Topology Module

Provides topology jump engine for Atlas (cognitive state graph) changes.
Per docs/ats/10_mathematical_core/topology_change_budget.md

Handles expansion, pruning, and restructuring of the Atlas with budget constraints.
"""

from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum

from cnsc_haai.consensus.jcs import jcs_canonical_bytes
from cnsc_haai.consensus.hash import sha256, sha256_prefixed
from cnsc_haai.consensus.chain import chain_hash_v1_prefixed


class TopologyChangeType(Enum):
    """Types of topology changes."""
    EXPAND = "EXPAND"      # Adding nodes
    PRUNE = "PRUNE"        # Removing nodes
    RESTRUCTURE = "RESTRUCTURE"  # Changing connectivity only


@dataclass
class TopologyState:
    """
    Represents the topology of an Atlas.
    """
    atlas_hash: str
    rank: int  # Number of nodes
    edge_count: int
    connectivity_matrix_hash: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "atlas_hash": self.atlas_hash,
            "rank": self.rank,
            "edge_count": self.edge_count,
            "connectivity_matrix_hash": self.connectivity_matrix_hash,
        }


@dataclass
class TopologyJumpReceipt:
    """
    Receipt for a topology change (jump).
    """
    version: str = "1.0.0"
    receipt_id: str = ""
    A_prev_hash: str = ""
    A_next_hash: str = ""
    delta_struct: int = 0
    budget_deduction: int = 0
    distortion_bound: int = 0
    spectral_signature_claim: str = ""
    transport_distortion_bound: int = 0
    hysteresis_verified: bool = False
    slab_boundary_verified: bool = False
    chain_hash: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "receipt_id": self.receipt_id,
            "A_prev_hash": self.A_prev_hash,
            "A_next_hash": self.A_next_hash,
            "delta_struct": self.delta_struct,
            "budget_deduction": str(self.budget_deduction),
            "distortion_bound": str(self.distortion_bound),
            "spectral_signature_claim": self.spectral_signature_claim,
            "transport_distortion_bound": str(self.transport_distortion_bound),
            "hysteresis_verified": self.hysteresis_verified,
            "slab_boundary_verified": self.slab_boundary_verified,
            "chain_hash": self.chain_hash,
        }


# Constants
HYSTERESIS_THRESHOLD = 1  # Minimum nodes to change
SLAB_SIZE = 1000  # Blocks per slab


def compute_rank(atlas: Dict[str, Any]) -> int:
    """
    Compute the rank (number of nodes) of an atlas.
    
    Args:
        atlas: Atlas dictionary with nodes
        
    Returns:
        Number of nodes
    """
    if "nodes" in atlas:
        return len(atlas["nodes"])
    return 0


def compute_delta_struct(prev_atlas: Dict[str, Any], next_atlas: Dict[str, Any]) -> int:
    """
    Compute structural change between two atlas states.
    
    Args:
        prev_atlas: Previous atlas state
        next_atlas: Next atlas state
        
    Returns:
        Delta in rank (positive = expansion, negative = pruning)
    """
    prev_rank = compute_rank(prev_atlas)
    next_rank = compute_rank(next_atlas)
    return next_rank - prev_rank


def compute_atlas_hash(atlas: Dict[str, Any]) -> str:
    """
    Compute hash of atlas state.
    
    Args:
        atlas: Atlas dictionary
        
    Returns:
        sha256: prefixed hash
    """
    atlas_bytes = jcs_canonical_bytes(atlas)
    atlas_hash = sha256(atlas_bytes)
    return sha256_prefixed(atlas_hash)


def check_hysteresis(delta_struct: int, threshold: int = HYSTERESIS_THRESHOLD) -> bool:
    """
    Check if change exceeds hysteresis threshold.
    
    Args:
        delta_struct: Structural change
        threshold: Minimum threshold
        
    Returns:
        True if hysteresis satisfied
    """
    return abs(delta_struct) >= threshold


def check_slab_boundary(current_height: int, slab_size: int = SLAB_SIZE) -> bool:
    """
    Check if current height is at a slab boundary.
    
    Args:
        current_height: Current block height
        slab_size: Size of each slab
        
    Returns:
        True if at slab boundary
    """
    return current_height % slab_size == 0


def check_budget_gate(budget_q: int, delta_struct: int) -> Tuple[bool, int]:
    """
    Check budget gate for topology change.
    
    For expansion: deduct budget equal to delta_struct
    For pruning: no deduction (but check distortion)
    
    Args:
        budget_q: Current budget (QFixed)
        delta_struct: Structural change
        
    Returns:
        (allowed, deduction)
    """
    if delta_struct > 0:
        # Expansion: need budget >= delta_struct
        if budget_q >= delta_struct:
            return True, delta_struct
        else:
            return False, 0
    else:
        # Pruning: always allowed (but check distortion separately)
        return True, 0


def compute_distortion_bound(
    prev_atlas: Dict[str, Any],
    next_atlas: Dict[str, Any],
) -> int:
    """
    Compute distortion bound for pruning.
    
    This is a simplified version - real implementation would
    compute actual connectivity and weight changes.
    
    Args:
        prev_atlas: Previous atlas
        next_atlas: Next atlas
        
    Returns:
        Distortion bound (QFixed)
    """
    # Simplified: use rank change as proxy
    delta = abs(compute_delta_struct(prev_atlas, next_atlas))
    return delta * 1000000000000000000  # Scale to QFixed


# Maximum allowed distortion
MAX_DISTORTION = 100000000000000000000  # 100 QFixed


def verify_topology_jump(
    prev_atlas: Dict[str, Any],
    next_atlas: Dict[str, Any],
    budget_q: int,
    current_height: int,
    hysteresis_threshold: int = HYSTERESIS_THRESHOLD,
    slab_size: int = SLAB_SIZE,
) -> Tuple[bool, Optional[str], Optional[TopologyJumpReceipt]]:
    """
    Verify and create a topology jump receipt.
    
    Args:
        prev_atlas: Previous atlas state
        next_atlas: Next atlas state
        budget_q: Current budget
        current_height: Current block height
        hysteresis_threshold: Minimum change threshold
        slab_size: Slab size
        
    Returns:
        (allowed, error_message, receipt)
    """
    # 1. Check slab boundary (critical for hybrid safe)
    if not check_slab_boundary(current_height, slab_size):
        return False, "REJECT: Topology change only at slab boundaries", None
    
    # 2. Compute delta_struct
    delta_struct = compute_delta_struct(prev_atlas, next_atlas)
    
    # 3. Check hysteresis
    if not check_hysteresis(delta_struct, hysteresis_threshold):
        return False, f"REJECT: delta_struct {delta_struct} below hysteresis threshold", None
    
    # 4. Check budget gate
    allowed, deduction = check_budget_gate(budget_q, delta_struct)
    if not allowed:
        return False, f"REJECT: Insufficient budget for expansion", None
    
    # 5. For pruning, check distortion bound
    distortion_bound = 0
    if delta_struct < 0:  # Pruning
        distortion_bound = compute_distortion_bound(prev_atlas, next_atlas)
        if distortion_bound > MAX_DISTORTION:
            return False, f"REJECT: Distortion bound {distortion_bound} exceeds max", None
    
    # 6. Compute hashes
    A_prev_hash = compute_atlas_hash(prev_atlas)
    A_next_hash = compute_atlas_hash(next_atlas)
    
    # 7. Build receipt
    receipt_data = {
        "A_prev_hash": A_prev_hash,
        "A_next_hash": A_next_hash,
        "delta_struct": delta_struct,
        "budget_deduction": str(deduction),
        "distortion_bound": str(distortion_bound),
        "hysteresis_verified": True,
        "slab_boundary_verified": True,
    }
    
    # 8. Compute receipt ID (single hash, no double-hash)
    receipt_bytes = jcs_canonical_bytes(receipt_data)
    receipt_id = sha256_prefixed(receipt_bytes)
    
    # 9. Compute chain hash (using genesis as placeholder)
    chain_hash = chain_hash_v1_prefixed(
        "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        receipt_data
    )
    
    receipt = TopologyJumpReceipt(
        version="1.0.0",
        receipt_id=receipt_id,
        A_prev_hash=A_prev_hash,
        A_next_hash=A_next_hash,
        delta_struct=delta_struct,
        budget_deduction=deduction,
        distortion_bound=distortion_bound,
        hysteresis_verified=True,
        slab_boundary_verified=True,
        chain_hash=chain_hash,
    )
    
    return True, None, receipt


class TopologyEngine:
    """
    Engine for managing topology changes.
    """
    
    def __init__(
        self,
        hysteresis_threshold: int = HYSTERESIS_THRESHOLD,
        slab_size: int = SLAB_SIZE,
    ):
        self._hysteresis_threshold = hysteresis_threshold
        self._slab_size = slab_size
        self._current_atlas: Optional[Dict[str, Any]] = None
        self._current_budget_q: int = 0
    
    def set_atlas(self, atlas: Dict[str, Any]) -> None:
        """Set current atlas state."""
        self._current_atlas = atlas
    
    def set_budget(self, budget_q: int) -> None:
        """Set current budget."""
        self._current_budget_q = budget_q
    
    def apply_topology_jump(
        self,
        next_atlas: Dict[str, Any],
        current_height: int,
    ) -> Tuple[bool, Optional[str], Optional[TopologyJumpReceipt]]:
        """
        Apply a topology jump.
        
        Args:
            next_atlas: Proposed next atlas state
            current_height: Current block height
            
        Returns:
            (allowed, error_message, receipt)
        """
        if self._current_atlas is None:
            return False, "No current atlas set", None
        
        return verify_topology_jump(
            prev_atlas=self._current_atlas,
            next_atlas=next_atlas,
            budget_q=self._current_budget_q,
            current_height=current_height,
            hysteresis_threshold=self._hysteresis_threshold,
            slab_size=self._slab_size,
        )
    
    def terminate_slab(
        self,
        current_height: int,
    ) -> bool:
        """
        Check if current slab should be terminated for topology change.
        
        Args:
            current_height: Current block height
            
        Returns:
            True if slab should be terminated
        """
        # Check if we're at a slab boundary
        return check_slab_boundary(current_height, self._slab_size)
