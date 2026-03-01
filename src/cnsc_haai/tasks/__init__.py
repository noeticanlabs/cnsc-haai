"""
CLATL Task Layer

Implements the adaptive task layer for the GMI system.
Includes deterministic environments and task loss functions.
"""

from .gridworld_env import (
    GridWorldState,
    GridWorldObs,
    CELL_EMPTY,
    CELL_WALL,
    CELL_HAZARD,
    CELL_GOAL,
    create_gridworld,
    create_initial_state,
    env_step,
    get_observation,
    drift_goal,
    hash_gridworld_state,
)
from .task_loss import (
    V_task_distance,
    V_task_success,
    CompetenceMetrics,
    compute_competence,
    W_MOVE,
    W_PROPOSE,
    W_MEMORY_WRITE,
    W_REJECTED_ATTEMPT,
    compute_metabolic_cost,
)

__all__ = [
    # Gridworld
    "GridWorldState",
    "GridWorldObs",
    "CELL_EMPTY",
    "CELL_WALL",
    "CELL_HAZARD",
    "CELL_GOAL",
    "create_gridworld",
    "create_initial_state",
    "env_step",
    "get_observation",
    "drift_goal",
    "hash_gridworld_state",
    # Task loss
    "V_task_distance",
    "V_task_success",
    "CompetenceMetrics",
    "compute_competence",
    "compute_metabolic_cost",
    "W_MOVE",
    "W_PROPOSE",
    "W_MEMORY_WRITE",
    "W_REJECTED_ATTEMPT",
]
