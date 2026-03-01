"""
Option Runtime - Execute Options

Executes options by unfolding them into primitive actions.
Tracks internal steps and handles termination conditions.
"""

from __future__ import annotations
from typing import List, Optional, Tuple
import hashlib

# Import GMI types
from cnsc_haai.gmi.types import GMIState, GMIAction

# Import option types
from .option_types import Option, OptionExecution, ExecutionStatus, OptionState, SimpleOptionState
from .option_registry import get_option


# =============================================================================
# Execution Functions
# =============================================================================

def execute_option(
    option: Option,
    state: GMIState,
    goal_position: Tuple[int, int],
    hazards: List[Tuple[int, int]] = None,
    walls: List[Tuple[int, int]] = None,
    max_steps: Optional[int] = None,
) -> OptionExecution:
    """
    Execute an option until termination or max_steps.
    
    Args:
        option: The option to execute
        state: Current GMI state
        goal_position: Target position
        hazards: Hazard positions
        walls: Wall positions
        max_steps: Optional override for max_steps
    
    Returns:
        OptionExecution with all actions and final state
    """
    # Create simple state for predicates
    simple_state = SimpleOptionState.from_gmi_state(
        state, goal_position, hazards, walls
    )
    
    # Check initiation
    if not option.initiation(simple_state):
        return OptionExecution(
            status=ExecutionStatus.FAILED,
            option_id=option.id,
            actions=[],
            final_state_hash="",
            termination_reason="initiation_failed",
            steps_executed=0,
        )
    
    # Determine max steps
    effective_max_steps = max_steps if max_steps is not None else option.max_steps
    
    # Track execution
    actions: List[GMIAction] = []
    current_state = simple_state
    step = 0
    
    # Execute until termination or max steps
    while step < effective_max_steps:
        # Check termination
        if option.termination(current_state):
            return OptionExecution(
                status=ExecutionStatus.TERMINATION_PREDICATE,
                option_id=option.id,
                actions=actions,
                final_state_hash=_hash_state(current_state),
                termination_reason="termination_predicate",
                steps_executed=len(actions),
            )
        
        # Get action from policy
        action = option.policy(current_state)
        actions.append(action)
        
        # Update state (simplified - would use dynamics model)
        # For now, just update position based on action
        row, col = current_state.position
        if action.drho and action.drho[0]:
            row += action.drho[0][0]
            if len(action.drho[0]) > 1:
                col += action.drho[0][1]
        
        # Create new state
        current_state = SimpleOptionState(
            position=(row, col),
            goal=current_state.goal,
            hazards=current_state.hazards,
            walls=current_state.walls,
            budget=current_state.budget - 1,  # Assume cost per step
        )
        
        step += 1
        
        # Check termination after update
        if option.termination(current_state):
            return OptionExecution(
                status=ExecutionStatus.TERMINATION_PREDICATE,
                option_id=option.id,
                actions=actions,
                final_state_hash=_hash_state(current_state),
                termination_reason="termination_predicate_after_step",
                steps_executed=len(actions),
            )
    
    # Max steps reached
    return OptionExecution(
        status=ExecutionStatus.MAX_STEPS,
        option_id=option.id,
        actions=actions,
        final_state_hash=_hash_state(current_state),
        termination_reason="max_steps_reached",
        steps_executed=len(actions),
    )


def execute_option_steps(
    option_id: str,
    state: GMIState,
    goal_position: Tuple[int, int],
    hazards: List[Tuple[int, int]] = None,
    walls: List[Tuple[int, int]] = None,
    max_steps: Optional[int] = None,
) -> OptionExecution:
    """
    Execute an option by ID.
    
    Args:
        option_id: The option ID
        state: Current GMI state
        goal_position: Target position
        hazards: Hazard positions
        walls: Wall positions
        max_steps: Optional override for max_steps
    
    Returns:
        OptionExecution with all actions and final state
    """
    option = get_option(option_id)
    return execute_option(option, state, goal_position, hazards, walls, max_steps)


def can_initiate(
    option_id: str,
    state: GMIState,
    goal_position: Tuple[int, int],
    hazards: List[Tuple[int, int]] = None,
    walls: List[Tuple[int, int]] = None,
) -> bool:
    """
    Check if an option can be initiated.
    
    Args:
        option_id: The option ID
        state: Current GMI state
        goal_position: Target position
        hazards: Hazard positions
        walls: Wall positions
    
    Returns:
        True if option can be initiated
    """
    option = get_option(option_id)
    simple_state = SimpleOptionState.from_gmi_state(state, goal_position, hazards, walls)
    return option.initiation(simple_state)


def get_option_actions(
    option_id: str,
    state: GMIState,
    goal_position: Tuple[int, int],
    hazards: List[Tuple[int, int]] = None,
    walls: List[Tuple[int, int]] = None,
    num_steps: int = 1,
) -> List[GMIAction]:
    """
    Get next N actions from an option.
    
    Does not execute termination checks - just returns actions.
    Useful for planning with options.
    
    Args:
        option_id: The option ID
        state: Current GMI state
        goal_position: Target position
        hazards: Hazard positions
        walls: Wall positions
        num_steps: Number of actions to get
    
    Returns:
        List of actions
    """
    option = get_option(option_id)
    simple_state = SimpleOptionState.from_gmi_state(state, goal_position, hazards, walls)
    
    actions: List[GMIAction] = []
    current_state = simple_state
    
    for _ in range(num_steps):
        action = option.policy(current_state)
        actions.append(action)
        
        # Update position (simplified)
        row, col = current_state.position
        if action.drho and action.drho[0]:
            row += action.drho[0][0]
            if len(action.drho[0]) > 1:
                col += action.drho[0][1]
        
        current_state = SimpleOptionState(
            position=(row, col),
            goal=current_state.goal,
            hazards=current_state.hazards,
            walls=current_state.walls,
            budget=current_state.budget,
        )
    
    return actions


# =============================================================================
# Helper Functions
# =============================================================================

def _hash_state(state: SimpleOptionState) -> str:
    """Compute hash of simple state."""
    config_str = f"{state.position}:{state.goal}:{state.hazards}:{state.walls}:{state.budget}"
    return hashlib.sha256(config_str.encode()).hexdigest()[:16]
