"""
Plan Scoring - J(Pi) Computation

Computes the cost function for admissible plans:
J(Pi) = sum_h [lambda_T * V_task + lambda_C * CurvPenalty - alpha(b) * InfoGain] + lambda_F * V_task_final

Where:
- V_task: Task loss (e.g., distance to goal)
- CurvPenalty: Penalty for hazard-proximal trajectories
- InfoGain: Optional exploration bonus
- alpha(b): Budget-dependent coefficient (alpha(0) = 0)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Callable
import hashlib

# Import GMI types
from cnsc_haai.gmi.types import GMIState
from .planset_generator import Plan, PlanSet, ACTION_NAMES


# =============================================================================
# Scoring Configuration
# =============================================================================

@dataclass(frozen=True)
class ScoringConfig:
    """
    Configuration for plan scoring.
    
    Immutable for receipt compatibility.
    """
    lambda_task: int = 1000     # Weight for task loss
    lambda_curvature: int = 100  # Weight for curvature penalty
    lambda_final: int = 500      # Weight for final state task loss
    alpha_base: int = 10         # Base for info gain coefficient
    use_info_gain: bool = False  # Whether to use info gain
    
    def to_dict(self) -> Dict:
        """Convert to dict for hashing."""
        return {
            "lambda_task": self.lambda_task,
            "lambda_curvature": self.lambda_curvature,
            "lambda_final": self.lambda_final,
            "alpha_base": self.alpha_base,
            "use_info_gain": self.use_info_gain,
        }
    
    def hash(self) -> str:
        """Compute hash of config."""
        config_str = str(self.to_dict())
        return hashlib.sha256(config_str.encode()).hexdigest()[:16]


def create_scoring_config(
    lambda_task: int = 1000,
    lambda_curvature: int = 100,
    lambda_final: int = 500,
    alpha_base: int = 10,
    use_info_gain: bool = False,
) -> ScoringConfig:
    """Create a ScoringConfig with defaults."""
    return ScoringConfig(
        lambda_task=lambda_task,
        lambda_curvature=lambda_curvature,
        lambda_final=lambda_final,
        alpha_base=alpha_base,
        use_info_gain=use_info_gain,
    )


# =============================================================================
# Task Loss Functions
# =============================================================================

def compute_task_loss(
    state: GMIState,
    goal_position: Tuple[int, int],
) -> int:
    """
    Compute task loss (distance to goal).
    
    Uses Manhattan distance in grid coordinates.
    Returns QFixed scaled integer.
    """
    # Extract position from state
    # For simplicity, use theta[0][0] as row, theta[0][1] as col (if exists)
    if not state.theta or not state.theta[0]:
        return 0
    
    row = state.theta[0][0]
    col = state.theta[0][1] if len(state.theta[0]) > 1 else 0
    
    # Manhattan distance to goal
    distance = abs(row - goal_position[0]) + abs(col - goal_position[1])
    
    # Scale to QFixed (assume factor of 1 for now)
    return distance


def compute_curvature_penalty(
    state: GMIState,
    hazard_mask: List[List[int]],
    curvature_threshold: int = 5,
) -> int:
    """
    Compute curvature penalty for hazard proximity.
    
    Higher curvature near hazards = higher penalty.
    Returns QFixed scaled integer.
    """
    if not hazard_mask:
        return 0
    
    # Extract position
    if not state.theta or not state.theta[0]:
        return 0
    
    row = state.theta[0][0]
    col = state.theta[0][1] if len(state.theta[0]) > 1 else 0
    
    # Check if position is valid in hazard mask
    if row < 0 or row >= len(hazard_mask) or col < 0 or col >= len(hazard_mask[0]):
        return 0
    
    # Get curvature at current position
    curvature = state.C[0][0] if state.C and state.C[0] else 0
    
    # Get hazard value
    hazard_value = hazard_mask[row][col]
    
    # Penalty: curvature * hazard proximity
    # Higher curvature near hazards = worse
    if hazard_value > 0:
        return curvature * hazard_value
    
    return 0


def compute_info_gain(
    state: GMIState,
    model,  # Dynamics model for ensemble disagreement
) -> int:
    """
    Compute info gain as ensemble disagreement.
    
    Optional: for exploration bonus.
    Returns QFixed scaled integer.
    """
    # Simplified: return 0 if no model
    # In full implementation, would use ensemble of models
    return 0


def compute_alpha(budget: int, alpha_base: int) -> int:
    """
    Compute alpha(b) coefficient.
    
    alpha(b) is monotone with alpha(0) = 0.
    Simple linear function: alpha(b) = alpha_base * b / max_budget
    """
    if budget <= 0:
        return 0
    # Simple: alpha = alpha_base * sign(budget)
    return alpha_base


# =============================================================================
# Main Scoring Functions
# =============================================================================

def score_plan(
    plan: Plan,
    state: GMIState,
    scoring_config: ScoringConfig,
    goal_position: Tuple[int, int],
    hazard_mask: Optional[List[List[int]]] = None,
    dynamics_model=None,
) -> int:
    """
    Compute J(Pi) cost for a single plan.
    
    J(Pi) = sum_h [lambda_T * V_task + lambda_C * CurvPenalty - alpha(b) * InfoGain] + lambda_F * V_task_final
    
    Args:
        plan: The plan to score
        state: Current GMI state
        scoring_config: Scoring configuration
        goal_position: Target position (row, col)
        hazard_mask: Optional hazard grid
        dynamics_model: Optional model for info gain
    
    Returns:
        J(Pi) cost (lower is better, QFixed)
    """
    total_cost = 0
    current_state = state
    budget = state.b
    
    # Compute alpha(budget) for info gain
    alpha = compute_alpha(budget, scoring_config.alpha_base)
    
    # Score each step
    for step in range(plan.horizon):
        # Task loss (distance to goal)
        task_loss = compute_task_loss(current_state, goal_position)
        
        # Curvature penalty
        curv_penalty = 0
        if hazard_mask:
            curv_penalty = compute_curvature_penalty(current_state, hazard_mask)
        
        # Info gain (optional)
        info_gain = 0
        if scoring_config.use_info_gain and dynamics_model:
            info_gain = compute_info_gain(current_state, dynamics_model)
        
        # Step cost
        step_cost = (
            scoring_config.lambda_task * task_loss +
            scoring_config.lambda_curvature * curv_penalty -
            alpha * info_gain
        )
        
        total_cost += step_cost
        
        # Update state (simplified - would use dynamics model)
        # For now, just advance
        # In full impl: current_state = model.predict(current_state, action)
    
    # Final state task loss
    final_task_loss = compute_task_loss(current_state, goal_position)
    total_cost += scoring_config.lambda_final * final_task_loss
    
    return total_cost


def score_planset(
    planset: PlanSet,
    state: GMIState,
    scoring_config: ScoringConfig,
    goal_position: Tuple[int, int],
    hazard_mask: Optional[List[List[int]]] = None,
    dynamics_model=None,
) -> List[Tuple[int, int]]:
    """
    Score all plans in a PlanSet.
    
    Args:
        planset: The PlanSet to score
        state: Current GMI state
        scoring_config: Scoring configuration
        goal_position: Target position
        hazard_mask: Optional hazard grid
        dynamics_model: Optional model
    
    Returns:
        List of (plan_index, score) tuples, sorted by score (ascending)
    """
    scores: List[Tuple[int, int]] = []
    
    for idx, plan in enumerate(planset.plans):
        score = score_plan(
            plan, state, scoring_config,
            goal_position, hazard_mask, dynamics_model
        )
        scores.append((idx, score))
    
    # Sort by score (lower is better)
    scores.sort(key=lambda x: (x[1], x[0]))
    
    return scores


def get_best_admissible_plan(
    planset: PlanSet,
    gate_results: List["GateResult"],
    state: GMIState,
    scoring_config: ScoringConfig,
    goal_position: Tuple[int, int],
    hazard_mask: Optional[List[List[int]]] = None,
    dynamics_model=None,
) -> Optional[Tuple[int, Plan, int]]:
    """
    Get the best admissible plan (passed gating).
    
    Args:
        planset: The PlanSet
        gate_results: Results from gating
        state: Current GMI state
        scoring_config: Scoring configuration
        goal_position: Target position
        hazard_mask: Optional hazard grid
        dynamics_model: Optional model
    
    Returns:
        (plan_index, plan, score) or None if no admissible plans
    """
    # Filter to admissible plans
    admissible: List[Tuple[int, Plan]] = []
    for idx, gate_result in enumerate(gate_results):
        if gate_result.accepted and idx < len(planset.plans):
            admissible.append((idx, planset.plans[idx]))
    
    if not admissible:
        return None
    
    # Score each admissible plan
    scored: List[Tuple[int, Plan, int]] = []
    for idx, plan in admissible:
        score = score_plan(
            plan, state, scoring_config,
            goal_position, hazard_mask, dynamics_model
        )
        scored.append((idx, plan, score))
    
    # Sort by score (lower is better)
    scored.sort(key=lambda x: (x[2], x[0]))
    
    return scored[0]  # Return best
