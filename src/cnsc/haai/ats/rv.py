"""
Receipt Verifier (RV) - The Heart of ATS

This module implements the sovereign Receipt Verifier that enforces ATS invariants.
Every state transition must pass through RV verification.

Per docs/ats/20_coh_kernel/rv_step_spec.md:
    The RV is a pure function - same inputs always produce same outputs.
    This is the EXECUTABLE LAW of ATS.

Verification Steps:
1. Recompute state_hash_before
2. Recompute state_hash_after
3. Recompute risk_before_q
4. Recompute risk_after_q
5. Compute delta_plus
6. Validate budget rule
7. Validate receipt hash
8. Validate chain link
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, Optional
import hashlib

from .numeric import QFixed
from .types import State, Action, Receipt, ReceiptContent, Budget
from .errors import (
    ATSError, StateHashMismatchError, InvalidReceiptHashError,
    RiskMismatchError, BudgetViolationError, InsufficientBudgetError,
    InvalidChainLinkError, RejectionCode
)
from .risk import RiskFunctional, default_risk_functional
from .budget import BudgetManager, GENESIS_RECEIPT_ID


# Genesis constants
# Per Gap D: Genesis definition
GENESIS_CHAIN_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

# SHA256 of empty bytes - the hash of empty state
GENESIS_STATE_HASH = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

# Genesis receipt ID
GENESIS_RECEIPT_ID = "00000000"


@dataclass
class Genesis:
    """
    Genesis state definition for replay anchoring.
    
    Per Gap D: Genesis definition
    
    The genesis receipt serves as the trusted root of the receipt chain.
    All trajectories must start from this known state.
    """
    state_hash: str = GENESIS_STATE_HASH
    chain_hash: str = GENESIS_CHAIN_HASH
    receipt_id: str = GENESIS_RECEIPT_ID
    
    def verify(self, receipt: Receipt) -> bool:
        """Verify a receipt matches genesis."""
        return (
            receipt.previous_receipt_id == GENESIS_RECEIPT_ID and
            receipt.chain_hash == GENESIS_CHAIN_HASH
        )


class ReceiptVerifier:
    """
    The sovereign Receipt Verifier (RV).
    
    Per docs/ats/20_coh_kernel/rv_step_spec.md:
    The RV is the SOVEREIGN verification component.
    The Runtime is UNTRUSTED.
    """
    
    def __init__(
        self,
        risk_functional: RiskFunctional = None,
        initial_budget: QFixed = None,
        kappa: QFixed = None,
    ):
        """
        Initialize the Receipt Verifier.
        
        Args:
            risk_functional: The risk functional V (default: default_risk_functional)
            initial_budget: Initial budget B₀
            kappa: Risk coefficient κ
        """
        self.risk_functional = risk_functional or default_risk_functional
        self.initial_budget = initial_budget or QFixed.from_int(1)
        self.kappa = kappa or QFixed.ONE
        
        # Budget manager for this verifier
        self.budget_manager = BudgetManager(self.initial_budget, self.kappa)
        
        # Track previous receipt for chain verification
        self._previous_receipt_id = GENESIS_RECEIPT_ID
    
    def verify_step(
        self,
        state_before: State,
        state_after: State,
        action: Action,
        receipt: Receipt,
        budget_before: QFixed,
        budget_after: QFixed,
        kappa: QFixed = None,
    ) -> Tuple[bool, Optional[ATSError]]:
        """
        Verify a single ATS step.
        
        This is the main entry point for step verification.
        
        Per docs/ats/20_coh_kernel/rv_step_spec.md:
        
        Returns: (accepted: bool, error: Optional[ATSError])
        """
        kappa = kappa or self.kappa
        
        # Version check: v1 receipts are telemetry-only, not consensus-safe
        # Per consensus boundary: GML receipts are for debugging/telemetry
        if hasattr(receipt, 'version') and receipt.version:
            if receipt.version.startswith("1."):
                return False, ATSError(
                    code=RejectionCode.INVALID_ACTION_TYPE,  # Reuse code for clarity
                    reason=f"Receipt version {receipt.version} is telemetry-only (v1). Use v2+ for consensus."
                )
        
        # Step 1: Verify state hash before
        error = self._verify_state_hash_before(state_before, receipt)
        if error:
            return False, error
        
        # Step 2: Verify state hash after
        error = self._verify_state_hash_after(state_after, receipt)
        if error:
            return False, error
        
        # Step 3 & 4: Verify risk values
        error = self._verify_risk_values(state_before, state_after, receipt)
        if error:
            return False, error
        
        # Step 5 & 6: Verify budget law
        error = self._verify_budget_law(
            budget_before, budget_after, receipt, kappa
        )
        if error:
            return False, error
        
        # Step 7: Verify receipt hash
        error = self._verify_receipt_hash(receipt)
        if error:
            return False, error
        
        # Step 8: Verify chain link
        error = self._verify_chain_link(receipt)
        if error:
            return False, error
        
        # All checks passed
        return True, None
    
    def _verify_state_hash_before(
        self,
        state: State,
        receipt: Receipt
    ) -> Optional[ATSError]:
        """
        Step 1: Recompute state_hash_before
        
        Per docs/ats/20_coh_kernel/rv_step_spec.md:
        1. Compute: state_hash_before_computed = sha256(state_before)
        2. Compare: == receipt.state_hash_before
        """
        computed_hash = state.state_hash()
        expected_hash = receipt.content.state_hash_before if receipt.content else ""
        
        if computed_hash != expected_hash:
            return StateHashMismatchError(expected_hash, computed_hash)
        
        return None
    
    def _verify_state_hash_after(
        self,
        state: State,
        receipt: Receipt
    ) -> Optional[ATSError]:
        """
        Step 2: Recompute state_hash_after
        """
        computed_hash = state.state_hash()
        expected_hash = receipt.content.state_hash_after if receipt.content else ""
        
        if computed_hash != expected_hash:
            return StateHashMismatchError(expected_hash, computed_hash)
        
        return None
    
    def _verify_risk_values(
        self,
        state_before: State,
        state_after: State,
        receipt: Receipt
    ) -> Optional[ATSError]:
        """
        Step 3, 4, 5: Verify risk values
        
        Per docs/ats/20_coh_kernel/rv_step_spec.md:
        - Verify risk_before matches V(state_before)
        - Verify risk_after matches V(state_after)
        - Verify delta_plus = max(0, risk_after - risk_before)
        """
        if not receipt.content:
            return None  # Skip for receipts without content
        
        # Compute actual risk values
        actual_risk_before = self.risk_functional.compute(state_before)
        actual_risk_after = self.risk_functional.compute(state_after)
        
        # Verify risk before
        expected_risk_before = receipt.content.risk_before_q
        if actual_risk_before != expected_risk_before:
            return RiskMismatchError(
                expected_risk_before.to_json(),
                actual_risk_before.to_json()
            )
        
        # Verify risk after
        expected_risk_after = receipt.content.risk_after_q
        if actual_risk_after != expected_risk_after:
            return RiskMismatchError(
                expected_risk_after.to_json(),
                actual_risk_after.to_json()
            )
        
        # Verify delta_plus
        delta = actual_risk_after - actual_risk_before
        delta_plus = delta if delta > QFixed.ZERO else QFixed.ZERO
        expected_delta_plus = receipt.content.delta_plus_q
        
        if delta_plus != expected_delta_plus:
            return RiskMismatchError(
                expected_delta_plus.to_json(),
                delta_plus.to_json()
            )
        
        return None
    
    def _verify_budget_law(
        self,
        budget_before: QFixed,
        budget_after: QFixed,
        receipt: Receipt,
        kappa: QFixed
    ) -> Optional[ATSError]:
        """
        Step 6: Validate Budget Rule
        
        Per docs/ats/20_coh_kernel/rv_step_spec.md:
        
        If ΔV ≤ 0:
            B_next = B_prev (budget preserved)
        
        If ΔV > 0:
            Require: B_prev ≥ κ × ΔV
            B_next = B_prev - κ × ΔV
        """
        if not receipt.content:
            return None
        
        # Use signed delta for proper sign detection
        # This avoids the floor-at-zero issue in QFixed subtraction
        from .numeric import compute_signed_delta
        risk_delta = compute_signed_delta(
            receipt.content.risk_after_q,
            receipt.content.risk_before_q
        )
        
        if not risk_delta.is_positive():  # ΔV ≤ 0
            # Risk decreased - budget must be preserved
            if budget_after != budget_before:
                return BudgetViolationError(
                    budget_before.to_json(),
                    budget_after.to_json(),
                    {"delta_raw": risk_delta.raw_delta, "delta_str": str(risk_delta)}
                )
        else:
            # Risk increased - check and consume budget
            # Use .plus() to get ΔV⁺ for the calculation
            delta_plus = risk_delta.plus()
            required = kappa * delta_plus
            if budget_before < required:
                return InsufficientBudgetError(
                    budget_before.to_json(),
                    required.to_json(),
                    {"delta_raw": risk_delta.raw_delta, "delta_str": str(risk_delta)}
                )
            
            expected_after = budget_before - required
            if budget_after != expected_after:
                return BudgetViolationError(
                    budget_before.to_json(),
                    budget_after.to_json(),
                    {"delta_raw": risk_delta.raw_delta, "delta_str": str(risk_delta)}
                )
        
        return None
    
    def _verify_receipt_hash(self, receipt: Receipt) -> Optional[ATSError]:
        """
        Step 7: Validate Receipt Hash
        
        Per docs/ats/20_coh_kernel/rv_step_spec.md:
        
        receipt_id = first8(sha256(canonical_bytes(receipt)))
        """
        # Compute receipt ID
        computed_id = receipt.compute_receipt_id()
        expected_id = receipt.receipt_id
        
        if computed_id != expected_id:
            return InvalidReceiptHashError(expected_id, computed_id)
        
        return None
    
    def _verify_chain_link(self, receipt: Receipt) -> Optional[ATSError]:
        """
        Step 8: Validate Chain Link
        
        Per docs/ats/20_coh_kernel/chain_hash_rule.md:
        
        For genesis: previous_receipt_id = "00000000"
        For others: previous_receipt_id links to previous receipt
        """
        expected_prev = self._previous_receipt_id
        actual_prev = receipt.previous_receipt_id
        
        if expected_prev != actual_prev:
            return InvalidChainLinkError(expected_prev, actual_prev)
        
        # Update for next verification
        self._previous_receipt_id = receipt.receipt_id
        
        return None
    
    def verify_trajectory(
        self,
        initial_state_hash: str,
        initial_budget: QFixed,
        receipts: list,
        kappa: QFixed = None,
    ) -> Tuple[bool, Optional[ATSError]]:
        """
        Verify a complete trajectory using ONLY receipt data.
        
        Per docs/ats/30_ats_runtime/replay_verification.md:
        - initial_state_hash: Starting state hash (provided externally)
        - Each receipt must contain:
          - state_hash_before (links to previous)
          - state_hash_after (for next link)
          - risk values (for V verification)
          - budget values (for B verification)
        
        This method does NOT trust runtime state - it verifies entirely
        from receipt-contained data.
        
        Returns: (accepted: bool, error: Optional[ATSError])
        """
        kappa = kappa or self.kappa
        
        # Reset verifier state
        self._previous_receipt_id = GENESIS_RECEIPT_ID
        self.budget_manager = BudgetManager(initial_budget, kappa)
        
        # Track expected state hash for chain verification
        expected_state_hash = initial_state_hash
        
        # Track previous chain hash for chain verification
        prev_chain_hash = GENESIS_CHAIN_HASH
        
        for i, receipt in enumerate(receipts):
            # Get content from receipt (not runtime)
            content = receipt.content
            if not content:
                return False, ATSError("Receipt missing content")
            
            # Step 1: Verify state hash chain (using receipt data only)
            if content.state_hash_before != expected_state_hash:
                return False, StateHashMismatchError(
                    expected_state_hash,
                    content.state_hash_before
                )
            
            # Step 2: Verify receipt hash (receipt_id)
            computed_id = receipt.compute_receipt_id()
            if computed_id != receipt.receipt_id:
                return False, InvalidReceiptHashError(receipt.receipt_id, computed_id)
            
            # Step 3: Verify chain hash (using new content-bound formula)
            computed_chain_hash = receipt.compute_chain_hash(prev_chain_hash)
            if computed_chain_hash != receipt.chain_hash:
                return False, InvalidChainLinkError(receipt.chain_hash, computed_chain_hash)
            
            # Step 4: Verify chain link (previous receipt ID)
            if receipt.previous_receipt_id != self._previous_receipt_id:
                return False, InvalidChainLinkError(
                    self._previous_receipt_id,
                    receipt.previous_receipt_id
                )
            
            # Step 5: Verify budget law using receipt data only
            # (We compute expected budget transition and compare to receipt)
            budget_before = self.budget_manager.budget
            budget_after = content.budget_after_q
            
            # Compute risk delta from receipt content
            risk_delta = content.risk_after_q - content.risk_before_q
            
            # Verify budget transition matches what receipt claims
            accepted, error = self._verify_budget_law(
                budget_before=budget_before,
                budget_after=budget_after,
                receipt=receipt,
                kappa=kappa,
            )
            
            if error:
                return False, error
            
            # Update expected state for next step (from receipt, not runtime)
            expected_state_hash = content.state_hash_after
            
            # Update chain hash for next iteration
            prev_chain_hash = receipt.chain_hash
            
            # Update budget for next iteration
            self.budget_manager.budget = budget_after
            
            # Update previous receipt ID for next iteration
            self._previous_receipt_id = receipt.receipt_id
        
        return True, None
    
    def reset(self) -> None:
        """Reset verifier state for new trajectory."""
        self._previous_receipt_id = GENESIS_RECEIPT_ID
        self.budget_manager = BudgetManager(self.initial_budget, self.kappa)


# Import ActionType for the verifier
from .types import ActionType


# Default verifier instance
default_verifier = ReceiptVerifier()


def verify_step(
    state_before: State,
    state_after: State,
    action: Action,
    receipt: Receipt,
    budget_before: QFixed,
    budget_after: QFixed,
    kappa: QFixed = None,
) -> Tuple[bool, Optional[ATSError]]:
    """
    Verify a single ATS step using default verifier.
    """
    return default_verifier.verify_step(
        state_before, state_after, action, receipt,
        budget_before, budget_after, kappa
    )


def verify_trajectory(
    initial_state: State,
    initial_budget: QFixed,
    receipts: list,
    kappa: QFixed = None,
) -> Tuple[bool, Optional[ATSError]]:
    """
    Verify a complete trajectory using default verifier.
    """
    return default_verifier.verify_trajectory(
        initial_state, initial_budget, receipts, kappa
    )
