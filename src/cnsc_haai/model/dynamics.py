"""
Dynamics Model - Predicts next latent state

For deterministic representation learning, all computations use QFixed integers.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple

# Import from encoder
from .encoder import LatentState, EncoderParams, LATENT_DIM


# =============================================================================
# Types
# =============================================================================

@dataclass(frozen=True)
class DynamicsParams:
    """
    Dynamics model parameters.
    
    Simple linear dynamics: s' = A * s + B * a + c
    """
    transition_matrix: Tuple[Tuple[int, ...], ...]  # A [latent x latent]
    action_matrix: Tuple[Tuple[int, ...], ...]      # B [latent x action]
    bias: Tuple[int, ...]                            # c [latent]


# Action encoding
ACTION_DIM = 5  # N, S, E, W, Stay


# =============================================================================
# Functions
# =============================================================================

def create_default_dynamics_params(seed: int = 43) -> DynamicsParams:
    """
    Create default dynamics parameters.
    
    For Phase 2, use near-identity dynamics.
    """
    import hashlib
    
    # Transition matrix: near-identity with small perturbations
    A = []
    for i in range(LATENT_DIM):
        row = []
        for j in range(LATENT_DIM):
            h = hashlib.sha256(f"{seed}:A:{i}:{j}".encode()).digest()
            if i == j:
                w = 1_000_000  # Identity
            else:
                w = (h[0] % 3 - 1) * 10000  # Small perturbation
            row.append(w)
        A.append(tuple(row))
    
    # Action matrix: small effects
    B = []
    for i in range(LATENT_DIM):
        row = []
        for a in range(ACTION_DIM):
            h = hashlib.sha256(f"{seed}:B:{i}:{a}".encode()).digest()
            w = (h[0] % 5 - 2) * 10000  # -20000 to 20000
            row.append(w)
        B.append(tuple(row))
    
    # Bias = 0
    c = tuple([0] * LATENT_DIM)
    
    return DynamicsParams(
        transition_matrix=tuple(A),
        action_matrix=tuple(B),
        bias=c,
    )


def encode_action(action: str) -> Tuple[int, ...]:
    """Encode action as one-hot vector."""
    action_map = {'N': 0, 'S': 1, 'E': 2, 'W': 3, 'Stay': 4}
    idx = action_map.get(action, 4)
    
    result = [0] * ACTION_DIM
    result[idx] = 1_000_000  # QFixed 1.0
    return tuple(result)


def predict_next_latent(
    latent: LatentState,
    action: str,
    params: DynamicsParams,
) -> LatentState:
    """
    Predict next latent state: s' = A * s + B * a + c
    
    Args:
        latent: Current latent state
        action: Action taken
        params: Dynamics parameters
    
    Returns:
        Predicted next latent state
    """
    # Encode action
    action_vec = encode_action(action)
    
    # Compute: s' = A * s + B * a + c
    result = []
    
    for i in range(LATENT_DIM):
        # A * s
        dot_s = 0
        for j, w in enumerate(params.transition_matrix[i]):
            if j < len(latent.values):
                dot_s += w * latent.values[j]
        
        # B * a
        dot_a = 0
        for j, w in enumerate(params.action_matrix[i]):
            if j < len(action_vec):
                dot_a += w * action_vec[j]
        
        # + c
        total = dot_s + dot_a
        if i < len(params.bias):
            total += params.bias[i]
        
        result.append(total)
    
    return LatentState(values=tuple(result))


def predict_next_latent_simple(
    latent: LatentState,
    action: str,
) -> LatentState:
    """
    Simple dynamics without learned parameters.
    
    For Phase 2 demo: small deterministic drift toward goal direction.
    """
    # Simple: add small action effect to latent
    action_effects = {
        'N': (0, -100000, 0, 0),
        'S': (0, 100000, 0, 0),
        'E': (100000, 0, 0, 0),
        'W': (-100000, 0, 0, 0),
        'Stay': (0, 0, 0, 0),
    }
    
    effect = action_effects.get(action, (0, 0, 0, 0))
    
    new_values = []
    for i, v in enumerate(latent.values):
        new_values.append(v + effect[i])
    
    return LatentState(values=tuple(new_values))
