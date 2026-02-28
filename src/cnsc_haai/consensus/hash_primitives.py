"""
Hashing Primitives Module

Canonical hash functions for CNSC-HAAI consensus system.

This module provides a single source of truth for all hashing operations,
eliminating inconsistencies from rolling custom hash implementations.

Domain Separation:
- receipt_id: Content hash for stable receipt identification (no prev)
- chain_digest: Actual chain digest with order binding (includes prev)
- merkle_leaf: Merkle tree leaf nodes
- merkle_internal: Merkle tree internal nodes
"""

import hashlib
from typing import Dict, Any, Union

# Type alias for 32-byte hashes
bytes32 = bytes

# Domain separators (per RFC8785-style canonicalization)
DOMAIN_RECEIPT_ID = b"COH_RECEIPT_ID_V1\n"
DOMAIN_CHAIN = b"COH_CHAIN_DIGEST_V1\n"
DOMAIN_MERKLE_LEAF = bytes([0x00])
DOMAIN_MERKLE_INTERNAL = bytes([0x01])


def sha256(data: Union[bytes, str]) -> bytes32:
    """
    Compute SHA256 hash of data.

    Args:
        data: Bytes or string to hash

    Returns:
        Raw 32-byte SHA256 hash
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).digest()


def sha256_hex(data: Union[bytes, str]) -> str:
    """
    Compute SHA256 hash and return as hex string.

    Args:
        data: Bytes or string to hash

    Returns:
        64-character hex string
    """
    return sha256(data).hex()


def sha256_prefixed(data: Union[bytes, str]) -> str:
    """
    Compute SHA256 hash and return with 'sha256:' prefix.

    This is the standard format for all digests in JSON.

    Args:
        data: Bytes or string to hash

    Returns:
        'sha256:' followed by 64 hex characters
    """
    return "sha256:" + sha256_hex(data)


def decode_sha256_prefixed(digest: str) -> bytes32:
    """
    Decode a 'sha256:' prefixed digest to raw 32 bytes.

    Args:
        digest: String like 'sha256:a1b2c3...'

    Returns:
        Raw 32-byte SHA256 hash

    Raises:
        ValueError: If format is invalid
    """
    PREFIX = "sha256:"
    if not digest.startswith(PREFIX):
        raise ValueError(f"Invalid digest format: missing '{PREFIX}' prefix")

    hex_part = digest[len(PREFIX) :]

    if len(hex_part) != 64:
        raise ValueError(f"Invalid SHA256 length: {len(hex_part)} (expected 64)")

    if not all(c in "0123456789abcdefABCDEF" for c in hex_part):
        raise ValueError(f"Invalid hex characters in digest")

    return bytes.fromhex(hex_part)


# ============================================================================
# Receipt ID - Content Hash (No Prev)
# ============================================================================


def receipt_id(receipt_core: Dict[str, Any]) -> str:
    """
    Compute receipt_id - content hash for stable receipt identification.

    This is a content-addressable ID: same receipt content always produces
    the same receipt_id. It does NOT include previous chain state.

    Args:
        receipt_core: Receipt core dictionary (JSON-serializable)

    Returns:
        Receipt ID with 'sha256:' prefix
    """
    from .jcs import jcs_canonical_bytes

    core_bytes = jcs_canonical_bytes(receipt_core)
    return sha256_prefixed(DOMAIN_RECEIPT_ID + core_bytes)


def receipt_id_bytes(receipt_core: Dict[str, Any]) -> bytes32:
    """
    Compute receipt_id as raw bytes.

    Args:
        receipt_core: Receipt core dictionary

    Returns:
        Raw 32-byte hash
    """
    from .jcs import jcs_canonical_bytes

    core_bytes = jcs_canonical_bytes(receipt_core)
    return sha256(DOMAIN_RECEIPT_ID + core_bytes)


# ============================================================================
# Chain Digest - Actual Chain (With Prev)
# ============================================================================


def chain_digest(prev_digest: Union[bytes32, str], receipt_id: Union[bytes32, str]) -> str:
    """
    Compute chain_digest - actual chain digest with order binding.

    This creates a true chain: each digest depends on the previous one.
    Chain_digest_next = SHA256(DOMAIN || chain_digest_prev || receipt_id)

    Args:
        prev_digest: Previous chain digest (32 bytes or 'sha256:' prefix)
        receipt_id: Current receipt_id (32 bytes or 'sha256:' prefix)

    Returns:
        Chain digest with 'sha256:' prefix

    Raises:
        ValueError: If input lengths are invalid
    """
    # Normalize to raw bytes
    if isinstance(prev_digest, str):
        prev_digest = decode_sha256_prefixed(prev_digest)
    if isinstance(receipt_id, str):
        receipt_id = decode_sha256_prefixed(receipt_id)

    if len(prev_digest) != 32:
        raise ValueError(f"Invalid prev_digest length: {len(prev_digest)}")
    if len(receipt_id) != 32:
        raise ValueError(f"Invalid receipt_id length: {len(receipt_id)}")

    # chain_digest = SHA256(DOMAIN || prev_digest || receipt_id)
    chain_input = DOMAIN_CHAIN + prev_digest + receipt_id
    return sha256_prefixed(chain_input)


def chain_digest_bytes(prev_digest: bytes32, receipt_id: bytes32) -> bytes32:
    """
    Compute chain_digest as raw bytes.

    Args:
        prev_digest: Previous chain digest (32 bytes)
        receipt_id: Current receipt_id (32 bytes)

    Returns:
        Raw 32-byte chain digest
    """
    if len(prev_digest) != 32:
        raise ValueError(f"Invalid prev_digest length: {len(prev_digest)}")
    if len(receipt_id) != 32:
        raise ValueError(f"Invalid receipt_id length: {len(receipt_id)}")

    chain_input = DOMAIN_CHAIN + prev_digest + receipt_id
    return sha256(chain_input)


# ============================================================================
# Merkle Tree Hashes - With Domain Separation
# ============================================================================


def merkle_leaf_hash(leaf_bytes: bytes) -> bytes32:
    """
    Compute Merkle tree leaf hash with domain separation.

    Leaf hash = SHA256(0x00 || leaf_bytes)

    Args:
        leaf_bytes: Raw leaf data bytes

    Returns:
        32-byte leaf hash
    """
    return sha256(DOMAIN_MERKLE_LEAF + leaf_bytes)


def merkle_leaf_hash_prefixed(leaf_bytes: bytes) -> str:
    """
    Compute Merkle leaf hash with 'sha256:' prefix.

    Args:
        leaf_bytes: Raw leaf data bytes

    Returns:
        Prefixed leaf hash
    """
    return sha256_prefixed(DOMAIN_MERKLE_LEAF + leaf_bytes)


def merkle_internal_hash(left: bytes32, right: bytes32) -> bytes32:
    """
    Compute Merkle tree internal node hash with domain separation.

    Internal hash = SHA256(0x01 || left || right)

    Args:
        left: Left child hash (32 bytes)
        right: Right child hash (32 bytes)

    Returns:
        32-byte internal node hash
    """
    if len(left) != 32:
        raise ValueError(f"Invalid left hash length: {len(left)}")
    if len(right) != 32:
        raise ValueError(f"Invalid right hash length: {len(right)}")

    return sha256(DOMAIN_MERKLE_INTERNAL + left + right)


def merkle_internal_hash_prefixed(left: str, right: str) -> str:
    """
    Compute Merkle internal hash from prefixed digests.

    Args:
        left: Left child prefixed digest
        right: Right child prefixed digest

    Returns:
        Prefixed internal hash
    """
    left_raw = decode_sha256_prefixed(left)
    right_raw = decode_sha256_prefixed(right)
    return sha256_prefixed(DOMAIN_MERKLE_INTERNAL + left_raw + right_raw)


# ============================================================================
# JCS Integration
# ============================================================================


def jcs_bytes(obj: Any) -> bytes:
    """
    Compute JCS canonical bytes for any JSON-serializable object.

    This is the STRICT version that rejects floats to enforce QFixed numeric
    domain in consensus-critical paths.

    Args:
        obj: Any JSON-serializable object

    Returns:
        JCS canonical bytes

    Raises:
        TypeError: If object contains floats or other non-JSON types
    """
    from .jcs import jcs_canonical_bytes

    return jcs_canonical_bytes(obj)


def receipt_core(receipt: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract receipt core - strip derived fields.

    The receipt core contains the essential content that gets hashed
    to produce receipt_id. It excludes:
    - receipt_id (derived from content)
    - chain_digest (derived from history)
    - signatures (external)
    - timestamps (non-deterministic)

    Args:
        receipt: Full receipt dictionary

    Returns:
        Receipt core dictionary with only essential fields
    """
    # Fields to exclude from core (derived or non-deterministic)
    exclude_keys = {
        "receipt_id",
        "chain_digest",
        "chain_digest_next",
        "signature",
        "signatures",
        "timestamp",
        "created_at",
        "slab_id",
        "merkle_root",
    }

    # Extract content - the core payload
    if "content" in receipt:
        core = dict(receipt["content"])
    else:
        core = {}

    # Add metadata if present (but filter out timestamps)
    if "metadata" in receipt:
        metadata = {}
        for k, v in receipt.get("metadata", {}).items():
            if k not in exclude_keys and not k.endswith("_at"):
                metadata[k] = v
        if metadata:
            core["metadata"] = metadata

    # Preserve version
    if "version" in receipt:
        core["version"] = receipt["version"]

    return core


def receipt_core_bytes(receipt: Dict[str, Any]) -> bytes:
    """
    Get canonical bytes for receipt core.

    Args:
        receipt: Full receipt dictionary

    Returns:
        JCS canonical bytes of receipt core
    """
    return jcs_bytes(receipt_core(receipt))


# ============================================================================
# Genesis Constants
# ============================================================================

# Genesis chain digest (all zeros)
GENESIS_CHAIN_DIGEST = "sha256:0000000000000000000000000000000000000000000000000000000000000000"
GENESIS_CHAIN_DIGEST_BYTES = bytes(32)


def is_genesis(digest: Union[bytes32, str]) -> bool:
    """
    Check if a digest is the genesis digest.

    Args:
        digest: Digest to check (bytes or prefixed string)

    Returns:
        True if genesis
    """
    if isinstance(digest, str):
        return digest == GENESIS_CHAIN_DIGEST
    return digest == GENESIS_CHAIN_DIGEST_BYTES
