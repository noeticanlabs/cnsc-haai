"""
Prediction Loss Functions

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
class PredictionLoss:
    """
    Prediction loss components.
    
    All values in QFixed scale.
    """
    observation_loss: int    # L2 loss on observation prediction
    reward_loss: int         # L2 loss on reward prediction
    total_loss: int          # Weighted sum
    
    def to_int(self) -> int:
        """Get total loss as integer."""
        return self.total_loss


# =============================================================================
# Constants
# =============================================================================

# Loss weights (QFixed)
OBS_LOSS_WEIGHT = 1_000_000  # 1.0
REWARD_LOSS_WEIGHT = 500_000  # 0.5


# =============================================================================
# Functions
# =============================================================================

def squared_error(predicted: int, actual: int) -> int:
    """
    Compute squared error: (pred - actual)^2
    
    All in QFixed scale.
    """
    diff = predicted - actual
    return diff * diff


def compute_observation_loss(
    predicted_features: Tuple[int, ...],
    actual_distance: int,
    actual_goal_delta: Tuple[int, int],
) -> int:
    """
    Compute observation prediction loss.
    
    Args:
        predicted_features: (distance, goal_dx, goal_dy, under_agent)
        actual_distance: Actual distance to goal
        actual_goal_delta: (dx, dy) to goal
    
    Returns:
        Squared error (QFixed)
    """
    if len(predicted_features) < 3:
        return 0
    
    # Distance prediction error
    dist_loss = squared_error(predicted_features[0], actual_distance * 1_000_000)
    
    # Goal delta prediction error
    dx_loss = squared_error(predicted_features[1], actual_goal_delta[0] * 1_000_000)
    dy_loss = squared_error(predicted_features[2], actual_goal_delta[1] * 1_000_000)
    
    # Weighted sum
    return (dist_loss + dx_loss + dy_loss) // 3


def compute_reward_loss(
    predicted_reward: int,
    actual_reward: int,
) -> int:
    """
    Compute reward prediction loss.
    
    Args:
        predicted_reward: Predicted reward (QFixed)
        actual_reward: Actual reward (QFixed)
    
    Returns:
        Squared error (QFixed)
    """
    return squared_error(predicted_reward, actual_reward)


def compute_prediction_loss(
    predicted_distance: int,
    actual_distance: int,
    predicted_reward: int,
    actual_reward: int,
) -> PredictionLoss:
    """
    Compute total prediction loss.
    
    V_pred(t) = ℓ(o_{t+1}, ô_{t+1}) + ℓ_r(r_{t+1}, r̂_{t+1})
    
    Args:
        predicted_distance: Predicted distance to goal (QFixed)
        actual_distance: Actual distance to goal (not scaled)
        predicted_reward: Predicted reward (QFixed)
        actual_reward: Actual reward (not scaled)
    
    Returns:
        PredictionLoss
    """
    # Scale actual values to QFixed
    actual_distance_q = actual_distance * 1_000_000
    actual_reward_q = actual_reward * 1_000_000
    
    # Compute losses
    obs_loss = squared_error(predicted_distance, actual_distance_q)
    rew_loss = squared_error(predicted_reward, actual_reward_q)
    
    # Weighted sum
    total = (obs_loss * OBS_LOSS_WEIGHT + rew_loss * REWARD_LOSS_WEIGHT) // 1_000_000
    
    return PredictionLoss(
        observation_loss=obs_loss,
        reward_loss=rew_loss,
        total_loss=total,
    )


def compute_simple_loss(
    predicted_latent: LatentState,
    actual_latent: LatentState,
) -> int:
    """
    Compute simple latent prediction loss.
    
    For Phase 2 demo without full prediction heads.
    """
    total = 0
    for p, a in zip(predicted_latent.values, actual_latent.values):
        total += squared_error(p, a)
    
    return total // max(1, len(actual_latent.values))
