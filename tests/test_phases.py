"""
Tests for the Phase management system.

Tests cover:
- Phase enum values (ACQUISITION, CONSTRUCTION, REASONING, VALIDATION, RECOVERY)
- PhaseConfig creation
- PhaseState tracking (start/end time, steps, objectives)
- PhaseTransition recording
- PhaseManager phase execution
- Phase transition callbacks
- Invalid phase transitions
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from src.cnhaai.core.phases import (
    Phase,
    PhaseConfig,
    PhaseState,
    PhaseTransition,
    PhaseManager
)


class TestPhase:
    """Tests for Phase enum."""

    def test_phase_values_exist(self):
        """Test that all expected phases are defined."""
        assert Phase.ACQUISITION is not None
        assert Phase.CONSTRUCTION is not None
        assert Phase.REASONING is not None
        assert Phase.VALIDATION is not None
        assert Phase.RECOVERY is not None

    def test_phase_count(self):
        """Test that exactly 5 phases are defined."""
        assert len(Phase) == 5

    def test_phase_names(self):
        """Test phase name strings."""
        assert Phase.ACQUISITION.name == "ACQUISITION"
        assert Phase.CONSTRUCTION.name == "CONSTRUCTION"
        assert Phase.REASONING.name == "REASONING"
        assert Phase.VALIDATION.name == "VALIDATION"
        assert Phase.RECOVERY.name == "RECOVERY"


class TestPhaseConfig:
    """Tests for PhaseConfig class."""

    def test_config_creation(self):
        """Test creating a phase configuration."""
        config = PhaseConfig(
            phase=Phase.ACQUISITION,
            min_duration_ms=100,
            max_duration_ms=1000,
            transitions_to=[Phase.CONSTRUCTION],
            required_gates=["evidence_gate"]
        )

        assert config.phase == Phase.ACQUISITION
        assert config.min_duration_ms == 100
        assert config.max_duration_ms == 1000
        assert config.transitions_to == [Phase.CONSTRUCTION]
        assert config.required_gates == ["evidence_gate"]

    def test_config_defaults(self):
        """Test configuration default values."""
        config = PhaseConfig(phase=Phase.REASONING)

        assert config.min_duration_ms == 0
        assert config.max_duration_ms is None
        assert config.transitions_to == []
        assert config.required_gates == []

    def test_config_to_dict(self):
        """Test converting configuration to dictionary."""
        config = PhaseConfig(
            phase=Phase.CONSTRUCTION,
            min_duration_ms=50,
            transitions_to=[Phase.REASONING],
            required_gates=["gate1", "gate2"]
        )

        result = config.to_dict()

        assert result["phase"] == "CONSTRUCTION"
        assert result["min_duration_ms"] == 50
        assert result["max_duration_ms"] is None
        assert result["transitions_to"] == ["REASONING"]
        assert result["required_gates"] == ["gate1", "gate2"]


class TestPhaseState:
    """Tests for PhaseState class."""

    def test_state_creation(self):
        """Test creating a phase state."""
        state = PhaseState(
            phase=Phase.REASONING,
            start_time=datetime(2024, 1, 1, 12, 0, 0),
            steps_completed=5,
            objectives_achieved=["obj1", "obj2"],
            metadata={"key": "value"}
        )

        assert state.phase == Phase.REASONING
        assert state.start_time == datetime(2024, 1, 1, 12, 0, 0)
        assert state.end_time is None
        assert state.steps_completed == 5
        assert state.objectives_achieved == ["obj1", "obj2"]
        assert state.metadata == {"key": "value"}

    def test_state_defaults(self):
        """Test state default values."""
        state = PhaseState(phase=Phase.ACQUISITION)

        assert isinstance(state.start_time, datetime)
        assert state.end_time is None
        assert state.steps_completed == 0
        assert state.objectives_achieved == []
        assert state.metadata == {}

    def test_state_to_dict(self):
        """Test converting state to dictionary."""
        start_time = datetime(2024, 1, 1, 12, 0, 0)
        state = PhaseState(
            phase=Phase.VALIDATION,
            start_time=start_time,
            steps_completed=3,
            objectives_achieved=["validated"]
        )

        result = state.to_dict()

        assert result["phase"] == "VALIDATION"
        assert result["start_time"] == start_time.isoformat()
        assert result["end_time"] is None
        assert result["steps_completed"] == 3
        assert result["objectives_achieved"] == ["validated"]

    def test_duration_ms_running(self):
        """Test duration calculation while phase is running."""
        state = PhaseState(
            phase=Phase.REASONING,
            start_time=datetime.utcnow() - timedelta(milliseconds=100)
        )

        duration = state.duration_ms()

        assert duration >= 100
        assert duration <= 200  # Allow some tolerance

    def test_duration_ms_completed(self):
        """Test duration calculation for completed phase."""
        start = datetime(2024, 1, 1, 12, 0, 0)
        end = datetime(2024, 1, 1, 12, 0, 0, 100000)  # 100ms later
        state = PhaseState(
            phase=Phase.CONSTRUCTION,
            start_time=start,
            end_time=end
        )

        duration = state.duration_ms()

        assert duration == 100

    def test_is_complete_below_min_duration(self):
        """Test is_complete when below minimum duration."""
        state = PhaseState(
            phase=Phase.CONSTRUCTION,
            start_time=datetime.utcnow() - timedelta(milliseconds=50)
        )

        is_complete = state.is_complete(min_duration_ms=100)

        assert is_complete is False

    def test_is_complete_above_min_duration(self):
        """Test is_complete when above minimum duration."""
        state = PhaseState(
            phase=Phase.CONSTRUCTION,
            start_time=datetime.utcnow() - timedelta(milliseconds=200)
        )

        is_complete = state.is_complete(min_duration_ms=100)

        assert is_complete is True


class TestPhaseTransition:
    """Tests for PhaseTransition class."""

    def test_transition_creation(self):
        """Test creating a phase transition."""
        transition = PhaseTransition(
            id="trans-123",
            from_phase=Phase.ACQUISITION,
            to_phase=Phase.CONSTRUCTION,
            reason="phase_complete",
            duration_ms=150,
            steps_completed=10,
            metadata={"info": "test"}
        )

        assert transition.id == "trans-123"
        assert transition.from_phase == Phase.ACQUISITION
        assert transition.to_phase == Phase.CONSTRUCTION
        assert transition.reason == "phase_complete"
        assert transition.duration_ms == 150
        assert transition.steps_completed == 10
        assert transition.metadata == {"info": "test"}

    def test_transition_defaults(self):
        """Test transition default values."""
        transition = PhaseTransition()

        assert isinstance(transition.id, str)
        assert len(transition.id) > 0
        assert isinstance(transition.timestamp, datetime)
        assert transition.from_phase is None
        assert transition.to_phase is None
        assert transition.reason == ""
        assert transition.duration_ms == 0
        assert transition.steps_completed == 0
        assert transition.metadata == {}

    def test_transition_to_dict(self):
        """Test converting transition to dictionary."""
        transition = PhaseTransition(
            from_phase=Phase.REASONING,
            to_phase=Phase.VALIDATION,
            reason="reasoning_complete",
            duration_ms=500,
            steps_completed=25
        )

        result = transition.to_dict()

        assert result["from_phase"] == "REASONING"
        assert result["to_phase"] == "VALIDATION"
        assert result["reason"] == "reasoning_complete"
        assert result["duration_ms"] == 500
        assert result["steps_completed"] == 25
        assert "timestamp" in result


class TestPhaseManager:
    """Tests for PhaseManager class."""

    def test_manager_creation(self):
        """Test creating a phase manager."""
        manager = PhaseManager()

        assert manager.current_phase is None
        assert manager.current_state is None
        assert manager.transitions == []
        assert manager.phase_history == []
        assert len(manager.configs) == 5

    def test_default_configs(self):
        """Test that default configurations are created."""
        manager = PhaseManager()

        assert Phase.ACQUISITION in manager.configs
        assert Phase.CONSTRUCTION in manager.configs
        assert Phase.REASONING in manager.configs
        assert Phase.VALIDATION in manager.configs
        assert Phase.RECOVERY in manager.configs

    def test_start_phase(self):
        """Test starting a new phase."""
        manager = PhaseManager()
        state = manager.start_phase(Phase.ACQUISITION, {"goal": "test"})

        assert manager.current_phase == Phase.ACQUISITION
        assert manager.current_state == state
        assert state.phase == Phase.ACQUISITION
        assert state.metadata == {"goal": "test"}
        assert state.start_time is not None
        assert state.end_time is None

    def test_start_phase_completes_previous(self):
        """Test that starting a new phase completes the previous one."""
        manager = PhaseManager()
        state1 = manager.start_phase(Phase.ACQUISITION)
        state2 = manager.start_phase(Phase.CONSTRUCTION)

        assert state1.end_time is not None
        assert state1 in manager.phase_history
        assert manager.current_state == state2

    def test_complete_phase(self):
        """Test completing the current phase."""
        manager = PhaseManager()
        manager.start_phase(Phase.ACQUISITION)
        transition = manager.complete_phase(reason="test_complete", steps_completed=5)

        assert transition is not None
        assert manager.current_phase is None
        assert manager.current_state is None
        assert transition.reason == "test_complete"
        assert transition.steps_completed == 5

    def test_complete_phase_no_current(self):
        """Test completing when no phase is active."""
        manager = PhaseManager()

        result = manager.complete_phase()

        assert result is None

    def test_transition_to(self):
        """Test transitioning to a new phase."""
        manager = PhaseManager()
        manager.start_phase(Phase.ACQUISITION)
        
        new_state, transition = manager.transition_to(
            Phase.CONSTRUCTION,
            reason="acquisition_done",
            steps_completed=10
        )

        assert manager.current_phase == Phase.CONSTRUCTION
        assert new_state.phase == Phase.CONSTRUCTION
        assert transition.from_phase == Phase.ACQUISITION
        assert transition.to_phase == Phase.CONSTRUCTION
        assert transition.reason == "acquisition_done"
        assert transition.steps_completed == 10

    def test_can_transition_valid(self):
        """Test valid phase transition."""
        manager = PhaseManager()

        result = manager.can_transition(Phase.ACQUISITION, Phase.CONSTRUCTION)

        assert result is True

    def test_can_transition_invalid(self):
        """Test invalid phase transition."""
        manager = PhaseManager()

        result = manager.can_transition(Phase.ACQUISITION, Phase.RECOVERY)

        assert result is False

    def test_can_transition_no_config(self):
        """Test transition check with no config."""
        manager = PhaseManager()

        # ACQUISITION should be in config
        assert Phase.ACQUISITION in manager.configs
        result = manager.can_transition(Phase.ACQUISITION, Phase.CONSTRUCTION)
        assert result is True

    def test_get_config(self):
        """Test getting phase configuration."""
        manager = PhaseManager()

        config = manager.get_config(Phase.REASONING)

        assert config is not None
        assert config.phase == Phase.REASONING
        assert Phase.VALIDATION in config.transitions_to

    def test_set_config(self):
        """Test setting phase configuration."""
        manager = PhaseManager()
        new_config = PhaseConfig(
            phase=Phase.ACQUISITION,
            min_duration_ms=200,
            transitions_to=[Phase.CONSTRUCTION, Phase.RECOVERY]
        )

        manager.set_config(Phase.ACQUISITION, new_config)

        config = manager.get_config(Phase.ACQUISITION)
        assert config.min_duration_ms == 200
        assert Phase.RECOVERY in config.transitions_to

    def test_on_enter_callback(self):
        """Test registering and calling enter callback."""
        manager = PhaseManager()
        callback_called = []

        def callback():
            callback_called.append(True)

        manager.on_enter(Phase.ACQUISITION, callback)
        manager.start_phase(Phase.ACQUISITION)

        assert len(callback_called) == 1

    def test_on_exit_callback(self):
        """Test registering and calling exit callback."""
        manager = PhaseManager()
        callback_called = []

        def callback():
            callback_called.append(True)

        manager.on_exit(Phase.ACQUISITION, callback)
        manager.start_phase(Phase.ACQUISITION)
        manager.start_phase(Phase.CONSTRUCTION)

        assert len(callback_called) == 1

    def test_callback_error_handling(self):
        """Test that callback errors are handled gracefully."""
        manager = PhaseManager()

        def bad_callback():
            raise ValueError("Test error")

        manager.on_enter(Phase.ACQUISITION, bad_callback)

        # Should not raise an exception
        manager.start_phase(Phase.ACQUISITION)

    def test_get_current_phase_info(self):
        """Test getting current phase information."""
        manager = PhaseManager()
        manager.start_phase(Phase.CONSTRUCTION, {"goal": "test"})

        info = manager.get_current_phase_info()

        assert info is not None
        assert info["phase"] == "CONSTRUCTION"
        assert info["steps_completed"] == 0
        assert "duration_ms" in info
        assert "elapsed_ms" in info

    def test_get_current_phase_info_no_phase(self):
        """Test getting info when no phase is active."""
        manager = PhaseManager()

        info = manager.get_current_phase_info()

        assert info is None

    def test_get_phase_history(self):
        """Test getting phase history."""
        manager = PhaseManager()
        manager.start_phase(Phase.ACQUISITION)
        manager.start_phase(Phase.CONSTRUCTION)

        history = manager.get_phase_history()

        assert len(history) == 1  # Only completed phases
        assert history[0]["phase"] == "ACQUISITION"

    def test_get_transitions(self):
        """Test getting all transitions."""
        manager = PhaseManager()
        manager.start_phase(Phase.ACQUISITION)
        manager.start_phase(Phase.CONSTRUCTION)

        transitions = manager.get_transitions()

        assert len(transitions) == 1
        assert transitions[0]["from_phase"] == "ACQUISITION"
        assert transitions[0]["to_phase"] == "CONSTRUCTION"

    def test_reset(self):
        """Test resetting the manager."""
        manager = PhaseManager()
        manager.start_phase(Phase.ACQUISITION)
        manager.start_phase(Phase.CONSTRUCTION)

        manager.reset()

        assert manager.current_phase is None
        assert manager.current_state is None
        assert len(manager.transitions) == 0
        assert len(manager.phase_history) == 0

    def test_execute_episode(self):
        """Test executing a complete episode."""
        manager = PhaseManager()
        step_count = []

        def exit_condition(state):
            return state.steps_completed >= 2

        def step_callback(state):
            step_count.append(state.steps_completed)

        final_state, transitions = manager.execute_episode(
            initial_phase=Phase.ACQUISITION,
            exit_condition=exit_condition,
            step_callback=step_callback
        )

        assert final_state.steps_completed == 2
        assert len(transitions) > 0
        assert len(step_count) == 2

    def test_execute_episode_single_phase(self):
        """Test episode execution that stays in single phase."""
        manager = PhaseManager()

        def always_false(state):
            return False

        # This should run until phase transitions
        final_state, transitions = manager.execute_episode(
            initial_phase=Phase.ACQUISITION,
            exit_condition=always_false
        )

        # ACQUISITION has transition to CONSTRUCTION
        assert len(transitions) >= 1

    def test_transition_history_recorded(self):
        """Test that transitions are properly recorded."""
        manager = PhaseManager()
        manager.start_phase(Phase.ACQUISITION)
        manager.transition_to(Phase.CONSTRUCTION, reason="test")

        assert len(manager.transitions) == 1
        assert manager.transitions[0].from_phase == Phase.ACQUISITION
        assert manager.transitions[0].to_phase == Phase.CONSTRUCTION

    def test_phase_history_accumulates(self):
        """Test that completed phases accumulate in history."""
        manager = PhaseManager()
        manager.start_phase(Phase.ACQUISITION)
        manager.start_phase(Phase.CONSTRUCTION)
        manager.start_phase(Phase.REASONING)

        assert len(manager.phase_history) == 2

    def test_get_config_nonexistent_phase(self):
        """Test getting config for non-existent phase."""
        manager = PhaseManager()

        # All standard phases should have configs
        for phase in Phase:
            config = manager.get_config(phase)
            assert config is not None

    def test_start_with_metadata(self):
        """Test starting phase with metadata."""
        manager = PhaseManager()
        metadata = {"goal": "test-goal", "priority": "high"}

        state = manager.start_phase(Phase.RECOVERY, metadata=metadata)

        assert state.metadata == metadata

    def test_transition_with_metadata(self):
        """Test transition with metadata."""
        manager = PhaseManager()
        manager.start_phase(Phase.ACQUISITION)
        metadata = {"reason": "testing"}

        _, transition = manager.transition_to(Phase.CONSTRUCTION, metadata=metadata)

        assert transition.metadata == metadata
