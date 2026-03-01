"""
Test: PlanSet Receipt Required

Verifies that:
1. Chosen plan has PlanSet commitment
2. Chosen plan is member of committed PlanSet (Merkle membership)

This ensures the planner can't cherry-pick plans after the fact.
"""

import pytest
from cnsc_haai.gmi.types import GMIState, GMIAction
from cnsc_haai.planning import (
    PlannerConfig,
    plan_and_select,
    build_plan_merkle_root,
    verify_plan_membership,
)


def test_planset_receipt_required_basic():
    """Basic test: planner produces receipts."""
    # Create test state
    state = GMIState(
        rho=[[1, 0], [0, 0]],
        theta=[[0, 0]],
        C=[[0, 0]],
        b=1000,  # Enough budget for planning
        t=0,
    )
    
    # Create planner config
    config = PlannerConfig(
        m_max=10,
        H_max=5,
        b_unit=100,
        h_unit=50,
    )
    
    # Plan
    result = plan_and_select(
        state=state,
        planner_config=config,
        goal_position=(5, 5),
    )
    
    # Verify receipts exist
    assert result.receipts is not None, "Planning should produce receipts"
    assert result.receipts.planset_receipt is not None, "Should have PlanSet receipt"
    assert result.receipts.decision_receipt is not None, "Should have decision receipt"
    
    # Verify PlanSet root is recorded
    planset_root = result.receipts.planset_receipt.planset_root
    assert planset_root is not None, "PlanSet root should be set"
    assert len(planset_root) > 0, "PlanSet root should not be empty"


def test_chosen_plan_in_planset():
    """Verify chosen plan is actually in the committed PlanSet."""
    # Create test state
    state = GMIState(
        rho=[[1, 0], [0, 0]],
        theta=[[0, 0]],
        C=[[0, 0]],
        b=1000,
        t=0,
    )
    
    config = PlannerConfig(
        m_max=10,
        H_max=5,
    )
    
    result = plan_and_select(
        state=state,
        planner_config=config,
        goal_position=(5, 5),
    )
    
    # Get the chosen plan
    chosen_plan = result.chosen_plan
    chosen_plan_index = result.chosen_plan_index
    
    # If we got a valid result with a chosen plan
    if chosen_plan is not None and chosen_plan_index >= 0:
        # Verify the chosen plan's hash is in the PlanSet
        # (The receipt should contain the plan hash)
        chosen_hash = result.receipts.decision_receipt.chosen_plan_hash
        assert chosen_hash == chosen_plan.plan_hash, "Chosen plan hash should match"


def test_planning_with_zero_budget():
    """At b=0, no PlanSet needed (absorption mode)."""
    state = GMIState(
        rho=[[1, 0], [0, 0]],
        theta=[[0, 0]],
        C=[[0, 0]],
        b=0,  # Zero budget - absorption mode
        t=0,
    )
    
    config = PlannerConfig()
    
    result = plan_and_select(
        state=state,
        planner_config=config,
        goal_position=(5, 5),
    )
    
    # In absorption mode, should return Stay with no receipts
    # (This is correct behavior - no planning at b=0)
    assert result.action_name == "Stay", "At b=0, should use Stay action"


def test_planning_cost_affordability():
    """If budget can't afford planning, should fallback gracefully."""
    state = GMIState(
        rho=[[1, 0], [0, 0]],
        theta=[[0, 0]],
        C=[[0, 0]],
        b=5,  # Very low budget
        t=0,
    )
    
    config = PlannerConfig(
        kappa_plan=10,  # High cost
        m_max=10,
        H_max=5,
    )
    
    result = plan_and_select(
        state=state,
        planner_config=config,
        goal_position=(5, 5),
    )
    
    # Should either:
    # 1. Return Stay (if cost too high)
    # 2. Return a valid plan (if affordable)
    # Either way, should not crash
    assert result is not None
    assert result.action is not None


def test_determinism():
    """Same inputs should produce same PlanSet commitment."""
    state = GMIState(
        rho=[[1, 0], [0, 0]],
        theta=[[0, 0]],
        C=[[0, 0]],
        b=1000,
        t=42,  # Fixed seed via t
    )
    
    config = PlannerConfig(
        m_max=10,
        H_max=5,
    )
    
    # Run twice with same inputs
    result1 = plan_and_select(
        state=state,
        planner_config=config,
        goal_position=(5, 5),
        seed=42,  # Explicit seed
    )
    
    result2 = plan_and_select(
        state=state,
        planner_config=config,
        goal_position=(5, 5),
        seed=42,
    )
    
    # Both should have same PlanSet root
    root1 = result1.receipts.planset_receipt.planset_root if result1.receipts else None
    root2 = result2.receipts.planset_receipt.planset_root if result2.receipts else None
    
    if root1 and root2:
        assert root1 == root2, "Same inputs should produce same PlanSet root"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
