"""
Planner MPC - Main Model Predictive Control Planning Entry Point

This module implements the main planning loop:
1. Generate PlanSet (deterministic)
2. Commit PlanSet (Merkle root)
3. Gate each plan (safety-first)
4. Score admissible plans
5. Tie-break if needed
6. Return first action + receipts

Budget-adaptive planning:
- m = min(m_max, 1 + b // b_unit)
- H = min(H_max, 1 + b // h_unit)

Absorption rule:
- If b == 0, only "Stay" action allowed, planning disabled
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any
import hashlib
import json

# Import GMI types
from cnsc_haai.gmi.types import GMIState, GMIAction

# Import planning modules
from .planset_generator import (
    Plan, PlanSet, generate_planset, compute_adaptive_params, ACTION_NAMES
)
from .plan_gating import GateResult, GateConfig, gate_planset, create_gate_config
from .plan_scoring import (
    ScoringConfig, score_plan, score_planset, get_best_admissible_plan,
    create_scoring_config
)
from .plan_receipts import (
    PlanSetReceipt, PlanDecisionReceipt, GateWitnessReceipt, PlanReceiptBundle,
    create_planset_receipt, create_plan_decision_receipt, create_gate_witness_receipt,
    GateWitnessStep
)
from .plan_merkle import build_plan_merkle_root, verify_plan_membership
from .tie_break import tie_break_plans


# =============================================================================
# Planner Configuration
# =============================================================================

@dataclass(frozen=True)
class PlannerConfig:
    """
    Configuration for the MPC planner.
    
    Immutable for receipt compatibility.
    """
    # Planning parameters
    m_max: int = 20              # Maximum number of plans
    H_max: int = 10              # Maximum horizon
    b_unit: int = 100            # Budget unit for plan count scaling
    h_unit: int = 50             # Budget unit for horizon scaling
    
    # Cost weights (scoring)
    lambda_task: int = 1000
    lambda_curvature: int = 100
    lambda_final: int = 500
    alpha_base: int = 10
    use_info_gain: bool = False
    
    # Gate config
    hazard_positions: Tuple[Tuple[int, int], ...] = ()
    grid_bounds: Tuple[int, int] = (10, 10)
    action_cost: int = 1
    min_budget: int = 0
    
    # Planning cost constants
    kappa_plan: int = 1          # Cost per plan-horizon unit
    kappa_gate: int = 0          # Cost per gate check
    kappa_exec: int = 1           # Cost per execution
    
    def to_dict(self) -> Dict:
        """Convert to dict for hashing."""
        return {
            "m_max": self.m_max,
            "H_max": self.H_max,
            "b_unit": self.b_unit,
            "h_unit": self.h_unit,
            "lambda_task": self.lambda_task,
            "lambda_curvature": self.lambda_curvature,
            "lambda_final": self.lambda_final,
            "alpha_base": self.alpha_base,
            "use_info_gain": self.use_info_gain,
            "hazard_positions": list(self.hazard_positions),
            "grid_bounds": self.grid_bounds,
            "action_cost": self.action_cost,
            "min_budget": self.min_budget,
            "kappa_plan": self.kappa_plan,
            "kappa_gate": self.kappa_gate,
            "kappa_exec": self.kappa_exec,
        }
    
    def hash(self) -> str:
        """Compute hash of config."""
        config_str = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()[:16]
    
    def compute_planning_cost(self, m: int, H: int) -> int:
        """
        Compute planning cost: W_plan = kappa_plan * m * H + kappa_gate * m + kappa_exec
        """
        return self.kappa_plan * m * H + self.kappa_gate * m + self.kappa_exec


def create_planner_config(
    m_max: int = 20,
    H_max: int = 10,
    b_unit: int = 100,
    h_unit: int = 50,
    lambda_task: int = 1000,
    lambda_curvature: int = 100,
    lambda_final: int = 500,
    alpha_base: int = 10,
    use_info_gain: bool = False,
    hazard_positions: Optional[List[Tuple[int, int]]] = None,
    grid_bounds: Tuple[int, int] = (10, 10),
    action_cost: int = 1,
    min_budget: int = 0,
    kappa_plan: int = 1,
    kappa_gate: int = 0,
    kappa_exec: int = 1,
) -> PlannerConfig:
    """Create a PlannerConfig with defaults."""
    return PlannerConfig(
        m_max=m_max,
        H_max=H_max,
        b_unit=b_unit,
        h_unit=h_unit,
        lambda_task=lambda_task,
        lambda_curvature=lambda_curvature,
        lambda_final=lambda_final,
        alpha_base=alpha_base,
        use_info_gain=use_info_gain,
        hazard_positions=tuple(hazard_positions) if hazard_positions else (),
        grid_bounds=grid_bounds,
        action_cost=action_cost,
        min_budget=min_budget,
        kappa_plan=kappa_plan,
        kappa_gate=kappa_gate,
        kappa_exec=kappa_exec,
    )


# =============================================================================
# Planning Result Types
# =============================================================================

@dataclass
class PlanningResult:
    """
    Result of a planning step.
    """
    action: GMIAction
    action_name: str
    chosen_plan: Plan
    chosen_plan_index: int
    planning_cost: int
    budget_after_planning: int
    receipts: PlanReceiptBundle


@dataclass(frozen=True)
class PlanningReceipts:
    """
    Receipts from planning.
    """
    planset_receipt: PlanSetReceipt
    decision_receipt: PlanDecisionReceipt
    witness_receipt: Optional[GateWitnessReceipt] = None


# =============================================================================
# Main Planning Function
# =============================================================================

def plan_and_select(
    state: GMIState,
    planner_config: PlannerConfig,
    goal_position: Tuple[int, int],
    hazard_mask: Optional[List[List[int]]] = None,
    dynamics_model: Any = None,
    seed: Optional[int] = None,
) -> PlanningResult:
    """
    Main MPC planning function.
    
    At each timestep:
    1. Generate PlanSet (deterministic)
    2. Commit PlanSet (Merkle root)
    3. Gate each plan (safety-first)
    4. Score admissible plans
    5. Tie-break if needed
    6. Return first action + receipts
    
    Args:
        state: Current GMI state
        planner_config: Planner configuration
        goal_position: Target position (row, col)
        hazard_mask: Optional hazard grid
        dynamics_model: Optional dynamics model for rollouts
        seed: Optional seed (defaults to state.t)
    
    Returns:
        PlanningResult with action and receipts
    
    Raises:
        ValueError: If no admissible plans or budget exhausted
    """
    # Handle absorption: if budget is 0, only Stay allowed
    if state.b <= 0:
        # Create Stay action
        stay_action = GMIAction(drho=[[0, 0]], dtheta=[[0, 0]])
        
        # Create minimal receipts
        # Note: In absorption mode, we don't need full receipts
        return PlanningResult(
            action=stay_action,
            action_name="Stay",
            chosen_plan=None,  # No plan in absorption mode
            chosen_plan_index=-1,
            planning_cost=0,
            budget_after_planning=0,
            receipts=None,
        )
    
    # Compute adaptive parameters based on budget
    m, H = compute_adaptive_params(
        budget=state.b,
        m_max=planner_config.m_max,
        H_max=planner_config.H_max,
        b_unit=planner_config.b_unit,
        h_unit=planner_config.h_unit,
    )
    
    # Determine seed (deterministic)
    if seed is None:
        seed = state.t
    
    # Step 1: Generate PlanSet
    planset = generate_planset(
        horizon=H,
        num_plans=m,
        seed=seed,
        include_special_plans=True,
    )
    
    # Step 2: Commit PlanSet (build Merkle root)
    planset_root = build_plan_merkle_root(planset)
    
    # Compute planning cost
    planning_cost = planner_config.compute_planning_cost(m, H)
    budget_after_planning = state.b - planning_cost
    
    # Check if we can afford planning
    if budget_after_planning < planner_config.min_budget:
        # Not enough budget for planning - fall back to Stay
        stay_action = GMIAction(drho=[[0, 0]], dtheta=[[0, 0]])
        return PlanningResult(
            action=stay_action,
            action_name="Stay",
            chosen_plan=None,
            chosen_plan_index=-1,
            planning_cost=0,
            budget_after_planning=state.b,
            receipts=None,
        )
    
    # Create configs
    gate_config = create_gate_config(
        hazard_positions=list(planner_config.hazard_positions),
        grid_bounds=planner_config.grid_bounds,
        action_cost=planner_config.action_cost,
        min_budget=planner_config.min_budget,
    )
    
    scoring_config = create_scoring_config(
        lambda_task=planner_config.lambda_task,
        lambda_curvature=planner_config.lambda_curvature,
        lambda_final=planner_config.lambda_final,
        alpha_base=planner_config.alpha_base,
        use_info_gain=planner_config.use_info_gain,
    )
    
    # Step 3: Gate each plan
    gate_results = gate_planset(planset, state, gate_config)
    
    # Collect rejection reason codes
    rejection_counts: Dict[str, int] = {}
    for result in gate_results:
        if not result.accepted:
            for reason in result.reason_codes:
                rejection_counts[reason] = rejection_counts.get(reason, 0) + 1
    
    # Step 4: Get best admissible plan
    best = get_best_admissible_plan(
        planset=planset,
        gate_results=gate_results,
        state=state,
        scoring_config=scoring_config,
        goal_position=goal_position,
        hazard_mask=hazard_mask,
        dynamics_model=dynamics_model,
    )
    
    # Handle case with no admissible plans
    if best is None:
        # No admissible plans - must use Stay
        stay_action = GMIAction(drho=[[0, 0]], dtheta=[[0, 0]])
        
        # Create receipts even for fallback
        planset_receipt = create_planset_receipt(
            t=state.t,
            env_state_hash="",  # Would be provided by environment
            gmi_state_hash="",   # Would be computed from state
            planner_config_hash=planner_config.hash(),
            seed=seed,
            planset_root=planset_root,
            plans_count=len(planset.plans),
            horizon=H,
        )
        
        decision_receipt = create_plan_decision_receipt(
            t=state.t,
            planset_root=planset_root,
            chosen_plan_index=-1,
            chosen_plan_hash="",
            gate_reason_codes_summary=rejection_counts,
            chosen_action_index=4,  # Stay
            chosen_action="Stay",
            predicted_cost_J=0,
            budget_before_planning=state.b,
            budget_after_planning=budget_after_planning,
        )
        
        return PlanningResult(
            action=stay_action,
            action_name="Stay",
            chosen_plan=None,
            chosen_plan_index=-1,
            planning_cost=planning_cost,
            budget_after_planning=budget_after_planning,
            receipts=PlanReceiptBundle(
                planset_receipt=planset_receipt,
                decision_receipt=decision_receipt,
                witness_receipt=None,
            ),
        )
    
    # Unpack best result
    chosen_idx, chosen_plan, predicted_cost = best
    
    # Step 5: Get first action from chosen plan
    first_action = chosen_plan.actions[0]
    action_name = "Stay"  # Default
    
    # Determine action name from delta
    if first_action.dtheta and first_action.dtheta[0]:
        dtheta_val = first_action.dtheta[0][0]
        if dtheta_val == 1:
            action_name = "N"
        elif dtheta_val == -1:
            action_name = "S"
        elif len(first_action.dtheta[0]) > 1:
            if first_action.dtheta[0][1] == 1:
                action_name = "E"
            elif first_action.dtheta[0][1] == -1:
                action_name = "W"
            elif first_action.dtheta[0][1] == 0:
                action_name = "Stay"
    
    # Find action index
    action_index = 4  # Stay default
    if first_action.dtheta and first_action.dtheta[0]:
        if first_action.dtheta[0][0] == 1:
            action_index = 0  # N
        elif first_action.dtheta[0][0] == -1:
            action_index = 1  # S
        elif len(first_action.dtheta[0]) > 1:
            if first_action.dtheta[0][1] == 1:
                action_index = 2  # E
            elif first_action.dtheta[0][1] == -1:
                action_index = 3  # W
    
    # Step 6: Create receipts
    planset_receipt = create_planset_receipt(
        t=state.t,
        env_state_hash="",  # Would be provided by environment
        gmi_state_hash="",  # Would be computed from state
        planner_config_hash=planner_config.hash(),
        seed=seed,
        planset_root=planset_root,
        plans_count=len(planset.plans),
        horizon=H,
    )
    
    decision_receipt = create_plan_decision_receipt(
        t=state.t,
        planset_root=planset_root,
        chosen_plan_index=chosen_idx,
        chosen_plan_hash=chosen_plan.plan_hash,
        gate_reason_codes_summary=rejection_counts,
        chosen_action_index=action_index,
        chosen_action=action_name,
        predicted_cost_J=predicted_cost,
        budget_before_planning=state.b,
        budget_after_planning=budget_after_planning,
    )
    
    # Get gate witness for chosen plan
    chosen_gate_result = gate_results[chosen_idx] if chosen_idx < len(gate_results) else None
    witness_steps: List[GateWitnessStep] = []
    if chosen_gate_result:
        for witness in chosen_gate_result.step_witnesses:
            witness_steps.append(GateWitnessStep(
                step=witness.get("step", 0),
                predicted_state_hash="",  # Would be computed from predicted state
                safety_check_passed=witness.get("passed", True),
                hazard_proximity=0,
                budget_after_step=witness.get("current_budget", state.b),
            ))
    
    witness_receipt = create_gate_witness_receipt(
        t=state.t,
        chosen_plan_hash=chosen_plan.plan_hash,
        witness_steps=witness_steps,
    )
    
    return PlanningResult(
        action=first_action,
        action_name=action_name,
        chosen_plan=chosen_plan,
        chosen_plan_index=chosen_idx,
        planning_cost=planning_cost,
        budget_after_planning=budget_after_planning,
        receipts=PlanReceiptBundle(
            planset_receipt=planset_receipt,
            decision_receipt=decision_receipt,
            witness_receipt=witness_receipt,
        ),
    )


# =============================================================================
# Utility Functions
# =============================================================================

def is_planning_enabled(state: GMIState, min_budget: int = 10) -> bool:
    """
    Check if planning is enabled based on budget.
    
    Args:
        state: Current GMI state
        min_budget: Minimum budget required for planning
    
    Returns:
        True if planning is enabled
    """
    return state.b > min_budget


def get_planning_budget_estimate(
    planner_config: PlannerConfig,
    budget: int,
) -> Tuple[int, int, int]:
    """
    Estimate planning parameters and cost for given budget.
    
    Returns:
        (m, H, estimated_cost)
    """
    m, H = compute_adaptive_params(
        budget=budget,
        m_max=planner_config.m_max,
        H_max=planner_config.H_max,
        b_unit=planner_config.b_unit,
        h_unit=planner_config.h_unit,
    )
    cost = planner_config.compute_planning_cost(m, H)
    return m, H, cost
