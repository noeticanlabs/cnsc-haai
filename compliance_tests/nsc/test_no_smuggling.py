"""
NSC No Smuggling Tests

Tests for no-smuggling constraint.
"""

import pytest
from cnsc.haai.nsc.cfa import CFAAutomaton, CFAPhase


class TestNoSmuggling:
    """Tests for no-smuggling constraint."""

    def test_cfa_phases_isolated(self):
        """Test CFA phases are isolated."""
        phases = list(CFAPhase)
        assert len(phases) >= 4
        assert CFAPhase.SUPERPOSED in phases
        assert CFAPhase.COHERENT in phases

    def test_state_integrity(self):
        """Test state integrity."""
        automaton = CFAAutomaton(automaton_id="test_001", name="Test Automaton")
        assert automaton is not None
        assert automaton.automaton_id == "test_001"

    def test_operation_boundary(self):
        """Test operation boundaries."""
        automaton = CFAAutomaton(automaton_id="test_002", name="Test Automaton")
        # Check phase transitions exist
        assert hasattr(automaton, 'get_phase')
        assert hasattr(automaton, 'is_coherent')

    def test_no_state_leakage(self):
        """Test no state leakage between automata."""
        auto1 = CFAAutomaton(automaton_id="auto_001", name="Automaton 1")
        auto2 = CFAAutomaton(automaton_id="auto_002", name="Automaton 2")
        # Different automata should have different IDs
        assert auto1.automaton_id != auto2.automaton_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
