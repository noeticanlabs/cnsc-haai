"""
JCS (JSON Canonicalization Scheme) - RFC 8785 Implementation

This module provides deterministic JSON serialization per RFC 8785:
https://www.rfc-editor.org/rfc/rfc8785.html

All implementations must produce identical byte output for the same JSON input.
"""

import json
from typing import Any, Dict, List, Union


def jcs_canonical_bytes(obj: Any) -> bytes:
    """
    Serialize an object to canonical JSON bytes per RFC 8785.

    Rules:
    1. Objects: sorted keys, no whitespace variation
    2. Arrays: preserve order, no whitespace
    3. Strings: UTF-8 encoded
    4. Numbers: no unnecessary leading zeros, no + sign, no scientific notation
    5. null: lowercase

    Args:
        obj: The object to serialize

    Returns:
        Canonical JSON bytes (UTF-8)
    """
    return _encode_value(obj).encode("utf-8")


def _encode_value(value: Any) -> str:
    """Encode a single value to canonical JSON string."""
    if value is None:
        return "null"
    elif isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, int):
        # Integers are allowed (QFixed domain)
        return _encode_number(value)
    elif isinstance(value, float):
        # Floats are NOT allowed in consensus - reject them
        raise TypeError(f"Floats not allowed in consensus - use QFixed int: got {type(value)}")
    elif isinstance(value, str):
        return _encode_string(value)
    elif isinstance(value, (list, tuple)):
        return _encode_array(value)
    elif isinstance(value, dict):
        return _encode_object(value)
    else:
        raise TypeError(f"Cannot encode type: {type(value)}")


def _encode_string(s: str) -> str:
    """Encode a string with proper escaping per RFC 8785."""
    # JSON escaping rules
    result = []
    for char in s:
        code = ord(char)
        if code < 0x20:
            # Control characters must be escaped
            escape_map = {
                0x08: "\\b",
                0x0C: "\\f",
                0x0A: "\\n",
                0x0D: "\\r",
                0x09: "\\t",
            }
            result.append(escape_map.get(code, f"\\u{code:04x}"))
        elif char == '"':
            result.append('\\"')
        elif char == "\\":
            result.append("\\\\")
        else:
            # ASCII printable chars pass through
            if code < 0x80 and 0x20 <= code < 0x7F:
                result.append(char)
            else:
                # Unicode - encode as UTF-8 bytes, then escape
                result.append(char)
    return '"' + "".join(result) + '"'


def _encode_number(n: Union[int, float]) -> str:
    """Encode a number canonically."""
    if isinstance(n, int):
        # Integers: no leading zeros, no + sign
        if n == 0:
            return "0"
        elif n > 0:
            return str(n)
        else:
            return str(n)
    else:
        # Floats: no scientific notation, no unnecessary trailing zeros
        if n != n:  # NaN
            return "null"
        if n == float("inf"):
            return "null"
        if n == float("-inf"):
            return "null"

        # Format without scientific notation
        s = f"{n:.15f}".rstrip("0").rstrip(".")
        # Remove leading zeros after decimal point
        if "." in s:
            s = s.lstrip("0") or "0"
        return s


def _encode_array(arr: List[Any]) -> str:
    """Encode an array with preserved order."""
    items = [_encode_value(item) for item in arr]
    return "[" + ",".join(items) + "]"


def _encode_object(obj: Dict[str, Any]) -> str:
    """Encode an object with sorted keys."""
    # Sort keys lexicographically
    keys = sorted(obj.keys())
    items = [f"{_encode_string(k)}:{_encode_value(obj[k])}" for k in keys]
    return "{" + ",".join(items) + "}"


class JCSEncoder:
    """
    RFC 8785 JSON Canonicalization Scheme encoder.

    Usage:
        encoder = JCSEncoder()
        canonical_bytes = encoder.encode(data)
    """

    def __init__(self):
        """Initialize the JCS encoder."""
        pass

    def encode(self, obj: Any) -> bytes:
        """
        Encode an object to canonical JSON bytes.

        Args:
            obj: The object to serialize

        Returns:
            Canonical JSON bytes (UTF-8)
        """
        return jcs_canonical_bytes(obj)

    def encode_to_string(self, obj: Any) -> str:
        """
        Encode an object to canonical JSON string.

        Args:
            obj: The object to serialize

        Returns:
            Canonical JSON string
        """
        return jcs_canonical_bytes(obj).decode("utf-8")

    def verify_deterministic(self, data: Any) -> bool:
        """
        Verify that encoding is deterministic by double-encoding.

        Args:
            data: The data to test

        Returns:
            True if encoding is deterministic
        """
        first = jcs_canonical_bytes(data)
        second = jcs_canonical_bytes(json.loads(first.decode("utf-8")))
        return first == second


# Convenience function
encode = jcs_canonical_bytes
