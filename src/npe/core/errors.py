"""
Error Codes and Structured Exceptions for NPE.

Defines standardized error codes and exception classes for consistent
error handling across the NPE service.
"""

from enum import Enum
from typing import Any, Dict, Optional


class ErrorCode(str, Enum):
    """Standardized error codes for NPE."""

    # Success
    SUCCESS = "NPE_SUCCESS"

    # Request errors
    INVALID_REQUEST = "NPE_INVALID_REQUEST"
    MISSING_REQUIRED_FIELD = "NPE_MISSING_FIELD"
    INVALID_REQUEST_TYPE = "NPE_INVALID_REQUEST_TYPE"
    INVALID_DOMAIN = "NPE_INVALID_DOMAIN"
    INVALID_BUDGET = "NPE_INVALID_BUDGET"

    # Processing errors
    PROCESSING_TIMEOUT = "NPE_TIMEOUT"
    PROCESSING_ERROR = "NPE_PROCESSING_ERROR"
    BUDGET_EXCEEDED = "NPE_BUDGET_EXCEEDED"

    # Registry errors
    REGISTRY_LOAD_ERROR = "NPE_REGISTRY_LOAD_ERROR"
    PROPOSER_NOT_FOUND = "NPE_PROPOSER_NOT_FOUND"
    PROPOSER_ERROR = "NPE_PROPOSER_ERROR"

    # Retrieval errors
    CORPUS_LOAD_ERROR = "NPE_CORPUS_LOAD_ERROR"
    INDEX_ERROR = "NPE_INDEX_ERROR"
    NO_EVIDENCE_FOUND = "NPE_NO_EVIDENCE"

    # Validation errors
    SCHEMA_VALIDATION_ERROR = "NPE_SCHEMA_ERROR"
    HASH_MISMATCH = "NPE_HASH_MISMATCH"

    # Internal errors
    INTERNAL_ERROR = "NPE_INTERNAL_ERROR"
    NOT_IMPLEMENTED = "NPE_NOT_IMPLEMENTED"


class NPEError(Exception):
    """Base exception for NPE errors.

    Attributes:
        code: Error code
        message: Human-readable error message
        details: Additional error details
        request_id: Related request ID
    """

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        self.request_id = request_id
        super().__init__(f"[{code.value}] {message}")


class InvalidRequestError(NPEError):
    """Raised when a request is invalid."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code=ErrorCode.INVALID_REQUEST,
            message=message,
            details=details,
        )


class ProposerNotFoundError(NPEError):
    """Raised when a proposer is not found in registry."""

    def __init__(self, proposer_id: str):
        super().__init__(
            code=ErrorCode.PROPOSER_NOT_FOUND,
            message=f"Proposer not found: {proposer_id}",
            details={"proposer_id": proposer_id},
        )


class ProposerError(NPEError):
    """Raised when a proposer fails during execution."""

    def __init__(self, proposer_id: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code=ErrorCode.PROPOSER_ERROR,
            message=f"Proposer error [{proposer_id}]: {message}",
            details={"proposer_id": proposer_id, **(details or {})},
        )


class ProcessingTimeoutError(NPEError):
    """Raised when processing exceeds budget."""

    def __init__(self, elapsed_ms: int, budget_ms: int):
        super().__init__(
            code=ErrorCode.PROCESSING_TIMEOUT,
            message=f"Processing timeout: {elapsed_ms}ms > budget {budget_ms}ms",
            details={"elapsed_ms": elapsed_ms, "budget_ms": budget_ms},
        )


class BudgetExceededError(NPEError):
    """Raised when budget is exceeded."""

    def __init__(self, budget_type: str, current: int, limit: int):
        super().__init__(
            code=ErrorCode.BUDGET_EXCEEDED,
            message=f"Budget exceeded: {budget_type} {current} > {limit}",
            details={"budget_type": budget_type, "current": current, "limit": limit},
        )


class RegistryLoadError(NPEError):
    """Raised when registry manifest fails to load."""

    def __init__(self, path: str, reason: str):
        super().__init__(
            code=ErrorCode.REGISTRY_LOAD_ERROR,
            message=f"Failed to load registry from {path}: {reason}",
            details={"path": path, "reason": reason},
        )


class SchemaValidationError(NPEError):
    """Raised when schema validation fails."""

    def __init__(self, field: str, reason: str, value: Any = None):
        super().__init__(
            code=ErrorCode.SCHEMA_VALIDATION_ERROR,
            message=f"Schema validation failed for field '{field}': {reason}",
            details={"field": field, "reason": reason, "value": value},
        )


def create_error_response(
    code: ErrorCode,
    message: str,
    request_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a standardized error response.

    Args:
        code: Error code
        message: Error message
        request_id: Related request ID
        details: Additional error details

    Returns:
        Error response dictionary
    """
    return {
        "spec": "NPE-RESPONSE-1.0",
        "response_id": "",  # Will be computed
        "request_id": request_id or "",
        "domain": "gr",
        "determinism_tier": "d0",
        "error": {
            "code": code.value,
            "message": message,
            "details": details or {},
        },
    }
