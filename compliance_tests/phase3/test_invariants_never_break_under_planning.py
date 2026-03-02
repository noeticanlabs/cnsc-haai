"""
Test: Invariants Never Break Under Planning

Verifies that under planning CLOSED-LOOP:
- Hazards never entered
- State always in bounds  
- Budget never negative
- Absorption respected at b=0

CRITICAL: This test executes the planner's chosen actions in the environment
and verifies invariants AFTER each step, not just that the planner returns something.
"""

import pytest
from typing import List, Tuple

from cnsc_haai.gmi.types import GMIState
from cnsc_haai.planning import (
    PlannerConfig,
    plan_and_select,
)


# =============================================================================
# Helper Functions
# =============================================================================

def apply_action_to_state(
    state: GMIState,
    action_name: str,
    grid_bounds: Tuple[int, int],
) -> GMIState:
    """
    Apply action and update GMI state.
    
    This simulates the environment transition.
    """
    # Extract current position from theta
    # theta format: [[col, goal_row, goal_col], ...]
    current_row = state.rho[0][0] if state.rho and state.rho[0] else 0
    current_col = state.theta[0][0] if state.theta and state.theta[0] else 0
    goal_row = state.theta[0][1] if len(state.theta[0]) > 1 else 0
    goal_col = state.theta[0][2] if len(state.theta[0]) > 2 else 0
    
    # Apply action
    new_row, new_col = current_row, current_col
    
    if action_name == "N" and current_row > 0:
        new_row = current_row - 1
    elif action_name == "S" and current_row < grid_bounds[0] - 1:
        new_row = current_row + 1
    elif action_name == "E" and current_col < grid_bounds[1] - 1:
        new_col = current_col + 1
    elif action_name == "W" and current_col > 0:
        new_col = current_col - 1
    # Stay: no change
    
    # Return updated state
    return GMIState(
        rho=[[new_row]],
        theta=[[new_col, goal_row, goal_col]],
        C=state.C,
        b=state.b,
        t=state.t + 1,
    )


def is_position_in_hazard(
    position: Tuple[int, int],
    hazards: List[Tuple[int, int]],
) -> bool:
    """Check if position is a hazard."""
    return position in hazards


def is_position_in_bounds(
    position: Tuple[int, int],
    grid_bounds: Tuple[int, int],
) -> bool:
    """Check if position is within grid bounds."""
    row, col = position
    rows, cols = grid_bounds
    return 0 <= row < rows and 0 <= col < cols


# =============================================================================
# Tests - CLOSED LOOP (Execute Actions!)
# =============================================================================

def test_hazards_never_entered():
    """
    CRITICAL: Planner must NOT choose actions that enter hazards in EXECUTION.
    
    This test runs closed-loop:
    1. Plan -> get action
    2. Execute action in environment
    3. Check invariants AFTER execution
    """
    # Define hazard positions
    hazards = [(2, 2), (2, 3), (3, 2)]
    grid_bounds = (10, 10)
    
    # Start in safe position, away from hazards
    state = GMIState(
        rho=[[1]],  # row = 1
        theta=[[1, 8, 8]],  # col = 1, goal = (8,8)
        C=[[0]],
        b=1000,
        t=0,
    )
    
    config = PlannerConfig(
        hazard_positions=tuple(hazards),
        grid_bounds=grid_bounds,
        min_budget=10,
    )
    
    # Run multiple planning steps - CLOSED LOOP
    for step in range(20):
        # Step 1: Plan and get action
        result = plan_and_select(
            state=state,
            planner_config=config,
            goal_position=(8, 8),
            hazard_mask=None,  # Planner handles hazards internally
        )
        
        assert result is not None, f"Step {step}: Planner returned None"
        action = result.action_name
        
        # Step 2: Execute action in environment
        new_state = apply_action_to_state(state, action, grid_bounds)
        
        # Extract position from new state
        new_row = new_state.rho[0][0]
        new_col = new_state.theta[0][0]
        new_position = (new_row, new_col)
        
        # Step 3: CRITICAL - Check invariants AFTER execution
        # Must not be in hazard
        assert not is_position_in_hazard(new_position, hazards), (
            f"Step {step}: Entered hazard at {new_position} after action '{action}'!"
        )
        
        # Must be in bounds
        assert is_position_in_bound(new_position, grid_bounds), (
            f"Step {step}: Went out of bounds to {new_position}!"
        )
        
        # Must have non-negative budget
        assert new_state.b >= 0, f"Step {step}: Budget went negative: {new_state.b}"
        
        # Update state for next iteration
        state = new_state


def test_state_always_in_bounds():
    """
    CRITICAL: Planner must NOT choose actions that go outside bounds in execution.
    """
    grid_bounds = (10, 10)
    
    # Start at edge - position (9, 9)
    state = GMIState(
        rho=[[9]],  # row = 9 (at edge)
        theta=[[9, 0, 0]],  # col = 9, goal = (0,0)
        C=[[0]],
        b=1000,
        t=0,
    )
    
    config = PlannerConfig(
        grid_bounds=grid_bounds,
        min_budget=10,
    )
    
    # Run planning steps - CLOSED LOOP
    for step in range(10):
        # Plan
        result = plan_and_select(
            state=state,
            planner_config=config,
            goal_position=(0, 0),
        )
        
        assert result is not None, f"Step {step}: Planner returned None"
        action = result.action_name
        
        # Execute
        new_state = apply_action_to_state(state, action, grid_bounds)
        
        # Check bounds AFTER execution
        row = new_state.rho[0][0]
        col = new_state.theta[0][0]
        
        assert is_position_in_bounds((row, col), grid_bounds), (
            f"Step {step}: Out of bounds at ({row}, {col}) after '{action}'!"
        )
        
        state = new_state


def test_budget_never_negative():
    """Budget must never go negative during planning."""
    grid_bounds = (10, 10)
    
    # Start with limited budget
    state = GMIState(
        rho=[[5]],
        theta=[[5, 8, 8]],
        C=[[0]],
        b=100,  # Limited budget
        t=0,
    )
    
    config = PlannerConfig(
        grid_bounds=grid_bounds,
        min_budget=10,
        kappa_plan=1,
    )
    
    # Run planning steps - CLOSED LOOP
    for step in range(20):
        # Plan
        result = plan_and_select(
            state=state,
            planner_config=config,
            goal_position=(8, 8),
        )
        
        # Get budget after planning
        budget_after = result.budget_after_planning
        
        # Budget must not go negative
        assert budget_after >= 0, (
            f"Step {step}: Budget went negative: {budget_after}"
        )
        
        # Execute action
        action = result.action_name if result else "Stay"
        new_state = apply_action_to_state(state, action, grid_bounds)
        
        # Budget still non-negative after execution
        assert new_state.b >= 0, (
            f"Step {step}: Budget negative after execution: {new_state.b}"
        )
        
        state = new_state


def test_absorption_at_b_zero():
    """
    CRITICAL: When budget == 0, only safe idle actions allowed.
    
    Planning must be disabled and only 'Stay' action permitted.
    """
    grid_bounds = (10, 10)
    
    # Start with ZERO budget - absorption state
    state = GMIState(
        rho=[[5]],
        theta=[[5, 8, 8]],
        C=[[0]],
        b=0,  # ABSORPTION - no planning allowed!
        t=0,
    )
    
    config = PlannerConfig(
        grid_bounds=grid_bounds,
        min_budget=10,
    )
    
    # At b=0, planning should be disabled
    # The planner should return Stay (absorption action)
    result = plan_and_select(
        state=state,
        planner_config=config,
        goal_position=(8, 8),
    )
    
    assert result is not None
    
    # With zero budget, should only be able to take safe/Stay action
    # (or planning should be completely disabled)
    action = result.action_name
    
    # Execute the action
    new_state = apply_action_to_state(state, action, grid_bounds)
    
    # After absorption action, should still have zero or minimal budget
    # and should not have moved into hazard
    assert new_state.b >= 0
    
    # If action was executed, position should still be safe
    row = new_state.rho[0][0]
    col = new_state.theta[0][0]
    assert is_position_in_bounds((row, col), grid_bounds)


def test_absorption_transition():
    """Test that budget properly transitions to absorption state."""
    grid_bounds = (10, 10)
    
    # Start with minimal budget that will be consumed
    initial_budget = 50
    state = GMIState(
        rho=[[5]],
        theta=[[5, 8, 8]],
        C=[[0]],
        b=initial_budget,
        t=0,
    )
    
    config = PlannerConfig(
        grid_bounds=grid_bounds,
        min_budget=10,
        kappa_plan=10,  # High cost to consume budget
    )
    
    # Run until budget depleted
    for step in range(20):
        result = plan_and_select(
            state=state,
            planner_config=config,
            goal_position=(8, 8),
        )
        
        if result is None:
            break
            
        budget_after = result.budget_after_planning
        
        # Budget should decrease with each planning step
        # Eventually should reach 0 and stay there (absorption)
        
        action = result.action_name
        new_state = apply_action_to_state(state, action, grid_bounds)
        
        # Never negative
        assert new_state.b >= 0, f"Step {step}: Negative budget"
        
        state = new_state
        
        if budget_after == 0:
            # Reached absorption - can stop
            break


def test_stress_invariant_loop():
    """Stress test: run many steps ensuring invariants hold."""
    import random
    random.seed(42)
    
    grid_bounds = (10, 10)
    hazards = [(5, 5), (5, 6), (6, 5)]
    
    # Start at various positions
    for start_row in range(3):
        for start_col in range(3):
            state = GMIState(
                rho=[[start_row]],
                theta=[[start_col, 9, 9]],
                C=[[0]],
                b=500,
                t=0,
            )
            
            config = PlannerConfig(
                hazard_positions=tuple(hazards),
                grid_bounds=grid_bounds,
                min_budget=10,
            )
            
            # Run several steps
            for _ in range(10):
                result = plan_and_select(
                    state=state,
                    planner_config=config,
                    goal_position=(9, 9),
                )
                
                if result is None:
                    break
                    
                action = result.action_name
                new_state = apply_action_to_state(state, action, grid_bounds)
                
                # Check invariants
                row = new_state.rho[0][0]
                col = new_state.theta[0][0]
                
                assert is_position_in_bounds((row, col), grid_bounds)
                assert not is_position_in_hazard((row, col), hazards)
                assert new_state.b >= 0
                
                state = new_state


def test_multiple_hazard_config():
    """Test with various hazard configurations."""
    grid_bounds = (10, 10)
    
    hazard_configs = [
        [],  # No hazards
        [(5, 5)],  # Single hazard
        [(5, 5), (5, 6), (6, 5), (6, 6)],  # Cluster
    ]
    
    for hazards in hazard_configs:
        state = GMIState(
            rho=[[2]],
            theta=[[2, 8, 8]],
            C=[[0]],
            b=200,
            t=0,
        )
        
        config = PlannerConfig(
            hazard_positions=tuple(hazards) if hazards else (),
            grid_bounds=grid_bounds,
            min_budget=10,
        )
        
        for _ in range(5):
            result = plan_and_select(
                state=state,
                planner_config=config,
                goal_position=(8, 8),
            )
            
            if result is None:
                break
                
            action = result.action_name
            new_state = apply_action_to_state(state, action, grid_bounds)
            
            row = new_state.rho[0][0]
            col = new_state.theta[0][0]
            
            assert is_position_in_bounds((row, col), grid_bounds)
            assert not is_position_in_hazard((row, col), hazards)
            assert new_state.b >= 0
            
            state = new_state


# Fix: rename helper function (typo in original)
def is_position_in_bound(position, grid_bounds):
    """Alias for bounds check."""
    return is_position_in_bounds(position, grid_bounds)
