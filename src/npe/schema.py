"""
Schema Loading Utilities for NPE.

Provides robust schema loading using pathlib.Path,
allowing schemas to be loaded from the package regardless of
the current working directory.
"""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Optional


# Schema file names to NPE spec type mapping
SCHEMA_FILES = {
    "npe_request.schema.json": "request",
    "npe_response.schema.json": "response",
}

# Cache for loaded schemas
_schema_cache: Dict[str, Any] = {}

# Cache for schema hashes
_schema_hash_cache: Dict[str, str] = {}


def get_schema_dir() -> Path:
    """Get the directory containing NPE schemas.
    
    Returns:
        Path to the schemas directory within the npe package.
    """
    # Navigate from this file to the package root, then to schemas
    # This file is at src/npe/schema.py, so:
    # - parent = src/npe/
    # - parent.parent = src/
    # - parent.parent.parent = repo root
    # Schemas are at src/npe/schemas/
    return Path(__file__).parent / "schemas"


def load_schema(schema_filename: str) -> Optional[Any]:
    """Load a JSON schema from the package schemas directory.
    
    Args:
        schema_filename: Name of the schema file (e.g., 'npe_request.schema.json')
        
    Returns:
        Parsed JSON schema as a dict, or None if loading fails.
    """
    # Check cache first
    if schema_filename in _schema_cache:
        return _schema_cache[schema_filename]
    
    try:
        schema_dir = get_schema_dir()
        schema_path = schema_dir / schema_filename
        
        if not schema_path.exists():
            # Fall back to legacy location (repo root schemas/)
            repo_root = Path(__file__).parent.parent.parent
            legacy_path = repo_root / "schemas" / schema_filename
            if legacy_path.exists():
                with open(legacy_path, "r") as f:
                    schema = json.load(f)
                    _schema_cache[schema_filename] = schema
                    return schema
            return None
        
        with open(schema_path, "r") as f:
            schema = json.load(f)
            _schema_cache[schema_filename] = schema
            return schema
    
    except (OSError, json.JSONDecodeError) as e:
        print(f"Warning: Failed to load schema '{schema_filename}': {e}")
        return None


def load_request_schema() -> Optional[Any]:
    """Load the NPE request schema.
    
    Returns:
        Parsed request schema or None if loading fails.
    """
    return load_schema("npe_request.schema.json")


def load_response_schema() -> Optional[Any]:
    """Load the NPE response schema.
    
    Returns:
        Parsed response schema or None if loading fails.
    """
    return load_schema("npe_response.schema.json")


def clear_schema_cache() -> None:
    """Clear the schema cache. Useful for testing."""
    _schema_cache.clear()
    _schema_hash_cache.clear()


def get_schema_hash(schema_filename: str) -> Optional[str]:
    """Get the hash of a schema file for deterministic identification.
    
    Args:
        schema_filename: Name of the schema file
        
    Returns:
        SHA256 hash of the schema content, or None if loading fails
    """
    # Check hash cache first
    if schema_filename in _schema_hash_cache:
        return _schema_hash_cache[schema_filename]
    
    # Load schema to get hash
    schema = load_schema(schema_filename)
    if schema is None:
        return None
    
    # Compute hash from canonical JSON representation
    # Use sorted keys for deterministic hashing
    schema_str = json.dumps(schema, sort_keys=True)
    schema_hash = hashlib.sha256(schema_str.encode('utf-8')).hexdigest()
    
    # Cache the hash
    _schema_hash_cache[schema_filename] = schema_hash
    
    return schema_hash


def get_all_schema_hashes() -> Dict[str, str]:
    """Get hashes of all known schemas.
    
    Returns:
        Dict mapping schema filename to its hash
    """
    hashes = {}
    for schema_filename in SCHEMA_FILES:
        schema_hash = get_schema_hash(schema_filename)
        if schema_hash:
            hashes[schema_filename] = schema_hash
    return hashes


def get_schema_bundle_hash() -> Optional[str]:
    """Get a combined hash of all schemas (schema bundle version).
    
    Returns:
        Combined hash of all schema hashes, or None if no schemas load
    """
    all_hashes = get_all_schema_hashes()
    if not all_hashes:
        return None
    
    # Sort and combine hashes deterministically
    sorted_items = sorted(all_hashes.items())
    combined = "".join(f"{k}:{v}" for k, v in sorted_items)
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()
