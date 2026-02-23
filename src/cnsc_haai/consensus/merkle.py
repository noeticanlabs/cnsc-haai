"""
Merkle Tree Implementation

Provides deterministic Merkle tree construction per Coh Merkle v1 spec:
- Leaf hash: SHA256(0x00 || leaf_bytes)
- Internal hash: SHA256(0x01 || left || right)
- Odd node handling: duplicate last node
"""

import hashlib
from typing import List, Optional, Tuple

# Import from hash_primitives for canonical hashing
from .hash_primitives import sha256 as _hp_sha256, sha256_prefixed as _hp_sha256_prefixed


# Merkle node prefixes - DOMAIN SEPARATION (0x00 for leaf, 0x01 for internal)
# This is the canonical convention per hash_primitives module
LEAF_PREFIX = bytes([0x00])
INTERNAL_PREFIX = bytes([0x01])


def sha256(data):
    """DEPRECATED: Use hash_primitives.sha256 directly"""
    import warnings
    warnings.warn("Use hash_primitives.sha256 directly", DeprecationWarning, stacklevel=2)
    return _hp_sha256(data)


def sha256_prefixed(data):
    """DEPRECATED: Use hash_primitives.sha256_prefixed directly"""
    import warnings
    warnings.warn("Use hash_primitives.sha256_prefixed directly", DeprecationWarning, stacklevel=2)
    return _hp_sha256_prefixed(data)


def leaf_hash(leaf_bytes: bytes) -> bytes:
    """
    Compute leaf hash per Coh Merkle v1 spec.
    
    Leaf hash = SHA256(0x01 || leaf_bytes)
    
    Args:
        leaf_bytes: Raw leaf data bytes
        
    Returns:
        32-byte hash
    """
    return sha256(LEAF_PREFIX + leaf_bytes)


def leaf_hash_prefixed(leaf_bytes: bytes) -> str:
    """
    Compute leaf hash with 'sha256:' prefix.
    
    Args:
        leaf_bytes: Raw leaf data bytes
        
    Returns:
        Prefixed digest string
    """
    return sha256_prefixed(LEAF_PREFIX + leaf_bytes)


def internal_hash(left: bytes, right: bytes) -> bytes:
    """
    Compute internal node hash per Coh Merkle v1 spec.
    
    Internal hash = SHA256(0x01 || left || right)
    
    Args:
        left: Left child hash (32 bytes)
        right: Right child hash (32 bytes)
        
    Returns:
        32-byte hash
    """
    return sha256(INTERNAL_PREFIX + left + right)


def internal_hash_prefixed(left: str, right: str) -> str:
    """
    Compute internal node hash from prefixed digests.
    
    Args:
        left: Left child prefixed digest
        right: Right child prefixed digest
        
    Returns:
        Prefixed digest string
    """
    from .hash import decode_sha256_prefixed
    
    left_raw = decode_sha256_prefixed(left)
    right_raw = decode_sha256_prefixed(right)
    return sha256_prefixed(INTERNAL_PREFIX + left_raw + right_raw)


class MerkleTree:
    """
    Deterministic Merkle tree per Coh Merkle v1 specification.
    
    Usage:
        tree = MerkleTree()
        root = tree.build(leaves)
        proof = tree.get_proof(index)
        verified = verify_inclusion_proof(leaf, proof, root)
    """
    
    def __init__(self):
        """Initialize the Merkle tree builder."""
        self._leaves: List[bytes] = []
        self._tree: List[List[bytes]] = []
        self._root: Optional[bytes] = None
    
    def build(self, leaves: List[bytes]) -> bytes:
        """
        Build a Merkle tree from leaf data.
        
        Args:
            leaves: List of leaf data bytes
            
        Returns:
            Root hash (32 bytes)
        """
        if not leaves:
            # Empty tree - return zero hash
            self._root = bytes(32)
            return self._root
        
        self._leaves = leaves
        
        # Level 0: leaf hashes
        current_level = [leaf_hash(leaf) for leaf in leaves]
        self._tree = [current_level]
        
        # Build levels up to root
        while len(current_level) > 1:
            next_level = []
            
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                next_level.append(internal_hash(left, right))
            
            self._tree.append(next_level)
            current_level = next_level
        
        self._root = current_level[0]
        return self._root
    
    def root(self) -> Optional[bytes]:
        """Get the root hash."""
        return self._root
    
    def root_prefixed(self) -> str:
        """Get the root hash as prefixed string."""
        if self._root is None:
            return sha256_prefixed(b"")
        return sha256_prefixed(self._root)
    
    def get_proof(self, leaf_index: int) -> List[Tuple[str, str]]:
        """
        Get inclusion proof for a leaf.
        
        Args:
            leaf_index: Index of the leaf
            
        Returns:
            List of (side, hash) tuples for proof path
        """
        if not self._tree or self._root is None:
            return []
        
        proof = []
        index = leaf_index
        
        for level in range(len(self._tree) - 1):
            level_hashes = self._tree[level]
            
            if index % 2 == 0:
                # Left sibling
                if index + 1 < len(level_hashes):
                    # The sibling is on the RIGHT of our leaf
                    proof.append(("R", level_hashes[index + 1].hex()))
                else:
                    # No sibling - use self (shouldn't happen in proper tree)
                    proof.append(("L", level_hashes[index].hex()))
            else:
                # Right sibling - the sibling is on the LEFT of our leaf
                proof.append(("L", level_hashes[index - 1].hex()))
            
            index = index // 2
        
        return proof
    
    def get_proof_prefixed(self, leaf_index: int) -> List[dict]:
        """
        Get inclusion proof with prefixed hashes.
        
        Args:
            leaf_index: Index of the leaf
            
        Returns:
            List of {side, hash} dicts with prefixed hashes
        """
        proof = self.get_proof(leaf_index)
        return [{"side": side, "hash": f"sha256:{hash_}"} for side, hash_ in proof]


def verify_inclusion_proof(
    leaf_bytes: bytes,
    proof: List[Tuple[str, str]],
    root: bytes
) -> bool:
    """
    Verify a Merkle inclusion proof.
    
    Args:
        leaf_bytes: The leaf data
        proof: List of (side, hash) tuples
        root: Expected root hash
        
    Returns:
        True if proof is valid
    """
    current = leaf_hash(leaf_bytes)
    
    for side, hash_str in proof:
        sibling = bytes.fromhex(hash_str)
        
        if side == "L":
            # Sibling is on the LEFT: hash(L || current)
            current = internal_hash(sibling, current)
        else:  # "R"
            # Sibling is on the RIGHT: hash(current || R)
            current = internal_hash(current, sibling)
    
    return current == root


def verify_inclusion_proof_prefixed(
    leaf_bytes: bytes,
    proof: List[dict],
    root
) -> bool:
    """
    Verify a Merkle inclusion proof with prefixed hashes.
    
    Args:
        leaf_bytes: The leaf data
        proof: List of {side, hash} dicts (with prefixed hashes)
        root: Expected root hash (can be raw bytes or prefixed string)
        
    Returns:
        True if proof is valid
    """
    from .hash import decode_sha256_prefixed
    
    current = leaf_hash(leaf_bytes)
    
    # Handle both raw bytes and prefixed string for root
    if isinstance(root, bytes):
        root_raw = root
    else:
        root_raw = decode_sha256_prefixed(root)
    
    for step in proof:
        sibling = decode_sha256_prefixed(step["hash"])
        
        if step["side"] == "L":
            # Sibling is on the LEFT: hash(L || current)
            current = internal_hash(sibling, current)
        else:  # "R"
            # Sibling is on the RIGHT: hash(current || R)
            current = internal_hash(current, sibling)
    
    return current == root_raw


def compute_merkle_root(leaves: List[bytes]) -> bytes:
    """
    Convenience function to compute Merkle root.
    
    Args:
        leaves: List of leaf data bytes
        
    Returns:
        Root hash (32 bytes)
    """
    tree = MerkleTree()
    return tree.build(leaves)
