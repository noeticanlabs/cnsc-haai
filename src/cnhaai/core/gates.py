"""
Gate System for CNHAAI

This module provides the gate infrastructure including:
- Gate: Base class for all gates
- EvidenceSufficiencyGate: Validates evidence quality
- CoherenceCheckGate: Validates coherence
- GateManager: Manages and evaluates gates
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from abc import ABC, abstractmethod
from datetime import datetime
from uuid import uuid4


class GateDecision(Enum):
    """Possible decisions from gate evaluation."""

    PASS = auto()  # Condition satisfied, proceed
    FAIL = auto()  # Condition violated, block
    WARN = auto()  # Condition marginal, proceed with warning
    SKIP = auto()  # Gate not applicable, skip


class GateType(Enum):
    """Types of gates in CNHAAI."""

    EVIDENCE_SUFFICIENCY = auto()
    COHERENCE_CHECK = auto()
    RECONSTRUCTION_BOUND = auto()
    CONTRADICTION = auto()
    SCOPE = auto()
    TEMPORAL = auto()


@dataclass
class GateResult:
    """Result of gate evaluation."""

    decision: GateDecision
    gate_type: GateType
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "decision": self.decision.name,
            "gate_type": self.gate_type.name,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "message": self.message,
        }


class Gate(ABC):
    """
    Base class for all gates in CNHAAI.

    A gate is a runtime constraint that validates transitions between states.
    Gates can be triggered by various conditions and produce decisions
    that determine whether reasoning can proceed.
    """

    def __init__(
        self,
        gate_type: GateType,
        name: str,
        description: str = "",
        threshold: float = 0.8,
        strict: bool = True,
    ):
        """
        Initialize a gate.

        Args:
            gate_type: The type of gate
            name: Human-readable name
            description: Detailed description
            threshold: Default threshold for decision making
            strict: If True, FAIL on error; if False, WARN
        """
        self.gate_type = gate_type
        self.name = name
        self.description = description
        self.threshold = threshold
        self.strict = strict
        self.enabled = True

    @abstractmethod
    def evaluate(self, context: Dict[str, Any], state: Dict[str, Any]) -> GateResult:
        """
        Evaluate the gate against the given context and state.

        Args:
            context: The current reasoning context
            state: The current system state

        Returns:
            GateResult with decision and details
        """
        pass

    def check_applicable(self, context: Dict[str, Any]) -> bool:
        """
        Check if this gate is applicable for the given context.

        Args:
            context: The current reasoning context

        Returns:
            True if gate should be evaluated
        """
        return self.enabled

    def __repr__(self) -> str:
        return f"Gate(name={self.name}, type={self.gate_type.name}, enabled={self.enabled})"


class EvidenceSufficiencyGate(Gate):
    """
    Gate that validates evidence quality and sufficiency.

    This gate ensures that reasoning is based on adequate evidence
    before allowing transitions or conclusions.
    """

    def __init__(self, threshold: float = 0.8, strict: bool = True, min_evidence_count: int = 1):
        """
        Initialize the evidence sufficiency gate.

        Args:
            threshold: Minimum evidence score threshold (0-1)
            strict: If True, FAIL on error
            min_evidence_count: Minimum number of evidence items required
        """
        super().__init__(
            gate_type=GateType.EVIDENCE_SUFFICIENCY,
            name="Evidence Sufficiency Gate",
            description="Validates that evidence quality and quantity meets threshold",
            threshold=threshold,
            strict=strict,
        )
        self.min_evidence_count = min_evidence_count

    def evaluate(self, context: Dict[str, Any], state: Dict[str, Any]) -> GateResult:
        """
        Evaluate evidence sufficiency.

        Args:
            context: The current reasoning context
            state: The current system state

        Returns:
            GateResult with PASS/FAIL/WARN decision
        """
        # Get evidence from context or state
        evidence = context.get("evidence", [])
        evidence_scores = context.get("evidence_scores", [])

        # Check evidence count
        if len(evidence) < self.min_evidence_count:
            return GateResult(
                decision=GateDecision.FAIL if self.strict else GateDecision.WARN,
                gate_type=self.gate_type,
                details={"evidence_count": len(evidence), "min_required": self.min_evidence_count},
                message=f"Insufficient evidence: {len(evidence)} < {self.min_evidence_count}",
            )

        # Calculate evidence quality score
        if evidence_scores:
            avg_score = sum(evidence_scores) / len(evidence_scores)
        else:
            # If no scores, assume neutral
            avg_score = 0.5

        # Calculate coverage score
        required_claims = context.get("required_claims", [])
        if required_claims:
            covered = sum(1 for claim in required_claims if claim in evidence)
            coverage_score = covered / len(required_claims)
        else:
            coverage_score = 1.0

        # Combined score
        combined_score = (avg_score * 0.6) + (coverage_score * 0.4)

        # Make decision
        if combined_score >= self.threshold:
            return GateResult(
                decision=GateDecision.PASS,
                gate_type=self.gate_type,
                details={
                    "avg_score": avg_score,
                    "coverage_score": coverage_score,
                    "combined_score": combined_score,
                    "evidence_count": len(evidence),
                },
                message=f"Evidence sufficient: score={combined_score:.2f}",
            )
        elif combined_score >= self.threshold * 0.7:
            return GateResult(
                decision=GateDecision.WARN,
                gate_type=self.gate_type,
                details={
                    "avg_score": avg_score,
                    "coverage_score": coverage_score,
                    "combined_score": combined_score,
                    "evidence_count": len(evidence),
                },
                message=f"Evidence marginal: score={combined_score:.2f} < {self.threshold}",
            )
        else:
            return GateResult(
                decision=GateDecision.FAIL if self.strict else GateDecision.WARN,
                gate_type=self.gate_type,
                details={
                    "avg_score": avg_score,
                    "coverage_score": coverage_score,
                    "combined_score": combined_score,
                    "evidence_count": len(evidence),
                },
                message=f"Evidence insufficient: score={combined_score:.2f} < {self.threshold}",
            )


class CoherenceCheckGate(Gate):
    """
    Gate that validates coherence of reasoning.

    This gate ensures that conclusions and intermediate states
    maintain coherence with existing knowledge and constraints.
    """

    def __init__(self, threshold: float = 0.8, strict: bool = True):
        """
        Initialize the coherence check gate.

        Args:
            threshold: Minimum coherence score threshold (0-1)
            strict: If True, FAIL on error
        """
        super().__init__(
            gate_type=GateType.COHERENCE_CHECK,
            name="Coherence Check Gate",
            description="Validates coherence of reasoning with existing constraints",
            threshold=threshold,
            strict=strict,
        )

    def evaluate(self, context: Dict[str, Any], state: Dict[str, Any]) -> GateResult:
        """
        Evaluate coherence.

        Args:
            context: The current reasoning context
            state: The current system state

        Returns:
            GateResult with PASS/FAIL/WARN decision
        """
        # Get coherence-relevant data
        conclusions = context.get("conclusions", [])
        constraints = context.get("constraints", [])
        coherence_budget = state.get("coherence_budget", 1.0)

        # Check for contradictions
        contradictions = self._find_contradictions(conclusions, constraints)

        # Calculate consistency score
        if contradictions:
            consistency_score = 1.0 - (len(contradictions) * 0.2)
            consistency_score = max(0.0, consistency_score)
        else:
            consistency_score = 1.0

        # Check against coherence budget
        budget_sufficient = coherence_budget >= self.threshold

        # Combined coherence check
        coherence_score = consistency_score if budget_sufficient else consistency_score * 0.5

        # Make decision
        if coherence_score >= self.threshold:
            return GateResult(
                decision=GateDecision.PASS,
                gate_type=self.gate_type,
                details={
                    "consistency_score": consistency_score,
                    "coherence_budget": coherence_budget,
                    "contradictions_found": len(contradictions),
                    "budget_sufficient": budget_sufficient,
                },
                message=f"Coherence check passed: score={coherence_score:.2f}",
            )
        elif coherence_score >= self.threshold * 0.7:
            return GateResult(
                decision=GateDecision.WARN,
                gate_type=self.gate_type,
                details={
                    "consistency_score": consistency_score,
                    "coherence_budget": coherence_budget,
                    "contradictions_found": len(contradictions),
                    "budget_sufficient": budget_sufficient,
                },
                message=f"Coherence marginal: score={coherence_score:.2f}",
            )
        else:
            return GateResult(
                decision=GateDecision.FAIL if self.strict else GateDecision.WARN,
                gate_type=self.gate_type,
                details={
                    "consistency_score": consistency_score,
                    "coherence_budget": coherence_budget,
                    "contradictions_found": len(contradictions),
                    "budget_sufficient": budget_sufficient,
                },
                message=f"Coherence check failed: score={coherence_score:.2f}",
            )

    def _find_contradictions(
        self, conclusions: List[str], constraints: List[Dict[str, Any]]
    ) -> List[str]:
        """Find contradictions between conclusions and constraints."""
        contradictions = []
        for constraint in constraints:
            constraint_type = constraint.get("type", "must")
            constraint_value = constraint.get("value", "")
            if constraint_type == "must" and constraint_value in conclusions:
                continue
            if constraint_type == "must_not" and constraint_value in conclusions:
                contradictions.append(f"Violated must_not: {constraint_value}")
        return contradictions


@dataclass
class GateManager:
    """
    Manages and evaluates gates for CNHAAI reasoning.

    The gate manager coordinates multiple gates, supports composition,
    and provides unified evaluation and reporting.
    """

    gates: List[Gate] = field(default_factory=list)
    enforcement: str = "strict"  # "strict", "permissive"
    short_circuit: bool = True  # Stop on first failure

    def add_gate(self, gate: Gate) -> None:
        """Add a gate to the manager."""
        self.gates.append(gate)

    def remove_gate(self, gate_name: str) -> bool:
        """Remove a gate by name."""
        for i, gate in enumerate(self.gates):
            if gate.name == gate_name:
                self.gates.pop(i)
                return True
        return False

    def get_gate(self, gate_name: str) -> Optional[Gate]:
        """Get a gate by name."""
        for gate in self.gates:
            if gate.name == gate_name:
                return gate
        return None

    def evaluate_all(
        self, context: Dict[str, Any], state: Dict[str, Any]
    ) -> Tuple[List[GateResult], bool]:
        """
        Evaluate all applicable gates.

        Args:
            context: The current reasoning context
            state: The current system state

        Returns:
            Tuple of (list of results, all passed flag)
        """
        results = []
        all_passed = True

        for gate in self.gates:
            if not gate.check_applicable(context):
                results.append(
                    GateResult(
                        decision=GateDecision.SKIP,
                        gate_type=gate.gate_type,
                        message=f"Gate '{gate.name}' not applicable",
                    )
                )
                continue

            result = gate.evaluate(context, state)
            results.append(result)

            if result.decision == GateDecision.FAIL:
                all_passed = False
                if self.short_circuit:
                    break
            elif result.decision == GateDecision.WARN:
                # Warnings don't fail but track that not all passed cleanly
                if self.enforcement == "strict":
                    all_passed = False

        return results, all_passed

    def evaluate_required(self, context: Dict[str, Any], state: Dict[str, Any]) -> List[GateResult]:
        """
        Evaluate only gates that are applicable and required.

        Args:
            context: The current reasoning context
            state: The current system state

        Returns:
            List of gate results
        """
        results = []
        for gate in self.gates:
            if gate.check_applicable(context):
                result = gate.evaluate(context, state)
                results.append(result)
        return results

    def get_summary(self, results: List[GateResult]) -> Dict[str, Any]:
        """
        Get a summary of gate evaluation results.

        Args:
            results: List of gate results

        Returns:
            Summary dictionary with counts and details
        """
        summary = {
            "total": len(results),
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "skipped": 0,
            "by_type": {},
        }

        for result in results:
            if result.decision == GateDecision.PASS:
                summary["passed"] += 1
            elif result.decision == GateDecision.FAIL:
                summary["failed"] += 1
            elif result.decision == GateDecision.WARN:
                summary["warnings"] += 1
            elif result.decision == GateDecision.SKIP:
                summary["skipped"] += 1

            type_name = result.gate_type.name
            if type_name not in summary["by_type"]:
                summary["by_type"][type_name] = {
                    "passed": 0,
                    "failed": 0,
                    "warnings": 0,
                    "skipped": 0,
                }
            # Use full decision name for consistency
            decision_key = result.decision.name.lower()
            if decision_key == "pass":
                summary["by_type"][type_name]["passed"] += 1
            elif decision_key == "fail":
                summary["by_type"][type_name]["failed"] += 1
            elif decision_key == "warn":
                summary["by_type"][type_name]["warnings"] += 1
            elif decision_key == "skip":
                summary["by_type"][type_name]["skipped"] += 1

        return summary

    def create_default_gates(self) -> None:
        """Create and add default gates for minimal kernel."""
        self.gates = [EvidenceSufficiencyGate(threshold=0.8), CoherenceCheckGate(threshold=0.8)]
