"""
ATS Kernel - Admissible Trajectory Space Implementation

This package implements the Coh-compliant Admissible Trajectory Space (ATS) kernel
for dynamical cognitive systems.

Per docs/ats/00_identity/project_identity.md:
    CNsc-HAAI implements a Coh-compliant Admissible Trajectory Space (ATS) kernel
    for dynamical cognitive systems.

Module Structure:
- numeric.py: QFixed(18) deterministic numeric domain
- types.py: Core ATS types (State, Action, Receipt, Budget)
- errors.py: Rejection error codes
- risk.py: Risk functional V implementation
- budget.py: Budget law implementation
- rv.py: Receipt Verifier (the heart)

Usage:
    from cnsc.haai.ats import ReceiptVerifier, State, QFixed
    
    verifier = ReceiptVerifier(initial_budget=QFixed.from_int(1), kappa=QFixed.ONE)
    accepted, error = verifier.verify_step(state_before, state_after, action, receipt, budget_before, budget_after)
"""

# Core exports
from .numeric import QFixed, QFixedOverflow, QFixedUnderflow, QFixedInvalid, SCALE
from .types import (
    State,
    Action,
    ActionType,
    Receipt,
    ReceiptContent,
    Budget,
    BeliefState,
    MemoryState,
    PlanState,
    PolicyState,
    IOState,
    VerificationResult,
    Rejection,
)
from .errors import (
    ATSError,
    RejectionCode,
    InvalidActionTypeError,
    InvalidStateSerializationError,
    StateHashMismatchError,
    InvalidReceiptHashError,
    RiskMismatchError,
    BudgetViolationError,
    InsufficientBudgetError,
    NegativeBudgetError,
    InvalidChainLinkError,
)
from .risk import RiskFunctional, compute_risk, compute_delta, compute_delta_plus
from .budget import BudgetManager, create_budget_manager
from .rv import ReceiptVerifier, verify_step, verify_trajectory


# Version
__version__ = "1.0.0-draft"

# Module exports
__all__ = [
    # Numeric
    "QFixed",
    "QFixedOverflow",
    "QFixedUnderflow", 
    "QFixedInvalid",
    "SCALE",
    
    # Types
    "State",
    "Action",
    "ActionType",
    "Receipt",
    "ReceiptContent",
    "Budget",
    "BeliefState",
    "MemoryState",
    "PlanState",
    "PolicyState",
    "IOState",
    "VerificationResult",
    "Rejection",
    
    # Errors
    "ATSError",
    "RejectionCode",
    "InvalidActionTypeError",
    "InvalidStateSerializationError",
    "StateHashMismatchError",
    "InvalidReceiptHashError",
    "RiskMismatchError",
    "BudgetViolationError",
    "InsufficientBudgetError",
    "NegativeBudgetError",
    "InvalidChainLinkError",
    
    # Risk
    "RiskFunctional",
    "compute_risk",
    "compute_delta",
    "compute_delta_plus",
    
    # Budget
    "BudgetManager",
    "create_budget_manager",
    
    # RV
    "ReceiptVerifier",
    "verify_step",
    "verify_trajectory",
]
