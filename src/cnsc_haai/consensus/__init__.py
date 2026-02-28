"""
CNSC-HAAI Consensus Utilities

This module provides consensus-critical cryptographic utilities:
- JCS: RFC8785 JSON Canonicalization
- Hash: SHA256 with prefix handling
- Hash Primitives: Canonical receipt_id and chain_digest (receipt_id vs chain_digest)
- Merkle: Merkle tree construction
- Chain: Universal chain hashing
- Codec: Micro leaf encoding
- Compat: Backward compatibility layer

All implementations are deterministic and verified against compliance vectors.

================================================================================
CONSENSUS BOUNDARY GUARD
================================================================================

THIS MODULE IS CONSENSUS-CRITICAL.

DO NOT import from the following modules (they may contain non-deterministic code):
- src/cnsc/haai/gml/*      (telemetry/tracing)
- src/cnsc/haai/tgs/*      (debug/telemetry)
- src/cnhaai/*             (UI heuristics, non-consensus)

Importing from these modules may introduce:
- Floating-point arithmetic (non-deterministic)
- Timestamps (vary across runs)
- UUIDs (randomness)
- Non-canonical serialization

If you need to bridge consensus and non-consensus code, use the explicit
conversion functions in src/cnsc/haai/ats/bridge.py.

================================================================================
HASHING PRIMITIVES CONVENTIONS
================================================================================

For deterministic consensus, use these canonical functions:

- receipt_id(receipt_core): Content hash, stable ID for this receipt's content
- chain_digest(prev, receipt_id): Actual chain with order binding (includes prev)
- merkle_leaf_hash(leaf_bytes): Leaf nodes with domain separation (0x00)
- merkle_internal_hash(left, right): Internal nodes with domain separation (0x01)

Never use raw sha256() calls in consensus-critical code - always use these
canonical primitives to ensure consistency across implementations.
"""

from .jcs import jcs_canonical_bytes, JCSEncoder

# Note: hash.py is deprecated, but we re-export from here for compatibility
# The deprecated hash.py module is now just a shim
import warnings

with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    from .hash import sha256, sha256_prefixed, decode_sha256_prefixed
from .merkle import MerkleTree, verify_inclusion_proof
from .chain import chain_hash_v1, chain_hash_sequence
from .codec import MicroLeafCodec, encode_micro_leaf, strip_to_core
from .compat import compat_sha256, compat_decode, compat_chain_hash, canonical_bytes_legacy

# NEW: Canonical hashing primitives (receipt_id vs chain_digest)
from .hash_primitives import (
    receipt_id,
    receipt_id_bytes,
    chain_digest,
    chain_digest_bytes,
    merkle_leaf_hash,
    merkle_leaf_hash_prefixed,
    merkle_internal_hash,
    merkle_internal_hash_prefixed,
    GENESIS_CHAIN_DIGEST,
    GENESIS_CHAIN_DIGEST_BYTES,
    is_genesis,
    # Re-export for convenience
    sha256 as hp_sha256,
    sha256_prefixed as hp_sha256_prefixed,
    decode_sha256_prefixed as hp_decode_sha256_prefixed,
    # JCS and receipt core utilities
    jcs_bytes,
    receipt_core,
    receipt_core_bytes,
)

__all__ = [
    # Core
    "jcs_canonical_bytes",
    "JCSEncoder",
    "sha256",
    "sha256_prefixed",
    "decode_sha256_prefixed",
    "MerkleTree",
    "verify_inclusion_proof",
    "chain_hash_v1",
    "chain_hash_sequence",
    # Codec
    "MicroLeafCodec",
    "encode_micro_leaf",
    "strip_to_core",
    # Compatibility
    "compat_sha256",
    "compat_decode",
    "compat_chain_hash",
    "canonical_bytes_legacy",
    # New hashing primitives
    "receipt_id",
    "receipt_id_bytes",
    "chain_digest",
    "chain_digest_bytes",
    "merkle_leaf_hash",
    "merkle_leaf_hash_prefixed",
    "merkle_internal_hash",
    "merkle_internal_hash_prefixed",
    "GENESIS_CHAIN_DIGEST",
    "GENESIS_CHAIN_DIGEST_BYTES",
    "is_genesis",
    "hp_sha256",
    "hp_sha256_prefixed",
    "hp_decode_sha256_prefixed",
    # JCS and receipt core
    "jcs_bytes",
    "receipt_core",
    "receipt_core_bytes",
]
