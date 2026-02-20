"""
ATS Rejection Reason Codes

This module defines all possible rejection codes for ATS verification.

Per docs/ats/50_security_model/rejection_reason_codes.md
"""

from __future__ import annotations
from enum import Enum, auto


class RejectionCode(Enum):
    """
    Complete list of ATS rejection codes.
    
    Per docs/ats/50_security_model/rejection_reason_codes.md
    """
    # Verification Failures
    INVALID_ACTION_TYPE = auto()
    INVALID_STATE_SERIALIZATION = auto()
    STATE_HASH_MISMATCH = auto()
    INVALID_RECEIPT_HASH = auto()
    RISK_MISMATCH = auto()
    
    # Budget Violations
    BUDGET_VIOLATION = auto()
    INSUFFICIENT_BUDGET = auto()
    NEGATIVE_BUDGET = auto()
    
    # Chain Failures
    INVALID_CHAIN_LINK = auto()
    GENESIS_REQUIRED = auto()
    CHAIN_TOO_SHORT = auto()
    
    # Generic
    UNKNOWN_ERROR = auto()


class ATSError(Exception):
    """Base exception for ATS errors."""
    def __init__(self, code: RejectionCode, reason: str, details: dict = None):
        self.code = code
        self.reason = reason
        self.details = details or {}
        super().__init__(f"{code.name}: {reason}")
    
    def to_dict(self) -> dict:
        return {
            'result': 'REJECT',
            'code': self.code.name,
            'reason': self.reason,
            'details': self.details,
        }


# Specific exception classes for convenience

class InvalidActionTypeError(ATSError):
    """Action type not in action algebra."""
    def __init__(self, action_type: str):
        super().__init__(
            RejectionCode.INVALID_ACTION_TYPE,
            f"Action type not in action algebra: {action_type}",
            {'action_type': action_type}
        )


class InvalidStateSerializationError(ATSError):
    """State cannot be serialized."""
    def __init__(self, reason: str = "State serialization failed"):
        super().__init__(
            RejectionCode.INVALID_STATE_SERIALIZATION,
            reason
        )


class StateHashMismatchError(ATSError):
    """State hash doesn't match receipt claim."""
    def __init__(self, expected: str, actual: str):
        super().__init__(
            RejectionCode.STATE_HASH_MISMATCH,
            "State hash doesn't match receipt claim",
            {'expected': expected, 'actual': actual}
        )


class InvalidReceiptHashError(ATSError):
    """Receipt self-invalid."""
    def __init__(self, expected: str, actual: str):
        super().__init__(
            RejectionCode.INVALID_RECEIPT_HASH,
            "Receipt hash doesn't match receipt_id",
            {'expected': expected, 'actual': actual}
        )


class RiskMismatchError(ATSError):
    """Risk value doesn't match receipt claim."""
    def __init__(self, expected: str, actual: str):
        super().__init__(
            RejectionCode.RISK_MISMATCH,
            "Risk value doesn't match receipt claim",
            {'expected': expected, 'actual': actual}
        )


class BudgetViolationError(ATSError):
    """Budget law not satisfied."""
    def __init__(self, budget_before: str, budget_after: str, delta: str):
        super().__init__(
            RejectionCode.BUDGET_VIOLATION,
            "Budget transition doesn't follow law",
            {
                'budget_before': budget_before,
                'budget_after': budget_after,
                'delta': delta
            }
        )


class InsufficientBudgetError(ATSError):
    """Not enough budget for risk increase."""
    def __init__(self, available: str, required: str, delta: str):
        super().__init__(
            RejectionCode.INSUFFICIENT_BUDGET,
            "Not enough budget for risk increase",
            {
                'budget_available': available,
                'budget_required': required,
                'risk_delta': delta
            }
        )


class NegativeBudgetError(ATSError):
    """Budget went negative."""
    def __init__(self, budget: str):
        super().__init__(
            RejectionCode.NEGATIVE_BUDGET,
            "Budget went negative",
            {'budget': budget}
        )


class InvalidChainLinkError(ATSError):
    """Receipt chain broken."""
    def __init__(self, expected: str, actual: str):
        super().__init__(
            RejectionCode.INVALID_CHAIN_LINK,
            "Receipt chain broken",
            {'expected': expected, 'actual': actual}
        )


# Error message templates

ERROR_MESSAGES = {
    RejectionCode.INVALID_ACTION_TYPE: "Action type {action_type} not in action algebra",
    RejectionCode.INVALID_STATE_SERIALIZATION: "State cannot be serialized: {reason}",
    RejectionCode.STATE_HASH_MISMATCH: "State hash mismatch: expected {expected}, got {actual}",
    RejectionCode.INVALID_RECEIPT_HASH: "Receipt hash mismatch: expected {expected}, got {actual}",
    RejectionCode.RISK_MISMATCH: "Risk mismatch: expected {expected}, got {actual}",
    RejectionCode.BUDGET_VIOLATION: "Budget violation: {reason}",
    RejectionCode.INSUFFICIENT_BUDGET: "Insufficient budget: have {available}, need {required}",
    RejectionCode.NEGATIVE_BUDGET: "Budget went negative: {budget}",
    RejectionCode.INVALID_CHAIN_LINK: "Chain link broken: expected {expected}, got {actual}",
    RejectionCode.GENESIS_REQUIRED: "Genesis receipt required",
    RejectionCode.CHAIN_TOO_SHORT: "Chain too short: {length} receipts",
    RejectionCode.UNKNOWN_ERROR: "Unknown error: {reason}",
}


def format_error(code: RejectionCode, **kwargs) -> str:
    """Format an error message with parameters."""
    template = ERROR_MESSAGES.get(code, "Error: {code}")
    try:
        return template.format(**kwargs)
    except KeyError:
        return template
