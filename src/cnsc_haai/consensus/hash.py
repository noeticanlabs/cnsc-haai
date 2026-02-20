"""
SHA256 Hash Utilities

Provides SHA256 operations with the 'sha256:' prefix convention required for ATS v3 receipts.
All digests in JSON use the 'sha256:' prefix for clarity.
"""

import hashlib
from typing import Union


# Prefix constant
SHA256_PREFIX = "sha256:"


def sha256(data: Union[bytes, str]) -> bytes:
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
        64-character hex string (without prefix)
    """
    return sha256(data).hex()


def sha256_prefixed(data: Union[bytes, str]) -> str:
    """
    Compute SHA256 hash and return with 'sha256:' prefix.
    
    This is the standard format for all digests in ATS v3 receipts.
    
    Args:
        data: Bytes or string to hash
        
    Returns:
        'sha256:' followed by 64 hex characters
    """
    return SHA256_PREFIX + sha256_hex(data)


def decode_sha256_prefixed(digest: str) -> bytes:
    """
    Decode a 'sha256:' prefixed digest to raw 32 bytes.
    
    Args:
        digest: String like 'sha256:a1b2c3...'
        
    Returns:
        Raw 32-byte SHA256 hash
        
    Raises:
        ValueError: If format is invalid
    """
    if not digest.startswith(SHA256_PREFIX):
        raise ValueError(f"Invalid digest format: missing '{SHA256_PREFIX}' prefix")
    
    hex_part = digest[len(SHA256_PREFIX):]
    
    if len(hex_part) != 64:
        raise ValueError(f"Invalid SHA256 length: {len(hex_part)} (expected 64)")
    
    if not all(c in "0123456789abcdefABCDEF" for c in hex_part):
        raise ValueError(f"Invalid hex characters in digest")
    
    return bytes.fromhex(hex_part)


def verify_sha256_prefixed(digest: str, data: Union[bytes, str]) -> bool:
    """
    Verify that data produces the given digest.
    
    Args:
        digest: Expected digest with 'sha256:' prefix
        data: Data to verify
        
    Returns:
        True if hash matches
    """
    try:
        expected = decode_sha256_prefixed(digest)
        actual = sha256(data)
        return expected == actual
    except ValueError:
        return False


class Sha256Digest:
    """
    Helper class for working with SHA256 digests.
    
    Usage:
        digest = Sha256Digest.from_data(data)
        print(digest.prefixed)  # 'sha256:...'
        print(digest.raw)        # b'...'
    """
    
    def __init__(self, raw: bytes):
        """
        Create digest from raw bytes.
        
        Args:
            raw: 32-byte SHA256 hash
        """
        if len(raw) != 32:
            raise ValueError(f"Invalid SHA256 length: {len(raw)}")
        self._raw = raw
    
    @classmethod
    def from_data(cls, data: Union[bytes, str]) -> "Sha256Digest":
        """Create digest from data."""
        return cls(sha256(data))
    
    @classmethod
    def from_prefixed(cls, digest: str) -> "Sha256Digest":
        """Create digest from prefixed string."""
        return cls(decode_sha256_prefixed(digest))
    
    @property
    def raw(self) -> bytes:
        """Get raw 32-byte hash."""
        return self._raw
    
    @property
    def hex(self) -> str:
        """Get 64-character hex string."""
        return self._raw.hex()
    
    @property
    def prefixed(self) -> str:
        """Get prefixed digest string."""
        return SHA256_PREFIX + self.hex
    
    def __str__(self) -> str:
        return self.prefixed
    
    def __repr__(self) -> str:
        return f"Sha256Digest('{self.prefixed}')"
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, Sha256Digest):
            return self._raw == other._raw
        elif isinstance(other, str):
            return self.prefixed == other
        elif isinstance(other, bytes):
            return self._raw == other
        return False
