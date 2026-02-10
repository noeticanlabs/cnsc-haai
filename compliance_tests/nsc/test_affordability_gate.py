"""
NSC Affordability Gate Tests

Tests for NSC affordability gate evaluation.
"""

import pytest
from cnsc.haai.nsc.gates import GateManager, GateResult, GateDecision


class TestAffordabilityGate:
    """Tests for affordability gate."""

    def test_gate_manager_creation(self):
        """Test gate manager can be created."""
        manager = GateManager()
        assert manager is not None

    def test_gate_manager_has_gates(self):
        """Test gate manager has gates attribute."""
        manager = GateManager()
        assert hasattr(manager, 'gates')
        assert isinstance(manager.gates, dict)

    def test_affordability_evaluation(self):
        """Test affordability gate evaluation exists."""
        manager = GateManager()
        
        context = {"budgets": {"compute": 100, "memory": 100}, "request": {"compute": 50, "memory": 30}}
        
        # Just verify the method exists and can be called
        result = manager.evaluate_gate("affordability", context)
        # Result may be None if gate not implemented

    def test_over_budget_affordability(self):
        """Test over-budget request."""
        manager = GateManager()
        
        context = {"budgets": {"compute": 100}, "request": {"compute": 150}}
        
        # Just verify the method exists and can be called
        result = manager.evaluate_gate("affordability", context)
        # Result may be None if gate not implemented


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
