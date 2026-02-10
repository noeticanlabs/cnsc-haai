"""
NSC Replay Audit Tests

Tests for NSC replay audit functionality.
"""

import pytest
from cnsc.haai.gml.replay import ReplayEngine, Verifier, ReplayStatus


class TestReplayAudit:
    """Tests for replay audit functionality."""

    def test_replay_engine_creation(self):
        """Test replay engine creation."""
        engine = ReplayEngine()
        assert engine is not None

    def test_replay_status_constants(self):
        """Test replay status constants."""
        assert ReplayStatus.PENDING is not None
        assert ReplayStatus.IN_PROGRESS is not None
        assert ReplayStatus.COMPLETED is not None
        assert ReplayStatus.FAILED is not None

    def test_verifier_creation(self):
        """Test verifier creation."""
        verifier = Verifier()
        assert verifier is not None

    def test_create_replay_engine(self):
        """Test create_replay_engine function."""
        from cnsc.haai.gml.replay import create_replay_engine
        engine = create_replay_engine()
        assert engine is not None

    def test_create_verifier(self):
        """Test create_verifier function."""
        from cnsc.haai.gml.replay import create_verifier
        verifier = create_verifier()
        assert verifier is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
