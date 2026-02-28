"""
Budget Accounting and Enforcement.

Tracks and enforces budget constraints for NPE operations including
time, candidates, evidence, and search expansions.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class BudgetAccounting:
    """Accounting for budget consumption.

    Attributes:
        wall_ms_used: Wall-clock time used in ms
        candidates_generated: Number of candidates generated
        evidence_retrieved: Number of evidence items retrieved
        search_expansions: Number of search expansions performed
        proposer_wall_ms: Per-proposer time tracking
    """

    wall_ms_used: int = 0
    candidates_generated: int = 0
    evidence_retrieved: int = 0
    search_expansions: int = 0
    proposer_wall_ms: Dict[str, int] = field(default_factory=dict)

    def add_wall_time(self, ms: int) -> None:
        """Add wall time usage.

        Args:
            ms: Milliseconds to add
        """
        self.wall_ms_used += ms

    def add_candidates(self, count: int) -> None:
        """Add candidate count.

        Args:
            count: Number of candidates to add
        """
        self.candidates_generated += count

    def add_evidence(self, count: int) -> None:
        """Add evidence count.

        Args:
            count: Number of evidence items to add
        """
        self.evidence_retrieved += count

    def add_search_expansions(self, count: int) -> None:
        """Add search expansion count.

        Args:
            count: Number of expansions to add
        """
        self.search_expansions += count

    def add_proposer_time(self, proposer_id: str, ms: int) -> None:
        """Add time for a specific proposer.

        Args:
            proposer_id: Proposer identifier
            ms: Milliseconds to add
        """
        self.proposer_wall_ms[proposer_id] = self.proposer_wall_ms.get(proposer_id, 0) + ms

    def is_within_budget(self, budget: "Budgets") -> bool:
        """Check if current usage is within budget.

        Args:
            budget: Budget constraints to check against

        Returns:
            True if within budget, False otherwise
        """
        return (
            self.wall_ms_used <= budget.max_wall_ms
            and self.candidates_generated <= budget.max_candidates
            and self.evidence_retrieved <= budget.max_evidence_items
            and self.search_expansions <= budget.max_search_expansions
        )

    def get_remaining(self, budget: "Budgets") -> Dict[str, int]:
        """Get remaining budget capacity.

        Args:
            budget: Budget constraints

        Returns:
            Dict of remaining budget by category
        """
        return {
            "wall_ms": budget.max_wall_ms - self.wall_ms_used,
            "candidates": budget.max_candidates - self.candidates_generated,
            "evidence": budget.max_evidence_items - self.evidence_retrieved,
            "search_expansions": budget.max_search_expansions - self.search_expansions,
        }

    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary for serialization.

        Returns:
            Accounting data as dict
        """
        return {
            "wall_ms_used": self.wall_ms_used,
            "candidates_generated": self.candidates_generated,
            "evidence_retrieved": self.evidence_retrieved,
            "search_expansions": self.search_expansions,
            "proposer_wall_ms": self.proposer_wall_ms,
        }


class BudgetEnforcer:
    """Enforces budget constraints during NPE operation."""

    def __init__(self, budget: "Budgets"):
        """Initialize enforcer with budget.

        Args:
            budget: Budget constraints to enforce
        """
        self._budget = budget
        self._accounting = BudgetAccounting()

    @property
    def budget(self) -> "Budgets":
        """Get the budget."""
        return self._budget

    @property
    def accounting(self) -> BudgetAccounting:
        """Get the accounting."""
        return self._accounting

    def check_time_budget(self, additional_ms: int = 0) -> bool:
        """Check if time budget allows more operations.

        Args:
            additional_ms: Additional time to check

        Returns:
            True if within budget, False if exceeded
        """
        total = self._accounting.wall_ms_used + additional_ms
        return total <= self._budget.max_wall_ms

    def check_candidates_budget(self, additional: int = 0) -> bool:
        """Check if candidate budget allows more candidates.

        Args:
            additional: Additional candidates to check

        Returns:
            True if within budget, False if exceeded
        """
        total = self._accounting.candidates_generated + additional
        return total <= self._budget.max_candidates

    def check_evidence_budget(self, additional: int = 0) -> bool:
        """Check if evidence budget allows more items.

        Args:
            additional: Additional evidence items to check

        Returns:
            True if within budget, False if exceeded
        """
        total = self._accounting.evidence_retrieved + additional
        return total <= self._budget.max_evidence_items

    def check_search_budget(self, additional: int = 0) -> bool:
        """Check if search expansion budget allows more.

        Args:
            additional: Additional expansions to check

        Returns:
            True if within budget, False if exceeded
        """
        total = self._accounting.search_expansions + additional
        return total <= self._budget.max_search_expansions

    def record_time(self, ms: int, proposer_id: Optional[str] = None) -> None:
        """Record time usage.

        Args:
            ms: Milliseconds to record
            proposer_id: Optional proposer identifier
        """
        self._accounting.add_wall_time(ms)
        if proposer_id:
            self._accounting.add_proposer_time(proposer_id, ms)

    def record_candidates(self, count: int) -> None:
        """Record candidate generation.

        Args:
            count: Number of candidates to record
        """
        self._accounting.add_candidates(count)

    def record_evidence(self, count: int) -> None:
        """Record evidence retrieval.

        Args:
            count: Number of evidence items to record
        """
        self._accounting.add_evidence(count)

    def record_search_expansions(self, count: int) -> None:
        """Record search expansions.

        Args:
            count: Number of expansions to record
        """
        self._accounting.add_search_expansions(count)

    def get_summary(self) -> Dict[str, int]:
        """Get budget summary.

        Returns:
            Summary dict with usage and limits
        """
        remaining = self._accounting.get_remaining(self._budget)
        return {
            "limits": {
                "max_wall_ms": self._budget.max_wall_ms,
                "max_candidates": self._budget.max_candidates,
                "max_evidence_items": self._budget.max_evidence_items,
                "max_search_expansions": self._budget.max_search_expansions,
            },
            "used": self._accounting.to_dict(),
            "remaining": remaining,
        }


# Backwards compatibility: re-export Budgets from types
# This allows imports like: from npe.core.budgets import Budgets
# (Budgets is defined in npe.core.types)
try:
    from .types import Budgets
except ImportError:
    pass  # types may not have Budgets, which is fine
