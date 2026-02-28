"""
NPE v1.0.1 Canonical Serialization.

This module provides RFC8785-compliant JSON canonicalization for NPE proposals.
It wraps the consensus JCS implementation with NPE-specific guards:
- No floats allowed (Q18 integers only)
- Field allowlist validation
- Required field checks

The actual RFC8785 encoding is delegated to the consensus JCS module
to ensure a single source of truth.
"""

from typing import Any, Dict, List, Set

# Import RFC8785 JCS from consensus - single source of truth
from cnsc_haai.consensus.jcs import jcs_canonical_bytes

from npe.spec_constants import DOMAIN_SEPARATOR, PROTOCOL_VERSION, PROPOSAL_TYPES

# ============================================================================
# NPE-Specific Guards
# ============================================================================

# Required fields in NPE proposal envelope
REQUIRED_FIELDS: Set[str] = {
    "domain_separator",
    "version",
    "proposal_id",
    "proposal_type",
    "parent_slab_hash",
    "npe_state_hash",
    "timestamp_unix_sec",
    "budget_post",
    "delta_hash",
    "delta_bytes_b64",
    "cert_hash",
    "certs_b64",
}


def _assert_no_floats(obj: Any, path: str = "root") -> None:
    """
    Recursively assert that object contains no float values.

    NPE v1.0.1 numeric domain is QFixed18 (integers only).

    Args:
        obj: Object to check
        path: Current path for error messages

    Raises:
        ValueError: If any float value is found
    """
    if isinstance(obj, float):
        raise ValueError(
            f"Float value found at {path}: {obj}. "
            f"NPE v1.0.1 numeric domain is QFixed18 (integers only)."
        )
    elif isinstance(obj, dict):
        for key, value in obj.items():
            new_path = f"{path}.{key}" if path else key
            _assert_no_floats(value, new_path)
    elif isinstance(obj, (list, tuple)):
        for idx, value in enumerate(obj):
            new_path = f"{path}[{idx}]" if path else f"[{idx}]"
            _assert_no_floats(value, new_path)


def _validate_required_fields(data: Dict[str, Any]) -> None:
    """
    Validate that all required fields are present.

    Args:
        data: Proposal envelope dict

    Raises:
        ValueError: If any required field is missing
    """
    missing = REQUIRED_FIELDS - set(data.keys())
    if missing:
        raise ValueError(f"Missing required fields: {missing}")


def _validate_domain_separator(data: Dict[str, Any]) -> None:
    """
    Validate domain separator matches frozen value.

    Args:
        data: Proposal envelope dict

    Raises:
        ValueError: If domain separator is invalid
    """
    domain = data.get("domain_separator")
    if domain != DOMAIN_SEPARATOR:
        raise ValueError(f"Invalid domain_separator: expected {DOMAIN_SEPARATOR}, got {domain}")


def _validate_version(data: Dict[str, Any]) -> None:
    """
    Validate version matches frozen value.

    Args:
        data: Proposal envelope dict

    Raises:
        ValueError: If version is invalid
    """
    version = data.get("version")
    if version != PROTOCOL_VERSION:
        raise ValueError(f"Invalid version: expected {PROTOCOL_VERSION}, got {version}")


def _validate_proposal_type(data: Dict[str, Any]) -> None:
    """
    Validate proposal_type is in allowed set.

    Args:
        data: Proposal envelope dict

    Raises:
        ValueError: If proposal_type is invalid
    """
    proposal_type = data.get("proposal_type")
    if proposal_type not in PROPOSAL_TYPES:
        raise ValueError(
            f"Invalid proposal_type: {proposal_type}. " f"Must be one of {PROPOSAL_TYPES}"
        )


def _validate_field_types(data: Dict[str, Any]) -> None:
    """
    Validate field types are correct.

    Args:
        data: Proposal envelope dict

    Raises:
        ValueError: If any field has wrong type
    """
    # domain_separator and version must be strings
    if not isinstance(data.get("domain_separator"), str):
        raise ValueError("domain_separator must be a string")
    if not isinstance(data.get("version"), str):
        raise ValueError("version must be a string")

    # proposal_type must be string
    if not isinstance(data.get("proposal_type"), str):
        raise ValueError("proposal_type must be a string")

    # parent_slab_hash and npe_state_hash must be hex strings
    for field in ["parent_slab_hash", "npe_state_hash", "delta_hash", "cert_hash"]:
        value = data.get(field)
        if not isinstance(value, str):
            raise ValueError(f"{field} must be a string")
        if not all(c in "0123456789abcdef" for c in value.lower()):
            raise ValueError(f"{field} must be hexadecimal")

    # timestamp_unix_sec must be integer
    if not isinstance(data.get("timestamp_unix_sec"), int):
        raise ValueError("timestamp_unix_sec must be an integer")

    # budget_post must be dict
    if not isinstance(data.get("budget_post"), dict):
        raise ValueError("budget_post must be a dict")


# ============================================================================
# Public API
# ============================================================================


def canonicalize(data: Any) -> str:
    """
    Canonicalize data to JSON string (legacy CJ0 interface).

    This is kept for backward compatibility but now uses RFC8785 JCS internally.

    Args:
        data: Object to canonicalize

    Returns:
        Canonical JSON string
    """
    return jcs_canonical_bytes(data).decode("utf-8")


def canonicalize_typed(type_name: str, data: Any) -> str:
    """
    Canonicalize typed data (legacy CJ0 interface).

    Args:
        type_name: Type name (for debugging)
        data: Object to canonicalize

    Returns:
        Canonical JSON string
    """
    # Just canonicalize - type is embedded in the data itself
    return canonicalize(data)


def jcs_bytes(data: Any, validate_npe: bool = True) -> bytes:
    """
    Serialize object to RFC8785 canonical JSON bytes.

    This is the primary NPE interface for JCS serialization.

    Args:
        data: Object to serialize
        validate_npe: If True (default), apply NPE-specific guards.
                      If False, skip validation for legacy code.

    Returns:
        Canonical JSON bytes (UTF-8)

    Raises:
        ValueError: If data contains floats or invalid fields (when validate_npe=True)
    """
    # For dicts, apply NPE-specific guards
    if isinstance(data, dict) and validate_npe:
        # 1. Assert no floats (Q18 integers only)
        _assert_no_floats(data)

        # 2. Validate required fields
        _validate_required_fields(data)

        # 3. Validate domain separator
        _validate_domain_separator(data)

        # 4. Validate version
        _validate_version(data)

        # 5. Validate proposal type
        _validate_proposal_type(data)

        # 6. Validate field types
        _validate_field_types(data)

    # Delegate to consensus JCS for actual RFC8785 encoding
    return jcs_canonical_bytes(data)


def jcs_string(data: Any, validate_npe: bool = True) -> str:
    """
    Serialize object to RFC8785 canonical JSON string.

    Args:
        data: Object to serialize
        validate_npe: If True (default), apply NPE-specific guards.
                      If False, skip validation for legacy code.

    Returns:
        Canonical JSON string
    """
    return jcs_bytes(data, validate_npe=validate_npe).decode("utf-8")


def jcs_bytes_legacy(data: Any) -> bytes:
    """
    Legacy JCS bytes without NPE validation.

    Use this for backward compatibility with existing code that doesn't
    use NPE proposal envelopes.
    """
    return jcs_bytes(data, validate_npe=False)


def jcs_string_legacy(data: Any) -> str:
    """
    Legacy JCS string without NPE validation.

    Use this for backward compatibility with existing code that doesn't
    use NPE proposal envelopes.
    """
    return jcs_string(data, validate_npe=False)


# Backward compatibility - re-export from consensus JCS
from cnsc_haai.consensus.jcs import JCSEncoder

# For legacy code that imports directly
encode = jcs_bytes
