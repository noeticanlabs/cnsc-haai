"""
PlanSet Generator - Deterministic Plan Generation

Generates candidate plans using mixed-radix indexing with hash-based action selection.
Each plan is a finite action sequence of length H.

Key features:
- Deterministic: same seed + params -> same planset
- Diverse: hash-based action selection spreads across action space
- Special plans: greedy, wall-follow, backtrack, stay
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Optional
import hashlib

# Import GMI types for action representation
from cnsc_haai.gmi.types import GMIAction


# =============================================================================
# Action Constants (must match model/dynamics.py)
# =============================================================================

ACTION_DIM = 5  # N, S, E, W, Stay

# Action deltas for gridworld (drho, dtheta)
# These map to: 0=N, 1=S, 2=E, 3=W, 4=Stay
ACTION_DELTAS = [
    ([0, 0], [1, 0]),   # N: rho increases (up in grid)
    ([0, 0], [-1, 0]),  # S: rho decreases
    ([0, 0], [0, 1]),   # E: theta increases (right)
    ([0, 0], [0, -1]),  # W: theta decreases (left)
    ([0, 0], [0, 0]),   # Stay: no change
]

ACTION_NAMES = ["N", "S", "E", "W", "Stay"]


# =============================================================================
# Plan Types
# =============================================================================

@dataclass(frozen=True)
class Plan:
    """
    A plan is a finite action sequence of fixed horizon H.
    
    Immutable for receipt compatibility.
    """
    actions: Tuple[GMIAction, ...]
    horizon: int
    plan_hash: str  # Deterministic hash for Merkle inclusion
    
    def __post_init__(self):
        """Validate plan structure."""
        if len(self.actions) != self.horizon:
            raise ValueError(f"Actions length {len(self.actions)} != horizon {self.horizon}")
        if self.horizon <= 0:
            raise ValueError(f"Horizon must be positive, got {self.horizon}")


@dataclass(frozen=True)
class PlanSet:
    """
    A set of candidate plans generated at a single timestep.
    """
    plans: Tuple[Plan, ...]
    horizon: int
    seed: int
    planset_hash: str  # Hash of all plans for commitment
    
    def __post_init__(self):
        """Validate planset."""
        if not self.plans:
            raise ValueError("PlanSet cannot be empty")
        if len(self.plans) > 1000:
            raise ValueError(f"PlanSet too large: {len(self.plans)}")


# =============================================================================
# Helper Functions
# =============================================================================

def _compute_plan_hash(actions: List[GMIAction]) -> str:
    """Compute deterministic hash of a plan's actions."""
    # Serialize actions to bytes
    action_bytes = b""
    for a in actions:
        drho_str = "".join(str(x) for row in a.drho for x in row)
        dtheta_str = "".join(str(x) for row in a.dtheta for x in row)
        action_bytes += drho_str.encode() + dtheta_str.encode()
    
    return hashlib.sha256(action_bytes).hexdigest()[:16]


def _create_action(action_index: int) -> GMIAction:
    """Create a GMIAction from an action index (0-4)."""
    if action_index < 0 or action_index >= ACTION_DIM:
        raise ValueError(f"Action index {action_index} out of range [0, {ACTION_DIM})")
    
    drho, dtheta = ACTION_DELTAS[action_index]
    return GMIAction(drho=[list(drho)], dtheta=[list(dtheta)])


def _hash_action_index(plan_idx: int, step: int, seed: int) -> int:
    """
    Hash-based action selection for deterministic generation.
    
    Uses SHA256 to get deterministic but seemingly random action indices.
    """
    combined = f"{plan_idx}:{step}:{seed}".encode()
    hash_bytes = hashlib.sha256(combined).digest()
    # Use first 2 bytes as integer, modulo action dimension
    return int.from_bytes(hash_bytes[:2], 'big') % ACTION_DIM


# =============================================================================
# Plan Generation
# =============================================================================

def generate_planset(
    horizon: int,
    num_plans: int,
    seed: int,
    include_special_plans: bool = True,
) -> PlanSet:
    """
    Generate a deterministic PlanSet.
    
    Args:
        horizon: Length of each plan (H)
        num_plans: Number of candidate plans to generate (m)
        seed: Seed for deterministic generation
        include_special_plans: Whether to include greedy/wall-follow/stay plans
    
    Returns:
        PlanSet with deterministic plans
    """
    if horizon <= 0:
        raise ValueError(f"Horizon must be positive, got {horizon}")
    if num_plans <= 0:
        raise ValueError(f"num_plans must be positive, got {num_plans}")
    
    plans: List[Plan] = []
    
    # Generate hash-based plans
    for plan_idx in range(num_plans):
        actions: List[GMIAction] = []
        for step in range(horizon):
            action_idx = _hash_action_index(plan_idx, step, seed)
            actions.append(_create_action(action_idx))
        
        plan_hash = _compute_plan_hash(actions)
        plans.append(Plan(
            actions=tuple(actions),
            horizon=horizon,
            plan_hash=plan_hash,
        ))
    
    # Add special plans if requested
    if include_special_plans:
        # Add greedy plan (always choose best 1-step action)
        # Note: This is a placeholder - actual greedy would use model
        greedy_actions = [_create_action(0)] * horizon  # Default to N
        plans.append(Plan(
            actions=tuple(greedy_actions),
            horizon=horizon,
            plan_hash=_compute_plan_hash(greedy_actions),
        ))
        
        # Add stay plan (important for absorption)
        stay_actions = [_create_action(4)] * horizon
        plans.append(Plan(
            actions=tuple(stay_actions),
            horizon=horizon,
            plan_hash=_compute_plan_hash(stay_actions),
        ))
    
    # Compute planset hash
    plans_bytes = b"".join(p.plan_hash.encode() for p in plans)
    planset_hash = hashlib.sha256(plans_bytes).hexdigest()[:16]
    
    return PlanSet(
        plans=tuple(plans),
        horizon=horizon,
        seed=seed,
        planset_hash=planset_hash,
    )


def generate_single_plan(horizon: int, seed: int) -> Plan:
    """Generate a single plan (for quick testing)."""
    planset = generate_planset(horizon, 1, seed, include_special_plans=False)
    return planset.plans[0]


# =============================================================================
# Budget-Adaptive Planning
# =============================================================================

def compute_adaptive_params(
    budget: int,
    m_max: int = 20,
    H_max: int = 10,
    b_unit: int = 100,
    h_unit: int = 50,
) -> Tuple[int, int]:
    """
    Compute adaptive m and H based on remaining budget.
    
    Budget-adaptive formula:
        m = min(m_max, 1 + b // b_unit)
        H = min(H_max, 1 + b // h_unit)
    
    Args:
        budget: Current budget (QFixed)
        m_max: Maximum number of plans
        H_max: Maximum horizon
        b_unit: Budget unit for plan count scaling
        h_unit: Budget unit for horizon scaling
    
    Returns:
        (m, H) tuple
    """
    m = min(m_max, 1 + budget // b_unit)
    H = min(H_max, 1 + budget // h_unit)
    return max(1, m), max(1, H)
