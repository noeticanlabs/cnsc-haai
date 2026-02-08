"""
CJ0 Canonical JSON Encoder.

Implements canonical JSON serialization with the following rules:
- Sort keys lexicographically
- No extra whitespace
- Arrays preserve order
- Numbers normalized (ints as decimal, floats as fixed precision)
- UTF-8 encoding
"""

import json
from typing import Any, Union


# Precision for float serialization
FLOAT_PRECISION = 15


def _encode_value(value: Any) -> Any:
    """Encode a single value to its canonical form.
    
    Args:
        value: The value to encode
        
    Returns:
        Canonically encoded value
    """
    if value is None:
        return None
    elif isinstance(value, bool):
        return value
    elif isinstance(value, (int, float)):
        return _encode_number(value)
    elif isinstance(value, str):
        return value
    elif isinstance(value, dict):
        return _encode_dict(value)
    elif isinstance(value, (list, tuple)):
        return _encode_list(value)
    elif isinstance(value, bytes):
        return value.decode("utf-8")
    else:
        # For other types, convert to string
        return str(value)


def _encode_number(value: Union[int, float]) -> Union[int, str]:
    """Encode a number to its canonical form.
    
    Args:
        value: The number to encode
        
    Returns:
        Integer as-is, float as fixed-precision string
    """
    if isinstance(value, int):
        return value
    elif isinstance(value, float):
        if value != value:  # NaN check
            return "null"
        elif value == float("inf"):
            return "Infinity"
        elif value == float("-inf"):
            return "-Infinity"
        else:
            # Format with fixed precision, removing trailing zeros
            formatted = f"{value:.{FLOAT_PRECISION}f}"
            # Remove trailing zeros after decimal point
            if "." in formatted:
                formatted = formatted.rstrip("0").rstrip(".")
            return formatted
    else:
        return str(value)


def _encode_dict(obj: dict) -> dict:
    """Encode a dict with sorted keys.
    
    Args:
        obj: The dict to encode
        
    Returns:
        New dict with sorted keys and encoded values
    """
    return {k: _encode_value(obj[k]) for k in sorted(obj.keys())}


def _encode_list(arr: list) -> list:
    """Encode a list with preserved order.
    
    Args:
        arr: The list to encode
        
    Returns:
        New list with encoded values
    """
    return [_encode_value(item) for item in arr]


def canonicalize(obj: Any) -> str:
    """Convert an object to canonical JSON string.
    
    Args:
        obj: The object to serialize
        
    Returns:
        Canonical JSON string
    """
    encoded = _encode_value(obj)
    return json.dumps(encoded, separators=(",", ":"), ensure_ascii=False)


def canonicalize_typed(type_name: str, payload: Any) -> str:
    """Create a typed canonical string for hashing.
    
    Args:
        type_name: The type name prefix
        payload: The payload to serialize
        
    Returns:
        Typed canonical string: "NPE|1.0|type|CJ0(payload)"
    """
    cj0 = canonicalize(payload)
    return f"NPE|1.0|{type_name}|{cj0}"


def canonicalize_for_hash(payload: Any) -> str:
    """Create a canonical string suitable for hashing.
    
    Args:
        payload: The payload to serialize
        
    Returns:
        Canonical JSON string for hashing
    """
    return canonicalize(payload)
