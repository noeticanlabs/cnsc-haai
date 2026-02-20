"""
Budget Law Implementation

This module implements the budget law for ATS.

Per docs/ats/10_mathematical_core/budget_law.md:
- If ΔV ≤ 0: B_next = B_prev
- If ΔV > 0: B_next = B_prev - κ × ΔV

Core invariant: Σ(ΔV)⁺ ≤ B₀ / κ
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple

from .numeric import QFixed
from .types import Budget as BudgetType


# Genesis receipt ID constant
GENESIS_RECEIPT_ID = "00000000"
GENESIS_RECEIPT_HASH = "0000000000000000000000000000000000000000000000000000000000000000"


class BudgetManager:
    """
    Manages budget state and transitions per the budget law.
    
    Per docs/ats/10_mathematical_core/budget_law.md
    """
    
    def __init__(self, initial_budget: QFixed, kappa: QFixed):
        """
        Initialize budget manager.
        
        Args:
            initial_budget: B₀ - initial budget
            kappa: κ - risk coefficient
        """
        self._initial_budget = initial_budget
        self._kappa = kappa
        self._current_budget = initial_budget
        self._total_consumed = QFixed.ZERO
    
    @property
    def current_budget(self) -> QFixed:
        """Get current budget."""
        return self._current_budget
    
    @property
    def kappa(self) -> QFixed:
        """Get kappa value."""
        return self._kappa
    
    @property
    def initial_budget(self) -> QFixed:
        """Get initial budget."""
        return self._initial_budget
    
    @property
    def total_consumed(self) -> QFixed:
        """Get total budget consumed."""
        return self._total_consumed
    
    def compute_transition(self, risk_delta: QFixed) -> Tuple[QFixed, bool]:
        """
        Compute budget transition for a step.
        
        Per docs/ats/10_mathematical_core/budget_law.md:
        
        If ΔV ≤ 0:
            B_next = B_prev (no budget consumed)
        
        If ΔV > 0:
            Require: B_prev ≥ κ × ΔV
            B_next = B_prev - κ × ΔV
        
        Returns: (new_budget, accepted)
        """
        if risk_delta <= QFixed.ZERO:
            # Risk decreased - budget preserved
            return self._current_budget, True
        
        # Risk increased - check sufficiency
        required = self._kappa * risk_delta
        
        if self._current_budget < required:
            # Insufficient budget
            return QFixed.ZERO, False
        
        # Budget consumed
        new_budget = self._current_budget - required
        self._total_consumed = self._total_consumed + required
        
        return new_budget, True
    
    def apply_transition(self, risk_delta: QFixed) -> Tuple[QFixed, bool]:
        """
        Apply budget transition and update state.
        
        Returns: (new_budget, accepted)
        """
        new_budget, accepted = self.compute_transition(risk_delta)
        if accepted:
            self._current_budget = new_budget
        return new_budget, accepted
    
    def reset(self) -> None:
        """Reset to initial budget."""
        self._current_budget = self._initial_budget
        self._total_consumed = QFixed.ZERO
    
    def to_budget_type(self) -> BudgetType:
        """Convert to Budget type."""
        return BudgetType.create(self._current_budget, self._kappa)
    
    def to_json(self) -> dict:
        """Serialize to JSON."""
        return {
            'current_budget_q': self._current_budget.to_json(),
            'initial_budget_q': self._initial_budget.to_json(),
            'kappa_q': self._kappa.to_json(),
            'total_consumed_q': self._total_consumed.to_json(),
        }
    
    @classmethod
    def from_json(cls, data: dict) -> 'BudgetManager':
        """Deserialize from JSON."""
        return cls(
            initial_budget=QFixed.from_json(data['initial_budget_q']),
            kappa=QFixed.from_json(data['kappa_q'])
        )
    
    def check_invariant(self) -> bool:
        """
        Check budget invariant: total_consumed ≤ initial_budget
        
        Per docs/ats/10_mathematical_core/budget_law.md
        """
        return self._total_consumed <= self._initial_budget


def create_budget_manager(initial: QFixed, kappa: QFixed) -> BudgetManager:
    """Create a budget manager."""
    return BudgetManager(initial, kappa)
