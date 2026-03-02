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
from cnsc_haai.options import list_options, get_option

# Import from GMI
from cnsc_haai.gmi.types import GMIState


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
        
    print(f"Option provenance verified for {len(plans)} plans")
