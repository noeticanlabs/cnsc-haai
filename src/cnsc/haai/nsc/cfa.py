"""
CFA (Control Flow Automaton)

Control Flow Automaton for phase enforcement in the Coherence Framework.

This module provides:
- CFAPhase: Enumeration of reasoning phases
- CFAState: Individual state node in the automaton
- CFATransition: Transition between states
- CFAAutomaton: Complete automaton with phase state machine
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, Tuple
from datetime import datetime, timedelta
from uuid import uuid4


class CFAPhase(Enum):
    """
    CFA Phases per spec.

    Phases represent distinct stages in reasoning with specific
    objectives and transition conditions.
    """

    SUPERPOSED = auto()  # Initial superposition of possibilities
    COHERENT = auto()  # Coherence check passed
    GATED = auto()  # Gate evaluation passed
    COLLAPSED = auto()  # Final collapsed state

    def to_string(self) -> str:
        """Convert to string representation."""
        return {
            CFAPhase.SUPERPOSED: "SUPERPOSED",
            CFAPhase.COHERENT: "COHERENT",
            CFAPhase.GATED: "GATED",
            CFAPhase.COLLAPSED: "COLLAPSED",
        }.get(self, "UNKNOWN")

    def can_transition_to(self, other: "CFAPhase") -> bool:
        """Check if transition to other phase is allowed."""
        allowed_transitions = {
            CFAPhase.SUPERPOSED: [CFAPhase.COHERENT, CFAPhase.SUPERPOSED],
            CFAPhase.COHERENT: [CFAPhase.GATED, CFAPhase.COHERENT, CFAPhase.SUPERPOSED],
            CFAPhase.GATED: [CFAPhase.COLLAPSED, CFAPhase.GATED, CFAPhase.COHERENT],
            CFAPhase.COLLAPSED: [CFAPhase.COLLAPSED],
        }
        return other in allowed_transitions.get(self, [])


@dataclass
class CFATransition:
    """
    CFA Transition.

    Represents a valid transition between states with conditions.
    """

    transition_id: str
    from_state: str
    to_state: str
    phase: CFAPhase
    condition: Optional[str] = None
    guard_check: Optional[Callable] = None
    rail_check: Optional[Callable] = None
    min_duration_ms: int = 0
    max_retries: int = 3
    retry_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "transition_id": self.transition_id,
            "from_state": self.from_state,
            "to_state": self.to_state,
            "phase": self.phase.to_string(),
            "condition": self.condition,
            "min_duration_ms": self.min_duration_ms,
            "max_retries": self.max_retries,
            "retry_count": self.retry_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CFATransition":
        """Create from dictionary."""
        return cls(
            transition_id=data["transition_id"],
            from_state=data["from_state"],
            to_state=data["to_state"],
            phase=(
                CFAPhase[data["phase"]]
                if isinstance(data["phase"], str)
                else CFAPhase(data["phase"])
            ),
            condition=data.get("condition"),
            min_duration_ms=data.get("min_duration_ms", 0),
            max_retries=data.get("max_retries", 3),
            retry_count=data.get("retry_count", 0),
        )


@dataclass
class CFAState:
    """
    CFA State.

    Individual state node in the automaton with phase information.
    """

    state_id: str
    name: str
    phase: CFAPhase
    is_entry: bool = False
    is_exit: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    # State validation
    coherence_requirement: float = 0.5
    gate_requirements: List[str] = field(default_factory=list)
    rail_constraints: List[str] = field(default_factory=list)

    # State metrics
    entry_count: int = 0
    total_duration_ms: int = 0
    last_entry_time: Optional[datetime] = None

    def enter(self) -> None:
        """Called when entering this state."""
        self.entry_count += 1
        self.last_entry_time = datetime.utcnow()

    def exit(self) -> timedelta:
        """Called when exiting this state. Returns duration."""
        if self.last_entry_time:
            duration = datetime.utcnow() - self.last_entry_time
            self.total_duration_ms += int(duration.total_seconds() * 1000)
            self.last_entry_time = None
            return duration
        return timedelta(0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "state_id": self.state_id,
            "name": self.name,
            "phase": self.phase.to_string(),
            "is_entry": self.is_entry,
            "is_exit": self.is_exit,
            "coherence_requirement": self.coherence_requirement,
            "gate_requirements": self.gate_requirements,
            "rail_constraints": self.rail_constraints,
            "entry_count": self.entry_count,
            "total_duration_ms": self.total_duration_ms,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CFAState":
        """Create from dictionary."""
        phase = data["phase"]
        if isinstance(phase, str):
            phase = CFAPhase[phase]
        else:
            phase = CFAPhase(phase)
        return cls(
            state_id=data["state_id"],
            name=data["name"],
            phase=phase,
            is_entry=data.get("is_entry", False),
            is_exit=data.get("is_exit", False),
            coherence_requirement=data.get("coherence_requirement", 0.5),
            gate_requirements=data.get("gate_requirements", []),
            rail_constraints=data.get("rail_constraints", []),
            entry_count=data.get("entry_count", 0),
            total_duration_ms=data.get("total_duration_ms", 0),
            metadata=data.get("metadata", {}),
        )


@dataclass
class CFAAutomaton:
    """
    CFA Automaton.

    Complete control flow automaton with states, transitions, and
    phase enforcement rules.
    """

    automaton_id: str
    name: str

    # States and transitions
    states: Dict[str, CFAState] = field(default_factory=dict)
    transitions: Dict[str, List[CFATransition]] = field(default_factory=dict)

    # Current state
    current_state: Optional[str] = None
    phase_history: List[Tuple[datetime, CFAPhase]] = field(default_factory=list)

    # Configuration
    default_phase: CFAPhase = CFAPhase.SUPERPOSED
    enforce_temporal_constraints: bool = True
    max_phase_duration_ms: Optional[int] = None

    # Callbacks
    on_enter_callbacks: Dict[str, List[Callable]] = field(default_factory=dict)
    on_exit_callbacks: Dict[str, List[Callable]] = field(default_factory=dict)
    on_transition_callbacks: List[Callable] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Initialize automaton with default states."""
        self._create_default_states()

    def _create_default_states(self) -> None:
        """Create default states for each phase."""
        if not self.states:
            # Create states for each phase
            phases = [
                (CFAPhase.SUPERPOSED, True, False),
                (CFAPhase.COHERENT, False, False),
                (CFAPhase.GATED, False, False),
                (CFAPhase.COLLAPSED, False, True),
            ]

            for phase, is_entry, is_exit in phases:
                state_id = str(uuid4())[:8]
                state = CFAState(
                    state_id=state_id,
                    name=f"STATE_{phase.to_string()}",
                    phase=phase,
                    is_entry=is_entry,
                    is_exit=is_exit,
                )
                self.add_state(state)

            # Set initial state
            for state_id, state in self.states.items():
                if state.is_entry:
                    self.current_state = state_id
                    break

    def add_state(self, state: CFAState) -> None:
        """Add state to automaton."""
        self.states[state.state_id] = state
        self.transitions[state.state_id] = []

    def add_transition(self, transition: CFATransition) -> None:
        """Add transition to automaton."""
        if transition.from_state not in self.transitions:
            self.transitions[transition.from_state] = []
        self.transitions[transition.from_state].append(transition)

    def get_state(self, state_id: str) -> Optional[CFAState]:
        """Get state by ID."""
        return self.states.get(state_id)

    def get_current_state(self) -> Optional[CFAState]:
        """Get current state."""
        if self.current_state:
            return self.states.get(self.current_state)
        return None

    def can_transition(self, from_state_id: str, to_state_id: str) -> bool:
        """Check if transition is valid."""
        from_state = self.states.get(from_state_id)
        to_state = self.states.get(to_state_id)

        if not from_state or not to_state:
            return False

        # Check phase transition rules
        if not from_state.phase.can_transition_to(to_state.phase):
            return False

        # Check if transition exists
        transitions = self.transitions.get(from_state_id, [])
        for t in transitions:
            if t.to_state == to_state_id:
                return True

        return False

    def transition_to(
        self,
        to_state_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Transition to a new state.

        Returns:
            Tuple of (success, error_message)
        """
        if not self.current_state:
            return False, "No current state"

        from_state = self.states.get(self.current_state)
        to_state = self.states.get(to_state_id)

        if not to_state:
            return False, f"State {to_state_id} not found"

        # Check phase transition rules
        if not from_state.phase.can_transition_to(to_state.phase):
            return (
                False,
                f"Invalid phase transition: {from_state.phase.to_string()} -> {to_state.phase.to_string()}",
            )

        # Check temporal constraints
        if self.enforce_temporal_constraints:
            if from_state.total_duration_ms < from_state.coherence_requirement * 1000:
                return False, "Coherence requirement not met"

        # Execute exit callbacks
        for callback in self.on_exit_callbacks.get(self.current_state, []):
            callback(context or {})

        # Execute transition callbacks
        for callback in self.on_transition_callbacks:
            callback(from_state, to_state, context or {})

        # Exit old state
        from_state.exit()

        # Enter new state
        to_state.enter()

        # Record phase history
        self.phase_history.append((datetime.utcnow(), to_state.phase))

        # Update current state
        self.current_state = to_state_id

        # Execute enter callbacks
        for callback in self.on_enter_callbacks.get(to_state_id, []):
            callback(context or {})

        return True, None

    def on_enter(self, state_id: str, callback: Callable) -> None:
        """Register enter callback for state."""
        if state_id not in self.on_enter_callbacks:
            self.on_enter_callbacks[state_id] = []
        self.on_enter_callbacks[state_id].append(callback)

    def on_exit(self, state_id: str, callback: Callable) -> None:
        """Register exit callback for state."""
        if state_id not in self.on_exit_callbacks:
            self.on_exit_callbacks[state_id] = []
        self.on_exit_callbacks[state_id].append(callback)

    def on_transition(self, callback: Callable) -> None:
        """Register transition callback."""
        self.on_transition_callbacks.append(callback)

    def get_phase(self) -> Optional[CFAPhase]:
        """Get current phase."""
        current = self.get_current_state()
        if current:
            return current.phase
        return None

    def is_coherent(self) -> bool:
        """Check if automaton is in coherent state."""
        phase = self.get_phase()
        # SUPERPOSED, COHERENT, GATED, and COLLAPSED are all coherent states
        return phase is not None

    def is_gated(self) -> bool:
        """Check if automaton has passed gate evaluation."""
        phase = self.get_phase()
        return phase in [CFAPhase.GATED, CFAPhase.COLLAPSED]

    def is_collapsed(self) -> bool:
        """Check if automaton is in collapsed state."""
        return self.get_phase() == CFAPhase.COLLAPSED

    def get_stats(self) -> Dict[str, Any]:
        """Get automaton statistics."""
        return {
            "automaton_id": self.automaton_id,
            "name": self.name,
            "current_phase": self.get_phase().to_string() if self.get_phase() else None,
            "state_count": len(self.states),
            "transition_count": sum(len(t) for t in self.transitions.values()),
            "phase_history_length": len(self.phase_history),
            "is_coherent": self.is_coherent(),
            "is_gated": self.is_gated(),
            "is_collapsed": self.is_collapsed(),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "automaton_id": self.automaton_id,
            "name": self.name,
            "states": {k: s.to_dict() for k, s in self.states.items()},
            "transitions": {k: [t.to_dict() for t in v] for k, v in self.transitions.items()},
            "current_state": self.current_state,
            "phase_history": [(t.isoformat(), p.to_string()) for t, p in self.phase_history],
            "default_phase": self.default_phase.to_string(),
            "enforce_temporal_constraints": self.enforce_temporal_constraints,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CFAAutomaton":
        """Create from dictionary."""
        automaton = cls(
            automaton_id=data["automaton_id"],
            name=data["name"],
            default_phase=(
                CFAPhase[data["default_phase"]]
                if isinstance(data["default_phase"], str)
                else CFAPhase(data["default_phase"])
            ),
            enforce_temporal_constraints=data.get("enforce_temporal_constraints", True),
        )

        automaton.states = {k: CFAState.from_dict(v) for k, v in data.get("states", {}).items()}
        automaton.transitions = {}
        for k, v in data.get("transitions", {}).items():
            automaton.transitions[k] = [CFATransition.from_dict(t) for t in v]
        automaton.current_state = data.get("current_state")
        automaton.phase_history = [
            (datetime.fromisoformat(t), CFAPhase[p]) for t, p in data.get("phase_history", [])
        ]

        return automaton


def create_cfa_automaton(name: str, automaton_id: Optional[str] = None) -> CFAAutomaton:
    """Create a new CFA automaton."""
    return CFAAutomaton(
        automaton_id=automaton_id or str(uuid4()),
        name=name,
    )
