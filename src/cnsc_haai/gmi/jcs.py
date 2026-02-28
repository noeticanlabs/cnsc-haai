"""
JCS (JSON Canonicalization) - RFC8785 Subset

This module provides deterministic JSON serialization for GMI.
Floats are forbidden - only int, bool, str, list, dict, None allowed.
"""

import json
from typing import Any


def jcs_dumps(obj: Any) -> bytes:
    """
    Canonical JSON serialization (RFC8785 subset).

    Rules:
    - Sorted object keys (alphabetical)
    - No whitespace variations (minimal separators)
    - No floats allowed (must be int/bool/str/list/dict/None)
    - Non-string keys forbidden

    Args:
        obj: Python object to serialize (no floats!)

    Returns:
        UTF-8 encoded canonical JSON bytes

    Raises:
        TypeError: If floats are present
    """

    def check_no_float(x: Any) -> None:
        """Recursively check for floats."""
        if isinstance(x, float):
            raise TypeError("Floats forbidden in JCS")
        if isinstance(x, dict):
            for k, v in x.items():
                if not isinstance(k, str):
                    raise TypeError("Non-string key forbidden in JCS")
                check_no_float(v)
        elif isinstance(x, list):
            for v in x:
                check_no_float(v)

    check_no_float(obj)

    # Minimal separators for deterministic output
    s = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return s.encode("utf-8")


def jcs_dumps_str(obj: Any) -> str:
    """Return canonical JSON as string."""
    return jcs_dumps(obj).decode("utf-8")


def jcs_verify(obj: Any) -> bool:
    """
    Verify object contains no floats (required for JCS).

    Returns:
        True if float-free, False otherwise
    """
    try:
        jcs_dumps(obj)
        return True
    except TypeError:
        return False
