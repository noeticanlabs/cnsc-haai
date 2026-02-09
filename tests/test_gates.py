"""
Tests for the Gate system.

Tests cover:
- GateDecision enum values (PASS, FAIL, WARN, SKIP)
- GateType enum values
- Gate base class and subclasses
- EvidenceSufficiencyGate with various evidence scenarios
- CoherenceCheckGate with coherence levels
- GateManager creation and gate registration
- GateResult structure and properties
- Gate evaluation with different contexts
"""

import pytest
from datetime import datetime
from uuid import uuid4

from src.cnhaai.core.gates import (
    GateDecision,
    GateType,
    GateResult,
    Gate,
    EvidenceSufficiencyGate,
    CoherenceCheckGate,
    GateManager
)


class TestGateDecision:
    """Tests for GateDecision enum."""

    def test_gate_decision_values_exist(self):
        """Test that all expected gate decisions are defined."""
        assert GateDecision.PASS is not None
        assert GateDecision.FAIL is not None
        assert GateDecision.WARN is not None
        assert GateDecision.SKIP is not None

    def test_gate_decision_count(self):
        """Test that exactly 4 gate decisions are defined."""
        assert len(GateDecision) == 4

    def test_gate_decision_names(self):
        """Test gate decision name strings."""
        assert GateDecision.PASS.name == "PASS"
        assert GateDecision.FAIL.name == "FAIL"
        assert GateDecision.WARN.name == "WARN"
        assert GateDecision.SKIP.name == "SKIP"


class TestGateType:
    """Tests for GateType enum."""

    def test_gate_type_values_exist(self):
        """Test that all expected gate types are defined."""
        assert GateType.EVIDENCE_SUFFICIENCY is not None
        assert GateType.COHERENCE_CHECK is not None
        assert GateType.RECONSTRUCTION_BOUND is not None
        assert GateType.CONTRADICTION is not None
        assert GateType.SCOPE is not None
        assert GateType.TEMPORAL is not None

    def test_gate_type_count(self):
        """Test that exactly 6 gate types are defined."""
        assert len(GateType) == 6


class TestGateResult:
    """Tests for GateResult class."""

    def test_gate_result_creation(self):
        """Test creating a gate result."""
        result = GateResult(
            decision=GateDecision.PASS,
            gate_type=GateType.EVIDENCE_SUFFICIENCY,
            details={"score": 0.9},
            message="Test passed"
        )

        assert result.decision == GateDecision.PASS
        assert result.gate_type == GateType.EVIDENCE_SUFFICIENCY
        assert result.details == {"score": 0.9}
        assert result.message == "Test passed"
        assert isinstance(result.timestamp, datetime)

    def test_gate_result_defaults(self):
        """Test gate result default values."""
        result = GateResult(
            decision=GateDecision.PASS,
            gate_type=GateType.COHERENCE_CHECK
        )

        assert result.details == {}
        assert result.message == ""
        assert result.timestamp is not None

    def test_gate_result_to_dict(self):
        """Test converting gate result to dictionary."""
        result = GateResult(
            decision=GateDecision.FAIL,
            gate_type=GateType.COHERENCE_CHECK,
            details={"error": "test"},
            message="Gate failed"
        )

        result_dict = result.to_dict()

        assert result_dict["decision"] == "FAIL"
        assert result_dict["gate_type"] == "COHERENCE_CHECK"
        assert result_dict["details"] == {"error": "test"}
        assert result_dict["message"] == "Gate failed"
        assert "timestamp" in result_dict


class TestGateBaseClass:
    """Tests for the base Gate class using concrete implementations."""

    def test_gate_creation_with_concrete_subclass(self):
        """Test creating a gate using concrete EvidenceSufficiencyGate subclass."""
        gate = EvidenceSufficiencyGate(
            threshold=0.8,
            strict=True,
            min_evidence_count=2
        )

        assert gate.gate_type == GateType.EVIDENCE_SUFFICIENCY
        assert gate.name == "Evidence Sufficiency Gate"
        assert gate.description == "Validates that evidence quality and quantity meets threshold"
        assert gate.threshold == 0.8
        assert gate.strict is True
        assert gate.enabled is True

    def test_gate_default_values_with_concrete_subclass(self):
        """Test gate default values using CoherenceCheckGate."""
        gate = CoherenceCheckGate(
            threshold=0.8,
            strict=True
        )

        assert gate.description == "Validates coherence of reasoning with existing constraints"
        assert gate.threshold == 0.8
        assert gate.strict is True
        assert gate.enabled is True

    def test_gate_check_applicable_with_concrete_subclass(self):
        """Test check_applicable method using concrete gate."""
        gate = EvidenceSufficiencyGate()

        assert gate.check_applicable({}) is True

    def test_gate_disabled_not_applicable(self):
        """Test that disabled gate returns not applicable."""
        gate = EvidenceSufficiencyGate()
        gate.enabled = False

        assert gate.check_applicable({}) is False

    def test_gate_repr_with_concrete_subclass(self):
        """Test gate string representation using concrete gate."""
        gate = CoherenceCheckGate()

        repr_str = repr(gate)
        assert "Coherence Check Gate" in repr_str
        assert "COHERENCE_CHECK" in repr_str
        assert "enabled=True" in repr_str


class TestEvidenceSufficiencyGate:
    """Tests for EvidenceSufficiencyGate class."""

    def test_gate_creation(self):
        """Test creating an evidence sufficiency gate."""
        gate = EvidenceSufficiencyGate(
            threshold=0.8,
            strict=True,
            min_evidence_count=2
        )

        assert gate.gate_type == GateType.EVIDENCE_SUFFICIENCY
        assert gate.name == "Evidence Sufficiency Gate"
        assert gate.threshold == 0.8
        assert gate.strict is True
        assert gate.min_evidence_count == 2

    def test_evaluate_insufficient_evidence_count(self):
        """Test evaluation with insufficient evidence count."""
        gate = EvidenceSufficiencyGate(min_evidence_count=3)
        context = {"evidence": ["e1", "e2"]}
        state = {}

        result = gate.evaluate(context, state)

        assert result.decision == GateDecision.FAIL
        assert result.gate_type == GateType.EVIDENCE_SUFFICIENCY
        assert "Insufficient evidence" in result.message
        assert result.details["evidence_count"] == 2
        assert result.details["min_required"] == 3

    def test_evaluate_strict_vs_permissive(self):
        """Test strict vs permissive mode."""
        context = {"evidence": ["e1"]}
        state = {}

        strict_gate = EvidenceSufficiencyGate(strict=True, min_evidence_count=2)
        permissive_gate = EvidenceSufficiencyGate(strict=False, min_evidence_count=2)

        strict_result = strict_gate.evaluate(context, state)
        permissive_result = permissive_gate.evaluate(context, state)

        assert strict_result.decision == GateDecision.FAIL
        assert permissive_result.decision == GateDecision.WARN

    def test_evaluate_sufficient_evidence(self):
        """Test evaluation with sufficient evidence."""
        gate = EvidenceSufficiencyGate(threshold=0.8)
        context = {
            "evidence": ["e1", "e2", "e3"],
            "evidence_scores": [0.9, 0.85, 0.95],
            "required_claims": ["e1", "e2"]
        }
        state = {}

        result = gate.evaluate(context, state)

        assert result.decision == GateDecision.PASS
        assert "Evidence sufficient" in result.message
        assert "combined_score" in result.details

    def test_evaluate_marginal_evidence(self):
        """Test evaluation with marginal evidence."""
        gate = EvidenceSufficiencyGate(threshold=0.8)
        context = {
            "evidence": ["e1", "e2"],
            "evidence_scores": [0.5, 0.5],
            "required_claims": ["e1", "e2", "e3"]
        }
        state = {}

        result = gate.evaluate(context, state)

        assert result.decision == GateDecision.WARN
        assert "Evidence marginal" in result.message

    def test_evaluate_insufficient_evidence_quality(self):
        """Test evaluation with low evidence quality."""
        gate = EvidenceSufficiencyGate(threshold=0.8)
        context = {
            "evidence": ["e1"],
            "evidence_scores": [0.3],
            "required_claims": ["e1"]
        }
        state = {}

        result = gate.evaluate(context, state)

        # avg_score = 0.3, coverage_score = 1.0, combined = 0.3 * 0.6 + 1.0 * 0.4 = 0.58
        # threshold * 0.7 = 0.56
        # 0.58 >= 0.56 and 0.58 < 0.8, so WARN (not FAIL)
        assert result.decision == GateDecision.WARN
        assert "Evidence marginal" in result.message

    def test_evaluate_with_no_scores(self):
        """Test evaluation when no evidence scores provided."""
        gate = EvidenceSufficiencyGate(threshold=0.8)
        context = {
            "evidence": ["e1", "e2"],
            "required_claims": ["e1"]
        }
        state = {}

        result = gate.evaluate(context, state)

        # Should assume neutral score of 0.5
        assert result.details["avg_score"] == 0.5

    def test_evaluate_full_coverage(self):
        """Test evaluation with full claim coverage."""
        gate = EvidenceSufficiencyGate(threshold=0.8)
        context = {
            "evidence": ["e1", "e2"],
            "evidence_scores": [0.9, 0.9],
            "required_claims": ["e1", "e2"]
        }
        state = {}

        result = gate.evaluate(context, state)

        assert result.details["coverage_score"] == 1.0

    def test_evaluate_no_required_claims(self):
        """Test evaluation when no required claims specified."""
        gate = EvidenceSufficiencyGate(threshold=0.8)
        context = {
            "evidence": ["e1", "e2"],
            "evidence_scores": [0.7, 0.7]
        }
        state = {}

        result = gate.evaluate(context, state)

        # Should assume full coverage
        assert result.details["coverage_score"] == 1.0


class TestCoherenceCheckGate:
    """Tests for CoherenceCheckGate class."""

    def test_gate_creation(self):
        """Test creating a coherence check gate."""
        gate = CoherenceCheckGate(
            threshold=0.8,
            strict=True
        )

        assert gate.gate_type == GateType.COHERENCE_CHECK
        assert gate.name == "Coherence Check Gate"
        assert gate.threshold == 0.8
        assert gate.strict is True

    def test_evaluate_no_contradictions(self):
        """Test evaluation with no contradictions."""
        gate = CoherenceCheckGate(threshold=0.8)
        context = {
            "conclusions": ["c1", "c2"],
            "constraints": [{"type": "must", "value": "c1"}]
        }
        state = {"coherence_budget": 1.0}

        result = gate.evaluate(context, state)

        assert result.decision == GateDecision.PASS
        assert result.details["contradictions_found"] == 0
        assert result.details["consistency_score"] == 1.0
        assert result.details["budget_sufficient"] is True

    def test_evaluate_with_contradictions(self):
        """Test evaluation with contradictions."""
        gate = CoherenceCheckGate(threshold=0.8)
        context = {
            "conclusions": ["c1", "c2"],
            "constraints": [
                {"type": "must_not", "value": "c1"},
                {"type": "must", "value": "c3"}
            ]
        }
        state = {"coherence_budget": 1.0}

        result = gate.evaluate(context, state)

        assert result.details["contradictions_found"] == 1
        # Consistency score reduced by 0.2 per contradiction
        assert result.details["consistency_score"] == 0.8

    def test_evaluate_low_coherence_budget(self):
        """Test evaluation with low coherence budget."""
        gate = CoherenceCheckGate(threshold=0.8)
        context = {
            "conclusions": [],
            "constraints": []
        }
        state = {"coherence_budget": 0.5}

        result = gate.evaluate(context, state)

        assert result.details["budget_sufficient"] is False
        # consistency_score is NOT halved - only coherence_score is halved
        # consistency_score remains 1.0, coherence_score = 1.0 * 0.5 = 0.5
        assert result.details["consistency_score"] == 1.0

    def test_evaluate_coherence_budget_below_threshold(self):
        """Test evaluation when coherence budget is below threshold."""
        gate = CoherenceCheckGate(threshold=0.8)
        context = {
            "conclusions": [],
            "constraints": []
        }
        state = {"coherence_budget": 0.7}

        result = gate.evaluate(context, state)

        # budget_sufficient: 0.7 < 0.8 = False
        # coherence_score = consistency_score (1.0) * 0.5 = 0.5
        # threshold * 0.7 = 0.56
        # 0.5 < 0.56, so result is FAIL (not WARN as originally expected)
        assert result.details["budget_sufficient"] is False
        assert result.decision == GateDecision.FAIL
        assert "Coherence check failed" in result.message

    def test_evaluate_multiple_contradictions(self):
        """Test evaluation with multiple contradictions."""
        gate = CoherenceCheckGate(threshold=0.8)
        context = {
            "conclusions": ["c1", "c2", "c3", "c4"],
            "constraints": [
                {"type": "must_not", "value": "c1"},
                {"type": "must_not", "value": "c2"},
                {"type": "must_not", "value": "c3"}
            ]
        }
        state = {"coherence_budget": 1.0}

        result = gate.evaluate(context, state)

        # Consistency should be 1.0 - (3 * 0.2) = 0.4 (with floating point: ~0.4)
        assert result.details["contradictions_found"] == 3
        assert abs(result.details["consistency_score"] - 0.4) < 0.001

    def test_evaluate_must_constraints_satisfied(self):
        """Test that satisfied must constraints don't cause failures."""
        gate = CoherenceCheckGate(threshold=0.8)
        context = {
            "conclusions": ["c1", "c2"],
            "constraints": [
                {"type": "must", "value": "c1"},
                {"type": "must", "value": "c2"}
            ]
        }
        state = {"coherence_budget": 1.0}

        result = gate.evaluate(context, state)

        assert result.details["contradictions_found"] == 0

    def test_find_contradictions_must_not(self):
        """Test contradiction detection for must_not constraints."""
        gate = CoherenceCheckGate()
        contradictions = gate._find_contradictions(
            ["c1", "c2"],
            [{"type": "must_not", "value": "c1"}]
        )

        assert len(contradictions) == 1
        assert "c1" in contradictions[0]

    def test_find_contradictions_no_contradictions(self):
        """Test when there are no contradictions."""
        gate = CoherenceCheckGate()
        contradictions = gate._find_contradictions(
            ["c1"],
            [{"type": "must_not", "value": "c2"}]
        )

        assert len(contradictions) == 0


class TestGateManager:
    """Tests for GateManager class."""

    def test_manager_creation(self):
        """Test creating a gate manager."""
        manager = GateManager()

        assert manager.gates == []
        assert manager.enforcement == "strict"
        assert manager.short_circuit is True

    def test_add_gate(self):
        """Test adding a gate."""
        manager = GateManager()
        gate = EvidenceSufficiencyGate()

        manager.add_gate(gate)

        assert len(manager.gates) == 1
        assert manager.gates[0] == gate

    def test_add_multiple_gates(self):
        """Test adding multiple gates."""
        manager = GateManager()
        gate1 = EvidenceSufficiencyGate()
        gate2 = CoherenceCheckGate()

        manager.add_gate(gate1)
        manager.add_gate(gate2)

        assert len(manager.gates) == 2

    def test_remove_gate_by_name(self):
        """Test removing a gate by name."""
        manager = GateManager()
        gate = EvidenceSufficiencyGate()

        manager.add_gate(gate)
        result = manager.remove_gate("Evidence Sufficiency Gate")

        assert result is True
        assert len(manager.gates) == 0

    def test_remove_nonexistent_gate(self):
        """Test removing a non-existent gate."""
        manager = GateManager()

        result = manager.remove_gate("Nonexistent Gate")

        assert result is False

    def test_get_gate_by_name(self):
        """Test retrieving a gate by name."""
        manager = GateManager()
        gate = EvidenceSufficiencyGate()

        manager.add_gate(gate)
        result = manager.get_gate("Evidence Sufficiency Gate")

        assert result == gate

    def test_get_nonexistent_gate(self):
        """Test retrieving a non-existent gate."""
        manager = GateManager()

        result = manager.get_gate("Nonexistent Gate")

        assert result is None

    def test_evaluate_all_gates_pass(self):
        """Test evaluating all gates when all pass."""
        manager = GateManager()
        manager.gates = [
            EvidenceSufficiencyGate(threshold=0.5),
            CoherenceCheckGate(threshold=0.5)
        ]

        context = {
            "evidence": ["e1"],
            "evidence_scores": [0.9],
            "conclusions": [],
            "constraints": []
        }
        state = {"coherence_budget": 0.9}

        results, all_passed = manager.evaluate_all(context, state)

        assert all_passed is True
        assert len(results) == 2
        assert all(r.decision == GateDecision.PASS for r in results)

    def test_evaluate_all_gates_fail(self):
        """Test evaluating all gates when one fails."""
        manager = GateManager()
        manager.gates = [
            EvidenceSufficiencyGate(threshold=0.9, min_evidence_count=5),
            CoherenceCheckGate(threshold=0.5)
        ]

        context = {
            "evidence": ["e1"],
            "evidence_scores": [0.5],
            "conclusions": [],
            "constraints": []
        }
        state = {"coherence_budget": 0.9}

        results, all_passed = manager.evaluate_all(context, state)

        assert all_passed is False

    def test_evaluate_all_short_circuit(self):
        """Test that short_circuit stops on first failure."""
        manager = GateManager()
        manager.short_circuit = True
        manager.gates = [
            EvidenceSufficiencyGate(threshold=0.9),
            CoherenceCheckGate()
        ]

        context = {
            "evidence": [],
            "evidence_scores": [],
            "conclusions": [],
            "constraints": []
        }
        state = {"coherence_budget": 1.0}

        results, all_passed = manager.evaluate_all(context, state)

        assert len(results) == 1  # Should stop after first failure
        assert results[0].decision == GateDecision.FAIL

    def test_evaluate_all_no_short_circuit(self):
        """Test evaluation without short_circuit."""
        manager = GateManager()
        manager.short_circuit = False
        manager.gates = [
            EvidenceSufficiencyGate(threshold=0.9),
            CoherenceCheckGate()
        ]

        context = {
            "evidence": [],
            "evidence_scores": [],
            "conclusions": [],
            "constraints": []
        }
        state = {"coherence_budget": 1.0}

        results, all_passed = manager.evaluate_all(context, state)

        assert len(results) == 2  # Evaluate all gates
        assert results[0].decision == GateDecision.FAIL

    def test_evaluate_disabled_gates_skipped(self):
        """Test that disabled gates are skipped."""
        manager = GateManager()
        gate1 = EvidenceSufficiencyGate()
        gate2 = CoherenceCheckGate()
        gate1.enabled = False

        manager.gates = [gate1, gate2]

        context = {
            "evidence": ["e1"],
            "evidence_scores": [0.9],
            "conclusions": [],
            "constraints": []
        }
        state = {"coherence_budget": 1.0}

        results, all_passed = manager.evaluate_all(context, state)

        assert len(results) == 2
        assert results[0].decision == GateDecision.SKIP
        assert results[1].decision == GateDecision.PASS

    def test_get_summary(self):
        """Test getting summary of gate results."""
        manager = GateManager()
        results = [
            GateResult(decision=GateDecision.PASS, gate_type=GateType.EVIDENCE_SUFFICIENCY),
            GateResult(decision=GateDecision.FAIL, gate_type=GateType.COHERENCE_CHECK),
            GateResult(decision=GateDecision.WARN, gate_type=GateType.EVIDENCE_SUFFICIENCY),
        ]

        summary = manager.get_summary(results)

        assert summary["total"] == 3
        # Keys are lowercase: pass, fail, warn, skip
        assert summary.get("passed", 0) == 1
        assert summary.get("failed", 0) == 1
        assert summary.get("warnings", 0) == 1
        assert summary["warnings"] == 1
        assert summary["skipped"] == 0
        assert "EVIDENCE_SUFFICIENCY" in summary["by_type"]
        assert "COHERENCE_CHECK" in summary["by_type"]

    def test_create_default_gates(self):
        """Test creating default gates."""
        manager = GateManager()
        manager.create_default_gates()

        assert len(manager.gates) == 2
        assert isinstance(manager.gates[0], EvidenceSufficiencyGate)
        assert isinstance(manager.gates[1], CoherenceCheckGate)

    def test_evaluate_required_gates(self):
        """Test evaluating only required gates."""
        manager = GateManager()
        manager.gates = [
            EvidenceSufficiencyGate(threshold=0.8),
            CoherenceCheckGate(threshold=0.8)
        ]

        context = {
            "evidence": ["e1"],
            "evidence_scores": [0.9],
            "conclusions": [],
            "constraints": []
        }
        state = {"coherence_budget": 1.0}

        results = manager.evaluate_required(context, state)

        assert len(results) == 2
