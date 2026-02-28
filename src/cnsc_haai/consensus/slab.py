"""
Slab Module

Provides slab receipt building and verification for ATS micro receipts.
Per docs/ats/20_coh_kernel/slab_compression_rules.md

A slab is a batch of micro receipts with a Merkle root and minimal basis
for fraud proof verification.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

from cnsc_haai.consensus.jcs import jcs_canonical_bytes
from cnsc_haai.consensus.hash import sha256, sha256_prefixed, decode_sha256_prefixed
from cnsc_haai.consensus.merkle import compute_merkle_root, MerkleTree, merkle_leaf_hash
from cnsc_haai.consensus.chain import chain_hash_v1_prefixed
from cnsc_haai.consensus.codec import encode_micro_leaf
from cnsc_haai.consensus.retention import (
    compute_window_end_height,
    get_policy,
    RetentionPolicy,
)

# Genesis chain hash (all zeros)
GENESIS_CHAIN_HASH = "sha256:0000000000000000000000000000000000000000000000000000000000000000"


@dataclass
class MinimalBasis:
    """
    Minimal basis for fraud proof verification.

    Contains the minimum information needed to verify any micro receipt
    in the slab without requiring all receipts.
    """

    # Budget bounds
    B_end_q: int  # End budget (QFixed scaled)
    V_max_q: int  # Maximum risk value in slab
    M_max_int: int  # Maximum memory in slab

    # Counts
    micro_step_count: int  # Number of micro receipts

    # Policy
    retention_policy_id: str  # Policy ID for this slab

    def to_dict(self) -> Dict[str, Any]:
        return {
            "B_end_q": self.B_end_q,
            "V_max_q": self.V_max_q,
            "M_max_int": self.M_max_int,
            "micro_step_count": self.micro_step_count,
            "retention_policy_id": self.retention_policy_id,
        }


@dataclass
class SlabReceipt:
    """
    Slab receipt - aggregates multiple micro receipts.
    """

    version: str = "1.0.0"
    slab_id: str = ""
    episode_id: str = ""
    merkle_root: str = ""
    micro_receipt_hashes: List[str] = field(default_factory=list)
    window_start: int = 0
    window_end: int = 0
    receipt_count: int = 0
    initial_state_hash: str = ""
    final_state_hash: str = ""
    chain_hash: str = ""
    minimal_basis: Optional[Dict[str, Any]] = None
    retention_policy_id: str = ""
    timestamp: str = ""

    @classmethod
    def from_micro_receipts(
        cls,
        micro_receipts: List[Dict[str, Any]],
        window_start: int,
        window_end: int,
        prev_chain_hash: str,
        retention_policy_id: str,
        initial_state_hash: str = "",
        final_state_hash: str = "",
    ) -> "SlabReceipt":
        """
        Build a slab receipt from a list of micro receipts.

        Args:
            micro_receipts: List of micro receipt dictionaries
            window_start: Starting block height
            window_end: Ending block height
            prev_chain_hash: Previous chain hash
            retention_policy_id: Policy ID for retention
            initial_state_hash: Initial state hash (optional)
            final_state_hash: Final state hash (optional)

        Returns:
            SlabReceipt with computed merkle root and chain hash
        """
        # Compute leaf hashes from micro receipts
        # Use codec + merkle_leaf_hash for proper domain separation
        leaf_hashes: List[bytes] = []
        for receipt in micro_receipts:
            # Use codec to strip to core, then merkle_leaf_hash for domain separation
            leaf_bytes = encode_micro_leaf(receipt)
            receipt_hash = merkle_leaf_hash(leaf_bytes)
            leaf_hashes.append(receipt_hash)

        # Compute Merkle root
        merkle_root_bytes = compute_merkle_root(leaf_hashes)
        merkle_root = sha256_prefixed(merkle_root_bytes)

        # Compute micro receipt hashes (with prefix)
        micro_receipt_hashes = [sha256_prefixed(h) for h in leaf_hashes]

        # Compute minimal basis
        basis = cls._compute_minimal_basis(micro_receipts, retention_policy_id)

        # Build slab core (without chain_hash - it's computed last)
        slab_core = {
            "version": "1.0.0",
            "slab_id": "",  # Will be computed
            "merkle_root": merkle_root,
            "micro_receipt_hashes": micro_receipt_hashes,
            "window_start": window_start,
            "window_end": window_end,
            "receipt_count": len(micro_receipts),
            "initial_state_hash": initial_state_hash,
            "final_state_hash": final_state_hash,
            "minimal_basis": basis.to_dict(),
            "retention_policy_id": retention_policy_id,
        }

        # Compute slab_id from core (single hash, no double-hash)
        core_bytes = jcs_canonical_bytes(slab_core)
        slab_id = sha256_prefixed(core_bytes)

        # Build full receipt for chain hashing
        full_receipt = dict(slab_core)
        full_receipt["slab_id"] = slab_id

        # Compute chain hash
        chain_hash = chain_hash_v1_prefixed(prev_chain_hash, full_receipt)

        return cls(
            version="1.0.0",
            slab_id=slab_id,
            merkle_root=merkle_root,
            micro_receipt_hashes=micro_receipt_hashes,
            window_start=window_start,
            window_end=window_end,
            receipt_count=len(micro_receipts),
            initial_state_hash=initial_state_hash,
            final_state_hash=final_state_hash,
            chain_hash=chain_hash,
            minimal_basis=basis.to_dict(),
            retention_policy_id=retention_policy_id,
        )

    @staticmethod
    def _compute_minimal_basis(
        micro_receipts: List[Dict[str, Any]], retention_policy_id: str
    ) -> MinimalBasis:
        """
        Compute minimal basis from micro receipts.

        Extracts the minimum information needed for fraud proof verification.

        Note: B_end_q is the FINAL budget (last receipt), not max.
        """
        # B_end = final budget (last receipt's budget_after_q), not max
        B_end_q = 0
        if micro_receipts:
            last_receipt = micro_receipts[-1]
            B_end_q = int(last_receipt.get("budget_after_q", 0))

        # V_max and M_max are still maxima
        V_max_q = 0
        M_max_int = 0

        for receipt in micro_receipts:
            # Extract max risk
            if "risk_after_q" in receipt:
                V_max_q = max(V_max_q, int(receipt["risk_after_q"]))

            # Extract max memory
            if "memory_used" in receipt:
                M_max_int = max(M_max_int, int(receipt["memory_used"]))

        return MinimalBasis(
            B_end_q=B_end_q,
            V_max_q=V_max_q,
            M_max_int=M_max_int,
            micro_step_count=len(micro_receipts),
            retention_policy_id=retention_policy_id,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version": self.version,
            "slab_id": self.slab_id,
            "episode_id": self.episode_id,
            "merkle_root": self.merkle_root,
            "micro_receipt_hashes": self.micro_receipt_hashes,
            "window_start": self.window_start,
            "window_end": self.window_end,
            "receipt_count": self.receipt_count,
            "initial_state_hash": self.initial_state_hash,
            "final_state_hash": self.final_state_hash,
            "chain_hash": self.chain_hash,
            "minimal_basis": self.minimal_basis,
            "retention_policy_id": self.retention_policy_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SlabReceipt":
        """Create from dictionary."""
        return cls(
            version=data.get("version", "1.0.0"),
            slab_id=data.get("slab_id", ""),
            episode_id=data.get("episode_id", ""),
            merkle_root=data.get("merkle_root", ""),
            micro_receipt_hashes=data.get("micro_receipt_hashes", []),
            window_start=data.get("window_start", 0),
            window_end=data.get("window_end", 0),
            receipt_count=data.get("receipt_count", 0),
            initial_state_hash=data.get("initial_state_hash", ""),
            final_state_hash=data.get("final_state_hash", ""),
            chain_hash=data.get("chain_hash", ""),
            minimal_basis=data.get("minimal_basis"),
            retention_policy_id=data.get("retention_policy_id", ""),
        )


# Slab buffer for accumulating micro receipts
class SlabBuffer:
    """
    Accumulates micro receipts and emits slab receipts when threshold is reached.
    """

    def __init__(
        self,
        max_micro_count: int = 1000,
        max_time_seconds: Optional[int] = None,
        retention_policy_id: str = "",
    ):
        """
        Initialize slab buffer.

        Args:
            max_micro_count: Maximum micro receipts before emitting slab
            max_time_seconds: Maximum time before emitting slab (optional)
            retention_policy_id: Policy ID for retention
        """
        self.max_micro_count = max_micro_count
        self.max_time_seconds = max_time_seconds
        self.retention_policy_id = retention_policy_id

        self._micro_receipts: List[Dict[str, Any]] = []
        self._window_start: int = 0
        self._initial_state_hash: str = ""

    def add_micro_receipt(self, receipt: Dict[str, Any]) -> Optional[SlabReceipt]:
        """
        Add a micro receipt to the buffer.

        Args:
            receipt: Micro receipt dictionary

        Returns:
            SlabReceipt if slab was emitted, None otherwise
        """
        if not self._micro_receipts:
            # First receipt - set window start and initial state
            self._window_start = receipt.get("block_height", 0)
            self._initial_state_hash = receipt.get("state_hash_before", "")

        self._micro_receipts.append(receipt)

        # Check if we should emit
        if len(self._micro_receipts) >= self.max_micro_count:
            return self.emit_slab()

        return None

    def emit_slab(
        self,
        prev_chain_hash: str = GENESIS_CHAIN_HASH,
        window_end: Optional[int] = None,
    ) -> Optional[SlabReceipt]:
        """
        Emit the current buffer as a slab receipt.

        Args:
            prev_chain_hash: Previous chain hash
            window_end: Window end height (computed from policy if not provided)

        Returns:
            SlabReceipt if there are micro receipts, None otherwise
        """
        if not self._micro_receipts:
            return None

        # Get policy for window_end
        if window_end is None and self.retention_policy_id:
            policy = get_policy(self.retention_policy_id)
            if policy:
                window_end = compute_window_end_height(
                    self._window_start,
                    policy.dispute_window_blocks,
                )
            else:
                window_end = self._window_start + 100  # default

        # Build slab receipt
        slab = SlabReceipt.from_micro_receipts(
            micro_receipts=self._micro_receipts,
            window_start=self._window_start,
            window_end=window_end,
            prev_chain_hash=prev_chain_hash,
            retention_policy_id=self.retention_policy_id,
            initial_state_hash=self._initial_state_hash,
            final_state_hash=self._micro_receipts[-1].get("state_hash_after", ""),
        )

        # Reset buffer
        self._micro_receipts = []
        self._window_start = 0
        self._initial_state_hash = ""

        return slab

    def get_count(self) -> int:
        """Get current micro receipt count."""
        return len(self._micro_receipts)

    def is_empty(self) -> bool:
        """Check if buffer is empty."""
        return len(self._micro_receipts) == 0


# Slab registry for tracking slabs
class SlabRegistry:
    """
    Registry for tracking slabs and their states.
    """

    def __init__(self):
        self._slabs: Dict[str, SlabReceipt] = {}
        self._slab_hashes: Dict[str, str] = {}  # hash -> slab_id

    def register(self, slab: SlabReceipt) -> None:
        """Register a slab receipt."""
        self._slabs[slab.slab_id] = slab
        self._slab_hashes[slab.chain_hash] = slab.slab_id

    def get(self, slab_id: str) -> Optional[SlabReceipt]:
        """Get slab by ID."""
        return self._slabs.get(slab_id)

    def get_by_hash(self, chain_hash: str) -> Optional[SlabReceipt]:
        """Get slab by chain hash."""
        slab_id = self._slab_hashes.get(chain_hash)
        if slab_id:
            return self._slabs.get(slab_id)
        return None

    def all_slabs(self) -> List[SlabReceipt]:
        """Get all registered slabs."""
        return list(self._slabs.values())


# Global slab registry
_slab_registry = SlabRegistry()


def get_slab_registry() -> SlabRegistry:
    """Get the global slab registry."""
    return _slab_registry


# Micro receipt storage for pruning
_micro_receipt_storage: Dict[str, Dict[str, Any]] = {}


def store_micro_receipt(micro_root: str, micro_receipt: Dict[str, Any]) -> None:
    """
    Store a micro receipt for a given micro_root.

    Args:
        micro_root: The Merkle root of the slab containing this receipt
        micro_receipt: The micro receipt data
    """
    receipt_id = micro_receipt.get("receipt_id", "")
    if receipt_id:
        if micro_root not in _micro_receipt_storage:
            _micro_receipt_storage[micro_root] = {}
        _micro_receipt_storage[micro_root][receipt_id] = micro_receipt


def get_micro_receipts(micro_root: str) -> List[Dict[str, Any]]:
    """
    Get all micro receipts for a given micro_root.

    Args:
        micro_root: The Merkle root of the slab

    Returns:
        List of micro receipts
    """
    return list(_micro_receipt_storage.get(micro_root, {}).values())


def delete_micro_receipts(micro_root: str) -> int:
    """
    Delete all micro receipts for a given micro_root.

    This is called after a slab is finalized, implementing the
    "certified forgetting" mechanism.

    Args:
        micro_root: The Merkle root of the slab

    Returns:
        Number of receipts deleted
    """
    if micro_root in _micro_receipt_storage:
        count = len(_micro_receipt_storage[micro_root])
        del _micro_receipt_storage[micro_root]
        return count
    return 0


def prune_finalized_slab(
    slab: SlabReceipt,
    current_height: int,
) -> Tuple[bool, Optional[str]]:
    """
    Prune micro receipts for a finalized slab.

    Called after successful finalization to implement certified forgetting.

    Args:
        slab: The finalized slab receipt
        current_height: Current block height

    Returns:
        (success, error_message)
    """
    from cnsc_haai.consensus.finalize import (
        get_finalized_registry,
        is_finalized as check_slab_finalized,
    )

    # Check if slab is actually finalized
    finalized_registry = get_finalized_registry()
    if not finalized_registry.is_finalized(slab.chain_hash):
        return False, "Slab not finalized"

    # Get policy to verify timing
    from cnsc_haai.consensus.retention import get_policy

    policy = get_policy(slab.retention_policy_id)
    if not policy:
        return False, "Policy not found"

    # Verify timing requirements
    from cnsc_haai.consensus.retention import compute_finalize_height

    finalize_height = compute_finalize_height(
        slab.window_end,
        policy.retention_period_blocks,
    )

    if current_height < finalize_height:
        return False, f"Premature: height {current_height} < finalize_height {finalize_height}"

    # Delete micro receipts
    deleted_count = delete_micro_receipts(slab.merkle_root)

    return True, f"Pruned {deleted_count} micro receipts"
