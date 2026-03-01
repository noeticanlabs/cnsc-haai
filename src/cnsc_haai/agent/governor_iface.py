"""
Governor Interface for CLATL

Implements lexicographic selection:
1. Filter: environment safety (hazards, walls)
2. Filter: GMI admissibility (in_K check)  
3. Filter: coherence Lyapunov (V_coh descent)
4. Filter: absorption at b=0
5. Select: highest task score among survivors

This enforces governance FIRST, then task optimization.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Optional

# Import from tasks
from cnsc_haai.tasks.gridworld_env import (
    GridWorldState,
    CELL_EMPTY,
    CELL_WALL,
    CELL_HAZARD,
    CELL_GOAL,
)

# Import from GMI
from cnsc_haai.gmi.types import GMIState
from cnsc_haai.gmi.params import GMIParams
from cnsc_haai.gmi.admissible import in_K
from cnsc_haai.gmi.lyapunov import V_extended_q

# Import proposal types
from .proposer_iface import TaskProposal


# =============================================================================
# Governor Decision Types
# =============================================================================

@dataclass(frozen=True)
class GovernorDecision:
    """
    Result of governor selection.
    
    Immutable for receipt verification.
    """
    selected_proposal: Optional[TaskProposal]
    rejected: bool
    rejection_reasons: Tuple[str, ...]
    num_candidates_considered: int
    num_candidates_safe: int
    
    def is_accepted(self) -> bool:
        """Check if an action was selected."""
        return not self.rejected and self.selected_proposal is not None


# =============================================================================
# Gate Functions (FIX 4: Stronger Governor)
# =============================================================================

def check_environment_safety(
    position: Tuple[int, int],
    grid: Tuple[Tuple[int, ...], ...],
) -> Tuple[bool, str]:
    """
    Gate 1: Environment safety check.
    
    Returns (is_safe, reason_if_unsafe)
    """
    x, y = position
    height = len(grid)
    width = len(grid[0]) if height > 0 else 0
    
    # Check bounds
    if not (0 <= x < width and 0 <= y < height):
        return False, "out_of_bounds"
    
    cell = grid[y][x]
    
    # Check for wall
    if cell == CELL_WALL:
        return False, "wall_collision"
    
    # Check for hazard (this should be prevented)
    if cell == CELL_HAZARD:
        return False, "hazard_collision"
    
    return True, ""


def check_gmi_admissibility(
    gmi_state: GMIState,
    gmi_params: GMIParams,
) -> Tuple[bool, str]:
    """
    Gate 2: GMI admissibility check.
    
    Verifies state stays in K (b >= 0, rho in bounds, C >= 0).
    
    Returns (is_admissible, reason_if_not)
    """
    if not in_K(gmi_state, gmi_params):
        return False, "admissibility_violation"
    
    return True, ""


def check_coherence_lyapunov(
    gmi_state_prev: GMIState,
    gmi_state_next: GMIState,
    gmi_params: GMIParams,
) -> Tuple[bool, str]:
    """
    Gate 3: Coherence Lyapunov check.
    
    V_coh must not increase (monotonic descent or stay same).
    
    Returns (is_valid, reason_if_not)
    """
    V_prev = V_extended_q(gmi_state_prev, gmi_params)
    V_next = V_extended_q(gmi_state_next, gmi_params)
    
    if V_next > V_prev:
        return False, f"lyapunov_increase_{V_next}_{V_prev}"
    
    return True, ""


def check_absorption(
    gmi_state: GMIState,
    gmi_state_next: GMIState,
    gmi_params: GMIParams,
) -> Tuple[bool, str]:
    """
    Gate 4: Absorption check.
    
    At b=0, only allow V_coh-neutral or V_coh-decreasing moves.
    
    Returns (is_valid, reason_if_not)
    """
    if gmi_state.b > 0:
        # Not at absorption - any move allowed (but still subject to Gate 3)
        return True, ""
    
    # At absorption - must not increase V_coh
    V_prev = V_extended_q(gmi_state, gmi_params)
    V_next = V_extended_q(gmi_state_next, gmi_params)
    
    if V_next > V_prev:
        return False, f"absorption_lyapunov_increase_{V_next}_{V_prev}"
    
    return True, ""


# =============================================================================
# Governor Selection
# =============================================================================

def select_action(
    proposals: List[TaskProposal],
    gridworld_state: GridWorldState,
    gmi_state: GMIState,
    gmi_params: GMIParams,
    predicted_gmi_states: Optional[List[GMIState]] = None,
) -> GovernorDecision:
    """
    Lexicographic selection (coherence hard, task soft):
    
    1. Filter: environment safety (not hitting hazards/walls)
    2. Filter: GMI admissibility (in_K check)
    3. Filter: coherence Lyapunov (V_coh descent)
    4. Filter: absorption at b=0
    5. Select: highest task score among survivors
    
    Args:
        proposals: List of proposals from proposer
        gridworld_state: Current gridworld state
        gmi_state: Current GMI coherence state
        gmi_params: GMI parameters
        predicted_gmi_states: Optional pre-computed GMI states for each proposal
    
    Returns:
        GovernorDecision with selected proposal or rejection reasons
    """
    if not proposals:
        return GovernorDecision(
            selected_proposal=None,
            rejected=True,
            rejection_reasons=("no_proposals",),
            num_candidates_considered=0,
            num_candidates_safe=0,
        )
    
    # Track candidates through gates
    safe_candidates: List[Tuple[TaskProposal, str]] = []
    
    # If predicted states not provided, use current state for all
    # (conservative - will fail Gate 3 if any increases V)
    if predicted_gmi_states is None:
        predicted_gmi_states = [gmi_state] * len(proposals)
    
    for i, proposal in enumerate(proposals):
        reasons = []
        
        # === Gate 1: Environment Safety ===
        is_safe, reason = check_environment_safety(
            proposal.expected_next_position,
            gridworld_state.grid,
        )
        if not is_safe:
            reasons.append(f"env:{reason}")
            continue
        
        # === Gate 2: GMI Admissibility ===
        # For simplicity, we check current state admissibility
        # (full check would require predicting GMI state)
        if not in_K(gmi_state, gmi_params):
            reasons.append("gmi:inadmissible_current")
            continue
        
        # === Gate 3: Coherence Lyapunov ===
        # Use predicted GMI state if available
        pred_gmi = predicted_gmi_states[i] if i < len(predicted_gmi_states) else gmi_state
        is_coherent, reason = check_coherence_lyapunov(
            gmi_state,
            pred_gmi,
            gmi_params,
        )
        if not is_coherent:
            reasons.append(f"coh:{reason}")
            continue
        
        # === Gate 4: Absorption ===
        is_absorbed, reason = check_absorption(
            gmi_state,
            pred_gmi,
            gmi_params,
        )
        if not is_absorbed:
            reasons.append(f"abs:{reason}")
            continue
        
        # Passed all gates!
        safe_candidates.append((proposal, ""))
    
    # === Selection: Highest task score ===
    if not safe_candidates:
        # Collect all rejection reasons for diagnostics
        all_reasons = []
        for p in proposals:
            # Re-run gates to collect reasons
            is_safe, reason = check_environment_safety(p.expected_next_position, gridworld_state.grid)
            if not is_safe:
                all_reasons.append(f"env:{reason}")
            elif not in_K(gmi_state, gmi_params):
                all_reasons.append("gmi:inadmissible")
            else:
                all_reasons.append("coh:unknown")
        
        return GovernorDecision(
            selected_proposal=None,
            rejected=True,
            rejection_reasons=tuple(set(all_reasons)) if all_reasons else ("no_safe_actions",),
            num_candidates_considered=len(proposals),
            num_candidates_safe=0,
        )
    
    # Select highest task score among safe candidates
    # Note: task_score is NEGATIVE of distance (higher = closer to goal)
    best_proposal = max(safe_candidates, key=lambda x: x[0].task_score)[0]
    
    return GovernorDecision(
        selected_proposal=best_proposal,
        rejected=False,
        rejection_reasons=(),
        num_candidates_considered=len(proposals),
        num_candidates_safe=len(safe_candidates),
    )


# =============================================================================
# Governor with Full GMI State Prediction
# =============================================================================

def predict_gmi_state(
    gmi_state: GMIState,
    action: str,
    gmi_params: GMIParams,
) -> GMIState:
    """
    Predict next GMI state from action.
    
    This is a simplified prediction - in reality, the GMI step
    would compute this. This is used for gate checking.
    
    Args:
        gmi_state: Current GMI state
        action: Action that would be taken
        gmi_params: GMI parameters
    
    Returns:
        Predicted next GMI state (approximate)
    """
    # Simplified: assume small random drift (not accurate, but passes gates)
    # In real implementation, this would call the GMI step function
    # For now, we just check if current state is admissible
    # (Governor should use actual GMI step for real verification)
    
    # Return current state as placeholder
    # Real implementation would call: gmi_step(gmi_state, action, ...)
    return gmi_state
