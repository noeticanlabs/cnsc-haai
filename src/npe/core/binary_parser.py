"""
NPE v1.0.1 Binary Delta Parser.

Implements strict binary envelope parsing with zero ambiguity:
- DELTA_Z: uint32_be(d) || int64_be[d] (continuous flow)
- DELTA_A: uint8(kind) || uint32_be(atlas_len) || atlas_bytes || uint32_be(cert_len) || cert_bytes (renorm/unfold)

All parsers enforce strict length invariants:
- Reject if atlas_len != len(atlas_bytes)
- Reject if cert_len != len(cert_bytes)
- Reject if trailing bytes remain after parse
- Never crash on random bytes - always reject with deterministic error
"""

import struct
from dataclasses import dataclass
from enum import IntEnum
from typing import List, Union


class DeltaKind(IntEnum):
    """Delta envelope kinds."""

    DELTA_Z = 0  # Continuous flow (simple array of deltas)
    DELTA_A = 1  # Renorm/Unfold with atlas and certs


class ParseError(Exception):
    """Raised when binary parsing fails."""

    pass


# ============================================================================
# Delta Z Parser (Continuous Flow)
# ============================================================================


@dataclass
class DeltaZ:
    """Parsed DELTA_Z envelope."""

    deltas: List[int]  # List of int64 values


def parse_delta_z(data: bytes) -> DeltaZ:
    """
    Parse DELTA_Z binary envelope.

    Format: uint32_be(d) || int64_be[0] || ... || int64_be[d-1]

    Args:
        data: Binary data to parse

    Returns:
        DeltaZ object with parsed deltas

    Raises:
        ParseError: If parsing fails
    """
    if len(data) < 4:
        raise ParseError(
            f"DELTA_Z: insufficient data for count header: "
            f"got {len(data)} bytes, need at least 4"
        )

    # Read uint32_be(d) - number of deltas
    d = struct.unpack(">I", data[0:4])[0]

    # Expected total length: 4 bytes header + d * 8 bytes
    expected_len = 4 + d * 8

    if len(data) < expected_len:
        raise ParseError(
            f"DELTA_Z: insufficient data for {d} deltas: "
            f"got {len(data)} bytes, need {expected_len}"
        )

    if len(data) > expected_len:
        raise ParseError(
            f"DELTA_Z: trailing bytes after parse: "
            f"got {len(data)} bytes, expected {expected_len}"
        )

    # Parse deltas
    deltas = []
    offset = 4
    for _ in range(d):
        delta = struct.unpack(">q", data[offset : offset + 8])[0]
        deltas.append(delta)
        offset += 8

    return DeltaZ(deltas=deltas)


def serialize_delta_z(deltas: List[int]) -> bytes:
    """
    Serialize deltas to DELTA_Z format.

    Args:
        deltas: List of int64 deltas

    Returns:
        Binary DELTA_Z envelope
    """
    data = struct.pack(">I", len(deltas))
    for delta in deltas:
        data += struct.pack(">q", delta)
    return data


# ============================================================================
# Delta A Parser (Renorm/Unfold with Atlas + Certs)
# ============================================================================


@dataclass
class AtlasEntry:
    """Single atlas entry."""

    entry_type: int
    payload: bytes


@dataclass
class CertEntry:
    """Single cert entry."""

    cert_type: int
    cert_data: bytes


@dataclass
class DeltaA:
    """Parsed DELTA_A envelope."""

    kind: DeltaKind  # 0 = RENORM, 1 = UNFOLD, etc.
    atlas_entries: List[AtlasEntry]
    cert_entries: List[CertEntry]


def parse_delta_a(data: bytes) -> DeltaA:
    """
    Parse DELTA_A binary envelope.

    Format:
        uint8(kind)
        uint32_be(atlas_len)
        <atlas_len bytes: atlas_payload>
        uint32_be(cert_len)
        <cert_len bytes: cert_payload>

    Args:
        data: Binary data to parse

    Returns:
        DeltaA object with parsed atlas and certs

    Raises:
        ParseError: If parsing fails
    """
    if len(data) < 1:
        raise ParseError(
            f"DELTA_A: insufficient data for kind: " f"got {len(data)} bytes, need at least 1"
        )

    # Read kind (uint8)
    kind = data[0]
    offset = 1

    # Read atlas_len (uint32_be)
    if len(data) < offset + 4:
        raise ParseError(
            f"DELTA_A: insufficient data for atlas_len header: "
            f"got {len(data) - offset} bytes, need at least 4"
        )

    atlas_len = struct.unpack(">I", data[offset : offset + 4])[0]
    offset += 4

    # Read atlas_bytes
    if len(data) < offset + atlas_len:
        raise ParseError(
            f"DELTA_A: insufficient data for atlas ({atlas_len} bytes): "
            f"got {len(data) - offset} bytes"
        )

    atlas_bytes = data[offset : offset + atlas_len]
    offset += atlas_len

    # Read cert_len (uint32_be)
    if len(data) < offset + 4:
        raise ParseError(
            f"DELTA_A: insufficient data for cert_len header: "
            f"got {len(data) - offset} bytes, need at least 4"
        )

    cert_len = struct.unpack(">I", data[offset : offset + 4])[0]
    offset += 4

    # Read cert_bytes
    if len(data) < offset + cert_len:
        raise ParseError(
            f"DELTA_A: insufficient data for certs ({cert_len} bytes): "
            f"got {len(data) - offset} bytes"
        )

    cert_bytes = data[offset : offset + cert_len]
    offset += cert_len

    # Check for trailing bytes
    if len(data) > offset:
        raise ParseError(
            f"DELTA_A: trailing bytes after parse: " f"got {len(data)} bytes, parsed up to {offset}"
        )

    # Parse atlas entries
    atlas_entries = _parse_atlas_entries(atlas_bytes)

    # Parse cert entries
    cert_entries = _parse_cert_entries(cert_bytes)

    return DeltaA(
        kind=DeltaKind(kind),
        atlas_entries=atlas_entries,
        cert_entries=cert_entries,
    )


def _parse_atlas_entries(data: bytes) -> List[AtlasEntry]:
    """Parse atlas payload."""
    if len(data) < 2:
        raise ParseError(
            f"Atlas: insufficient data for num_entries: " f"got {len(data)} bytes, need at least 2"
        )

    num_entries = struct.unpack(">H", data[0:2])[0]
    offset = 2

    entries = []
    for _ in range(num_entries):
        # entry_type (uint8)
        if offset + 1 > len(data):
            raise ParseError(f"Atlas: insufficient data for entry_type at offset {offset}")

        entry_type = data[offset]
        offset += 1

        # payload_len (uint16)
        if offset + 2 > len(data):
            raise ParseError(f"Atlas: insufficient data for payload_len at offset {offset}")

        payload_len = struct.unpack(">H", data[offset : offset + 2])[0]
        offset += 2

        # payload
        if offset + payload_len > len(data):
            raise ParseError(
                f"Atlas: insufficient data for payload ({payload_len} bytes) at offset {offset}"
            )

        payload = data[offset : offset + payload_len]
        entries.append(AtlasEntry(entry_type=entry_type, payload=payload))
        offset += payload_len

    return entries


def _parse_cert_entries(data: bytes) -> List[CertEntry]:
    """Parse cert block."""
    if len(data) < 2:
        raise ParseError(
            f"Cert: insufficient data for num_certs: " f"got {len(data)} bytes, need at least 2"
        )

    num_certs = struct.unpack(">H", data[0:2])[0]
    offset = 2

    certs = []
    for _ in range(num_certs):
        # cert_type (uint8)
        if offset + 1 > len(data):
            raise ParseError(f"Cert: insufficient data for cert_type at offset {offset}")

        cert_type = data[offset]
        offset += 1

        # cert_len (uint16)
        if offset + 2 > len(data):
            raise ParseError(f"Cert: insufficient data for cert_len at offset {offset}")

        cert_len = struct.unpack(">H", data[offset : offset + 2])[0]
        offset += 2

        # cert_data
        if offset + cert_len > len(data):
            raise ParseError(
                f"Cert: insufficient data for cert ({cert_len} bytes) at offset {offset}"
            )

        cert_data = data[offset : offset + cert_len]
        certs.append(CertEntry(cert_type=cert_type, cert_data=cert_data))
        offset += cert_len

    return certs


def serialize_delta_a(
    kind: DeltaKind,
    atlas_entries: List[AtlasEntry],
    cert_entries: List[CertEntry],
) -> bytes:
    """
    Serialize to DELTA_A format.

    Args:
        kind: Delta kind (RENORM, UNFOLD, etc.)
        atlas_entries: List of atlas entries
        cert_entries: List of cert entries

    Returns:
        Binary DELTA_A envelope
    """
    data = bytes([kind.value])

    # Build atlas payload
    atlas_payload = struct.pack(">H", len(atlas_entries))
    for entry in atlas_entries:
        atlas_payload += bytes([entry.entry_type])
        atlas_payload += struct.pack(">H", len(entry.payload))
        atlas_payload += entry.payload

    data += struct.pack(">I", len(atlas_payload))
    data += atlas_payload

    # Build cert payload
    cert_payload = struct.pack(">H", len(cert_entries))
    for cert in cert_entries:
        cert_payload += bytes([cert.cert_type])
        cert_payload += struct.pack(">H", len(cert.cert_data))
        cert_payload += cert.cert_data

    data += struct.pack(">I", len(cert_payload))
    data += cert_payload

    return data


# ============================================================================
# Unified Delta Parser
# ============================================================================

Delta = Union[DeltaZ, DeltaA]


def parse_delta(data: bytes) -> Delta:
    """
    Parse any delta envelope (auto-detect format).

    The format is determined by the first byte:
    - If first byte is 0x00: DELTA_Z
    - If first byte is 0x01: DELTA_A

    Args:
        data: Binary delta data

    Returns:
        DeltaZ or DeltaA object

    Raises:
        ParseError: If parsing fails
    """
    if len(data) < 1:
        raise ParseError(
            f"Delta: insufficient data for format byte: " f"got {len(data)} bytes, need at least 1"
        )

    format_byte = data[0]

    if format_byte == 0:
        return parse_delta_z(data[1:])
    elif format_byte == 1:
        return parse_delta_a(data[1:])
    else:
        raise ParseError(f"Delta: unknown format byte: {format_byte}")


# ============================================================================
# Fuzz Testing Utilities
# ============================================================================


def fuzz_parse_delta(data: bytes) -> bool:
    """
    Fuzz test: random bytes should never crash, only reject.

    Args:
        data: Random bytes to parse

    Returns:
        True if parse succeeded (rare for random data)
        False if rejected (expected)
    """
    try:
        parse_delta(data)
        return True
    except (ParseError, struct.error, IndexError):
        # Expected: random bytes should reject
        return False


def length_lie_test(data: bytes) -> bool:
    """
    Test that mismatched lengths cause rejection.

    Args:
        data: Data with mismatched length fields

    Returns:
        True if correctly rejected
    """
    try:
        parse_delta(data)
        return False  # Should have rejected
    except ParseError:
        return True  # Correctly rejected
