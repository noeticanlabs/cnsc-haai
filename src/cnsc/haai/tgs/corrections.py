"""
Correction System

Deterministic correction application for TGS governance.
Provides automatic corrections when rails are marginally passed.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Tuple
from cnsc.haai.tgs.rails import (
    RailResult,
    RailDecision,
    CoherenceRails,
)


class CorrectionType(Enum):
    """Types of corrections TGS can apply."""

    QUARANTINE_CLAIM = auto()
    CLAMP_CONFIDENCE = auto()
    DROP_LOW_PROVENANCE_EDGE = auto()
    ENFORCE_SPECULATIVE_TAG = auto()
    RESTRICT_ACTION_SCOPE = auto()
    ESCALATE_TO_GATE = auto()
    REJECT_PROPOSAL = auto()


@dataclass
class Correction:
    """
    A correction applied by TGS.

    Attributes:
        correction_type: Type of correction
        target: Target of correction (e.g., belief ID, claim ID)
        reason: Reason for applying correction
        details: Additional correction details
        confidence_impact: Impact on proposal confidence
    """

    correction_type: CorrectionType
    target: str
    reason: str
    details: Dict[str, Any] = field(default_factory=dict)
    confidence_impact: float = 0.0


@dataclass
class CorrectionResult:
    """Result of applying corrections."""

    corrections_applied: List[Correction]
    confidence_reduction: float
    success: bool
    message: str


class CorrectionEngine:
    """
    Deterministic correction application.

    Applies corrections to staged state when rails are marginal.
    All corrections are deterministic and reproducible.
    """

    def __init__(self):
        """Initialize correction engine."""
        self._correction_rules: Dict[str, List] = {}

    def apply(
        self, rail_results: List[RailResult], staged: "StagedState", proposal: "Proposal"
    ) -> Tuple["StagedState", List[Correction]]:
        """
        Apply corrections to staged state based on rail results.

        Args:
            rail_results: Results from rail evaluation
            staged: Staged state to modify
            proposal: Original proposal

        Returns:
            Tuple of (modified staged state, list of corrections)
        """
        corrections: List[Correction] = []

        for result in rail_results:
            if result.decision == RailDecision.FAIL:
                # For failed rails, apply rejection correction
                correction = Correction(
                    correction_type=CorrectionType.REJECT_PROPOSAL,
                    target=str(result.rail_id),
                    reason=f"Rail {result.rail_id} failed",
                    details={"rail_result": result.to_dict() if hasattr(result, "to_dict") else {}},
                )
                corrections.append(correction)

            elif result.decision == RailDecision.MARGINAL:
                # For marginal rails, apply specific corrections
                marginal_corrections = self._apply_marginal_correction(result, staged, proposal)
                corrections.extend(marginal_corrections)

        return staged, corrections

    def _apply_marginal_correction(
        self, result: RailResult, staged: "StagedState", proposal: "Proposal"
    ) -> List[Correction]:
        """Apply corrections for a marginal rail result."""
        corrections: List[Correction] = []

        rail_id = str(result.rail_id)

        if rail_id == "consistency":
            # Quarantine potentially contradictory claims
            correction = Correction(
                correction_type=CorrectionType.QUARANTINE_CLAIM,
                target="consistency",
                reason="Marginal consistency, quarantining affected claims",
                details={"margin": result.margin},
                confidence_impact=0.1,
            )
            corrections.append(correction)

            # Clamp confidence
            confidence_correction = Correction(
                correction_type=CorrectionType.CLAMP_CONFIDENCE,
                target=str(proposal.proposal_id),
                reason="Confidence clamped due to marginal consistency",
                details={"original_confidence": proposal.confidence},
                confidence_impact=result.margin,
            )
            corrections.append(confidence_correction)

        elif rail_id == "commitment":
            # Restrict action scope
            correction = Correction(
                correction_type=CorrectionType.RESTRICT_ACTION_SCOPE,
                target="obligations",
                reason="Commitment load elevated, restricting new obligations",
                details={"margin": result.margin},
                confidence_impact=0.05,
            )
            corrections.append(correction)

        elif rail_id == "causality":
            # Drop low provenance edges
            correction = Correction(
                correction_type=CorrectionType.DROP_LOW_PROVENANCE_EDGE,
                target="evidence",
                reason="Causality concerns, requiring higher provenance",
                details={"margin": result.margin},
                confidence_impact=0.15,
            )
            corrections.append(correction)

        elif rail_id == "resource":
            # Escalate to gate for resource check
            correction = Correction(
                correction_type=CorrectionType.ESCALATE_TO_GATE,
                target="resource",
                reason="Resource utilization high, escalating to gate",
                details={"margin": result.margin},
                confidence_impact=0.1,
            )
            corrections.append(correction)

        elif rail_id == "taint":
            # Enforce speculative tag
            correction = Correction(
                correction_type=CorrectionType.ENFORCE_SPECULATIVE_TAG,
                target="proposal",
                reason="Taint concerns, enforcing speculative handling",
                details={"margin": result.margin},
                confidence_impact=0.2,
            )
            corrections.append(correction)

        return corrections

    def apply_to_staged(
        self, staged: "StagedState", corrections: List[Correction]
    ) -> "StagedState":
        """
        Apply corrections to staged state.

        Args:
            staged: Staged state to modify
            corrections: List of corrections to apply

        Returns:
            Modified staged state
        """
        for correction in corrections:
            if correction.correction_type == CorrectionType.QUARANTINE_CLAIM:
                # Mark claims as quarantined
                if "quarantined_claims" not in staged.auxiliary:
                    staged.auxiliary["quarantined_claims"] = []
                staged.auxiliary["quarantined_claims"].append(correction.target)

            elif correction.correction_type == CorrectionType.ENFORCE_SPECULATIVE_TAG:
                # Add speculative tag
                staged.tags["speculative"] = {
                    "enforced": True,
                    "reason": correction.reason,
                    "confidence_reduction": correction.confidence_impact,
                }

            elif correction.correction_type == CorrectionType.RESTRICT_ACTION_SCOPE:
                # Reduce available budget
                if "budgets" in staged.resources:
                    for budget in staged.resources["budgets"]:
                        staged.resources["budgets"][budget] = max(
                            staged.resources["budgets"][budget] * 0.8,
                            0,
                        )

        return staged

    def compute_confidence_reduction(self, corrections: List[Correction]) -> float:
        """
        Compute total confidence reduction from corrections.

        Args:
            corrections: List of corrections applied

        Returns:
            Total confidence reduction (0.0 to 1.0)
        """
        total_impact = sum(c.confidence_impact for c in corrections)
        return min(total_impact, 1.0)

    def should_accept(
        self, corrections: List[Correction], base_confidence: float
    ) -> Tuple[bool, float]:
        """
        Determine if proposal should be accepted after corrections.

        Args:
            corrections: Corrections applied
            base_confidence: Original proposal confidence

        Returns:
            Tuple of (should_accept, adjusted_confidence)
        """
        # Check for rejection corrections
        rejection_corrections = [
            c for c in corrections if c.correction_type == CorrectionType.REJECT_PROPOSAL
        ]

        if rejection_corrections:
            return False, 0.0

        # Calculate adjusted confidence
        reduction = self.compute_confidence_reduction(corrections)
        adjusted_confidence = max(base_confidence - reduction, 0.0)

        # Accept if adjusted confidence >= 0.5
        return adjusted_confidence >= 0.5, adjusted_confidence


# Import StagedState and Proposal for type hints
from cnsc.haai.tgs.snapshot import StagedState
from cnsc.haai.tgs.proposal import Proposal
