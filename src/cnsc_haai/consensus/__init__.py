"""
CNSC-HAAI Consensus Utilities

This module provides consensus-critical cryptographic utilities:
- JCS: RFC8785 JSON Canonicalization
- Hash: SHA256 with prefix handling
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
"""

from .jcs import jcs_canonical_bytes, JCSEncoder
from .hash import sha256, sha256_prefixed, decode_sha256_prefixed
from .merkle import MerkleTree, verify_inclusion_proof
from .chain import chain_hash_v1, chain_hash_sequence
from .codec import MicroLeafCodec, encode_micro_leaf, strip_to_core
from .compat import compat_sha256, compat_decode, compat_chain_hash, canonical_bytes_legacy

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
]
