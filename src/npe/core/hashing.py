"""
NPE v1.0.1 Hashing Functions.

Implements SHA256 hashing with NPE v1.0.1 domain separation:
- Proposal hashing: sha256(jcs_bytes(proposal_envelope))
- Delta hashing: sha256(delta_bytes) after base64 decode
- Cert hashing: sha256(cert_bytes)

All hashing uses RFC8785 JCS canonicalization (via canon.py wrapper).
"""

import base64
import hashlib
from typing import Any, Optional

from .canon import jcs_bytes, jcs_string


def _compute_sha256(data: bytes) -> str:
    """
    Compute SHA256 hash of bytes.

    Args:
        data: Bytes to hash

    Returns:
        Lowercase hexadecimal hash string
    """
    return hashlib.sha256(data).hexdigest()


def hash_proposal(envelope: dict) -> str:
    """
    Hash a proposal envelope using RFC8785 JCS.

    This is the primary NPE proposal hash function. It uses JCS canonicalization
    to ensure byte-identical hashes regardless of JSON formatting.

    Args:
        envelope: Proposal envelope dict

    Returns:
        Lowercase hex SHA256 hash

    Raises:
        ValueError: If envelope contains floats or invalid fields
    """
    # jcs_bytes applies NPE-specific guards (no floats, required fields, etc.)
    canonical = jcs_bytes(envelope)
    return _compute_sha256(canonical)


def hash_delta(delta_bytes_b64: str) -> str:
    """
    Compute delta_hash from base64-encoded delta bytes.

    Per spec: delta_hash = sha256(raw_delta_bytes)

    Args:
        delta_bytes_b64: Base64-encoded delta bytes

    Returns:
        Lowercase hex SHA256 hash
    """
    delta_bytes = base64.b64decode(delta_bytes_b64)
    return _compute_sha256(delta_bytes)


def hash_cert(cert_bytes_b64: str) -> str:
    """
    Compute cert_hash from base64-encoded cert block.

    Per spec: cert_hash = sha256(cert_bytes_for_hash)

    Args:
        cert_bytes_b64: Base64-encoded cert block (or empty string)

    Returns:
        Lowercase hex SHA256 hash
    """
    if cert_bytes_b64:
        cert_bytes = base64.b64decode(cert_bytes_b64)
    else:
        cert_bytes = b""
    return _compute_sha256(cert_bytes)


def verify_proposal_hash(envelope: dict, expected_hash: str) -> bool:
    """
    Verify that proposal envelope hash matches expected.

    Args:
        envelope: Proposal envelope dict
        expected_hash: Expected hash value

    Returns:
        True if hash matches, False otherwise
    """
    try:
        actual = hash_proposal(envelope)
        return actual == expected_hash
    except (ValueError, Exception):
        return False


def verify_delta_hash(delta_bytes_b64: str, expected_hash: str) -> bool:
    """
    Verify that delta hash matches expected.

    Args:
        delta_bytes_b64: Base64-encoded delta bytes
        expected_hash: Expected hash value

    Returns:
        True if hash matches, False otherwise
    """
    try:
        actual = hash_delta(delta_bytes_b64)
        return actual == expected_hash
    except Exception:
        return False


# ============================================================================
# Legacy Compatibility Functions
# ============================================================================


def hash_request(payload: Any) -> str:
    """Hash an NPE request (legacy interface)."""
    from npe.core.canon import jcs_string_legacy

    canonical = jcs_string_legacy(payload)
    return _compute_sha256(canonical.encode("utf-8"))


def hash_evidence(payload: Any) -> str:
    """Hash an evidence item (legacy interface)."""
    from npe.core.canon import jcs_string_legacy

    canonical = jcs_string_legacy(payload)
    return _compute_sha256(canonical.encode("utf-8"))


def hash_candidate_payload(payload: Any) -> str:
    """Hash a candidate payload (legacy interface)."""
    from npe.core.canon import jcs_string_legacy

    canonical = jcs_string_legacy(payload)
    return _compute_sha256(canonical.encode("utf-8"))


def hash_candidate(envelope: Any) -> str:
    """Hash a candidate envelope (legacy interface)."""
    from npe.core.canon import jcs_string_legacy

    canonical = jcs_string_legacy(envelope)
    return _compute_sha256(canonical.encode("utf-8"))


def hash_response(payload: Any) -> str:
    """Hash an NPE response (legacy interface)."""
    from npe.core.canon import jcs_string_legacy

    canonical = jcs_string_legacy(payload)
    return _compute_sha256(canonical.encode("utf-8"))


def hash_registry(manifest_normalized: Any) -> str:
    """Hash a registry manifest (legacy interface)."""
    from npe.core.canon import jcs_string_legacy

    canonical = jcs_string_legacy(manifest_normalized)
    return _compute_sha256(canonical.encode("utf-8"))


def hash_string(data: str) -> str:
    """Hash a string (legacy interface)."""
    return _compute_sha256(data.encode("utf-8"))


def hash_dict(data: dict) -> str:
    """Hash a dict (legacy interface)."""
    from npe.core.canon import jcs_string_legacy

    canonical = jcs_string_legacy(data)
    return _compute_sha256(canonical.encode("utf-8"))


def hash_list(data: list) -> str:
    """Hash a list (legacy interface)."""
    canonical = jcs_string(data)
    return _compute_sha256(canonical.encode("utf-8"))


def hash_corpus_snapshot(chunk_hashes: list) -> str:
    """
    Hash a corpus snapshot from chunk hashes.

    Per spec: snapshot_hash = sha256(jcs_bytes(sorted(chunk_hashes)))

    Args:
        chunk_hashes: List of chunk hash strings

    Returns:
        Lowercase hex SHA256 hash
    """
    # Sort for deterministic ordering
    sorted_hashes = sorted(chunk_hashes)
    canonical = jcs_string(sorted_hashes)
    return _compute_sha256(canonical.encode("utf-8"))


def hash_receipts_snapshot(receipt_hashes: list) -> str:
    """
    Hash a receipts snapshot from receipt hashes.

    Per spec: snapshot_hash = sha256(jcs_bytes(sorted(receipt_hashes)))

    Args:
        receipt_hashes: List of receipt hash strings

    Returns:
        Lowercase hex SHA256 hash
    """
    # Sort for deterministic ordering
    sorted_hashes = sorted(receipt_hashes)
    canonical = jcs_string(sorted_hashes)
    return _compute_sha256(canonical.encode("utf-8"))
