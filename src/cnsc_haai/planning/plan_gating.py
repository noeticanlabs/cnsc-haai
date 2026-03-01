"""
Plan Gating - Safety Verification for Plans

Verifies that candidate plans satisfy safety constraints step-by-step:
- Hazard avoidance
- Admissibility bounds
- Budget feasibility

The gating function is "safety-first": unsafe plans are rejected before scoring.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional, Callable
import hashlib

# Import GMI types
from cnsc_haai.gmi.types import GMIState
from .planset_generator import Plan, PlanSet, ACTION_NAMES


# =============================================================================
# Gate Reason Codes
# =============================================================================

class GateReasonCode:
    """Reason codes for plan rejection during gating."""
    HAZARD_VIOLATION = "HAZARD_VIOLATION"
    BOUNDS_VIOLATION = "BOUNDS_VIOLATION"
    BUDGET_INFEASIBLE = "BUDGET_INFEASIBLE"
    ADMISSIBILITY_VIOLATION = "ADMISSIBILITY_VIOLATION"


# =============================================================================
# Gate Result Types
# =============================================================================

@dataclass(frozen=True)
class GateResult:
    """
    Result of gating a single plan.
    
    Immutable for receipt compatibility.
    """
    plan_index: int
    plan_hash: str
    accepted: bool
    reason_codes: Tuple[str, ...]  # Empty if accepted
    step_witnesses: Tuple[Dict, ...]  # Per-step witness data
    
    def to_dict(self) -> Dict:
        """Convert to dict for serialization."""
        return {
            "plan_index": self.plan_index,
            "plan_hash": self.plan_hash,
            "accepted": self.accepted,
            "reason_codes": list(self.reason_codes),
            "step_witnesses": list(self.step_witnesses),
        }


# =============================================================================
# Gate Functions
# =============================================================================

def check_hazard_avoidance(
    state: GMIState,
    action,
    hazard_positions: List[Tuple[int, int]],
    grid_bounds: Tuple[int, int],
) -> Tuple[bool, Optional[str]]:
    """
    Check if action leads to hazard position.
    
    Args:
        state: Current GMI state
        action: Proposed action
        hazard_positions: List of (row, col) positions that are hazards
        grid_bounds: (max_row, max_col) for the grid
    
    Returns:
        (passed: bool, reason: Optional[str])
    """
    # Compute new position based on action
    # For simplicity, use dtheta (horizontal) and drho (vertical) changes
    if not state.theta or not state.theta[0]:
        return True, None  # Can't check without position
    
    current_row = state.theta[0][0]  # This maps to grid position
    current_col = 0
    
    # Extract action delta
    if action.dtheta and action.dtheta[0]:
        current_col += action.dtheta[0][0]
    if action.drho and action.drho[0]:
        current_row += action.drho[0][0]
    
    # Check if new position is a hazard
    if (current_row, current_col) in hazard_positions:
        return False, GateReasonCode.HAZARD_VIOLATION
    
    return True, None


def check_bounds(
    state: GMIState,
    action,
    grid_bounds: Tuple[int, int],
) -> Tuple[bool, Optional[str]]:
    """
    Check if action stays within grid bounds.
    
    Args:
        state: Current GMI state
        action: Proposed action
        grid_bounds: (max_row, max_col) for the grid
    
    Returns:
        (passed: bool, reason: Optional[str])
    """
    max_row, max_col = grid_bounds
    
    if not state.theta or not state.theta[0]:
        return True, None
    
    current_row = state.theta[0][0]
    current_col = 0
    
    # Extract action delta
    if action.dtheta and action.dtheta[0]:
        current_col += action.dtheta[0][0]
    if action.drho and action.drho[0]:
        current_row += action.drho[0][0]
    
    # Check bounds
    if current_row < 0 or current_row >= max_row:
        return False, GateReasonCode.BOUNDS_VIOLATION
    if current_col < 0 or current_col >= max_col:
        return False, GateReasonCode.BOUNDS_VIOLATION
    
    return True, None


def check_budget_feasibility(
    current_budget: int,
    action_cost: int,
    planning_cost: int,
    min_budget: int = 0,
) -> Tuple[bool, Optional[str]]:
    """
    Check if budget remains feasible after action.
    
    Args:
        current_budget: Current budget (QFixed)
        action_cost: Cost of executing the action
        planning_cost: Planning cost already deducted
        min_budget: Minimum budget allowed (usually 0)
    
    Returns:
        (passed: bool, reason: Optional[str])
    """
    budget_after = current_budget - action_cost
    if budget_after < min_budget:
        return False, GateReasonCode.BUDGET_INFEASIBLE
    return True, None


def check_admissibility(
    state: GMIState,
    admissibility_check: Callable[[GMIState], bool],
) -> Tuple[bool, Optional[str]]:
    """
    Check if state is in admissible set K.
    
    Args:
        state: Current GMI state
        admissibility_check: Function that returns True if state is admissible
    
    Returns:
        (passed: bool, reason: Optional[str])
    """
    if not admissibility_check(state):
        return False, GateReasonCode.ADMISSIBILITY_VIOLATION
    return True, None


# =============================================================================
# Main Gating Functions
# =============================================================================

def gate_plan(
    plan: Plan,
    state: GMIState,
    gate_config: "GateConfig",
) -> GateResult:
    """
    Gate a single plan by checking all steps.
    
    Args:
        plan: The plan to gate
        state: Current GMI state
        gate_config: Configuration for gating
    
    Returns:
        GateResult with acceptance status and reason codes
    """
    reason_codes: List[str] = []
    witnesses: List[Dict] = []
    
    # Simulate each step of the plan
    current_state = state
    current_budget = state.b
    
    for step in range(plan.horizon):
        action = plan.actions[step]
        
        # Check hazard avoidance
        if gate_config.hazard_positions:
            passed, reason = check_hazard_avoidance(
                current_state, action,
                gate_config.hazard_positions,
                gate_config.grid_bounds,
            )
            if not passed:
                reason_codes.append(reason)
                witnesses.append({
                    "step": step,
                    "check": "hazard",
                    "passed": False,
                    "reason": reason,
                })
                # Early termination: unsafe plan
                return GateResult(
                    plan_index=-1,  # Will be set by caller
                    plan_hash=plan.plan_hash,
                    accepted=False,
                    reason_codes=tuple(reason_codes),
                    step_witnesses=tuple(witnesses),
                )
        
        # Check bounds
        passed, reason = check_bounds(
            current_state, action,
            gate_config.grid_bounds,
        )
        if not passed:
            reason_codes.append(reason)
            witnesses.append({
                "step": step,
                "check": "bounds",
                "passed": False,
                "reason": reason,
            })
            return GateResult(
                plan_index=-1,
                plan_hash=plan.plan_hash,
                accepted=False,
                reason_codes=tuple(reason_codes),
                step_witnesses=tuple(witnesses),
            )
        
        # Check budget feasibility (projected)
        passed, reason = check_budget_feasibility(
            current_budget,
            gate_config.action_cost,
            0,  # Planning cost already deducted
            gate_config.min_budget,
        )
        if not passed:
            reason_codes.append(reason)
            witnesses.append({
                "step": step,
                "check": "budget",
                "passed": False,
                "reason": reason,
            })
            return GateResult(
                plan_index=-1,
                plan_hash=plan.plan_hash,
                accepted=False,
                reason_codes=tuple(reason_codes),
                step_witnesses=tuple(witnesses),
            )
        
        # Check admissibility if checker provided
        if gate_config.admissibility_check:
            # Simulate state update (simplified)
            # In real implementation, use the dynamics model
            passed, reason = check_admissibility(
                current_state,
                gate_config.admissibility_check,
            )
            if not passed:
                reason_codes.append(reason)
                witnesses.append({
                    "step": step,
                    "check": "admissibility",
                    "passed": False,
                    "reason": reason,
                })
                return GateResult(
                    plan_index=-1,
                    plan_hash=plan.plan_hash,
                    accepted=False,
                    reason_codes=tuple(reason_codes),
                    step_witnesses=tuple(witnesses),
                )
        
        # Record witness for this step
        witnesses.append({
            "step": step,
            "check": "all",
            "passed": True,
            "current_budget": current_budget,
        })
        
        # Simulate budget decrease for next step
        current_budget -= gate_config.action_cost
    
    # All steps passed
    return GateResult(
        plan_index=-1,
        plan_hash=plan.plan_hash,
        accepted=True,
        reason_codes=(),
        step_witnesses=tuple(witnesses),
    )


def gate_planset(
    planset: PlanSet,
    state: GMIState,
    gate_config: "GateConfig",
) -> List[GateResult]:
    """
    Gate all plans in a PlanSet.
    
    Args:
        planset: The PlanSet to gate
        state: Current GMI state
        gate_config: Configuration for gating
    
    Returns:
        List of GateResult for each plan
    """
    results: List[GateResult] = []
    
    for idx, plan in enumerate(planset.plans):
        result = gate_plan(plan, state, gate_config)
        # Update plan_index
        results.append(GateResult(
            plan_index=idx,
            plan_hash=result.plan_hash,
            accepted=result.accepted,
            reason_codes=result.reason_codes,
            step_witnesses=result.step_witnesses,
        ))
    
    return results


# =============================================================================
# Gate Configuration
# =============================================================================

@dataclass(frozen=True)
class GateConfig:
    """
    Configuration for plan gating.
    
    Immutable for receipt compatibility.
    """
    hazard_positions: Tuple[Tuple[int, int], ...] = ()  # Hazard cells
    grid_bounds: Tuple[int, int] = (10, 10)  # (max_row, max_col)
    action_cost: int = 1  # Cost per action (QFixed)
    min_budget: int = 0  # Minimum budget allowed
    admissibility_check: Optional[Callable[[GMIState], bool]] = None
    
    def to_dict(self) -> Dict:
        """Convert to dict for hashing."""
        return {
            "hazard_positions": list(self.hazard_positions),
            "grid_bounds": self.grid_bounds,
            "action_cost": self.action_cost,
            "min_budget": self.min_budget,
        }
    
    def hash(self) -> str:
        """Compute hash of config."""
        config_str = str(self.to_dict())
        return hashlib.sha256(config_str.encode()).hexdigest()[:16]


def create_gate_config(
    hazard_positions: Optional[List[Tuple[int, int]]] = None,
    grid_bounds: Tuple[int, int] = (10, 10),
    action_cost: int = 1,
    min_budget: int = 0,
    admissibility_check: Optional[Callable[[GMIState], bool]] = None,
) -> GateConfig:
    """Create a GateConfig with defaults."""
    return GateConfig(
        hazard_positions=tuple(hazard_positions) if hazard_positions else (),
        grid_bounds=grid_bounds,
        action_cost=action_cost,
        min_budget=min_budget,
        admissibility_check=admissibility_check,
    )
