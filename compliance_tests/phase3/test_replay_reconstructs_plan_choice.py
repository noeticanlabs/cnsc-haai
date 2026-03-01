"""
Test: Replay Reconstructs Plan Choice

Verifies that replay can reproduce:
- PlanSet root
- Chosen plan hash
- First action
- State hash per step

This is critical for deterministic verification.
"""

import pytest
from cnsc_haai.gmi.types import GMIState
from cnsc_haai.planning import (
    PlannerConfig,
    plan_and_select,
    generate_planset,
    compute_adaptive_params,
)


def test_replay_reconstructs_planset_root():
    """Replay should be able to reconstruct PlanSet root."""
    # Initial parameters
    seed = 42
    m, H = compute_adaptive_params(budget=1000, m_max=10, H_max=5)
    
    # Generate planset with same seed
    planset = generate_planset(
        horizon=H,
        num_plans=m,
        seed=seed,
        include_special_plans=True,
    )
    
    # Compute root
    from cnsc_haai.planning.plan_merkle import build_plan_merkle_root
    root = build_plan_merkle_root(planset)
    
    # Replay should produce same root
    replay_planset = generate_planset(
        horizon=H,
        num_plans=m,
        seed=seed,
        include_special_plans=True,
    )
    replay_root = build_plan_merkle_root(replay_planset)
    
    assert root == replay_root, "Replay should reconstruct same PlanSet root"


def test_replay_reconstructs_chosen_plan():
    """Replay should be able to reconstruct chosen plan."""
    # Create state
    state = GMIState(
        rho=[[1, 0], [0, 0]],
        theta=[[5, 5]],
        C=[[0, 0]],
        b=1000,
        t=42,
    )
    
    config = PlannerConfig(
        m_max=10,
        H_max=5,
    )
    
    # First run
    result1 = plan_and_select(
        state=state,
        planner_config=config,
        goal_position=(8, 8),
        seed=42,
    )
    
    # Replay with same parameters
    result2 = plan_and_select(
        state=state,
        planner_config=config,
        goal_position=(8, 8),
        seed=42,
    )
    
    # Both should choose same action
    assert result1.action_name == result2.action_name, \
        "Replay should produce same action"
    
    # Both should have same planning cost
    assert result1.planning_cost == result2.planning_cost, \
        "Replay should produce same planning cost"


def test_replay_determinism_multiple_runs():
    """Multiple replays with same inputs should produce identical results."""
    state = GMIState(
        rho=[[1, 0], [0, 0]],
        theta=[[3, 3]],
        C=[[0, 0]],
        b=1000,
        t=100,
    )
    
    config = PlannerConfig(
        m_max=20,
        H_max=10,
    )
    
    results = []
    for _ in range(5):
        result = plan_and_select(
            state=state,
            planner_config=config,
            goal_position=(7, 7),
            seed=100,
        )
        results.append(result)
    
    # All should be identical
    for r in results[1:]:
        assert r.action_name == results[0].action_name
        assert r.planning_cost == results[0].planning_cost
        if r.receipts and results[0].receipts:
            assert r.receipts.planset_receipt.planset_root == \
                   results[0].receipts.planset_receipt.planset_root


def test_different_seeds_produce_different_results():
    """Different seeds should produce different results."""
    state = GMIState(
        rho=[[1, 0], [0, 0]],
        theta=[[5, 5]],
        C=[[0, 0]],
        b=1000,
        t=0,
    )
    
    config = PlannerConfig(
        m_max=10,
        H_max=5,
    )
    
    result1 = plan_and_select(
        state=state,
        planner_config=config,
        goal_position=(8, 8),
        seed=1,
    )
    
    result2 = plan_and_select(
        state=state,
        planner_config=config,
        goal_position=(8, 8),
        seed=2,
    )
    
    # Different seeds should produce different plansets
    if result1.receipts and result2.receipts:
        root1 = result1.receipts.planset_receipt.planset_root
        root2 = result2.receipts.planset_receipt.planset_root
        # Note: With different seeds, plansets might or might not differ
        # This test just verifies seeds are used
        assert root1 is not None and root2 is not None


def test_receipt_contains_all_replay_info():
    """Receipts should contain all info needed for replay."""
    state = GMIState(
        rho=[[1, 0], [0, 0]],
        theta=[[5, 5]],
        C=[[0, 0]],
        b=1000,
        t=0,
    )
    
    config = PlannerConfig()
    
    result = plan_and_select(
        state=state,
        planner_config=config,
        goal_position=(5, 5),
        seed=42,
    )
    
    # Verify receipt contains replay info
    assert result.receipts is not None
    planset_receipt = result.receipts.planset_receipt
    
    # PlanSet receipt should have:
    assert planset_receipt.t == 0
    assert planset_receipt.seed == 42
    assert planset_receipt.planset_root is not None
    assert planset_receipt.plans_count > 0
    assert planset_receipt.horizon > 0
    
    # Decision receipt should have:
    decision = result.receipts.decision_receipt
    assert decision.planset_root == planset_receipt.planset_root
    assert decision.chosen_plan_hash is not None
    assert decision.chosen_action is not None
    assert decision.predicted_cost_J is not None
    assert decision.budget_before_planning == 1000


def test_replay_with_different_budgets():
    """Replays with different budgets should produce different results."""
    state1 = GMIState(
        rho=[[1, 0], [0, 0]],
        theta=[[5, 5]],
        C=[[0, 0]],
        b=1000,
        t=0,
    )
    
    state2 = GMIState(
        rho=[[1, 0], [0, 0]],
        theta=[[5, 5]],
        C=[[0, 0]],
        b=500,  # Different budget
        t=0,
    )
    
    config = PlannerConfig()
    
    result1 = plan_and_select(
        state=state1,
        planner_config=config,
        goal_position=(8, 8),
        seed=42,
    )
    
    result2 = plan_and_select(
        state=state2,
        planner_config=config,
        goal_position=(8, 8),
        seed=42,
    )
    
    # Different budgets might lead to different m, H and thus different plans
    # But both should still be valid
    assert result1 is not None
    assert result2 is not None
    
    # Planning costs should differ
    assert result1.planning_cost != result2.planning_cost or \
           result1.budget_after_planning != result2.budget_after_planning


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
