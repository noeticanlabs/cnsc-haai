"""
Micro Leaf Codec for ATS Receipts

Provides encoding/decoding for micro leaves in Merkle trees:
- Codec ID: coh.micro.codec.ats_receipt_core.v1
- Encoding: JCS UTF-8 of stripped receipt core
"""

from typing import Dict, Any, Optional

from .jcs import jcs_canonical_bytes
from .hash import sha256_prefixed


# Micro leaf codec identifier
MICRO_LEAF_CODEC_ID = "coh.micro.codec.ats_receipt_core.v1"


# Fields to strip from receipt for micro leaf (non-consensus)
FIELDS_TO_STRIP = [
    "timestamp",
    "episode_id",
    "provenance",
    "signature",
    "metadata",
    "telemetry",
]


def strip_to_core(receipt: Dict[str, Any]) -> Dict[str, Any]:
    """
    Strip non-consensus fields from receipt to get core.
    
    Removes:
    - timestamp (non-deterministic)
    - episode_id (debug only)
    - provenance (debug only)
    - signature (debug only)
    - metadata (debug only)
    - telemetry (debug only)
    
    Args:
        receipt: Full receipt dictionary
        
    Returns:
        Receipt core with only consensus-critical fields
    """
    core = {}
    
    for key, value in receipt.items():
        if key in FIELDS_TO_STRIP:
            continue
        if key == "receipt_body":
            # Recursively strip receipt_body
            if isinstance(value, dict):
                core[key] = strip_to_core(value)
            else:
                core[key] = value
        elif isinstance(value, dict):
            # Recursively process nested dicts
            core[key] = strip_to_core(value)
        else:
            core[key] = value
    
    return core


def encode_micro_leaf(receipt: Dict[str, Any]) -> bytes:
    """
    Encode a receipt to micro leaf bytes.
    
    Leaf bytes = JCS UTF-8 of the stripped receipt core
    
    Args:
        receipt: Full receipt dictionary
        
    Returns:
        JCS canonical bytes of receipt core
    """
    core = strip_to_core(receipt)
    return jcs_canonical_bytes(core)


def encode_micro_leaf_hash(receipt: Dict[str, Any]) -> str:
    """
    Compute micro leaf hash.
    
    Args:
        receipt: Full receipt dictionary
        
    Returns:
        SHA256 prefixed hash of micro leaf
    """
    leaf_bytes = encode_micro_leaf(receipt)
    return sha256_prefixed(leaf_bytes)


def verify_micro_leaf(
    receipt: Dict[str, Any],
    expected_hash: str
) -> bool:
    """
    Verify that a receipt produces the expected micro leaf hash.
    
    Args:
        receipt: Full receipt dictionary
        expected_hash: Expected sha256: prefixed hash
        
    Returns:
        True if hash matches
    """
    actual_hash = encode_micro_leaf_hash(receipt)
    return actual_hash == expected_hash


class MicroLeafCodec:
    """
    Micro leaf codec for ATS receipt cores.
    
    Codec ID: coh.micro.codec.ats_receipt_core.v1
    
    Usage:
        codec = MicroLeafCodec()
        leaf_bytes = codec.encode(receipt)
        hash = codec.hash(receipt)
        verified = codec.verify(receipt, expected_hash)
    """
    
    CODEC_ID = MICRO_LEAF_CODEC_ID
    
    def __init__(self):
        """Initialize the micro leaf codec."""
        pass
    
    @property
    def codec_id(self) -> str:
        """Get the codec identifier."""
        return self.CODEC_ID
    
    def encode(self, receipt: Dict[str, Any]) -> bytes:
        """
        Encode a receipt to micro leaf bytes.
        
        Args:
            receipt: Full receipt dictionary
            
        Returns:
            JCS canonical bytes
        """
        return encode_micro_leaf(receipt)
    
    def hash(self, receipt: Dict[str, Any]) -> str:
        """
        Compute micro leaf hash.
        
        Args:
            receipt: Full receipt dictionary
            
        Returns:
            SHA256 prefixed hash
        """
        return encode_micro_leaf_hash(receipt)
    
    def verify(
        self,
        receipt: Dict[str, Any],
        expected_hash: str
    ) -> bool:
        """
        Verify micro leaf hash.
        
        Args:
            receipt: Full receipt dictionary
            expected_hash: Expected hash
            
        Returns:
            True if verified
        """
        return verify_micro_leaf(receipt, expected_hash)
    
    def strip(self, receipt: Dict[str, Any]) -> Dict[str, Any]:
        """
        Strip non-consensus fields from receipt.
        
        Args:
            receipt: Full receipt
            
        Returns:
            Receipt core
        """
        return strip_to_core(receipt)
