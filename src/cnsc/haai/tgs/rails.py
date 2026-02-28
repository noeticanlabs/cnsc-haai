"""
Coherence Rails

Extends GateManager with TGS-specific coherence rails.
Evaluates mandatory coherence constraints for governance.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple
from cnsc.haai.nsc.gates import (
    GateManager,
    GateResult,
    GateDecision,
)


class RailID(str):
    """Unique identifier for a coherence rail."""

    def __new__(cls, value: str):
        instance = super().__new__(cls, value)
        return instance


class RailDecision(Enum):
    """Rail evaluation decision."""

    PASS = auto()
    FAIL = auto()
    MARGINAL = auto()
    SKIP = auto()


@dataclass
class RailResult:
    """Result from rail evaluation."""

    rail_id: RailID
    decision: RailDecision
    margin: float  # Safety margin (0.0 to 1.0)
    details: Dict[str, Any] = field(default_factory=dict)
    message: str = ""


@dataclass
class CompositeRailResult:
    """Composite result from multiple rail evaluations."""

    all_passed: bool
    results: List[RailResult]
    failed_rails: List[RailID] = field(default_factory=list)
    marginal_rails: List[RailID] = field(default_factory=list)
    total_margin: float = 0.0

    @property
    def acceptance_margin(self) -> float:
        """Overall acceptance margin (min margin across all rails)."""
        if not self.results:
            return 0.0
        return min(r.margin for r in self.results)


class CoherenceRails:
    """
    Mandatory coherence rails for TGS.

    Evaluates the following rails:
    - Consistency: No contradictions in staged state
    - Commitment: Obligations are manageable
    - Causality: Evidence and prerequisites are available
    - Resource: Budget constraints are respected
    - Taint: Untrusted input is properly handled
    """

    RAIL_CONSISTENCY = RailID("consistency")
    RAIL_COMMITMENT = RailID("commitment")
    RAIL_CAUSALITY = RailID("causality")
    RAIL_RESOURCE = RailID("resource")
    RAIL_TAINT = RailID("taint")

    def __init__(self, gate_manager: Optional[GateManager] = None):
        """
        Initialize rails with optional gate manager.

        Args:
            gate_manager: Optional GateManager for integration
        """
        self._gate_manager = gate_manager

    def evaluate_consistency_rail(self, staged: "StagedState", proposal: "Proposal") -> RailResult:
        """Evaluate consistency rail."""
        # Check for belief contradictions
        beliefs = staged.memory.get("beliefs", {})

        contradictions = 0
        for belief_id, belief in beliefs.items():
            # Check if belief conflicts with other beliefs
            for other_id, other in beliefs.items():
                if belief_id != other_id:
                    if self._check_contradiction(belief, other):
                        contradictions += 1

        # Check if proposal introduces contradictions
        for delta in proposal.delta_ops:
            if delta.operation.name in ("ADD_BELIEF", "REVISE_BELIEF"):
                target = delta.target
                new_content = delta.payload.get("content", {})
                for other_id, other in beliefs.items():
                    if target != other_id:
                        if self._check_contradiction(new_content, other):
                            contradictions += 1

        # Calculate margin
        if contradictions == 0:
            margin = 1.0
            decision = RailDecision.PASS
            message = "No contradictions detected"
        elif contradictions <= 2:
            margin = 0.5
            decision = RailDecision.MARGINAL
            message = f"Minor contradictions detected: {contradictions}"
        else:
            margin = 0.0
            decision = RailDecision.FAIL
            message = f"Critical contradictions detected: {contradictions}"

        return RailResult(
            rail_id=self.RAIL_CONSISTENCY,
            decision=decision,
            margin=margin,
            details={"contradictions": contradictions},
            message=message,
        )

    def evaluate_commitment_rail(self, staged: "StagedState", proposal: "Proposal") -> RailResult:
        """Evaluate commitment rail."""
        # Check obligation load
        obligations = staged.memory.get("obligations", [])
        obligation_count = len(obligations)

        # Check intent stability
        intents = staged.memory.get("intents", [])
        unstable_intents = sum(1 for intent in intents if intent.get("stability", 1.0) < 0.5)

        # Calculate commitment load
        load = (obligation_count / 20.0) + (unstable_intents / 10.0)

        if load < 0.3:
            margin = 1.0 - load
            decision = RailDecision.PASS
            message = f"Commitment load acceptable: {load:.2f}"
        elif load < 0.6:
            margin = 0.5
            decision = RailDecision.MARGINAL
            message = f"Commitment load elevated: {load:.2f}"
        else:
            margin = 0.0
            decision = RailDecision.FAIL
            message = f"Commitment load critical: {load:.2f}"

        return RailResult(
            rail_id=self.RAIL_COMMITMENT,
            decision=decision,
            margin=margin,
            details={
                "obligation_count": obligation_count,
                "unstable_intents": unstable_intents,
                "load": load,
            },
            message=message,
        )

    def evaluate_causality_rail(self, staged: "StagedState", proposal: "Proposal") -> RailResult:
        """Evaluate causality rail."""
        # Check evidence availability
        evidence_pool = staged.memory.get("evidence", {})
        missing_evidence = 0

        for ref in proposal.evidence_refs:
            if ref not in evidence_pool:
                missing_evidence += 1

        # Check prerequisites
        unmet_prerequisites = 0
        events = staged.memory.get("events", {})
        current_time = staged.auxiliary.get("logical_time", 0)

        for delta in proposal.delta_ops:
            if hasattr(delta, "prerequisites"):
                for prereq in delta.prerequisites:
                    prereq_event = events.get(prereq, {})
                    prereq_time = prereq_event.get("time", 0)
                    if prereq_time > current_time:
                        unmet_prerequisites += 1

        # Calculate causality score
        evidence_score = 1.0 - (missing_evidence / max(len(proposal.evidence_refs), 1))
        prereq_score = 1.0 - (unmet_prerequisites / max(len(proposal.delta_ops), 1))

        causality_score = (evidence_score + prereq_score) / 2.0

        if causality_score >= 0.9:
            margin = causality_score
            decision = RailDecision.PASS
            message = "Causality requirements satisfied"
        elif causality_score >= 0.6:
            margin = causality_score
            decision = RailDecision.MARGINAL
            message = "Partial causality concerns"
        else:
            margin = 0.0
            decision = RailDecision.FAIL
            message = "Causality requirements violated"

        return RailResult(
            rail_id=self.RAIL_CAUSALITY,
            decision=decision,
            margin=margin,
            details={
                "missing_evidence": missing_evidence,
                "unmet_prerequisites": unmet_prerequisites,
                "causality_score": causality_score,
            },
            message=message,
        )

    def evaluate_resource_rail(self, staged: "StagedState", proposal: "Proposal") -> RailResult:
        """Evaluate resource rail."""
        budgets = staged.resources.get("budgets", {})
        cost_estimate = proposal.cost_estimate or {}

        # Calculate budget utilization
        violations = 0
        total_utilization = 0.0

        for resource, remaining in budgets.items():
            allocated = cost_estimate.get(resource, 0)
            utilization = allocated / max(remaining, 1)
            total_utilization += utilization

            if utilization > 1.0:
                violations += 1

        avg_utilization = total_utilization / max(len(budgets), 1)

        if violations == 0 and avg_utilization < 0.8:
            margin = 1.0 - avg_utilization
            decision = RailDecision.PASS
            message = "Resource constraints satisfied"
        elif violations == 0:
            margin = 0.3
            decision = RailDecision.MARGINAL
            message = "Resource utilization high"
        else:
            margin = 0.0
            decision = RailDecision.FAIL
            message = f"Resource violations: {violations}"

        return RailResult(
            rail_id=self.RAIL_RESOURCE,
            decision=decision,
            margin=margin,
            details={
                "violations": violations,
                "avg_utilization": avg_utilization,
            },
            message=message,
        )

    def evaluate_taint_rail(self, staged: "StagedState", proposal: "Proposal") -> RailResult:
        """Evaluate taint rail."""
        from cnsc.haai.tgs.proposal import TaintClass

        taint = proposal.taint_class

        if taint == TaintClass.TRUSTED:
            margin = 1.0
            decision = RailDecision.PASS
            message = "Input is trusted"
        elif taint == TaintClass.EXTERNAL:
            margin = 0.7
            decision = RailDecision.PASS
            message = "External input requires validation"
        elif taint == TaintClass.SPECULATIVE:
            margin = 0.5
            decision = RailDecision.MARGINAL
            message = "Speculative input requires quarantine"
        else:  # UNTRUSTED
            margin = 0.0
            decision = RailDecision.FAIL
            message = "Untrusted input rejected"

        return RailResult(
            rail_id=self.RAIL_TAINT,
            decision=decision,
            margin=margin,
            details={"taint_class": taint.name},
            message=message,
        )

    def evaluate_all(self, staged: "StagedState", proposal: "Proposal") -> CompositeRailResult:
        """
        Evaluate all coherence rails.

        Args:
            staged: Staged state to evaluate
            proposal: Proposal being evaluated

        Returns:
            Composite result with all rail evaluations
        """
        results = [
            self.evaluate_consistency_rail(staged, proposal),
            self.evaluate_commitment_rail(staged, proposal),
            self.evaluate_causality_rail(staged, proposal),
            self.evaluate_resource_rail(staged, proposal),
            self.evaluate_taint_rail(staged, proposal),
        ]

        failed_rails = [r.rail_id for r in results if r.decision == RailDecision.FAIL]
        marginal_rails = [r.rail_id for r in results if r.decision == RailDecision.MARGINAL]
        total_margin = sum(r.margin for r in results) / len(results)

        all_passed = len(failed_rails) == 0

        return CompositeRailResult(
            all_passed=all_passed,
            results=results,
            failed_rails=failed_rails,
            marginal_rails=marginal_rails,
            total_margin=total_margin,
        )

    def _check_contradiction(self, belief1: Dict, belief2: Dict) -> bool:
        """Check if two beliefs contradict each other."""
        # Simple contradiction check based on content
        content1 = belief1.get("content", {})
        content2 = belief2.get("content", {})

        # Check for conflicting predicates
        pred1 = content1.get("predicate")
        pred2 = content2.get("predicate")

        if pred1 and pred2 and pred1 == pred2:
            subj1 = content1.get("subject")
            subj2 = content2.get("subject")
            obj1 = content1.get("object")
            obj2 = content2.get("object")

            # Same subject, opposite object = contradiction
            if subj1 == subj2 and obj1 and obj2 and obj1 != obj2:
                return True

        return False


# Import StagedState and Proposal for type hints
from cnsc.haai.tgs.snapshot import StagedState
from cnsc.haai.tgs.proposal import Proposal
