"""
Test: Budget Charged for Planning

Verifies that budget debit is proportional to planning work:
W_plan = kappa_plan * m * H + kappa_gate * m + kappa_exec

This ensures planning has a real metabolic cost.
"""

import pytest
from cnsc_haai.gmi.types import GMIState
from cnsc_haai.planning import (
    PlannerConfig,
    plan_and_select,
    compute_adaptive_params,
)


def test_budget_proportional_to_m_h():
    """Budget should scale with m * H (planning work)."""
    # Test with different m, H values
    
    # High planning work
    state_high = GMIState(
        rho=[[1, 0], [0, 0]],
        theta=[[0, 0]],
        C=[[0, 0]],
        b=10000,  # Large budget
        t=0,
    )
    
    config_high = PlannerConfig(
        m_max=20,
        H_max=10,
        kappa_plan=1,
        kappa_gate=0,
        kappa_exec=1,
    )
    
    result_high = plan_and_select(
        state=state_high,
        planner_config=config_high,
        goal_position=(5, 5),
    )
    
    # Low planning work
    state_low = GMIState(
        rho=[[1, 0], [0, 0]],
        theta=[[0, 0]],
        C=[[0, 0]],
        b=10000,
        t=0,
    )
    
    # Force lower m, H via budget-adaptive
    config_low = PlannerConfig(
        m_max=2,  # Much lower
        H_max=2,  # Much lower
        kappa_plan=1,
        kappa_gate=0,
        kappa_exec=1,
    )
    
    result_low = plan_and_select(
        state=state_low,
        planner_config=config_low,
        goal_position=(5, 5),
    )
    
    # Higher m*H should result in higher planning cost
    cost_high = result_high.planning_cost
    cost_low = result_low.planning_cost
    
    # Note: actual values depend on budget-adaptive computation
    # But generally, more plans * longer horizon = more cost
    assert cost_high >= cost_low, "Higher planning work should cost more"


def test_planning_cost_formula():
    """Test the exact formula: W = kappa_plan * m * H + kappa_gate * m + kappa_exec"""
    # Different kappa values
    kappa_plan_values = [1, 2, 5]
    
    for kappa_plan in kappa_plan_values:
        config = PlannerConfig(
            m_max=10,
            H_max=5,
            kappa_plan=kappa_plan,
            kappa_gate=0,
            kappa_exec=1,
        )
        
        # Compute expected cost
        m, H = compute_adaptive_params(
            budget=10000,
            m_max=10,
            H_max=5,
        )
        expected_cost = kappa_plan * m * H + 0 * m + 1
        
        assert expected_cost == config.compute_planning_cost(m, H), \
            f"Cost formula incorrect for kappa_plan={kappa_plan}"


def test_zero_budget_absorption():
    """At b=0, no planning cost (absorption mode)."""
    state = GMIState(
        rho=[[1, 0], [0, 0]],
        theta=[[0, 0]],
        C=[[0, 0]],
        b=0,
        t=0,
    )
    
    config = PlannerConfig()
    
    result = plan_and_select(
        state=state,
        planner_config=config,
        goal_position=(5, 5),
    )
    
    # At b=0, planning is disabled, cost should be 0
    assert result.planning_cost == 0, "At b=0, planning should be free (disabled)"
    assert result.budget_after_planning == 0, "Budget should remain 0"


def test_low_budget_fallback():
    """If budget < planning cost, should fallback gracefully."""
    state = GMIState(
        rho=[[1, 0], [0, 0]],
        theta=[[0, 0]],
        C=[[0, 0]],
        b=10,  # Low budget
        t=0,
    )
    
    config = PlannerConfig(
        kappa_plan=100,  # Very high cost
        m_max=10,
        H_max=10,
    )
    
    result = plan_and_select(
        state=state,
        planner_config=config,
        goal_position=(5, 5),
    )
    
    # Should either:
    # 1. Not deduct planning cost (fallback)
    # 2. Deduct cost but return Stay
    # Either way, budget_after should not go negative
    assert result.budget_after_planning >= 0, "Budget should not go negative"


def test_budget_adaptive_scaling():
    """Test that m and H scale with budget."""
    # High budget
    m_high, H_high = compute_adaptive_params(budget=10000, m_max=20, H_max=10)
    
    # Low budget
    m_low, H_low = compute_adaptive_params(budget=100, m_max=20, H_max=10)
    
    # Higher budget should allow more plans and longer horizon
    assert m_high >= m_low, "Higher budget should allow more plans"
    assert H_high >= H_low, "Higher budget should allow longer horizon"


def test_planning_cost_deducted():
    """Verify planning cost is actually deducted from budget."""
    initial_budget = 1000
    
    state = GMIState(
        rho=[[1, 0], [0, 0]],
        theta=[[0, 0]],
        C=[[0, 0]],
        b=initial_budget,
        t=0,
    )
    
    config = PlannerConfig(
        m_max=10,
        H_max=5,
        kappa_plan=1,
        kappa_gate=0,
        kappa_exec=1,
    )
    
    result = plan_and_select(
        state=state,
        planner_config=config,
        goal_position=(5, 5),
    )
    
    # Budget after planning should be initial - planning_cost
    expected_after = initial_budget - result.planning_cost
    assert result.budget_after_planning == expected_after, \
        f"Budget should be {expected_after}, got {result.budget_after_planning}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
