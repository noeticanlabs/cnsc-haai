"""
CLATL Model Layer - World Model Components

Implements representation learning for Phase 2:
- Encoder: maps observations to latent state
- Dynamics: predicts next latent state
- Predictor: predicts observations/rewards
- Loss: prediction loss computation
"""

from .encoder import (
    EncoderParams,
    LatentState,
    encode,
)
from .dynamics import (
    DynamicsParams,
    predict_next_latent,
)
from .predictor import (
    PredictorParams,
    predict_observation_features,
    predict_reward,
)
from .loss import (
    PredictionLoss,
    compute_prediction_loss,
)

__all__ = [
    # Encoder
    "EncoderParams",
    "LatentState",
    "encode",
    # Dynamics
    "DynamicsParams",
    "predict_next_latent",
    # Predictor
    "PredictorParams",
    "predict_observation",
    "predict_reward",
    # Loss
    "PredictionLoss",
    "compute_prediction_loss",
]
