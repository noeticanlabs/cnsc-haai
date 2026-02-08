"""
Typed Hashing Functions.

Implements SHA256 hashing with type prefixes for different NPE objects.
All hashes follow the format: sha256("NPE|1.0|" + <type> + "|" + CJ0(payload))
"""

import hashlib
from typing import Any, List, Optional

from .canon import canonicalize, canonicalize_typed


def _compute_sha256(data: str) -> str:
    """Compute SHA256 hash of a string.
    
    Args:
        data: The string to hash
        
    Returns:
        Hexadecimal hash string
    """
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def hash_request(payload: Any) -> str:
    """Hash an NPE request.
    
    Args:
        payload: The request payload
        
    Returns:
        Request ID (hash)
    """
    cj0 = canonicalize_typed("request", payload)
    return _compute_sha256(cj0)


def hash_evidence(payload: Any) -> str:
    """Hash an evidence item.
    
    Args:
        payload: The evidence payload
        
    Returns:
        Evidence ID (hash)
    """
    cj0 = canonicalize_typed("evidence", payload)
    return _compute_sha256(cj0)


def hash_candidate_payload(payload: Any) -> str:
    """Hash a candidate payload.
    
    Args:
        payload: The candidate payload
        
    Returns:
        Payload hash
    """
    cj0 = canonicalize_typed("candidate_payload", payload)
    return _compute_sha256(cj0)


def hash_candidate(envelope: Any) -> str:
    """Hash a candidate envelope.
    
    Args:
        envelope: The candidate envelope
        
    Returns:
        Candidate hash
    """
    cj0 = canonicalize_typed("candidate", envelope)
    return _compute_sha256(cj0)


def hash_response(payload: Any) -> str:
    """Hash an NPE response.
    
    Args:
        payload: The response payload
        
    Returns:
        Response ID (hash)
    """
    cj0 = canonicalize_typed("response", payload)
    return _compute_sha256(cj0)


def hash_registry(manifest_normalized: Any) -> str:
    """Hash a registry manifest.
    
    Args:
        manifest_normalized: The normalized manifest
        
    Returns:
        Registry hash
    """
    cj0 = canonicalize_typed("registry", manifest_normalized)
    return _compute_sha256(cj0)


def hash_corpus_snapshot(sorted_chunk_hashes: List[str]) -> str:
    """Hash a corpus snapshot from sorted chunk hashes.
    
    Args:
        sorted_chunk_hashes: Sorted list of chunk hashes
        
    Returns:
        Corpus snapshot hash
    """
    payload = {"chunks": sorted_chunk_hashes}
    cj0 = canonicalize_typed("corpus_snapshot", payload)
    return _compute_sha256(cj0)


def hash_receipts_snapshot(sorted_receipt_hashes: List[str]) -> str:
    """Hash a receipts snapshot from sorted receipt hashes.
    
    Args:
        sorted_receipt_hashes: Sorted list of receipt hashes
        
    Returns:
        Receipts snapshot hash
    """
    payload = {"receipts": sorted_receipt_hashes}
    cj0 = canonicalize_typed("receipts_snapshot", payload)
    return _compute_sha256(cj0)


def hash_string(content: str) -> str:
    """Hash a plain string content.
    
    Args:
        content: The string content
        
    Returns:
        Hash string
    """
    return _compute_sha256(content)


def hash_dict(obj: dict) -> str:
    """Hash a dictionary (sorted keys).
    
    Args:
        obj: The dictionary to hash
        
    Returns:
        Hash string
    """
    return _compute_sha256(canonicalize(obj))


def hash_list(arr: List[Any]) -> str:
    """Hash a list (preserves order).
    
    Args:
        arr: The list to hash
        
    Returns:
        Hash string
    """
    return _compute_sha256(canonicalize(arr))
