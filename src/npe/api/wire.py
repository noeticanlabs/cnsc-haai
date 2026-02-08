"""
Wire Protocol - JSON Parsing and Schema Validation.

Handles request/response serialization with CJ0 canonicalization
and schema validation.
"""

import json
from typing import Any, Dict, List, Optional, Tuple

from ..core.canon import canonicalize, canonicalize_typed
from ..core.hashing import hash_request, hash_response
from ..core.types import (
    Budgets,
    Context,
    NPERequest,
    NPERepairRequest,
    NPEResponse,
)

# Wire protocol specifications
WIRE_SPECS = {
    "request": {
        "spec": "NPE-REQUEST-1.0",
        "required_fields": ["spec", "request_type", "request_id", "domain", "seed", "budgets", "inputs"],
    },
    "repair_request": {
        "spec": "NPE-REPAIR-REQUEST-1.0",
        "required_fields": ["spec", "request_type", "request_id", "domain", "seed", "budgets", "inputs", "failure"],
    },
    "response": {
        "spec": "NPE-RESPONSE-1.0",
        "required_fields": ["spec", "response_id", "request_id", "domain", "candidates"],
    },
}


def parse_request(data: Dict[str, Any]) -> Tuple[NPERequest, str]:
    """Parse and validate an NPE request from JSON dict.
    
    Args:
        data: The incoming JSON data
        
    Returns:
        Tuple of (parsed_request, request_hash)
    """
    # Validate spec
    spec = data.get("spec", "")
    if spec not in ["NPE-REQUEST-1.0", "NPE-REPAIR-REQUEST-1.0"]:
        raise ValueError(f"Invalid request spec: {spec}")
    
    # Parse budgets
    budgets_data = data.get("budgets", {})
    budgets = Budgets(
        max_wall_ms=budgets_data.get("max_wall_ms", 1000),
        max_candidates=budgets_data.get("max_candidates", 16),
        max_evidence_items=budgets_data.get("max_evidence_items", 100),
        max_search_expansions=budgets_data.get("max_search_expansions", 50),
    )
    
    # Parse inputs
    inputs = data.get("inputs", {})
    
    # Compute request hash from canonicalized data
    request_hash = hash_request(data)
    
    if spec == "NPE-REPAIR-REQUEST-1.0":
        # Parse repair request
        failure_data = data.get("failure", {})
        from ..core.types import FailureInfo
        failure = FailureInfo(
            proof_hash=failure_data.get("proof_hash", ""),
            gate_stack_id=failure_data.get("gate_stack_id", ""),
            registry_hash=failure_data.get("registry_hash", ""),
            failing_gates=failure_data.get("failing_gates", []),
        )
        
        request = NPERepairRequest(
            spec=spec,
            request_type=data.get("request_type", "repair"),
            request_id=request_hash,
            domain=data.get("domain", "gr"),
            determinism_tier=data.get("determinism_tier", "d0"),
            seed=data.get("seed", 0),
            budgets=budgets,
            inputs=inputs,
            failure=failure,
        )
    else:
        # Parse standard request
        request = NPERequest(
            spec=spec,
            request_type=data.get("request_type", "propose"),
            request_id=request_hash,
            domain=data.get("domain", "gr"),
            determinism_tier=data.get("determinism_tier", "d0"),
            seed=data.get("seed", 0),
            budgets=budgets,
            inputs=inputs,
        )
    
    return request, request_hash


def parse_json(content: bytes) -> Dict[str, Any]:
    """Parse JSON from bytes.
    
    Args:
        content: Raw bytes content
        
    Returns:
        Parsed JSON dict
    """
    # Ensure UTF-8 encoding
    text = content.decode("utf-8")
    return json.loads(text)


def serialize_response(response: NPEResponse) -> bytes:
    """Serialize an NPE response to JSON bytes.
    
    Args:
        response: The response to serialize
        
    Returns:
        JSON bytes with proper encoding
    """
    # Convert response to dict
    response_dict = response_to_dict(response)
    
    # Canonicalize for hashing
    canonical = canonicalize(response_dict)
    
    # Compute response hash
    response_id = hash_response(response_dict)
    response.response_id = response_id
    
    # Re-serialize with the computed ID
    response_dict = response_to_dict(response)
    
    # Return with proper encoding
    json_str = json.dumps(response_dict, separators=(",", ":"), ensure_ascii=False)
    return json_str.encode("utf-8")


def response_to_dict(response: NPEResponse) -> Dict[str, Any]:
    """Convert a response to a dict for serialization.
    
    Args:
        response: The response to convert
        
    Returns:
        Response as dict
    """
    return {
        "spec": response.spec,
        "response_id": response.response_id,
        "request_id": response.request_id,
        "domain": response.domain,
        "determinism_tier": response.determinism_tier,
        "seed": response.seed,
        "corpus_snapshot_hash": response.corpus_snapshot_hash,
        "memory_snapshot_hash": response.memory_snapshot_hash,
        "registry_hash": response.registry_hash,
        "candidates": [candidate_to_dict(c) for c in response.candidates],
        "diagnostics": response.diagnostics,
    }


def candidate_to_dict(candidate: Any) -> Dict[str, Any]:
    """Convert a candidate to a dict for serialization.
    
    Args:
        candidate: The candidate to convert
        
    Returns:
        Candidate as dict
    """
    return {
        "candidate_hash": candidate.candidate_hash,
        "candidate_type": candidate.candidate_type,
        "domain": candidate.domain,
        "input_state_hash": candidate.input_state_hash,
        "constraints_hash": candidate.constraints_hash,
        "payload_format": candidate.payload_format,
        "payload_hash": candidate.payload_hash,
        "payload": candidate.payload,
        "evidence": [
            {
                "evidence_id": e.evidence_id,
                "source_type": e.source_type,
                "source_ref": e.source_ref,
                "content_hash": e.content_hash,
                "taint_tags": e.taint_tags,
                "scope": e.scope,
                "filters_applied": e.filters_applied,
                "relevance": e.relevance,
            }
            for e in candidate.evidence
        ],
        "scores": {
            "risk": candidate.scores.risk,
            "utility": candidate.scores.utility,
            "cost": candidate.scores.cost,
            "confidence": candidate.scores.confidence,
        },
        "suggested_gate_stack": candidate.suggested_gate_stack,
        "proposer_meta": candidate.proposer_meta and {
            "proposer_id": candidate.proposer_meta.proposer_id,
            "invocation_order": candidate.proposer_meta.invocation_order,
            "execution_time_ms": candidate.proposer_meta.execution_time_ms,
        },
    }


def validate_schema(data: Dict[str, Any], spec_type: str) -> List[str]:
    """Validate data against wire protocol schema.
    
    Args:
        data: The data to validate
        spec_type: The spec type to validate against
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    spec_config = WIRE_SPECS.get(spec_type)
    if spec_config is None:
        errors.append(f"Unknown spec type: {spec_type}")
        return errors
    
    # Check spec version
    expected_spec = spec_config["spec"]
    actual_spec = data.get("spec", "")
    if actual_spec != expected_spec:
        errors.append(f"Expected spec '{expected_spec}', got '{actual_spec}'")
    
    # Check required fields
    for field in spec_config.get("required_fields", []):
        if field not in data:
            errors.append(f"Missing required field: {field}")
    
    return errors


def revalidate_and_reserialize(data: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
    """Re-validate and re-serialize a request using CJ0.
    
    Args:
        data: The incoming request data
        
    Returns:
        Tuple of (validated_data, request_hash)
    """
    # Validate schema
    errors = validate_schema(data, "request")
    if not errors:
        errors = validate_schema(data, "repair_request")
    
    if errors:
        raise ValueError(f"Schema validation failed: {', '.join(errors)}")
    
    # Canonicalize and re-serialize
    canonical = canonicalize(data)
    
    # Parse back to ensure round-trip consistency
    reparsed = json.loads(canonical)
    
    # Compute hash
    request_hash = hash_request(data)
    
    return reparsed, request_hash


def create_wire_error(message: str, code: str = "NPE_ERROR") -> bytes:
    """Create an error response wire format.
    
    Args:
        message: Error message
        code: Error code
        
    Returns:
        Error response as bytes
    """
    error_response = {
        "spec": "NPE-RESPONSE-1.0",
        "response_id": "",
        "request_id": "",
        "error": {
            "code": code,
            "message": message,
        },
    }
    
    json_str = json.dumps(error_response, separators=(",", ":"), ensure_ascii=False)
    return json_str.encode("utf-8")
