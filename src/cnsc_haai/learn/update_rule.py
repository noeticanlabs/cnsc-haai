"""
Update Rule - Learning with Linear Dynamics Model

Implements real prediction loss computation and parameter updates using
sign-descent on a linear latent dynamics model.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Optional
import hashlib
import json

from cnsc_haai.model.encoder import LatentState, encode, encode_simple, EncoderParams
from cnsc_haai.model.dynamics import (
    DynamicsParams, 
    predict_next_latent_simple,
    encode_action,
    LATENT_DIM,
    ACTION_DIM,
)
from cnsc_haai.memory.replay_buffer import Transition


# =============================================================================
# Constants
# =============================================================================

# Learning rate for sign-descent (QFixed scale)
LEARNING_RATE = 1000  # 0.001 in QFixed

# Cost per parameter update (metabolic cost)
COST_PER_PARAM = 100  # QFixed units


# =============================================================================
# Types
# =============================================================================

@dataclass(frozen=True)
class ModelParams:
    """
    Combined model parameters for the world model.
    
    Contains encoder, dynamics, and predictor parameters.
    """
    encoder: EncoderParams
    dynamics: DynamicsParams
    seed: int
    version: str = "v1"
    
    def to_dict(self) -> dict:
        """Serialize to dict."""
        return {
            'encoder_weights': str(self.encoder.weights),
            'encoder_bias': str(self.encoder.bias),
            'dynamics_A': str(self.dynamics.transition_matrix),
            'dynamics_B': str(self.dynamics.action_matrix),
            'seed': self.seed,
            'version': self.version,
        }


@dataclass(frozen=True)
class UpdateReceipt:
    """
    Receipt for a parameter update.
    
    Ensures deterministic replay.
    """
    old_params_hash: bytes
    new_params_hash: bytes
    delta_hash: bytes
    old_loss: int
    new_loss: int
    accepted: bool
    rejection_reason: Optional[str]
    batch_root: bytes
    update_cost: int


# =============================================================================
# Helper Functions
# =============================================================================

def _integer_sqrt(n: int) -> int:
    """
    Compute integer square root using binary search.
    
    Returns floor(sqrt(n)) as an integer.
    """
    if n < 0:
        raise ValueError("Cannot compute square root of negative number")
    if n < 2:
        return n
    
    # Binary search for integer sqrt
    left, right = 0, n
    while left <= right:
        mid = (left + right) // 2
        mid_sq = mid * mid
        if mid_sq == n:
            return mid
        elif mid_sq < n:
            left = mid + 1
            result = mid
        else:
            right = mid - 1
    return result


def compute_param_hash(params: ModelParams) -> bytes:
    """Compute deterministic hash of parameters."""
    data = {
        'encoder_weights': list(params.encoder.weights),
        'encoder_bias': list(params.encoder.bias),
        'dynamics_A': list(params.dynamics.transition_matrix),
        'dynamics_B': list(params.dynamics.action_matrix),
        'seed': params.seed,
        'version': params.version,
    }
    serialized = json.dumps(data, sort_keys=True)
    return hashlib.sha256(serialized.encode()).digest()


def compute_delta_hash(old_params: ModelParams, new_params: ModelParams) -> bytes:
    """Compute hash of parameter delta."""
    old_hash = compute_param_hash(old_params)
    new_hash = compute_param_hash(new_params)
    return hashlib.sha256(old_hash + new_hash).digest()


def compute_param_count(params: ModelParams) -> int:
    """Count number of parameters."""
    # Encoder: sum all weight entries + bias entries
    encoder_params = sum(len(row) for row in params.encoder.weights) + len(params.encoder.bias)
    
    # Dynamics: A matrix + B matrix + bias
    dynamics_a = sum(len(row) for row in params.dynamics.transition_matrix)
    dynamics_b = sum(len(row) for row in params.dynamics.action_matrix)
    dynamics_bias = len(params.dynamics.bias)
    dynamics_params = dynamics_a + dynamics_b + dynamics_bias
    
    return encoder_params + dynamics_params


def compute_delta_norm(old_params: ModelParams, new_params: ModelParams) -> int:
    """
    Compute norm of parameter change (in QFixed).
    
    Uses L2 norm of all parameter differences.
    """
    total_diff = 0
    
    # Encoder weights
    for old_row, new_row in zip(old_params.encoder.weights, new_params.encoder.weights):
        for old_w, new_w in zip(old_row, new_row):
            total_diff += (old_w - new_w) ** 2
    
    # Encoder bias
    for old_b, new_b in zip(old_params.encoder.bias, new_params.encoder.bias):
        total_diff += (old_b - new_b) ** 2
    
    # Dynamics A
    for old_row, new_row in zip(old_params.dynamics.transition_matrix, new_params.dynamics.transition_matrix):
        for old_a, new_a in zip(old_row, new_row):
            total_diff += (old_a - new_a) ** 2
    
    # Dynamics B
    for old_row, new_row in zip(old_params.dynamics.action_matrix, new_params.dynamics.action_matrix):
        for old_b, new_b in zip(old_row, new_row):
            total_diff += (old_b - new_b) ** 2
    
    # Dynamics bias
    for old_c, new_c in zip(old_params.dynamics.bias, new_params.dynamics.bias):
        total_diff += (old_c - new_c) ** 2
    
    # Return integer sqrt for deterministic computation
    return _integer_sqrt(total_diff)


def compute_delta_norm_sq(old_params: ModelParams, new_params: ModelParams) -> int:
    """
    Compute squared norm of parameter change (in QFixed).
    
    Returns sum of squared differences (no sqrt), useful for trust region
    computation where we need ||delta||^2 directly.
    """
    total_diff = 0
    
    # Encoder weights
    for old_row, new_row in zip(old_params.encoder.weights, new_params.encoder.weights):
        for old_w, new_w in zip(old_row, new_row):
            total_diff += (old_w - new_w) ** 2
    
    # Encoder bias
    for old_b, new_b in zip(old_params.encoder.bias, new_params.encoder.bias):
        total_diff += (old_b - new_b) ** 2
    
    # Dynamics A
    for old_row, new_row in zip(old_params.dynamics.transition_matrix, new_params.dynamics.transition_matrix):
        for old_a, new_a in zip(old_row, new_row):
            total_diff += (old_a - new_a) ** 2
    
    # Dynamics B
    for old_row, new_row in zip(old_params.dynamics.action_matrix, new_params.dynamics.action_matrix):
        for old_b, new_b in zip(old_row, new_row):
            total_diff += (old_b - new_b) ** 2
    
    # Dynamics bias
    for old_c, new_c in zip(old_params.dynamics.bias, new_params.dynamics.bias):
        total_diff += (old_c - new_c) ** 2
    
    return total_diff


def compute_update_cost(batch_size: int, param_count: int) -> int:
    """
    Compute metabolic cost of an update.
    
    Cost = k * batch_size * param_count
    """
    return COST_PER_PARAM * batch_size * param_count


# =============================================================================
# Prediction Loss Computation
# =============================================================================

def predict_next_latent_with_params(
    latent: LatentState,
    action: str,
    params: ModelParams,
) -> LatentState:
    """
    Predict next latent state using given parameters.
    
    Args:
        latent: Current latent state
        action: Action string
        params: Model parameters
    
    Returns:
        Predicted next latent state
    """
    # Encode action
    action_vec = encode_action(action)
    
    # Compute: s' = A * s + B * a
    next_values = []
    
    for i in range(LATENT_DIM):
        # A * s term
        a_term = 0
        for j in range(LATENT_DIM):
            a_term += params.dynamics.transition_matrix[i][j] * latent.values[j]
        
        # B * a term  
        b_term = 0
        for j in range(ACTION_DIM):
            b_term += params.dynamics.action_matrix[i][j] * action_vec[j]
        
        # Add bias
        total = a_term + b_term + params.dynamics.bias[i]
        
        # Scale down (QFixed division)
        total = total // 1_000_000
        next_values.append(total)
    
    return LatentState(tuple(next_values))


def compute_prediction_loss_on_batch(
    params: ModelParams,
    batch: List[Transition],
) -> int:
    """
    Compute prediction loss on a batch of transitions.
    
    Loss = sum(||s' - predicted_s'||^2) for each transition
    
    Args:
        params: Model parameters
        batch: List of transitions
    
    Returns:
        Total prediction loss (QFixed)
    """
    if not batch:
        return 0
    
    total_loss = 0
    
    for transition in batch:
        # Encode current observation to latent using learnable encoder
        current_latent = encode(transition.obs, params.encoder)
        
        # Predict next latent
        predicted_next = predict_next_latent_with_params(
            current_latent, 
            transition.action,
            params,
        )
        
        # Encode actual next observation using learnable encoder
        actual_next = encode(transition.next_obs, params.encoder)
        
        # Compute squared error
        loss = 0
        for pred, actual in zip(predicted_next.values, actual_next.values):
            diff = pred - actual
            loss += diff * diff
        
        total_loss += loss
    
    # Average loss
    return total_loss // len(batch)


# =============================================================================
# Parameter Update (Sign-Descent)
# =============================================================================

def propose_update_sign_descent(
    current_params: ModelParams,
    batch: List[Transition],
    learning_rate: int = LEARNING_RATE,
) -> ModelParams:
    """
    Propose parameter update using sign-descent.
    
    For each parameter, compute gradient direction and move in that direction.
    This is deterministic and doesn't require gradients.
    
    Args:
        current_params: Current model parameters
        batch: Batch of transitions
        learning_rate: Learning rate (QFixed)
    
    Returns:
        New model parameters
    """
    if not batch:
        return current_params
    
    # Compute gradient for each parameter by finite difference
    # We'll update dynamics matrix A (the most impactful)
    
    new_A = []
    epsilon = 10000  # Small perturbation for gradient estimation
    
    for i in range(LATENT_DIM):
        row = []
        for j in range(LATENT_DIM):
            # Compute loss with +epsilon
            params_plus = ModelParams(
                encoder=current_params.encoder,
                dynamics=DynamicsParams(
                    transition_matrix=_modify_matrix_entry(
                        current_params.dynamics.transition_matrix, i, j, epsilon
                    ),
                    action_matrix=current_params.dynamics.action_matrix,
                    bias=current_params.dynamics.bias,
                ),
                seed=current_params.seed,
                version=current_params.version,
            )
            loss_plus = compute_prediction_loss_on_batch(params_plus, batch)
            
            # Compute loss with -epsilon
            params_minus = ModelParams(
                encoder=current_params.encoder,
                dynamics=DynamicsParams(
                    transition_matrix=_modify_matrix_entry(
                        current_params.dynamics.transition_matrix, i, j, -epsilon
                    ),
                    action_matrix=current_params.dynamics.action_matrix,
                    bias=current_params.dynamics.bias,
                ),
                seed=current_params.seed,
                version=current_params.version,
            )
            loss_minus = compute_prediction_loss_on_batch(params_minus, batch)
            
            # Gradient approximation
            gradient = (loss_plus - loss_minus) // (2 * epsilon)
            
            # Sign-descent: move in direction opposite to gradient
            if gradient > 0:
                delta = -learning_rate
            elif gradient < 0:
                delta = learning_rate
            else:
                delta = 0
            
            new_value = current_params.dynamics.transition_matrix[i][j] + delta
            row.append(new_value)
        
        new_A.append(tuple(row))
    
    # Also update action matrix B
    new_B = []
    for i in range(LATENT_DIM):
        row = []
        for j in range(ACTION_DIM):
            # Compute loss with +epsilon
            params_plus = ModelParams(
                encoder=current_params.encoder,
                dynamics=DynamicsParams(
                    transition_matrix=current_params.dynamics.transition_matrix,
                    action_matrix=_modify_matrix_entry(
                        current_params.dynamics.action_matrix, i, j, epsilon
                    ),
                    bias=current_params.dynamics.bias,
                ),
                seed=current_params.seed,
                version=current_params.version,
            )
            loss_plus = compute_prediction_loss_on_batch(params_plus, batch)
            
            # Compute loss with -epsilon
            params_minus = ModelParams(
                encoder=current_params.encoder,
                dynamics=DynamicsParams(
                    transition_matrix=current_params.dynamics.transition_matrix,
                    action_matrix=_modify_matrix_entry(
                        current_params.dynamics.action_matrix, i, j, -epsilon
                    ),
                    bias=current_params.dynamics.bias,
                ),
                seed=current_params.seed,
                version=current_params.version,
            )
            loss_minus = compute_prediction_loss_on_batch(params_minus, batch)
            
            # Gradient approximation
            gradient = (loss_plus - loss_minus) // (2 * epsilon)
            
            # Sign-descent
            if gradient > 0:
                delta = -learning_rate
            elif gradient < 0:
                delta = learning_rate
            else:
                delta = 0
            
            new_value = current_params.dynamics.action_matrix[i][j] + delta
            row.append(new_value)
        
        new_B.append(tuple(row))
    
    # Return new params
    return ModelParams(
        encoder=current_params.encoder,
        dynamics=DynamicsParams(
            transition_matrix=tuple(new_A),
            action_matrix=tuple(new_B),
            bias=current_params.dynamics.bias,
        ),
        seed=current_params.seed,
        version=current_params.version,
    )


def _modify_matrix_entry(
    matrix: Tuple[Tuple[int, ...], ...],
    row: int,
    col: int,
    delta: int,
) -> Tuple[Tuple[int, ...], ...]:
    """Modify a single entry in a matrix."""
    new_matrix = []
    for i, r in enumerate(matrix):
        if i == row:
            new_row = list(r)
            new_row[col] = new_row[col] + delta
            new_matrix.append(tuple(new_row))
        else:
            new_matrix.append(r)
    return tuple(new_matrix)


# =============================================================================
# Update Functions
# =============================================================================

def apply_update(
    current_params: ModelParams,
    new_params: ModelParams,
) -> ModelParams:
    """
    Apply parameter update.
    
    For now, this just returns new_params.
    Could add validation here if needed.
    """
    return new_params


def compute_loss_with_params(
    params: ModelParams,
    batch: List[Transition],
) -> int:
    """
    Compute prediction loss with given parameters.
    
    This is a convenience wrapper.
    """
    return compute_prediction_loss_on_batch(params, batch)


# =============================================================================
# Tests
# =============================================================================

def test_prediction_loss():
    """Test that prediction loss can be computed."""
    from cnsc_haai.model.encoder import create_default_encoder_params
    from cnsc_haai.model.dynamics import create_default_dynamics_params
    from cnsc_haai.tasks.gridworld_env import GridWorldObs
    from cnsc_haai.memory.replay_buffer import create_transition
    
    # Create default params
    encoder = create_default_encoder_params(seed=42)
    dynamics = create_default_dynamics_params(seed=43)
    params = ModelParams(encoder=encoder, dynamics=dynamics, seed=44)
    
    # Create a batch
    obs1 = GridWorldObs(
        agent_x=0, agent_y=0,
        goal_x=2, goal_y=0,
        hazard_x=1, hazard_y=1,
        patch=[[0]*5 for _ in range(5)],
    )
    next_obs1 = GridWorldObs(
        agent_x=1, agent_y=0,
        goal_x=2, goal_y=0,
        hazard_x=1, hazard_y=1,
        patch=[[0]*5 for _ in range(5)],
    )
    t1 = create_transition(obs1, "east", next_obs1, 100)
    
    obs2 = GridWorldObs(
        agent_x=1, agent_y=0,
        goal_x=2, goal_y=0,
        hazard_x=1, hazard_y=1,
        patch=[[0]*5 for _ in range(5)],
    )
    next_obs2 = GridWorldObs(
        agent_x=2, agent_y=0,
        goal_x=2, goal_y=0,
        hazard_x=1, hazard_y=1,
        patch=[[0]*5 for _ in range(5)],
    )
    t2 = create_transition(obs2, "east", next_obs2, 100)
    
    batch = [t1, t2]
    
    # Compute loss
    loss = compute_prediction_loss_on_batch(params, batch)
    
    assert loss >= 0
    print(f"Initial loss: {loss}")
    
    # Try update
    new_params = propose_update_sign_descent(params, batch, learning_rate=1000)
    new_loss = compute_prediction_loss_on_batch(new_params, batch)
    
    print(f"Loss after update: {new_loss}")
    
    # Check that we actually changed parameters
    assert compute_delta_norm(params, new_params) > 0
    
    print("✓ Prediction loss test passed")


if __name__ == "__main__":
    test_prediction_loss()
    print("All update rule tests passed!")
