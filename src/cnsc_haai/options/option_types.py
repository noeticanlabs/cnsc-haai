"""
Option Types - Skill/Option Definitions

Defines the Option dataclass with:
- id: Unique identifier
- initiation predicate I(s): When option can start
- termination predicate beta(s): When option ends
- internal policy pi_omega(s): Action selection
- max_steps: Maximum steps before termination
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Optional, Tuple, List
import hashlib


# =============================================================================
# Option Definition
# =============================================================================

@dataclass(frozen=True)
class Option:
    """
    An option is a macro-action that unfolds into primitive actions.
    
    Frozen for receipt compatibility.
    """
    id: str
    initiation: Callable[["OptionState"], bool]  # I(s)
    termination: Callable[["OptionState"], bool]  # beta(s)
    policy: Callable[["OptionState"], "GMIAction"]  # pi_omega(s)
    max_steps: int
    invoke_cost: int = 1  # Fixed cost to invoke option
    
    def __post_init__(self):
        """Validate option."""
        if self.max_steps <= 0:
            raise ValueError(f"max_steps must be positive, got {self.max_steps}")
        if not self.id:
            raise ValueError("Option id cannot be empty")
    
    def hash(self) -> str:
        """Compute deterministic hash of option."""
        config_str = f"{self.id}:{self.max_steps}:{self.invoke_cost}"
        return hashlib.sha256(config_str.encode()).hexdigest()[:16]


# =============================================================================
# Option State (for execution)
# =============================================================================

@dataclass
class OptionState:
    """
    State maintained during option execution.
    """
    option_id: str
    start_step: int
    current_step: int
    start_state_hash: str
    last_action: Optional["GMIAction"] = None
    last_state_hash: Optional[str] = None
    
    @property
    def steps_taken(self) -> int:
        """Number of steps executed so far."""
        return self.current_step - self.start_step
    
    @property
    def is_active(self) -> bool:
        """Whether option is still running."""
        return self.last_action is not None and self.steps_taken < self.max_steps


# =============================================================================
# Option Execution Result
# =============================================================================

from enum import Enum


class ExecutionStatus(Enum):
    """Status of option execution."""
    RUNNING = "RUNNING"
    TERMINATED = "TERMINATED"
    MAX_STEPS = "MAX_STEPS"
    TERMINATION_PREDICATE = "TERMINATION_PREDICATE"
    FAILED = "FAILED"


@dataclass
class OptionExecution:
    """
    Result of executing an option.
    """
    status: ExecutionStatus
    option_id: str
    actions: List["GMIAction"]  # All actions executed
    final_state_hash: str
    termination_reason: str
    steps_executed: int
    
    def __post_init__(self):
        """Validate execution."""
        if self.steps_executed < 0:
            raise ValueError(f"steps_executed must be non-negative")


# =============================================================================
# Simple Option State (for predicates)
# =============================================================================

@dataclass(frozen=True)
class SimpleOptionState:
    """
    Simplified state for option predicates (position, goal, etc).
    """
    position: Tuple[int, int]  # (row, col)
    goal: Tuple[int, int]       # (row, col)
    hazards: Tuple[Tuple[int, int], ...]  # Hazard positions
    walls: Tuple[Tuple[int, int], ...]    # Wall positions
    budget: int
    
    @staticmethod
    def from_gmi_state(state, goal: Tuple[int, int], 
                       hazards: List[Tuple[int, int]] = None,
                       walls: List[Tuple[int, int]] = None) -> "SimpleOptionState":
        """Create from GMI state."""
        # Extract position from state
        row = state.theta[0][0] if state.theta and state.theta[0] else 0
        col = state.theta[0][1] if state.theta and state.theta[0] and len(state.theta[0]) > 1 else 0
        
        return SimpleOptionState(
            position=(row, col),
            goal=goal,
            hazards=tuple(hazards) if hazards else (),
            walls=tuple(walls) if walls else (),
            budget=state.b,
        )


# =============================================================================
# Placeholder for GMIAction import (avoid circular imports)
# =============================================================================

# This will be imported dynamically to avoid circular imports
GMIAction = None


def _set_gmi_action_type(action_type):
    """Set the GMIAction type (called at module initialization)."""
    global GMIAction
    GMIAction = action_type
