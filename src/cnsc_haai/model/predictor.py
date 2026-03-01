"""
Predictor - Predicts observations and rewards from latent state

For deterministic representation learning, all computations use QFixed integers.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple

# Import from encoder
from .encoder import LatentState


# =============================================================================
# Types
# =============================================================================

@dataclass(frozen=True)
class PredictorParams:
    """
    Predictor parameters.
    
    Maps latent state to predicted observation features and reward.
    """
    obs_matrix: Tuple[Tuple[int, ...], ...]  # [obs_dim x latent]
    reward_matrix: Tuple[Tuple[int, ...], ...]  # [1 x latent]
    obs_bias: Tuple[int, ...]
    reward_bias: int


# =============================================================================
# Functions
# =============================================================================

def create_default_predictor_params(seed: int = 44) -> PredictorParams:
    """
    Create default predictor parameters.
    """
    import hashlib
    
    # Observation matrix (maps to key features)
    obs_dim = 4  # distance, goal_dx, goal_dy, under_agent
    obs_matrix = []
    for i in range(obs_dim):
        row = []
        for j in range(4):  # LATENT_DIM = 4
            h = hashlib.sha256(f"{seed}:obs:{i}:{j}".encode()).digest()
            w = (h[0] % 5 - 2) * 10000  # Small weights
            row.append(w)
        obs_matrix.append(tuple(row))
    
    # Reward matrix (scalar)
    reward_matrix = []
    for j in range(4):
        h = hashlib.sha256(f"{seed}:rew:{j}".encode()).digest()
        w = (h[0] % 5 - 2) * 10000
        reward_matrix.append((w,))
    
    obs_bias = (0, 0, 0, 0)
    reward_bias = 0
    
    return PredictorParams(
        obs_matrix=tuple(obs_matrix),
        reward_matrix=tuple(reward_matrix),
        obs_bias=obs_bias,
        reward_bias=reward_bias,
    )


def predict_observation_features(
    latent: LatentState,
    params: PredictorParams,
) -> Tuple[int, int, int, int]:
    """
    Predict observation features from latent state.
    
    Returns: (distance, goal_dx, goal_dy, under_agent)
    """
    result = []
    
    for i, row in enumerate(params.obs_matrix):
        dot = 0
        for j, w in enumerate(row):
            if j < len(latent.values):
                dot += w * latent.values[j]
        
        if i < len(params.obs_bias):
            dot += params.obs_bias[i]
        
        result.append(dot)
    
    # Pad to 4 if needed
    while len(result) < 4:
        result.append(0)
    
    return tuple(result[:4])


def predict_reward(
    latent: LatentState,
    params: PredictorParams,
) -> int:
    """
    Predict reward from latent state.
    """
    # Simple linear: r = w * s + b
    dot = 0
    for j, w in enumerate(params.reward_matrix):
        if j < len(latent.values):
            dot += w[0] * latent.values[j]
    
    return dot + params.reward_bias


def predict_reward_simple(latent: LatentState) -> int:
    """
    Simple reward prediction.
    
    For Phase 2 demo: reward based on distance improvement.
    """
    # First value is distance
    if latent.values:
        return -latent.values[0]  # Negative distance = positive reward
    return 0
