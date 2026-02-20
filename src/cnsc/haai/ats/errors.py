"""
ATS Rejection Reason Codes

This module defines all possible rejection codes for ATS verification.

Per docs/ats/50_security_model/rejection_reason_codes.md
"""

from __future__ import annotations
from enum import Enum, auto


# Per Gap G: Rejection precedence
# The order matters! First failure wins.
REJECTION_PRECEDENCE = [
    'InvalidChainLinkError',       # 1. Chain broken
    'StateHashMismatchError',    # 2. State hash wrong
    'RiskMismatchError',         # 3. Risk values don't match
    'BudgetViolationError',      # 4. Budget law violated
    'InvalidReceiptHashError',  # 5. Receipt hash invalid
    'InsufficientBudgetError',   # 6. Not enough budget
    'InvalidActionTypeError',   # 7. Unknown action
    'ATSError',                 # 8. Generic error
]


class RejectionCode(Enum):
    """
    Complete list of ATS rejection codes.
    
    Per Gap G: Rejection precedence
    
    The precedence order matters for consensus:
    - Different nodes must return the SAME rejection reason
    - First failure in precedence order wins
    """
    # Chain Failures (highest priority)
    INVALID_CHAIN_LINK = auto()       # 1. Chain broken
    GENESIS_REQUIRED = auto()         # 2. Must start from genesis
    CHAIN_TOO_SHORT = auto()         # 3. Not enough steps
    
    # State Verification
    STATE_HASH_MISMATCH = auto()     # 4. State hash wrong
    
    # Receipt Verification
    INVALID_RECEIPT_HASH = auto()   # 5. Receipt hash invalid
    
    # Risk Verification
    RISK_MISMATCH = auto()           # 6. Risk values don't match
    
    # Budget Verification
    BUDGET_VIOLATION = auto()        # 7. Budget law violated
    INSUFFICIENT_BUDGET = auto()     # 8. Not enough budget
    NEGATIVE_BUDGET = auto()         # 9. Budget went negative
    
    # Action Verification
    INVALID_ACTION_TYPE = auto()     # 10. Unknown action
    INVALID_STATE_SERIALIZATION = auto()  # 11. Malformed state
    
    # Generic
    UNKNOWN_ERROR = auto()            # 12. Catch-all


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
