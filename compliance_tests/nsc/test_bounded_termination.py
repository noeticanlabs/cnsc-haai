"""
NSC Bounded Termination Tests

Tests for NSC bounded termination guarantees.
"""

import pytest
from cnsc.haai.nsc.cfa import CFAPhase


class TestBoundedTermination:
    """Tests for bounded termination guarantees."""

    def test_cfa_phases(self):
        """Test CFA phases are defined."""
        assert CFAPhase.SUPERPOSED is not None
        assert CFAPhase.COHERENT is not None
        assert CFAPhase.GATED is not None
        assert CFAPhase.COLLAPSED is not None

    def test_phase_transition_allowed(self):
        """Test phase transition rules."""
        assert CFAPhase.SUPERPOSED.can_transition_to(CFAPhase.COHERENT) is True
        assert CFAPhase.COHERENT.can_transition_to(CFAPhase.GATED) is True
        assert CFAPhase.GATED.can_transition_to(CFAPhase.COLLAPSED) is True

    def test_invalid_transition(self):
        """Test invalid transitions are rejected."""
        # Cannot go from COLLAPSED back to SUPERPOSED
        assert CFAPhase.COLLAPSED.can_transition_to(CFAPhase.SUPERPOSED) is False

    def test_phase_to_string(self):
        """Test phase string representation."""
        assert CFAPhase.SUPERPOSED.to_string() == "SUPERPOSED"
        assert CFAPhase.COHERENT.to_string() == "COHERENT"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
