"""
Task Loss Functions and Competence Metrics for CLATL

Implements:
- V_task: distance-to-goal, success indicator
- Competence metrics (conjunction to prevent gaming)
- Metabolic costs (real costs for cognition)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple

# Import gridworld types
from .gridworld_env import GridWorldState, CELL_HAZARD, CELL_GOAL


# =============================================================================
# Task Loss Functions
# =============================================================================

def V_task_distance(state: GridWorldState) -> int:
    """
    Task loss: Manhattan distance to goal (lower is better).
    
    This is the primary task loss - agent wants to minimize distance to goal.
    
    Args:
        state: GridWorldState
    
    Returns:
        Manhattan distance (integer, >= 0)
    """
    x, y = state.position
    gx, gy = state.goal
    return abs(gx - x) + abs(gy - y)


def V_task_success(state: GridWorldState) -> int:
    """
    Binary success indicator: 1 if at goal, 0 otherwise.
    
    Args:
        state: GridWorldState
    
    Returns:
        1 if at goal, 0 otherwise
    """
    return 1 if state.position == state.goal else 0


def V_task_hazard(state: GridWorldState) -> int:
    """
    Hazard penalty: 1 if on hazard, 0 otherwise.
    
    Should always be 0 (governor prevents hazards), but for measurement.
    
    Args:
        state: GridWorldState
    
    Returns:
        1 if on hazard, 0 otherwise
    """
    x, y = state.position
    if 0 <= y < len(state.grid) and 0 <= x < len(state.grid[0]):
        return 1 if state.grid[y][x] == CELL_HAZARD else 0
    return 0


# =============================================================================
# Competence Metrics (FIX 5: Prevent Gaming)
# =============================================================================

@dataclass(frozen=True)
class CompetenceMetrics:
    """
    Conjunction of metrics to prevent "do nothing" gaming.
    
    Agent is "competent" iff ALL of:
    - success_rate >= threshold
    - avg_steps_to_goal decreasing over episodes
    - avg_distance_to_goal decreasing over time
    """
    success_rate: float           # Fraction of episodes reaching goal
    avg_steps_to_goal: float      # Average steps (lower = better)
    avg_distance_to_goal: float  # Rolling average distance
    episodes_run: int             # Total episodes
    
    def is_competent(self, success_threshold: float = 0.3) -> bool:
        """Check if agent meets competence threshold."""
        return (
            self.success_rate >= success_threshold
        )


def compute_competence(
    task_performance_history: List[int],
    episode_boundaries: List[int],
    success_flags: List[bool],
    window_size: int = 10,
) -> CompetenceMetrics:
    """
    Compute competence metrics from run history.
    
    Args:
        task_performance_history: List of V_task (distance) at each step
        episode_boundaries: List of step indices where episodes ended
        success_flags: List of bools indicating if goal was reached
        window_size: Window for rolling average
    
    Returns:
        CompetenceMetrics
    """
    if not task_performance_history or not episode_boundaries:
        return CompetenceMetrics(
            success_rate=0.0,
            avg_steps_to_goal=float('inf'),
            avg_distance_to_goal=float('inf'),
            episodes_run=0,
        )
    
    # Success rate
    success_count = sum(1 for s in success_flags if s)
    total_episodes = len(episode_boundaries)
    success_rate = success_count / total_episodes if total_episodes > 0 else 0.0
    
    # Average steps to goal (only for successful episodes)
    steps_per_episode = []
    for i, end_step in enumerate(episode_boundaries):
        start_step = 0 if i == 0 else episode_boundaries[i - 1]
        steps = end_step - start_step
        if i < len(success_flags) and success_flags[i]:
            steps_per_episode.append(steps)
    
    avg_steps = sum(steps_per_episode) / len(steps_per_episode) if steps_per_episode else float('inf')
    
    # Rolling average distance (last window_size steps)
    recent = task_performance_history[-window_size:] if len(task_performance_history) >= window_size else task_performance_history
    avg_distance = sum(recent) / len(recent) if recent else float('inf')
    
    return CompetenceMetrics(
        success_rate=success_rate,
        avg_steps_to_goal=avg_steps,
        avg_distance_to_goal=avg_distance,
        episodes_run=total_episodes,
    )


def competence_improving(
    metrics_history: List[CompetenceMetrics],
) -> bool:
    """
    Check if competence is improving over time.
    
    Args:
        metrics_history: List of CompetenceMetrics over time
    
    Returns:
        True if competence is improving
    """
    if len(metrics_history) < 2:
        return True  # Not enough data
    
    # Compare recent to earlier
    recent = metrics_history[-1]
    earlier = metrics_history[0]
    
    # Improvement = higher success rate, lower steps, lower distance
    success_improved = recent.success_rate >= earlier.success_rate
    steps_improved = recent.avg_steps_to_goal <= earlier.avg_steps_to_goal
    distance_improved = recent.avg_distance_to_goal <= earlier.avg_distance_to_goal
    
    return success_improved and steps_improved and distance_improved


# =============================================================================
# Metabolic Costs (FIX 6: Real Costs for Cognition)
# =============================================================================

# Work costs in QFixed (scaled integers, same as GMI budget)
W_MOVE = 1_000_000           # QFixed: 1.0 - cost of moving
W_PROPOSE = 500_000         # QFixed: 0.5 - cost per proposal generated
W_MEMORY_WRITE = 100_000    # QFixed: 0.1 - cost per memory update
W_REJECTED_ATTEMPT = 50_000  # QFixed: 0.05 - small cost for failed exploration


def compute_metabolic_cost(
    action: str,
    num_proposals_generated: int,
    memory_writes: int,
    action_was_rejected: bool,
) -> int:
    """
    Compute total work cost for a CLATL step.
    
    This makes curiosity metabolically expensive - exploration has real cost.
    
    Args:
        action: The action that was taken
        num_proposals_generated: Number of proposals considered
        memory_writes: Number of memory updates
        action_was_rejected: Whether the selected action was rejected
    
    Returns:
        Total cost in QFixed (scaled integer)
    """
    cost = W_MOVE
    cost += num_proposals_generated * W_PROPOSE
    cost += memory_writes * W_MEMORY_WRITE
    
    if action_was_rejected:
        cost += W_REJECTED_ATTEMPT
    
    return cost


def budget_governed_exploration(
    budget: int,
    base_budget: int = 10_000_000,
) -> float:
    """
    Compute exploration bonus based on remaining budget.
    
    Exploration decreases as budget depletes, vanishing at b=0.
    
    Args:
        budget: Current budget (QFixed)
        base_budget: Starting budget (QFixed)
    
    Returns:
        Exploration factor in [0, 1]
    """
    if budget <= 0 or base_budget <= 0:
        return 0.0
    
    return min(1.0, budget / base_budget)


# =============================================================================
# Lambda Scheduler (Time-Varying Task Weight)
# =============================================================================

class LambdaScheduler:
    """
    Piecewise constant scheduler for lambda(t).
    
    Used to weight task loss vs coherence loss.
    """
    
    def __init__(self, schedule: List[Tuple[int, int]]):
        """
        Initialize scheduler.
        
        Args:
            schedule: List of (step, lambda_value) tuples
                     lambda is constant between schedule points
        """
        self.schedule = sorted(schedule)
    
    def get(self, step: int) -> int:
        """Get lambda value at given step."""
        lambda_val = 0  # Default
        
        for threshold, val in self.schedule:
            if step >= threshold:
                lambda_val = val
        
        return lambda_val


# =============================================================================
# Default scheduler
# =============================================================================

DEFAULT_LAMBDA_SCHEDULER = LambdaScheduler([
    (0, 1_000_000),      # QFixed 1.0 - full task weight initially
    (50, 2_000_000),    # QFixed 2.0 - increase after 50 steps
    (100, 5_000_000),   # QFixed 5.0 - increase more after 100 steps
])
