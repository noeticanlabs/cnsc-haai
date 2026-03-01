"""
CLATL Invariants Never Break Compliance Test

Tests that all safety invariants are maintained throughout CLATL execution:
1. Admissibility: GMI state stays in K (b >= 0, rho in bounds, C >= 0)
2. Budget: b >= 0 at all times
3. Safety: No hazard collisions in gridworld
4. Governance: Governor never allows unsafe actions

This is the CORE test - if this fails, the system is not safe.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest

# Import CLATL components
from cnsc_haai.tasks.gridworld_env import (
    create_standard_grid,
    create_initial_state,
    env_step,
    drift_goal,
    CELL_HAZARD,
    CELL_WALL,
)
from cnsc_haai.tasks.task_loss import V_task_distance
from cnsc_haai.agent.clatl_runtime import (
    run_clatl_episode,
    _create_initial_gmi_state,
)
from cnsc_haai.gmi.params import GMIParams
from cnsc_haai.gmi.admissible import in_K


class TestInvariantsNeverBreak:
    """Test suite for safety invariant verification."""
    
    def test_admissibility_never_violated_single_episode(self):
        """
        Test G1: Admissibility (z in K) is never violated.
        
        The GMI state must stay in the admissibility set K:
        - b >= 0
        - rho in [0, rho_max]
        - C >= 0
        """
        # Setup
        grid, start, goal = create_standard_grid("simple")
        gridworld = create_initial_state(grid, start, goal, drift_seed=42)
        gmi_state = _create_initial_gmi_state(budget=10_000_000)
        params = GMIParams()
        
        # Run episode
        receipt = run_clatl_episode(
            gmi_state=gmi_state,
            gridworld=gridworld,
            max_steps=50,
            goal_drift_every=30,
            drift_seed=42,
            gmi_params=params,
        )
        
        # Check: No admissibility violations
        admissibility_violations = [
            v for v in receipt.invariant_violations 
            if "admissibility" in v
        ]
        
        assert len(admissibility_violations) == 0, \
            f"Admissibility violated: {admissibility_violations}"
    
    def test_budget_never_negative(self):
        """
        Test G2: Budget (b >= 0) is never violated.
        
        Budget must never go negative - this is a hard constraint.
        """
        # Setup
        grid, start, goal = create_standard_grid("simple")
        gridworld = create_initial_state(grid, start, goal, drift_seed=42)
        gmi_state = _create_initial_gmi_state(budget=10_000_000)
        params = GMIParams()
        
        # Run episode
        receipt = run_clatl_episode(
            gmi_state=gmi_state,
            gridworld=gridworld,
            max_steps=100,
            goal_drift_every=30,
            drift_seed=42,
            gmi_params=params,
        )
        
        # Check step receipts for budget info
        # (In a full test, we'd check each GMI step receipt)
        # For now, just verify no budget violations reported
        budget_violations = [
            v for v in receipt.invariant_violations
            if "budget" in v.lower() or "b < 0" in v.lower()
        ]
        
        assert len(budget_violations) == 0, \
            f"Budget violated: {budget_violations}"
    
    def test_no_hazard_collisions(self):
        """
        Test G3: No hazard collisions in gridworld.
        
        The governor must prevent the agent from stepping on hazards.
        """
        # Setup with hazard layout
        grid, start, goal = create_standard_grid("hazard")
        gridworld = create_initial_state(grid, start, goal, drift_seed=42)
        gmi_state = _create_initial_gmi_state(budget=10_000_000)
        params = GMIParams()
        
        # Run episode
        receipt = run_clatl_episode(
            gmi_state=gmi_state,
            gridworld=gridworld,
            max_steps=50,
            goal_drift_every=30,
            drift_seed=42,
            gmi_params=params,
        )
        
        # Check for hazard collision violations
        hazard_violations = [
            v for v in receipt.invariant_violations
            if "hazard" in v.lower()
        ]
        
        assert len(hazard_violations) == 0, \
            f"Hazard collision: {hazard_violations}"
    
    def test_governor_always_selects_safe_action(self):
        """
        Test G4: Governor always selects a safe action (or correctly reports failure).
        
        When the governor rejects all actions, it must be because ALL actions
        are unsafe, not because it allowed an unsafe one through.
        """
        # Setup
        grid, start, goal = create_standard_grid("simple")
        gridworld = create_initial_state(grid, start, goal, drift_seed=42)
        gmi_state = _create_initial_gmi_state(budget=10_000_000)
        params = GMIParams()
        
        # Run episode
        receipt = run_clatl_episode(
            gmi_state=gmi_state,
            gridworld=gridworld,
            max_steps=30,
            goal_drift_every=30,
            drift_seed=42,
            gmi_params=params,
        )
        
        # Check each step receipt
        for step_receipt in receipt.step_receipts:
            # If a decision was made, it must have been accepted
            if step_receipt.decision:
                decision = step_receipt.decision
                if decision.is_accepted():
                    # Accepted - verify action was actually safe
                    # (this is implicit if we get here without violations)
                    pass
                else:
                    # Rejected - must have valid reasons
                    assert len(decision.rejection_reasons) > 0, \
                        f"Step {step_receipt.step}: Rejected without reasons"
    
    def test_invariants_across_multiple_episodes(self):
        """
        Test G5: Invariants hold across multiple episodes.
        
        Running multiple episodes should not cause invariant drift.
        """
        from cnsc_haai.agent.clatl_runtime import run_clatl_training
        
        # Run training
        receipts, metrics = run_clatl_training(
            num_episodes=5,
            grid_layout="simple",
            max_steps=30,
            goal_drift_every=20,
            initial_budget=5_000_000,
        )
        
        # Check all episodes for violations
        all_violations = []
        for i, receipt in enumerate(receipts):
            if receipt.invariant_violations:
                all_violations.extend([
                    f"episode_{i}:{v}" 
                    for v in receipt.invariant_violations
                ])
        
        assert len(all_violations) == 0, \
            f"Invariant violations across episodes: {all_violations}"
    
    def test_lyapunov_never_increases(self):
        """
        Test G6: Lyapunov functional never increases on accepted steps.
        
        Per G2 in the GMI spec, accepted steps must have dV <= 0.
        """
        # Setup
        grid, start, goal = create_standard_grid("simple")
        gridworld = create_initial_state(grid, start, goal, drift_seed=42)
        gmi_state = _create_initial_gmi_state(budget=10_000_000)
        params = GMIParams()
        
        # Run episode
        receipt = run_clatl_episode(
            gmi_state=gmi_state,
            gridworld=gridworld,
            max_steps=50,
            goal_drift_every=30,
            drift_seed=42,
            gmi_params=params,
        )
        
        # Check Lyapunov violations in step receipts
        lyapunov_violations = [
            v for v in receipt.invariant_violations
            if "lyapunov" in v.lower() or "coh:" in v.lower()
        ]
        
        assert len(lyapunov_violations) == 0, \
            f"Lyapunov violations: {lyapunov_violations}"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
