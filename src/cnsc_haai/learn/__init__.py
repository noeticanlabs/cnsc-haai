"""
Learning Module - Update Rules

Implements governed learning updates for Phase 2.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Optional
import hashlib
import json

from cnsc_haai.model.encoder import LatentState, encode_simple
from cnsc_haai.model.dynamics import predict_next_latent_simple
from cnsc_haai.model.loss import compute_simple_loss, PredictionLoss


# =============================================================================
# Types
# =============================================================================

@dataclass(frozen=True)
class ModelParams:
    """
    Combined model parameters.
    
    For Phase 2 demo, uses simple encoding/dynamics without learned params.
    """
    seed: int
    version: str = "v1"


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


# =============================================================================
# Constants
# =============================================================================

# Trust region parameters (QFixed)
GAMMA = 100_000  # Trust region coefficient
DELTA_MAX = 500_000  # Max update norm


# =============================================================================
# Update Functions
# =============================================================================

def compute_param_hash(params: ModelParams) -> bytes:
    """Compute hash of parameters."""
    data = {"seed": params.seed, "version": params.version}
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).digest()


def compute_delta_norm(old_params: ModelParams, new_params: ModelParams) -> int:
    """
    Compute norm of parameter change.
    
    For simple params, just use seed difference.
    """
    diff = abs(new_params.seed - old_params.seed)
    return diff * 1_000_000  # Scale to QFixed


def trust_region_update(
    current_params: ModelParams,
    batch: List[Tuple[LatentState, str, LatentState]],
    current_loss: int,
    gamma: int = GAMMA,
) -> Tuple[ModelParams, bool, UpdateReceipt]:
    """
    Apply trust-region update.
    
    Accept if:
    V_pred(π_{t+1}) ≤ V_pred(π_t) - γ * |π_{t+1} - π_t|²
    
    Args:
        current_params: Current model parameters
        batch: List of (s_t, a_t, s_{t+1}) transitions
        current_loss: Current prediction loss
        gamma: Trust region coefficient
    
    Returns:
        (new_params, accepted, receipt)
    """
    # Compute loss on batch with current params
    new_loss = current_loss  # Placeholder - would compute actual loss
    
    # For Phase 2 demo, we don't actually update params
    # (full learning requires more infrastructure)
    new_params = current_params
    
    # Compute delta norm
    delta_norm = compute_delta_norm(current_params, new_params)
    
    # Trust region check
    threshold = gamma * delta_norm // 1_000_000
    
    accepted = new_loss <= current_loss - threshold
    
    # Create receipt
    old_hash = compute_param_hash(current_params)
    new_hash = compute_param_hash(new_params)
    delta_hash = hashlib.sha256(f"{old_hash}{new_hash}".encode()).digest()
    
    # Batch root (simple hash of batch)
    batch_data = str([(s.values, a, sp.values) for s, a, sp in batch]).encode()
    batch_root = hashlib.sha256(batch_data).digest()
    
    receipt = UpdateReceipt(
        old_params_hash=old_hash,
        new_params_hash=new_hash,
        delta_hash=delta_hash,
        old_loss=current_loss,
        new_loss=new_loss,
        accepted=accepted,
        rejection_reason=None if accepted else "trust_region_violation",
        batch_root=batch_root,
    )
    
    return new_params, accepted, receipt


def bounded_update(
    current_params: ModelParams,
    batch: List[Tuple[LatentState, str, LatentState]],
    budget: int,
    delta_max: int = DELTA_MAX,
) -> Tuple[ModelParams, bool, UpdateReceipt]:
    """
    Apply bounded update.
    
    Accept if:
    - |Δπ| ≤ δ(b_t)  (norm bounded by budget)
    - validation loss doesn't increase
    
    Args:
        current_params: Current model parameters
        batch: List of (s_t, a_t, s_{t+1}) transitions
        budget: Remaining budget
        delta_max: Maximum allowed delta
    
    Returns:
        (new_params, accepted, receipt)
    """
    # For Phase 2 demo, params don't change
    new_params = current_params
    
    # Check budget constraint
    allowed_delta = (budget * delta_max) // 10_000_000
    delta_norm = compute_delta_norm(current_params, new_params)
    
    accepted = delta_norm <= allowed_delta
    
    # Create receipt
    old_hash = compute_param_hash(current_params)
    new_hash = compute_param_hash(new_params)
    delta_hash = hashlib.sha256(f"{old_hash}{new_hash}".encode()).digest()
    
    batch_data = str([(s.values, a, sp.values) for s, a, sp in batch]).encode()
    batch_root = hashlib.sha256(batch_data).digest()
    
    receipt = UpdateReceipt(
        old_params_hash=old_hash,
        new_params_hash=new_hash,
        delta_hash=delta_hash,
        old_loss=0,  # Would compute
        new_loss=0,
        accepted=accepted,
        rejection_reason=None if accepted else "budget_constraint",
        batch_root=batch_root,
    )
    
    return new_params, accepted, receipt


# =============================================================================
# Simplified Interface
# =============================================================================

def governed_update(
    current_params: ModelParams,
    batch: List[Tuple[LatentState, str, LatentState]],
    current_loss: int,
    budget: int,
    use_trust_region: bool = True,
) -> Tuple[ModelParams, UpdateReceipt]:
    """
    Apply governed update (main interface).
    
    Tries trust-region first, falls back to bounded if needed.
    
    Args:
        current_params: Current model parameters
        batch: Training batch
        current_loss: Current prediction loss
        budget: Remaining budget
        use_trust_region: Use trust region (vs bounded)
    
    Returns:
        (new_params, receipt)
    """
    if use_trust_region:
        new_params, accepted, receipt = trust_region_update(
            current_params, batch, current_loss
        )
    else:
        new_params, accepted, receipt = bounded_update(
            current_params, batch, budget
        )
    
    if not accepted:
        # Rejection - keep current params
        return current_params, receipt
    
    return new_params, receipt


def compute_loss_on_batch(
    params: ModelParams,
    batch: List[Tuple[LatentState, str, LatentState]],
) -> int:
    """
    Compute prediction loss on batch.
    
    Args:
        params: Model parameters
        batch: List of (s_t, a_t, s_{t+1}) transitions
    
    Returns:
        Total loss (QFixed)
    """
    total_loss = 0
    
    for s_t, a_t, s_next in batch:
        # Predict next state
        s_pred = predict_next_latent_simple(s_t, a_t)
        
        # Compute loss
        loss = compute_simple_loss(s_pred, s_next)
        total_loss += loss
    
    # Average
    return total_loss // max(1, len(batch))
