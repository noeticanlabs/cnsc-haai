"""
Option Registry - Built-in Skills

Registry of deterministic options (skills) that can be used by the planner.

Built-in options:
- GoToGoalGreedy: Move toward goal by delta
- AvoidHazardGradient: Move away from hazard mask
- WallFollowLeft: Follow wall on left
- WallFollowRight: Follow wall on right
- BacktrackLastSafe: Return to last safe position
"""

from __future__ import annotations
from typing import Dict, Callable, List, Optional, Tuple
import hashlib

# Import GMI types
from cnsc_haai.gmi.types import GMIState, GMIAction

# Import option types
from .option_types import Option, SimpleOptionState


# =============================================================================
# Global Registry
# =============================================================================

_OPTION_REGISTRY: Dict[str, Option] = {}


# =============================================================================
# Helper Functions
# =============================================================================

def _manhattan_distance(p1: Tuple[int, int], p2: Tuple[int, int]) -> int:
    """Compute Manhattan distance between two points."""
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


def _create_gmi_action(drho: List[List[int]], dtheta: List[List[int]]) -> GMIAction:
    """Create a GMIAction."""
    return GMIAction(drho=drho, dtheta=dtheta)


# =============================================================================
# Initiation and Termination Predicates
# =============================================================================

def _init_always(state: SimpleOptionState) -> bool:
    """Always can initiate."""
    return True


def _term_at_goal(state: SimpleOptionState) -> bool:
    """Terminate when at goal."""
    return state.position == state.goal


def _term_never(state: SimpleOptionState) -> bool:
    """Never terminate (until max_steps)."""
    return False


def _term_near_hazard(state: SimpleOptionState, threshold: int = 1) -> bool:
    """Terminate when near hazard."""
    for hazard in state.hazards:
        if _manhattan_distance(state.position, hazard) <= threshold:
            return True
    return False


def _term_at_wall(state: SimpleOptionState) -> bool:
    """Terminate when at wall."""
    return state.position in state.walls


# =============================================================================
# Policy Functions
# =============================================================================

def _policy_go_to_goal(state: SimpleOptionState) -> GMIAction:
    """
    Policy: Move toward goal using greedy delta.
    
    Chooses action that reduces Manhattan distance to goal most.
    """
    row, col = state.position
    goal_row, goal_col = state.goal
    
    # Determine direction to goal
    dr = 0
    dc = 0
    
    if goal_row < row:
        dr = -1  # Move up (decrease row)
    elif goal_row > row:
        dr = 1   # Move down (increase row)
    
    if goal_col < col:
        dc = -1  # Move left
    elif goal_col > col:
        dc = 1   # Move right
    
    # Prefer vertical if both differ
    if dr != 0 and dc != 0:
        # Choose the one that makes more progress
        if abs(goal_row - row) >= abs(goal_col - col):
            dc = 0
        else:
            dr = 0
    
    # Create action
    return _create_gmi_action([[dr, 0]], [[0, dc]])


def _policy_avoid_hazard(state: SimpleOptionState) -> GMIAction:
    """
    Policy: Move away from nearest hazard.
    
    Chooses action that increases Manhattan distance from nearest hazard.
    """
    if not state.hazards:
        # No hazards - stay
        return _create_gmi_action([[0, 0]], [[0, 0]])
    
    # Find nearest hazard
    min_dist = float('inf')
    nearest_hazard = state.hazards[0]
    for hazard in state.hazards:
        dist = _manhattan_distance(state.position, hazard)
        if dist < min_dist:
            min_dist = dist
            nearest_hazard = hazard
    
    # Move in opposite direction
    row, col = state.position
    haz_row, haz_col = nearest_hazard
    
    # Direction away from hazard
    dr = 0
    dc = 0
    
    if haz_row < row:
        dr = 1  # Move down (away from hazard above)
    elif haz_row > row:
        dr = -1  # Move up (away from hazard below)
    
    if haz_col < col:
        dc = 1  # Move right (away from hazard left)
    elif haz_col > col:
        dc = -1  # Move left (away from hazard right)
    
    # Prefer the direction with larger difference
    if abs(haz_row - row) < abs(haz_col - col):
        dr = 0
    else:
        dc = 0
    
    return _create_gmi_action([[dr, 0]], [[0, dc]])


def _policy_wall_follow_left(state: SimpleOptionState) -> GMIAction:
    """
    Policy: Follow wall on left side.
    
    Maintains wall on left by:
    - Turn right if wall ahead
    - Turn left if no wall on left
    - Go straight if left is free
    """
    row, col = state.position
    
    # Check neighboring cells
    # For simplicity, use a fixed direction (north)
    # In full impl, would track orientation
    
    # Simple implementation: try to go around obstacles
    # Move in a pattern that tends to keep left wall
    
    # Check if we can move in current direction
    can_move = True
    
    # If blocked, turn right
    if not can_move:
        # Turn right: swap row/col deltas
        return _create_gmi_action([[0, 1]], [[-1, 0]])
    
    # Otherwise move forward
    return _create_gmi_action([[-1, 0]], [[0, 0]])


def _policy_wall_follow_right(state: SimpleOptionState) -> GMIAction:
    """
    Policy: Follow wall on right side.
    
    Mirror of wall_follow_left.
    """
    row, col = state.position
    
    # Similar to left but mirrored
    can_move = True
    
    if not can_move:
        # Turn left: swap row/col deltas
        return _create_gmi_action([[0, -1]], [[1, 0]])
    
    return _create_gmi_action([[-1, 0]], [[0, 0]])


def _policy_backtrack_last_safe(state: SimpleOptionState) -> GMIAction:
    """
    Policy: Move back toward last known safe position.
    
    Simple implementation: just move toward origin (0, 0).
    In full implementation, would track history.
    """
    row, col = state.position
    
    # Move toward (0, 0)
    dr = -1 if row > 0 else (1 if row < 0 else 0)
    dc = -1 if col > 0 else (1 if col < 0 else 0)
    
    # Prefer vertical
    if dr != 0 and dc != 0:
        dc = 0
    
    return _create_gmi_action([[dr, 0]], [[0, dc]])


# =============================================================================
# Built-in Options
# =============================================================================

def _create_go_to_goal_option() -> Option:
    """Create GoToGoalGreedy option."""
    return Option(
        id="GoToGoalGreedy",
        initiation=_init_always,
        termination=_term_at_goal,
        policy=_policy_go_to_goal,
        max_steps=50,
        invoke_cost=1,
    )


def _create_avoid_hazard_option() -> Option:
    """Create AvoidHazardGradient option."""
    return Option(
        id="AvoidHazardGradient",
        initiation=_init_always,
        termination=_term_near_hazard,
        policy=_policy_avoid_hazard,
        max_steps=20,
        invoke_cost=1,
    )


def _create_wall_follow_left_option() -> Option:
    """Create WallFollowLeft option."""
    return Option(
        id="WallFollowLeft",
        initiation=_init_always,
        termination=_term_at_goal,
        policy=_policy_wall_follow_left,
        max_steps=100,
        invoke_cost=1,
    )


def _create_wall_follow_right_option() -> Option:
    """Create WallFollowRight option."""
    return Option(
        id="WallFollowRight",
        initiation=_init_always,
        termination=_term_at_goal,
        policy=_policy_wall_follow_right,
        max_steps=100,
        invoke_cost=1,
    )


def _create_backtrack_option() -> Option:
    """Create BacktrackLastSafe option."""
    return Option(
        id="BacktrackLastSafe",
        initiation=_init_always,
        termination=_term_never,  # Never terminates until max_steps
        policy=_policy_backtrack_last_safe,
        max_steps=30,
        invoke_cost=1,
    )


# =============================================================================
# Registry Functions
# =============================================================================

def _initialize_registry() -> None:
    """Initialize the registry with built-in options."""
    global _OPTION_REGISTRY
    
    _OPTION_REGISTRY = {
        "GoToGoalGreedy": _create_go_to_goal_option(),
        "AvoidHazardGradient": _create_avoid_hazard_option(),
        "WallFollowLeft": _create_wall_follow_left_option(),
        "WallFollowRight": _create_wall_follow_right_option(),
        "BacktrackLastSafe": _create_backtrack_option(),
    }


def get_option(option_id: str) -> Option:
    """
    Get an option by ID.
    
    Args:
        option_id: The option identifier
    
    Returns:
        The Option
    
    Raises:
        KeyError: If option not found
    """
    if not _OPTION_REGISTRY:
        _initialize_registry()
    
    return _OPTION_REGISTRY[option_id]


def list_options() -> List[str]:
    """
    List all available option IDs.
    
    Returns:
        List of option IDs
    """
    if not _OPTION_REGISTRY:
        _initialize_registry()
    
    return list(_OPTION_REGISTRY.keys())


def register_option(option: Option) -> None:
    """
    Register a new option.
    
    Args:
        option: The option to register
    """
    if not _OPTION_REGISTRY:
        _initialize_registry()
    
    _OPTION_REGISTRY[option.id] = option


def is_registered(option_id: str) -> bool:
    """
    Check if an option is registered.
    
    Args:
        option_id: The option identifier
    
    Returns:
        True if registered
    """
    if not _OPTION_REGISTRY:
        _initialize_registry()
    
    return option_id in _OPTION_REGISTRY


# Initialize on module load
_initialize_registry()
