"""
Phase Management for CNHAAI

This module provides phase management infrastructure:
- Phase: Enum for reasoning phases
- PhaseManager: Executes and transitions between phases
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from uuid import uuid4


class Phase(Enum):
    """
    Phases of CNHAAI reasoning.

    Each phase represents a distinct stage in the reasoning process
    with specific objectives and transition conditions.
    """

    ACQUISITION = auto()  # Gather evidence
    CONSTRUCTION = auto()  # Build abstractions
    REASONING = auto()  # Use abstractions for inference
    VALIDATION = auto()  # Verify results
    RECOVERY = auto()  # Repair degradation


@dataclass
class PhaseConfig:
    """Configuration for a phase."""

    phase: Phase
    min_duration_ms: int = 0
    max_duration_ms: Optional[int] = None
    transitions_to: List[Phase] = field(default_factory=list)
    required_gates: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "phase": self.phase.name,
            "min_duration_ms": self.min_duration_ms,
            "max_duration_ms": self.max_duration_ms,
            "transitions_to": [p.name for p in self.transitions_to],
            "required_gates": self.required_gates,
        }


@dataclass
class PhaseState:
    """Current state of a phase."""

    phase: Phase
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    steps_completed: int = 0
    objectives_achieved: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "phase": self.phase.name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "steps_completed": self.steps_completed,
            "objectives_achieved": self.objectives_achieved,
            "metadata": self.metadata,
        }

    def duration_ms(self) -> int:
        """Get duration in milliseconds."""
        end = self.end_time or datetime.utcnow()
        return int((end - self.start_time).total_seconds() * 1000)

    def is_complete(self, min_duration_ms: int = 0) -> bool:
        """Check if phase duration requirements are met."""
        return self.duration_ms() >= min_duration_ms


@dataclass
class PhaseTransition:
    """Record of a phase transition."""

    id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    from_phase: Optional[Phase] = None
    to_phase: Optional[Phase] = None
    reason: str = ""
    duration_ms: int = 0
    steps_completed: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "from_phase": self.from_phase.name if self.from_phase else None,
            "to_phase": self.to_phase.name if self.to_phase else None,
            "reason": self.reason,
            "duration_ms": self.duration_ms,
            "steps_completed": self.steps_completed,
            "metadata": self.metadata,
        }


class PhaseManager:
    """
    Manages phase execution and transitions.

    The phase manager coordinates the reasoning lifecycle,
    ensuring proper transitions and phase completion criteria.
    """

    def __init__(self):
        """Initialize the phase manager."""
        self.current_phase: Optional[Phase] = None
        self.current_state: Optional[PhaseState] = None
        self.transitions: List[PhaseTransition] = []
        self.phase_history: List[PhaseState] = []

        # Default phase configurations
        self.configs: Dict[Phase, PhaseConfig] = self._create_default_configs()

        # Phase callbacks
        self.on_enter_callbacks: Dict[Phase, List[Callable]] = {}
        self.on_exit_callbacks: Dict[Phase, List[Callable]] = {}

    def _create_default_configs(self) -> Dict[Phase, PhaseConfig]:
        """Create default phase configurations."""
        return {
            Phase.ACQUISITION: PhaseConfig(
                phase=Phase.ACQUISITION, min_duration_ms=0, transitions_to=[Phase.CONSTRUCTION]
            ),
            Phase.CONSTRUCTION: PhaseConfig(
                phase=Phase.CONSTRUCTION, min_duration_ms=100, transitions_to=[Phase.REASONING]
            ),
            Phase.REASONING: PhaseConfig(
                phase=Phase.REASONING,
                min_duration_ms=0,
                max_duration_ms=3600000,  # 1 hour
                transitions_to=[Phase.VALIDATION, Phase.RECOVERY],
            ),
            Phase.VALIDATION: PhaseConfig(
                phase=Phase.VALIDATION,
                min_duration_ms=50,
                transitions_to=[Phase.REASONING, Phase.RECOVERY],
            ),
            Phase.RECOVERY: PhaseConfig(
                phase=Phase.RECOVERY, min_duration_ms=0, transitions_to=[Phase.CONSTRUCTION]
            ),
        }

    def start_phase(
        self, phase: Phase, metadata: Optional[Dict[str, Any]] = None, steps_completed: int = 0
    ) -> PhaseState:
        """
        Start a new phase.

        Args:
            phase: The phase to start
            metadata: Optional metadata for the phase
            steps_completed: Steps completed from previous phase (for transition continuity)

        Returns:
            The new phase state
        """
        # Complete current phase if exists
        if self.current_state is not None:
            self.current_state.end_time = datetime.utcnow()
            self.phase_history.append(self.current_state)
            # Call exit callbacks for current phase
            self._call_callbacks(self.on_exit_callbacks.get(self.current_state.phase, []))
            # Create a transition record for implicit phase change
            transition = PhaseTransition(
                from_phase=self.current_state.phase,
                to_phase=phase,
                reason="phase_started",
                duration_ms=self.current_state.duration_ms(),
                steps_completed=self.current_state.steps_completed,
                metadata=metadata or {},
            )
            self.transitions.append(transition)

        # Create new state
        self.current_phase = phase
        self.current_state = PhaseState(
            phase=phase,
            start_time=datetime.utcnow(),
            steps_completed=steps_completed,
            metadata=metadata or {},
        )

        # Call enter callbacks
        self._call_callbacks(self.on_enter_callbacks.get(phase, []))

        return self.current_state

    def complete_phase(
        self, reason: str = "objectives_achieved", steps_completed: int = 0
    ) -> Optional[PhaseTransition]:
        """
        Complete the current phase and transition.

        Args:
            reason: Reason for completion
            steps_completed: Number of steps completed in phase

        Returns:
            PhaseTransition if successful, None if no current phase
        """
        if self.current_state is None:
            return None

        # Record transition
        transition = PhaseTransition(
            from_phase=self.current_state.phase,
            to_phase=None,  # Will be set by next phase
            reason=reason,
            duration_ms=self.current_state.duration_ms(),
            steps_completed=steps_completed,
        )

        # End current state
        self.current_state.end_time = datetime.utcnow()
        self.phase_history.append(self.current_state)

        self.transitions.append(transition)
        self.current_state = None
        self.current_phase = None

        return transition

    def transition_to(
        self,
        phase: Phase,
        reason: str = "",
        steps_completed: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[PhaseState, PhaseTransition]:
        """
        Transition to a new phase.

        Args:
            phase: Target phase
            reason: Reason for transition
            steps_completed: Steps completed in previous phase
            metadata: Optional metadata for new phase

        Returns:
            Tuple of (new phase state, transition record)
        """
        # Complete current phase
        transition = self.complete_phase(reason, steps_completed)

        # Start new phase, carrying over step count
        new_state = self.start_phase(phase, metadata, steps_completed=steps_completed)

        # Update transition with target phase
        if transition:
            transition.to_phase = phase
            transition.metadata = metadata or {}

        return new_state, transition

    def can_transition(self, from_phase: Phase, to_phase: Phase) -> bool:
        """
        Check if transition is allowed.

        Args:
            from_phase: Source phase
            to_phase: Target phase

        Returns:
            True if transition is allowed
        """
        config = self.configs.get(from_phase)
        if config is None:
            return False
        return to_phase in config.transitions_to

    def get_config(self, phase: Phase) -> Optional[PhaseConfig]:
        """Get configuration for a phase."""
        return self.configs.get(phase)

    def set_config(self, phase: Phase, config: PhaseConfig) -> None:
        """Set configuration for a phase."""
        self.configs[phase] = config

    def on_enter(self, phase: Phase, callback: Callable) -> None:
        """Register a callback for phase entry."""
        if phase not in self.on_enter_callbacks:
            self.on_enter_callbacks[phase] = []
        self.on_enter_callbacks[phase].append(callback)

    def on_exit(self, phase: Phase, callback: Callable) -> None:
        """Register a callback for phase exit."""
        if phase not in self.on_exit_callbacks:
            self.on_exit_callbacks[phase] = []
        self.on_exit_callbacks[phase].append(callback)

    def _call_callbacks(self, callbacks: List[Callable]) -> None:
        """Execute a list of callbacks."""
        for callback in callbacks:
            try:
                callback()
            except Exception:
                pass  # Swallow callback errors

    def get_current_phase_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the current phase."""
        if self.current_state is None:
            return None
        return {
            "phase": self.current_state.phase.name,
            "duration_ms": self.current_state.duration_ms(),
            "steps_completed": self.current_state.steps_completed,
            "elapsed_ms": (datetime.utcnow() - self.current_state.start_time).total_seconds()
            * 1000,
        }

    def get_phase_history(self) -> List[Dict[str, Any]]:
        """Get the phase history."""
        return [state.to_dict() for state in self.phase_history]

    def get_transitions(self) -> List[Dict[str, Any]]:
        """Get all phase transitions."""
        return [t.to_dict() for t in self.transitions]

    def reset(self) -> None:
        """Reset the phase manager to initial state."""
        self.current_phase = None
        self.current_state = None
        self.transitions.clear()
        self.phase_history.clear()

    def execute_episode(
        self,
        initial_phase: Phase,
        exit_condition: Callable[[PhaseState], bool],
        step_callback: Optional[Callable[[PhaseState], None]] = None,
    ) -> Tuple[PhaseState, List[PhaseTransition]]:
        """
        Execute a complete episode through phases.

        Args:
            initial_phase: Starting phase
            exit_condition: Function to check if episode should end
            step_callback: Optional callback after each step

        Returns:
            Tuple of (final state, list of transitions)
        """
        # Start initial phase
        state = self.start_phase(initial_phase)

        while not exit_condition(state):
            # Execute step in current phase
            state.steps_completed += 1
            if step_callback:
                step_callback(state)

            # Check if phase should transition
            config = self.configs.get(state.phase)
            if config and state.is_complete(config.min_duration_ms):
                # Try to transition to next phase
                if config.transitions_to:
                    next_phase = config.transitions_to[0]
                    state, _ = self.transition_to(
                        next_phase, reason="phase_complete", steps_completed=state.steps_completed
                    )
                else:
                    # No transitions defined, end episode
                    break

        # Complete final phase
        self.complete_phase(reason="episode_end", steps_completed=state.steps_completed)

        return state, self.transitions
