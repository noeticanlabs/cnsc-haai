"""
Canonical Hashing - Domain-Separated SHA256

This module provides deterministic hashing with domain separation.
Used for state hashing, chain hashing, and receipt hashing.
"""

import hashlib


def sha256_tagged(tag: str, payload: bytes) -> bytes:
    """
    Compute domain-separated SHA256 hash.

    H(tag || 0x00 || payload)

    Args:
        tag: Domain separation tag (e.g., "GMI_STATE_V1_5")
        payload: Data to hash

    Returns:
        32-byte SHA256 digest
    """
    h = hashlib.sha256()
    h.update(tag.encode("utf-8"))
    h.update(b"\x00")
    h.update(payload)
    return h.digest()


def sha256_tagged_hex(tag: str, payload: bytes) -> str:
    """Return hex-encoded domain-separated SHA256 hash."""
    return sha256_tagged(tag, payload).hex()


def chain_hash(prev_chain: bytes, receipt_payload: bytes) -> bytes:
    """
    Compute chain hash: H(prev_chain || receipt_payload)

    Args:
        prev_chain: Previous chain tip (32 bytes)
        receipt_payload: Canonical JSON bytes of receipt

    Returns:
        New chain tip (32 bytes)
    """
    h = hashlib.sha256()
    h.update(prev_chain)
    h.update(receipt_payload)
    return h.digest()
