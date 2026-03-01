"""
Encoder - Maps observations to latent state

For deterministic representation learning, all computations use QFixed integers.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple

# Import from tasks
from cnsc_haai.tasks.gridworld_env import GridWorldObs


# =============================================================================
# Types
# =============================================================================

@dataclass(frozen=True)
class LatentState:
    """
    Latent state representation.
    
    Fixed-size vector of QFixed integers for determinism.
    """
    values: Tuple[int, ...]  # QFixed scaled integers
    
    def __post_init__(self):
        """Validate."""
        if not isinstance(self.values, tuple):
            object.__setattr__(self, 'values', tuple(self.values))


@dataclass(frozen=True)
class EncoderParams:
    """
    Encoder parameters (QFixed for determinism).
    
    Simple linear embedding: s = W * obs + b
    """
    weights: Tuple[Tuple[int, ...], ...]  # Matrix [latent_dim x obs_dim]
    bias: Tuple[int, ...]                  # Bias [latent_dim]


# =============================================================================
# Constants
# =============================================================================

# Latent dimension (keep small for Phase 2 demo)
LATENT_DIM = 4

# Observation dimension (flattened patch + goal delta + distance)
# 5x5 patch = 25, goal_delta = 2, distance = 1
OBS_DIM = 28


# =============================================================================
# Functions
# =============================================================================

def create_default_encoder_params(seed: int = 42) -> EncoderParams:
    """
    Create default encoder parameters.
    
    For Phase 2, use identity-like mapping with small deterministic weights.
    """
    import hashlib
    
    # Generate deterministic weights from seed
    weights = []
    for i in range(LATENT_DIM):
        row = []
        for j in range(OBS_DIM):
            # Deterministic weight based on position
            h = hashlib.sha256(f"{seed}:w:{i}:{j}".encode()).digest()
            # Small weights: -1, 0, or 1
            w = (h[0] % 3) - 1  # -1, 0, or 1
            row.append(w * 100000)  # QFixed scale
        weights.append(tuple(row))
    
    # Bias = 0
    bias = tuple([0] * LATENT_DIM)
    
    return EncoderParams(
        weights=tuple(weights),
        bias=bias,
    )


def flatten_obs(obs: GridWorldObs) -> Tuple[int, ...]:
    """
    Flatten observation to vector.
    
    Args:
        obs: GridWorldObs
    
    Returns:
        Flattened observation vector
    """
    result = []
    
    # Flatten local patch (5x5 = 25 values)
    for row in obs.local_patch:
        result.extend(row)
    
    # Add goal delta (2 values)
    result.append(obs.goal_delta[0])
    result.append(obs.goal_delta[1])
    
    # Add distance (1 value)
    result.append(obs.distance_to_goal)
    
    return tuple(result)


def encode(obs: GridWorldObs, params: EncoderParams) -> LatentState:
    """
    Map observation to latent state: s = W * obs + b
    
    Args:
        obs: GridWorldObs
        params: Encoder parameters
    
    Returns:
        LatentState
    """
    # Flatten observation
    obs_vec = flatten_obs(obs)
    
    # Ensure dimensions match
    assert len(obs_vec) == OBS_DIM, f"Obs dim {len(obs_vec)} != {OBS_DIM}"
    assert len(params.weights) == LATENT_DIM, f"Weight dim {len(params.weights)} != {LATENT_DIM}"
    
    # Compute: s = W * obs + b
    result = []
    for i, row in enumerate(params.weights):
        # Dot product
        dot = 0
        for j, w in enumerate(row):
            if j < len(obs_vec):
                dot += w * obs_vec[j]
        
        # Add bias
        if i < len(params.bias):
            dot += params.bias[i]
        
        result.append(dot)
    
    return LatentState(values=tuple(result))


def encode_simple(obs: GridWorldObs) -> LatentState:
    """
    Simple encoding without learned parameters.
    
    Extracts key features directly.
    """
    # Feature vector: center position, goal delta, distance
    # This is a handcrafted encoding for Phase 2 demo
    values = (
        obs.distance_to_goal * 1_000_000,  # Distance to goal
        obs.goal_delta[0] * 500_000,       # Goal direction X
        obs.goal_delta[1] * 500_000,       # Goal direction Y
        obs.local_patch[2][2] * 1_000_000, # What's under agent
    )
    
    return LatentState(values=values)
