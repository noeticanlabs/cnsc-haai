"""
Consensus Compatibility Layer

This module provides backward compatibility for code using the old hash format.
It allows gradual migration from bare hex to sha256: prefix format.

Usage:
    from cnsc_haai.consensus.compat import compat_sha256, compat_verify

    # Old style (bare hex)
    digest = compat_sha256(data)  # Returns "sha256:..." prefix

    # New style (prefixed)
    digest = sha256_prefixed(data)  # Returns "sha256:..." prefix
"""

import hashlib
from typing import Union, Optional

# Import the new consensus functions
from .jcs import jcs_canonical_bytes
from .hash import (
    sha256 as _sha256,
    sha256_prefixed,
    decode_sha256_prefixed,
    verify_sha256_prefixed,
)
from .merkle import MerkleTree, verify_inclusion_proof_prefixed
from .chain import chain_hash_v1 as _chain_hash_v1


# Legacy alias - old code used this pattern
def compat_sha256(data: Union[bytes, str]) -> str:
    """
    Compute SHA256 hash (new format with prefix).

    This replaces the old pattern:
        hashlib.sha256(data).hexdigest()

    Args:
        data: Bytes or string to hash

    Returns:
        SHA256 hash with 'sha256:' prefix
    """
    return sha256_prefixed(data)


def compat_decode(digest: str) -> bytes:
    """
    Decode any SHA256 digest format to raw bytes.

    Handles both:
    - "sha256:..." (new format)
    - "..." (bare hex - legacy)

    Args:
        digest: SHA256 digest string

    Returns:
        Raw 32-byte hash
    """
    if digest.startswith("sha256:"):
        return decode_sha256_prefixed(digest)
    else:
        # Legacy bare hex
        return bytes.fromhex(digest)


def compat_chain_hash(prev_hash: str, receipt_core: dict) -> str:
    """
    Compute chain hash (supports both old and new formats).

    Args:
        prev_hash: Previous chain hash (any format)
        receipt_core: Receipt core dictionary

    Returns:
        Chain hash with 'sha256:' prefix
    """
    from .chain import chain_hash_v1_prefixed

    return chain_hash_v1_prefixed(prev_hash, receipt_core)


# Backward compatibility for old canonical_bytes methods
def canonical_bytes_legacy(obj) -> bytes:
    """
    Legacy canonical bytes using json.dumps with sort_keys.

    This is NOT RFC8785 compliant but maintained for backward compatibility.
    Use jcs_canonical_bytes for new code.
    """
    import json

    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


# Migration guide
MIGRATION_GUIDE = """
# Migration from Legacy to Consensus-Safe Hashing

## Old Pattern (deprecated):
    import hashlib
    digest = hashlib.sha256(data).hexdigest()  # Returns bare hex

## New Pattern (recommended):
    from cnsc_haai.consensus import sha256_prefixed
    digest = sha256_prefixed(data)  # Returns "sha256:..."

## Compatibility Layer:
    from cnsc_haai.consensus.compat import compat_sha256
    digest = compat_sha256(data)  # Returns prefixed, works with old code

## Chain Hash Migration:

Old:
    chain_hash = hashlib.sha256(prev.encode() + core_bytes).hexdigest()

New:
    from cnsc_haai.consensus.chain import chain_hash_v1_prefixed
    chain_hash = chain_hash_v1_prefixed(prev, core)
"""
