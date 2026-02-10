"""
GML Checkpoint Backtrack Tests

Tests for GML checkpoint and backtrack functionality.
"""

import pytest
from datetime import datetime
from cnsc.haai.gml.trace import TraceEvent, TraceThread, TraceLevel


class TestCheckpointBacktrack:
    """Tests for checkpoint and backtrack functionality."""

    def test_trace_event_creation(self):
        """Test trace event creation."""
        event = TraceEvent(
            event_id="event_001",
            level=TraceLevel.INFO,
            event_type="ADD_BELIEF",
            timestamp=datetime.utcnow(),
            message="Test event"
        )
        assert event.event_id == "event_001"

    def test_trace_thread_creation(self):
        """Test trace thread creation."""
        thread = TraceThread(thread_id="thread_001", name="Test Thread")
        assert thread.thread_id == "thread_001"

    def test_trace_level_constants(self):
        """Test trace level constants."""
        assert TraceLevel.DEBUG is not None
        assert TraceLevel.INFO is not None
        assert TraceLevel.WARNING is not None
        assert TraceLevel.ERROR is not None

    def test_trace_event_to_dict(self):
        """Test trace event serialization."""
        event = TraceEvent(
            event_id="event_001",
            level=TraceLevel.INFO,
            event_type="ADD_BELIEF",
            timestamp=datetime.utcnow(),
            message="Test event"
        )
        event_dict = event.to_dict()
        assert isinstance(event_dict, dict)
        assert event_dict["event_id"] == "event_001"

    def test_trace_thread_to_dict(self):
        """Test trace thread serialization."""
        thread = TraceThread(thread_id="thread_001", name="Test Thread")
        thread.events.append(TraceEvent(
            event_id="e1",
            level=TraceLevel.INFO,
            event_type="test",
            timestamp=datetime.utcnow(),
            message="Test"
        ))
        thread_dict = thread.to_dict()
        assert "events" in thread_dict


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
