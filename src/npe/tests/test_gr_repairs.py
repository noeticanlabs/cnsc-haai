"""
Tests for GR Repair Proposers.

Verifies that gate failures produce expected repair payloads.
"""

import pytest
import sys
sys.path.insert(0, '/workspaces/cnsc-haai/src')

from npe.core.budgets import Budgets
from npe.core.hashing import hash_candidate
from npe.proposers.gr.repair_from_gate_reasons import (
    propose as repair_propose,
    _score_repair,
)
from npe.core.types import Scores


class TestRepairFromGateReasons:
    """Tests for repair proposer."""
    
    def test_no_failing_gates_returns_empty(self):
        """No failing gates returns empty candidate list."""
        context = {"failure": {"failing_gates": []}}
        budget = Budgets()
        
        result = repair_propose(context, budget, None)
        
        assert result == []
    
    def test_empty_context_returns_empty(self):
        """Empty context returns empty candidate list."""
        context = {}
        budget = Budgets()
        
        result = repair_propose(context, budget, None)
        
        assert result == []
    
    def test_repair_candidate_structure(self):
        """Repair candidate has correct structure."""
        context = {
            "failure": {"failing_gates": ["safety_gate"]},
            "state_ref": {"state_hash": "abc123"},
            "constraints_ref": {"constraints_hash": "def456"},
        }
        budget = Budgets()
        
        # Mock codebook store
        class MockCodebookStore:
            def get_repair_actions(self, domain, gate_type):
                return [{
                    "type": "parameter_adjustment",
                    "description": "Adjust threshold",
                    "parameters": {"threshold": 0.8},
                    "rationale": "Lower threshold for safety",
                    "preconditions": [],
                    "safety_level": "high",
                    "impact": "low",
                }]
        
        context["codebook_store"] = MockCodebookStore()
        result = repair_propose(context, budget, None)
        
        assert len(result) >= 1
        candidate = result[0]
        
        # Check candidate structure
        assert candidate.candidate_type == "repair"
        assert candidate.domain == "gr"
        assert candidate.payload_format == "json"
        assert candidate.candidate_hash != ""
        assert candidate.payload_hash != ""
        
        # Check payload structure
        assert "repair_type" in candidate.payload
        assert "target_gate" in candidate.payload
        assert "description" in candidate.payload
        assert "parameters" in candidate.payload
    
    def test_repair_targets_correct_gate(self):
        """Repair targets the correct failing gate."""
        context = {
            "failure": {"failing_gates": ["auth_gate"]},
            "codebook_store": MockCodebookStore(),
        }
        budget = Budgets()
        
        result = repair_propose(context, budget, None)
        
        assert len(result) >= 1
        candidate = result[0]
        assert candidate.payload["target_gate"] == "auth_gate"
    
    def test_multiple_failing_gates(self):
        """Multiple failing gates produce multiple candidates."""
        context = {
            "failure": {"failing_gates": ["gate_A", "gate_B"]},
            "codebook_store": MockCodebookStore(),
        }
        budget = Budgets(max_candidates=10)
        
        result = repair_propose(context, budget, None)
        
        # Should have candidates for each gate
        assert len(result) >= 2
        
        target_gates = [c.payload["target_gate"] for c in result]
        assert "gate_A" in target_gates
        assert "gate_B" in target_gates
    
    def test_candidate_hash_deterministic(self):
        """Candidate hash is deterministic."""
        context = {
            "failure": {"failing_gates": ["test_gate"]},
            "codebook_store": MockCodebookStore(),
        }
        budget = Budgets()
        
        result1 = repair_propose(context, budget, None)
        result2 = repair_propose(context, budget, None)
        
        assert len(result1) == len(result2) == 1
        assert result1[0].candidate_hash == result2[0].candidate_hash
    
    def test_budget_limits_candidates(self):
        """Budget max_candidates limits output."""
        context = {
            "failure": {"failing_gates": ["gate1", "gate2", "gate3"]},
            "codebook_store": MockCodebookStore(),
        }
        budget = Budgets(max_candidates=2)
        
        result = repair_propose(context, budget, None)
        
        assert len(result) <= budget.max_candidates


class MockCodebookStore:
    """Mock codebook store for testing."""
    
    def get_repair_actions(self, domain, gate_type):
        return [{
            "type": "parameter_adjustment",
            "description": f"Repair for {gate_type}",
            "parameters": {"param": "value"},
            "rationale": "Test repair",
            "preconditions": [],
            "safety_level": "medium",
            "impact": "medium",
        }]


class TestRepairScoring:
    """Tests for repair scoring."""
    
    def test_safety_level_affects_risk(self):
        """High safety level reduces risk score."""
        action_high = {"safety_level": "high", "impact": "low"}
        action_low = {"safety_level": "low", "impact": "high"}
        
        base = Scores(risk=0.5, utility=0.5, cost=0.5, confidence=0.5)
        
        score_high = _score_repair(action_high, base, None)
        score_low = _score_repair(action_low, base, None)
        
        assert score_high.risk < score_low.risk
        assert score_high.confidence > score_low.confidence
    
    def test_impact_affects_utility_cost(self):
        """Impact level affects utility and cost scores."""
        action_low = {"safety_level": "medium", "impact": "low"}
        action_high = {"safety_level": "medium", "impact": "high"}
        
        base = Scores(risk=0.5, utility=0.5, cost=0.5, confidence=0.5)
        
        score_low = _score_repair(action_low, base, None)
        score_high = _score_repair(action_high, base, None)
        
        assert score_low.utility < score_high.utility
        assert score_low.cost < score_high.cost


class TestAtomicSafetyProposer:
    """Tests for atomic safety proposer."""
    
    def test_no_codebook_returns_empty(self):
        """No codebook store returns empty list."""
        from npe.proposers.gr.rule_atomic_safety import propose as safety_propose
        
        context = {"context": {"risk_posture": "conservative"}}
        budget = Budgets()
        
        result = safety_propose(context, budget, None)
        
        assert result == []
    
    def test_solver_config_produced(self):
        """Solver config candidate is produced."""
        from npe.proposers.gr.rule_atomic_safety import propose as safety_propose
        
        class MockCodebookStore:
            def get_conservative_knobs(self, domain):
                return {"max_iterations": 100, "timeout_ms": 5000}
            
            def get_rules(self, domain):
                return []
        
        context = {
            "context": {"risk_posture": "conservative"},
            "codebook_store": MockCodebookStore(),
        }
        budget = Budgets()
        
        result = safety_propose(context, budget, None)
        
        # Should have solver config
        config_candidates = [c for c in result if c.candidate_type == "solver_config"]
        assert len(config_candidates) >= 1


class TestTemplatePlanLibrary:
    """Tests for template plan library proposer."""
    
    def test_no_goals_returns_empty(self):
        """No goals in context returns empty list."""
        from npe.proposers.gr.template_plan_library import propose as plan_propose
        
        context = {"goals": []}
        budget = Budgets()
        
        result = plan_propose(context, budget, None)
        
        assert result == []
    
    def test_no_codebook_returns_empty(self):
        """No codebook store returns empty list."""
        from npe.proposers.gr.template_plan_library import propose as plan_propose
        
        context = {"goals": [{"goal_type": "optimize"}]}
        budget = Budgets()
        
        result = plan_propose(context, budget, None)
        
        assert result == []
    
    def test_plan_candidate_structure(self):
        """Plan candidate has correct structure."""
        from npe.proposers.gr.template_plan_library import propose as plan_propose
        
        class MockCodebookStore:
            def get_plan_templates(self, goal_type):
                return [{
                    "template_id": "plan_001",
                    "type": "optimization",
                    "name": "Optimize Process",
                    "description": "Optimization plan",
                    "goal_type": "optimize",
                    "steps": [
                        {
                            "step_id": "step1",
                            "action": "analyze",
                            "description": "Analyze current state",
                            "parameters": {},
                        },
                    ],
                    "parameters": {},
                    "tags": ["optimization"],
                    "complexity": "low",
                }]
        
        context = {
            "goals": [{"goal_type": "optimize", "payload": {}}],
            "codebook_store": MockCodebookStore(),
        }
        budget = Budgets()
        
        result = plan_propose(context, budget, None)
        
        assert len(result) >= 1
        candidate = result[0]
        
        assert candidate.candidate_type == "plan"
        assert "steps" in candidate.payload
        assert len(candidate.payload["steps"]) >= 1


class TestExplainReceiptSummarizer:
    """Tests for receipt summarizer proposer."""
    
    def test_no_receipts_returns_empty(self):
        """No receipts store returns empty list."""
        from npe.proposers.gr.explain_receipt_summarizer import propose as explain_propose
        
        context = {"failure": {"failing_gates": []}}
        budget = Budgets()
        
        result = explain_propose(context, budget, None)
        
        assert result == []
    
    def test_explain_candidate_structure(self):
        """Explain candidate has correct structure."""
        from npe.proposers.gr.explain_receipt_summarizer import propose as explain_propose
        from npe.retrieval.receipts_store import ReceiptsStore, Receipt
        
        # Create mock receipts
        store = ReceiptsStore()
        store.receipts = [
            Receipt(
                receipt_id="receipt_001",
                gate_id="safety_gate",
                reason_code="THRESHOLD_EXCEEDED",
                outcome="fail",
                content={"reason_code": "THRESHOLD_EXCEEDED"},
                metadata={"source": "test.jsonl"},
            ),
        ]
        store.index_by_gate = {"safety_gate": [0]}
        store.index_by_reason = {"THRESHOLD_EXCEEDED": [0]}
        store.index_by_outcome = {"fail": [0]}
        
        context = {
            "failure": {"failing_gates": ["safety_gate"]},
            "receipts_store": store,
            "state_ref": {"state_hash": "abc"},
        }
        budget = Budgets()
        
        result = explain_propose(context, budget, None)
        
        assert len(result) >= 1
        candidate = result[0]
        
        assert candidate.candidate_type == "explain"
        assert "summary" in candidate.payload
        assert "failure_analysis" in candidate.payload


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
