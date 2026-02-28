"""
Chain Hash v1 Implementation

Provides canonical chain hashing with proper receipt_id vs chain_digest distinction:
- receipt_id: Content hash for stable receipt identification (no prev)
- chain_digest: Actual chain with order binding (includes prev)

This module provides backward compatibility functions while also exposing
the new canonical primitives from hash_primitives.
"""

from typing import List, Optional

# Import the new canonical primitives
from .hash_primitives import (
    receipt_id,
    receipt_id_bytes,
    chain_digest,
    chain_digest_bytes,
    GENESIS_CHAIN_DIGEST,
    GENESIS_CHAIN_DIGEST_BYTES,
    is_genesis,
    sha256_prefixed,
    decode_sha256_prefixed,
)

# Import JCS for backward compatibility
from .jcs import jcs_canonical_bytes

# Keep legacy domain for backward compatibility
DOMAIN_SEPARATOR = b"COH_CHAIN_V1\n"


def chain_hash_v1(prev_chain_hash: bytes, receipt_core: dict) -> bytes:
    """
    Compute chain hash v1 per the UPDATED universal chain hashing spec.

    This function now CORRECTLY incorporates prev_chain_hash:
    1. Compute receipt_id = SHA256(DOMAIN || JCS(receipt_core))
    2. Compute chain_digest = SHA256(DOMAIN || prev_chain_hash || receipt_id)

    Args:
        prev_chain_hash: Previous chain digest (32 bytes) or 32 zero bytes for genesis
        receipt_core: Receipt core dictionary (must be JSON-serializable)

    Returns:
        32-byte chain digest
    """
    if len(prev_chain_hash) != 32:
        raise ValueError(f"Invalid prev_chain_hash length: {len(prev_chain_hash)}")

    # Step 1: Compute receipt_id (content hash)
    receipt_id = receipt_id_bytes(receipt_core)

    # Step 2: Compute chain_digest (includes prev)
    return chain_digest_bytes(prev_chain_hash, receipt_id)


def chain_hash_v1_prefixed(prev_chain_hash: str, receipt_core: dict) -> str:
    """
    Compute chain hash v1 and return as prefixed string.

    Args:
        prev_chain_hash: Previous chain hash with 'sha256:' prefix
        receipt_core: Receipt core dictionary

    Returns:
        Chain digest with 'sha256:' prefix
    """
    prev_raw = decode_sha256_prefixed(prev_chain_hash)
    result = chain_hash_v1(prev_raw, receipt_core)
    # Convert raw bytes to prefixed string
    return "sha256:" + result.hex()


def chain_hash_sequence(
    receipt_cores: List[dict], genesis_hash: Optional[bytes] = None
) -> List[bytes]:
    """
    Compute chain hash sequence for multiple receipts.

    Args:
        receipt_cores: List of receipt core dictionaries
        genesis_hash: Genesis hash (32 bytes), defaults to zeros

    Returns:
        List of chain hashes (one per receipt)
    """
    if genesis_hash is None:
        genesis_hash = bytes(32)

    if len(genesis_hash) != 32:
        raise ValueError(f"Invalid genesis_hash length: {len(genesis_hash)}")

    chain_hashes = []
    current_hash = genesis_hash

    for core in receipt_cores:
        current_hash = chain_hash_v1(current_hash, core)
        chain_hashes.append(current_hash)

    return chain_hashes


def chain_hash_sequence_prefixed(
    receipt_cores: List[dict], genesis_hash: Optional[str] = None
) -> List[str]:
    """
    Compute chain hash sequence and return as prefixed strings.

    Args:
        receipt_cores: List of receipt core dictionaries
        genesis_hash: Genesis hash with 'sha256:' prefix, defaults to zeros

    Returns:
        List of prefixed chain hashes
    """
    if genesis_hash is None:
        genesis_hash = "sha256:" + "0" * 64

    genesis_raw = decode_sha256_prefixed(genesis_hash)
    raw_hashes = chain_hash_sequence(receipt_cores, genesis_raw)

    # Convert raw bytes to prefixed strings
    return ["sha256:" + h.hex() for h in raw_hashes]


def verify_chain_link(
    prev_chain_hash: bytes, receipt_core: dict, expected_chain_hash: bytes
) -> bool:
    """
    Verify that a receipt's chain hash is correct.

    Args:
        prev_chain_hash: Previous chain hash (32 bytes)
        receipt_core: Receipt core dictionary
        expected_chain_hash: Expected chain hash (32 bytes)

    Returns:
        True if chain link is valid
    """
    computed = chain_hash_v1(prev_chain_hash, receipt_core)
    return computed == expected_chain_hash


def verify_chain_link_prefixed(
    prev_chain_hash: str, receipt_core: dict, expected_chain_hash: str
) -> bool:
    """
    Verify chain link with prefixed digests.

    Args:
        prev_chain_hash: Previous chain hash (prefixed)
        receipt_core: Receipt core dictionary
        expected_chain_hash: Expected chain hash (prefixed)

    Returns:
        True if chain link is valid
    """
    prev_raw = decode_sha256_prefixed(prev_chain_hash)
    expected_raw = decode_sha256_prefixed(expected_chain_hash)
    return verify_chain_link(prev_raw, receipt_core, expected_raw)


class ChainHashV1:
    """
    Chain hash v1 calculator with state.

    Usage:
        chain = ChainHashV1()
        for receipt in receipts:
            hash = chain.add(receipt_core)
            print(hash)  # 'sha256:...'
    """

    def __init__(self, genesis_hash: Optional[bytes] = None):
        """
        Initialize chain hasher.

        Args:
            genesis_hash: Starting hash (defaults to zeros)
        """
        self._current_hash = genesis_hash if genesis_hash else bytes(32)
        self._history: List[bytes] = []

    def add(self, receipt_core: dict) -> str:
        """
        Add a receipt to the chain.

        Args:
            receipt_core: Receipt core dictionary

        Returns:
            Chain hash with 'sha256:' prefix
        """
        self._current_hash = chain_hash_v1(self._current_hash, receipt_core)
        self._history.append(self._current_hash)
        return sha256_prefixed(self._current_hash)

    def current(self) -> str:
        """Get current chain hash as prefixed string."""
        return sha256_prefixed(self._current_hash)

    def history(self) -> List[str]:
        """Get chain hash history as prefixed strings."""
        return [sha256_prefixed(h) for h in self._history]

    def reset(self, genesis_hash: Optional[bytes] = None):
        """Reset the chain to genesis."""
        self._current_hash = genesis_hash if genesis_hash else bytes(32)
        self._history = []
