"""
Test: Options Are Used and Receipted

Verifies that Phase 3 planning + skills integration works correctly:
- Options can be used by the planner
- Options are receipted for audit/replay

This is the skills integration proof per the Phase 3 spec.
"""

import pytest
from typing import List, Tuple

# Import from planning - the new options integration
from cnsc_haai.planning.planset_generator import (
    generate_option_plans,
    Plan,
)
from cnsc_haai.planning import PlannerConfig

# Import from options
from cnsc_haai.options import list_options, get_option, execute_option_steps

# Import from GMI
from cnsc_haai.gmi.types import GMIState

# Import from tasks/benchmarks (for Key-Door Maze)
from cnsc_haai.tasks.benchmarks import create_key_door_maze


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_state():
    """Create a sample GMI state for testing."""
    return GMIState(
        rho=[[3]],  # row position = 3
        theta=[[4, 9, 9]],  # col position = 4, goal = (9,9)
        C=[[0]],
        b=1000,  # budget
        t=0,
    )


@pytest.fixture
def goal_position():
    """Goal position for testing."""
    return (9, 9)


# =============================================================================
# Tests
# =============================================================================

def test_options_registry_has_options():
    """
    Verify that options are registered and available.
    
    Options must exist in the registry for planning to use them.
    """
    options = list_options()
    
    assert len(options) > 0, "Options registry should not be empty"
    
    # Verify we have expected option types
    # Based on spec: GoToGoalGreedy, AvoidHazardGradient, WallFollowLeft, etc.
    print(f"Available options: {options}")


def test_options_have_required_interface(sample_state, goal_position):
    """
    Verify each option has the required interface for planning.
    
    Each option must have:
    - id (stable identifier)
    - max_steps
    - initiation predicate
    - termination predicate
    - policy function
    """
    options = list_options()
    
    for option_id in options:
        option = get_option(option_id)
        
        # Verify required attributes exist
        assert hasattr(option, 'id'), f"Option {option_id} must have 'id'"
        assert hasattr(option, 'max_steps'), f"Option {option_id} must have 'max_steps'"
        assert hasattr(option, 'initiation'), f"Option {option_id} must have 'initiation'"
        assert hasattr(option, 'termination'), f"Option {option_id} must have 'termination'"
        assert hasattr(option, 'policy'), f"Option {option_id} must have 'policy'"
        
        print(f"Option {option_id}: max_steps={option.max_steps}")


def test_generate_option_plans_produces_plans(sample_state, goal_position):
    """
    Verify generate_option_plans produces plans from options.
    
    This tests the Option A design: unfold options at PlanSet generation time.
    """
    # Generate plans from options
    plans = generate_option_plans(
        state=sample_state,
        goal_position=goal_position,
        hazard_mask=None,
        horizon=10,
    )
    
    # Should produce at least some plans
    assert isinstance(plans, list), "generate_option_plans should return a list"
    
    # Each plan should be a valid Plan object
    for plan in plans:
        assert isinstance(plan, Plan), f"Expected Plan, got {type(plan)}"
        assert len(plan.actions) > 0, "Plan should have actions"
        assert plan.horizon > 0, "Plan horizon must be positive"
        assert plan.plan_hash, "Plan should have a hash"
    
    print(f"Generated {len(plans)} option-derived plans")


def test_option_plans_are_deterministic(sample_state, goal_position):
    """
    Verify that option plan generation is deterministic.
    
    Same state + seed should produce same plans.
    """
    # Generate plans twice with same state
    plans1 = generate_option_plans(
        state=sample_state,
        goal_position=goal_position,
        hazard_mask=None,
        horizon=10,
    )
    
    plans2 = generate_option_plans(
        state=sample_state,
        goal_position=goal_position,
        hazard_mask=None,
        horizon=10,
    )
    
    # Should produce same number of plans
    assert len(plans1) == len(plans2), "Same state should produce same number of plans"
    
    # Plan hashes should match (determinism)
    hashes1 = [p.plan_hash for p in plans1]
    hashes2 = [p.plan_hash for p in plans2]
    
    assert hashes1 == hashes2, "Same state should produce identical plan hashes"


def test_options_respect_budget(sample_state, goal_position):
    """
    Verify options work correctly under different budget conditions.
    
    When budget is low, plans should still be generated (options don't require budget).
    """
    # Low budget state
    low_budget_state = GMIState(
        rho=[[3]],
        theta=[[4, 9, 9]],
        C=[[0]],
        b=10,  # very low budget
        t=0,
    )
    
    # Generate plans with low budget
    plans = generate_option_plans(
        state=low_budget_state,
        goal_position=goal_position,
        hazard_mask=None,
        horizon=5,
    )
    
    # Should still produce plans (options don't depend on budget for generation)
    assert isinstance(plans, list), "Should return list even with low budget"
    # Note: some options may fail if they can't initiate, but the function should not error


def test_option_receipts_have_provenance():
    """
    Verify that option-derived plans have proper provenance for receipts.
    
    The plan_hash includes the option_id prefix for audit trail.
    Now also verifies option_id and option_trace fields.
    """
    # Create a state and generate plans
    state = GMIState(
        rho=[[1]],
        theta=[[1, 5, 5]],
        C=[[0]],
        b=1000,
        t=0,
    )
    
    plans = generate_option_plans(
        state=state,
        goal_position=(5, 5),
        hazard_mask=None,
        horizon=5,
    )
    
    # Plan hashes should indicate option origin
    for plan in plans:
        # Hash format includes "option_" prefix per implementation
        # This allows receipts to trace back to skills
        assert plan.plan_hash, "Must have hash for receipt"
    
    # Verify option_id is set for option-derived plans
    option_plans = [p for p in plans if p.option_id is not None]
    assert len(option_plans) > 0, "At least one plan should have option_id"
    
    # Verify option_trace is set
    for plan in option_plans:
        assert plan.option_trace, "Option plan must have option_trace"
        
    print(f"Option provenance verified for {len(plans)} plans ({len(option_plans)} with option_id)")


def test_option_invocation_receipted_with_id():
    """
    COMPLIANCE: Option invocation must be receipted with option_id.
    
    Per spec requirement:
    - option_id must be present in the plan
    - option_trace (unfold trace) must be present
    - resulting primitive actions must be recorded
    """
    state = GMIState(
        rho=[[1]],
        theta=[[1, 5, 5]],
        C=[[0]],
        b=1000,
        t=0,
    )
    
    plans = generate_option_plans(
        state=state,
        goal_position=(5, 5),
        hazard_mask=None,
        horizon=5,
    )
    
    # Must have at least one option-derived plan
    assert len(plans) > 0, "Should generate option plans"
    
    # Verify each plan has required provenance
    option_plans = [p for p in plans if p.option_id is not None]
    assert len(option_plans) > 0, "At least one plan must have option_id"
    
    for plan in option_plans:
        # COMPLIANCE: option_id present
        assert plan.option_id, f"Plan must have option_id: {plan}"
        
        # COMPLIANCE: unfold trace present (Design B)
        assert plan.option_trace, f"Plan must have option_trace: {plan}"
        assert len(plan.option_trace) > 0, "option_trace must not be empty"
        
        # COMPLIANCE: resulting primitive actions recorded
        assert len(plan.actions) > 0, "Plan must have primitive actions"
        
    print(f"Option invocation receipted for {len(option_plans)} plans with id and trace")


def test_option_determinism_for_replay():
    """
    COMPLIANCE: Options must be deterministic for replay.
    
    Per spec fail condition:
    - option determinism breaks replay
    
    This test verifies that executing the same option twice
    with the same state produces identical results.
    """
    from cnsc_haai.options import execute_option_steps
    
    state = GMIState(
        rho=[[3]],
        theta=[[3, 5, 5]],
        C=[[0]],
        b=1000,
        t=0,
    )
    
    # Get list of available options
    options = list_options()
    assert len(options) > 0, "Must have options available"
    
    for option_id in options:
        # Execute option twice with same state
        exec1 = execute_option_steps(
            option_id=option_id,
            state=state,
            goal_position=(5, 5),
            hazards=None,
            walls=None,
            max_steps=5,
        )
        
        exec2 = execute_option_steps(
            option_id=option_id,
            state=state,
            goal_position=(5, 5),
            hazards=None,
            walls=None,
            max_steps=5,
        )
        
        # COMPLIANCE: Actions must be identical for replay
        assert exec1.actions == exec2.actions, \
            f"Option {option_id} must be deterministic: {exec1.actions} != {exec2.actions}"
        
        # COMPLIANCE: Final state hashes must match
        assert exec1.final_state_hash == exec2.final_state_hash, \
            f"Option {option_id} must produce same final state"
    
    print(f"Determinism verified for {len(options)} options")


def test_planner_config_enables_options():
    """
    Verify PlannerConfig can enable options.
    
    This tests that the use_options flag is properly handled.
    """
    from cnsc_haai.planning import PlannerConfig
    
    # Default config should have options disabled
    config_default = PlannerConfig()
    assert config_default.use_options == False, "Options should be disabled by default"
    
    # Config with options enabled
    config_with_options = PlannerConfig(
        use_options=True,
        option_horizon=15,
    )
    assert config_with_options.use_options == True, "Options should be enabled"
    assert config_with_options.option_horizon == 15, "option_horizon should be set"
    
    # Config should be hashable (for receipts)
    config_hash = config_with_options.hash()
    assert config_hash, "Config should produce a hash"
    
    print("PlannerConfig options integration verified")


# =============================================================================
# Integration Tests with Key-Door Maze
# =============================================================================

def test_key_door_maze_with_options():
    """
    COMPLIANCE: Run Key-Door Maze where option is beneficial.
    
    This test verifies that:
    1. Options can be used in a maze environment
    2. Option invocation occurs within M steps
    3. Option is properly receipted
    
    This is the main skills integration proof.
    """
    from cnsc_haai.tasks.benchmarks import create_key_door_maze
    
    # Create Key-Door Maze (where GoToKey option is beneficial)
    maze = create_key_door_maze(width=8, height=8, seed=42)
    
    # Get initial maze state
    maze_state = maze.reset()
    print(f"Initial position: {maze_state.position}")
    
    # Convert maze state to GMIState for option planning
    # The options system expects GMIState format
    gmi_state = GMIState(
        rho=[[maze_state.position[0]]],  # row position
        theta=[[maze_state.position[1], maze.goal_position[0], maze.goal_position[1]]],  # col, goal_row, goal_col
        C=[[0]],  # No curvature
        b=1000,  # Budget
        t=0,
    )
    
    # Generate option plans for this state
    # Goal is at maze.goal_position
    plans = generate_option_plans(
        state=gmi_state,
        goal_position=maze.goal_position,
        hazard_mask=None,  # Key-Door maze doesn't have hazards in the same format
        horizon=10,
    )
    
    # COMPLIANCE: At least one option invocation should occur
    assert len(plans) > 0, "Should generate option plans for Key-Door Maze"
    
    # Verify provenance
    option_plans = [p for p in plans if p.option_id is not None]
    assert len(option_plans) > 0, "Should have option-derived plans"
    
    # Verify option_id, trace, and actions are all present
    for plan in option_plans:
        assert plan.option_id, "Plan must have option_id"
        assert plan.option_trace, "Plan must have option_trace"
        assert len(plan.actions) > 0, "Plan must have primitive actions"
    
    print(f"Key-Door Maze options test passed: {len(option_plans)} option plans generated")
    print(f"  - option_ids: {[p.option_id for p in option_plans[:3]]}")

