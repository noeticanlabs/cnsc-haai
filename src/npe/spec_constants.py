"""
NPE v1.0.1 Locked Specification Constants.

All values in this module are FROZEN and must never change without a formal version bump.
This is the source of truth for domain separators, protocol version, numeric domain, and rounding rules.
"""

import hashlib
from enum import Enum
from typing import Final

# ============================================================================
# Protocol Version & Domain Separation
# ============================================================================

DOMAIN_SEPARATOR: Final[str] = "NPE|1.0.1"
"""Locked domain separator for all NPE v1.0.1 objects."""

PROTOCOL_VERSION: Final[str] = "1.0.1"
"""Locked protocol version."""

NUMERIC_DOMAIN: Final[str] = "QFixed18"
"""Locked numeric domain: all values are Q18 fixed-point (scaled by 2^18)."""

# ============================================================================
# Q18 Fixed-Point Constants
# ============================================================================

Q18_SCALE: Final[int] = 2**18
"""Q18 scaling factor: 262144."""

Q18_MIN: Final[int] = -(2**63)
"""Minimum Q18 value (int64 min)."""

Q18_MAX: Final[int] = 2**63 - 1
"""Maximum Q18 value (int64 max)."""

Q18_FRACTIONAL_MASK: Final[int] = (1 << 18) - 1
"""Bitmask for fractional part in Q18 multiplication: 0x3FFFF."""


# ============================================================================
# Rounding Enums
# ============================================================================


class RoundingMode(Enum):
    """Deterministic rounding modes for Q18 arithmetic."""

    UP = "UP"  # Ceiling (for debits)
    DOWN = "DOWN"  # Floor (for refunds)


ROUNDING_UP: Final[str] = RoundingMode.UP.value
"""Rounding mode for debits: always round UP (ceiling)."""

ROUNDING_DOWN: Final[str] = RoundingMode.DOWN.value
"""Rounding mode for refunds: always round DOWN (floor)."""


# ============================================================================
# PRNG Constants
# ============================================================================

PRNG_SEED_PREFIX: Final[bytes] = b"COH_NPE_PRNG_V1"
"""Locked seed preimage prefix (never change)."""

PRNG_NONCE_PREFIX: Final[bytes] = b"COH_NPE_PRNG_NONCE_V1"
"""Locked nonce preimage prefix (never change)."""

CHACHA20_SEED_LEN: Final[int] = 32
"""ChaCha20 seed length (sha256 output): 32 bytes."""

CHACHA20_NONCE_LEN: Final[int] = 16
"""ChaCha20 nonce length: 16 bytes (first 16 bytes of nonce derivation)."""


# ============================================================================
# Hash Lengths
# ============================================================================

SHA256_BYTES: Final[int] = 32
"""SHA256 output length in bytes."""

SHA256_HEX_LEN: Final[int] = 64
"""SHA256 hex representation length (2 * SHA256_BYTES)."""

PROPOSAL_ID_HEX_LEN: Final[int] = 16
"""Proposal ID hex length (uint64): 16 hex chars."""


# ============================================================================
# Proposal Types
# ============================================================================


class ProposalType(Enum):
    """Allowed proposal types."""

    RENORM_QUOTIENT = "RENORM_QUOTIENT"
    UNFOLD_QUOTIENT = "UNFOLD_QUOTIENT"
    CONTINUOUS_FLOW = "CONTINUOUS_FLOW"


PROPOSAL_TYPES: Final[set] = {pt.value for pt in ProposalType}
"""Set of allowed proposal type strings."""


# ============================================================================
# Binary Delta Envelope Types
# ============================================================================


class DeltaKind(Enum):
    """Delta envelope kinds."""

    DELTA_Z = 0  # Continuous flow
    DELTA_A = 1  # Renorm/Unfold with atlas


# ============================================================================
# Hashing Preimages (for audit trail)
# ============================================================================


def spec_version_hash() -> str:
    """
    Compute hash of the specification version and domain separator.

    This hash can be used to verify that the running code is based on
    a specific frozen version of the spec.

    Returns:
        Lowercase hex SHA256 hash
    """
    preimage = f"{DOMAIN_SEPARATOR}|{PROTOCOL_VERSION}|{NUMERIC_DOMAIN}".encode("utf-8")
    return hashlib.sha256(preimage).hexdigest()


def prng_seed_prefix_hash() -> str:
    """
    Compute hash of the PRNG seed prefix.

    Returns:
        Lowercase hex SHA256 hash
    """
    return hashlib.sha256(PRNG_SEED_PREFIX).hexdigest()


def prng_nonce_prefix_hash() -> str:
    """
    Compute hash of the PRNG nonce prefix.

    Returns:
        Lowercase hex SHA256 hash
    """
    return hashlib.sha256(PRNG_NONCE_PREFIX).hexdigest()


# ============================================================================
# Sanity Checks (Run at Import)
# ============================================================================


def _sanity_check() -> None:
    """
    Verify that all constants are valid and locked.

    Raises:
        AssertionError: If any constant violates frozen constraints
    """
    # Domain separator must be exactly this
    assert DOMAIN_SEPARATOR == "NPE|1.0.1", "Domain separator must be frozen"

    # Protocol version must match domain separator
    assert PROTOCOL_VERSION == "1.0.1", "Protocol version must be frozen"

    # Numeric domain must be Q18
    assert NUMERIC_DOMAIN == "QFixed18", "Numeric domain must be Q18"

    # Q18 scale must be 2^18
    assert Q18_SCALE == 262144, "Q18 scale must be 2^18"

    # Rounding modes must be exactly these strings
    assert ROUNDING_UP == "UP", "UP rounding mode must be frozen"
    assert ROUNDING_DOWN == "DOWN", "DOWN rounding mode must be frozen"

    # PRNG prefixes must be exactly these bytes
    assert PRNG_SEED_PREFIX == b"COH_NPE_PRNG_V1", "PRNG seed prefix must be frozen"
    assert PRNG_NONCE_PREFIX == b"COH_NPE_PRNG_NONCE_V1", "PRNG nonce prefix must be frozen"

    # Hash lengths must match standard sizes
    assert SHA256_HEX_LEN == 64, "SHA256 hex length must be 64"
    assert CHACHA20_NONCE_LEN == 16, "ChaCha20 nonce must be 16 bytes"

    # Proposal types must be exactly these
    assert "RENORM_QUOTIENT" in PROPOSAL_TYPES
    assert "UNFOLD_QUOTIENT" in PROPOSAL_TYPES
    assert "CONTINUOUS_FLOW" in PROPOSAL_TYPES
    assert len(PROPOSAL_TYPES) == 3, "Must have exactly 3 proposal types"


# Run sanity checks at module load time
_sanity_check()


# ============================================================================
# Test Vector Expectations (Computed on-demand, never hardcoded)
# ============================================================================


def expected_spec_hashes() -> dict:
    """
    Return expected hashes of spec components.

    These are computed from locked constants and can be used to verify
    that the running NPE matches the frozen specification.

    Returns:
        Dictionary with keys: spec_version, prng_seed_prefix, prng_nonce_prefix
    """
    return {
        "spec_version": spec_version_hash(),
        "prng_seed_prefix": prng_seed_prefix_hash(),
        "prng_nonce_prefix": prng_nonce_prefix_hash(),
    }


if __name__ == "__main__":
    # Print locked constants for verification
    print("NPE v1.0.1 Locked Constants")
    print("=" * 60)
    print(f"Domain Separator: {DOMAIN_SEPARATOR}")
    print(f"Protocol Version: {PROTOCOL_VERSION}")
    print(f"Numeric Domain: {NUMERIC_DOMAIN}")
    print()
    print("Q18 Fixed-Point")
    print(f"  Scale: {Q18_SCALE}")
    print(f"  Range: [{Q18_MIN}, {Q18_MAX}]")
    print(f"  Fractional Mask: 0x{Q18_FRACTIONAL_MASK:06x}")
    print()
    print("Rounding Modes")
    print(f"  UP (debits): {ROUNDING_UP}")
    print(f"  DOWN (refunds): {ROUNDING_DOWN}")
    print()
    print("PRNG")
    print(f"  Seed Prefix: {PRNG_SEED_PREFIX}")
    print(f"  Nonce Prefix: {PRNG_NONCE_PREFIX}")
    print(f"  Seed Length: {CHACHA20_SEED_LEN} bytes")
    print(f"  Nonce Length: {CHACHA20_NONCE_LEN} bytes")
    print()
    print("Hashes")
    print(f"  SHA256: {SHA256_BYTES} bytes ({SHA256_HEX_LEN} hex chars)")
    print(f"  Proposal ID: {PROPOSAL_ID_HEX_LEN} hex chars")
    print()
    print("Proposal Types")
    print(f"  {', '.join(PROPOSAL_TYPES)}")
    print()
    print("Spec Component Hashes")
    hashes = expected_spec_hashes()
    for key, value in hashes.items():
        print(f"  {key}: {value}")
