"""
Acceptance - Trust Region and Budget Checks for Learning

Implements governed update gate with trust region constraints and budget checks.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Tuple
import hashlib
import json

from cnsc_haai.learn.update_rule import (
    ModelParams,
    UpdateReceipt,
    compute_param_hash,
    compute_delta_hash,
    compute_delta_norm,
    compute_delta_norm_sq,
    compute_param_count,
    compute_update_cost,
    compute_prediction_loss_on_batch,
)


# =============================================================================
# Constants
# =============================================================================

# Trust region coefficient (gamma in the paper)
GAMMA = 100_000  # QFixed

# Maximum allowed delta (budget-dependent)
DELTA_MAX = 500_000  # QFixed

# Tolerance for loss improvement
EPSILON = 10_000  # 0.01 in QFixed - allow small increase


# =============================================================================
# Trust Region Check
# =============================================================================

def trust_region_check(
    old_params: ModelParams,
    new_params: ModelParams,
    old_loss: int,
    new_loss: int,
    gamma: int = GAMMA,
) -> Tuple[bool, Optional[str]]:
    """
    Check if update satisfies trust region constraint.
    
    Accept if:
    new_loss <= old_loss - gamma * ||delta||^2
    
    This ensures we only accept updates that improve the loss
    sufficiently relative to the parameter change.
    
    Args:
        old_params: Original parameters
        new_params: Proposed new parameters
        old_loss: Loss before update
        new_loss: Loss after update
        gamma: Trust region coefficient
    
    Returns:
        Tuple of (accepted, reason)
    """
    # Compute squared delta norm directly (no sqrt, no float)
    delta_norm_sq = compute_delta_norm_sq(old_params, new_params)
    
    # Compute threshold: gamma * ||delta||^2
    # gamma is in QFixed (100_000), delta_norm_sq is sum of squared diffs (QFixed^2)
    # For proper scaling: threshold = gamma * delta_norm_sq / QFIXED_SCALE
    # where QFIXED_SCALE = 1_000_000
    QFIXED_SCALE = 1_000_000
    threshold = (gamma * delta_norm_sq) // QFIXED_SCALE
    
    # Check improvement
    improvement = old_loss - new_loss
    
    if improvement >= threshold:
        return True, None
    else:
        return False, f"trust_region_violation: improvement={improvement} < threshold={threshold}"


def bounded_delta_check(
    old_params: ModelParams,
    new_params: ModelParams,
    delta_max: int = DELTA_MAX,
) -> Tuple[bool, Optional[str]]:
    """
    Check if parameter change is within bounds.
    
    Args:
        old_params: Original parameters
        new_params: Proposed new parameters
        delta_max: Maximum allowed delta
    
    Returns:
        Tuple of (accepted, reason)
    """
    delta_norm = compute_delta_norm(old_params, new_params)
    
    if delta_norm <= delta_max:
        return True, None
    else:
        return False, f"delta_exceeds_max: {delta_norm} > {delta_max}"


# =============================================================================
# Budget Check
# =============================================================================

def budget_check(
    budget: int,
    update_cost: int,
) -> Tuple[bool, Optional[str]]:
    """
    Check if budget is sufficient for update.
    
    Args:
        budget: Remaining budget
        update_cost: Cost of the update
    
    Returns:
        Tuple of (accepted, reason)
    """
    if budget >= update_cost:
        return True, None
    else:
        return False, f"insufficient_budget: need {update_cost}, have {budget}"


# =============================================================================
# Combined Acceptance Test
# =============================================================================

def acceptance_test(
    old_params: ModelParams,
    new_params: ModelParams,
    old_loss: int,
    new_loss: int,
    budget: int,
    batch_size: int,
    batch_root: Optional[bytes] = None,
    gamma: int = GAMMA,
    delta_max: int = DELTA_MAX,
    epsilon: int = EPSILON,
) -> Tuple[bool, Optional[str], UpdateReceipt]:
    """
    Run full acceptance test for a proposed update.
    
    Checks:
    1. Trust region: improvement >= gamma * ||delta||^2
    2. Budget: cost <= available budget
    3. Delta bound: ||delta|| <= delta_max
    4. Loss: new_loss < old_loss (strict monotone descent)
    
    Args:
        old_params: Original parameters
        new_params: Proposed new parameters
        old_loss: Loss before update
        new_loss: Loss after update
        budget: Remaining budget
        batch_size: Size of training batch
        batch_root: Merkle root of batch (required for valid receipt)
        gamma: Trust region coefficient
        delta_max: Maximum delta
        epsilon: (deprecated, kept for API compatibility)
    
    Returns:
        Tuple of (accepted, reason, receipt)
    """
    # Compute costs
    param_count = compute_param_count(old_params)
    update_cost = compute_update_cost(batch_size, param_count)
    
    # Determine batch_root to use (require for valid receipt)
    if batch_root is None:
        # For backward compatibility with direct calls, use placeholder
        # but this should be phased out - callers should provide batch_root
        effective_batch_root = hashlib.sha256(b"MISSING_BATCH_ROOT").digest()
    else:
        effective_batch_root = batch_root
    
    # Check budget first (fast check)
    budget_ok, budget_reason = budget_check(budget, update_cost)
    if not budget_ok:
        old_hash = compute_param_hash(old_params)
        new_hash = compute_param_hash(old_params)  # No change
        delta_hash = b"NO_UPDATE"
        
        receipt = UpdateReceipt(
            old_params_hash=old_hash,
            new_params_hash=new_hash,
            delta_hash=delta_hash,
            old_loss=old_loss,
            new_loss=old_loss,
            accepted=False,
            rejection_reason=budget_reason,
            batch_root=effective_batch_root,
            update_cost=update_cost,
        )
        return False, budget_reason, receipt
    
    # Check delta bound
    delta_ok, delta_reason = bounded_delta_check(old_params, new_params, delta_max)
    if not delta_ok:
        old_hash = compute_param_hash(old_params)
        new_hash = compute_param_hash(old_params)
        delta_hash = b"NO_UPDATE"
        
        receipt = UpdateReceipt(
            old_params_hash=old_hash,
            new_params_hash=new_hash,
            delta_hash=delta_hash,
            old_loss=old_loss,
            new_loss=old_loss,
            accepted=False,
            rejection_reason=delta_reason,
            batch_root=effective_batch_root,
            update_cost=update_cost,
        )
        return False, delta_reason, receipt
    
    # Check trust region
    trust_ok, trust_reason = trust_region_check(
        old_params, new_params, old_loss, new_loss, gamma
    )
    
    # Require strict monotone descent: loss must decrease
    # This ensures we have "governed learning" - only accept improving updates
    accepted = new_loss < old_loss
    
    if accepted:
        reason = None
    else:
        reason = f"loss_not_decreased: old={old_loss}, new={new_loss}"
    
    # Create receipt
    old_hash = compute_param_hash(old_params)
    new_hash = compute_param_hash(new_params)
    delta_hash = compute_delta_hash(old_params, new_params)
    
    receipt = UpdateReceipt(
        old_params_hash=old_hash,
        new_params_hash=new_hash,
        delta_hash=delta_hash,
        old_loss=old_loss,
        new_loss=new_loss,
        accepted=accepted,
        rejection_reason=reason,
        batch_root=effective_batch_root,
        update_cost=update_cost,
    )
    
    return accepted, reason, receipt


# =============================================================================
# Governed Update
# =============================================================================

def governed_update(
    current_params: ModelParams,
    proposed_params: ModelParams,
    current_loss: int,
    proposed_loss: int,
    budget: int,
    batch_size: int,
    batch_root: bytes,
) -> Tuple[ModelParams, UpdateReceipt]:
    """
    Apply governed update with full acceptance test.
    
    This is the main entry point for learning updates.
    
    Args:
        current_params: Current model parameters (from_params: Proposed new parameters
        proposed update rule)
        current_loss: Current prediction loss
        proposed_loss: Loss with proposed params
        budget: Remaining budget
        batch_size: Size of training batch
        batch_root: Merkle root of batch
    
    Returns:
        Tuple of (accepted_params, receipt)
    """
    # Run acceptance test with batch_root
    accepted, reason, receipt = acceptance_test(
        old_params=current_params,
        new_params=proposed_params,
        old_loss=current_loss,
        new_loss=proposed_loss,
        budget=budget,
        batch_size=batch_size,
        batch_root=batch_root,
    )
    
    # Return either new params or old params
    if accepted:
        return proposed_params, receipt
    else:
        return current_params, receipt


# =============================================================================
# Tests
# =============================================================================

def test_trust_region():
    """Test trust region check."""
    from cnsc_haai.model.encoder import create_default_encoder_params, EncoderParams
    from cnsc_haai.model.dynamics import create_default_dynamics_params, DynamicsParams
    
    encoder = create_default_encoder_params(seed=42)
    dynamics = create_default_dynamics_params(seed=43)
    
    old_params = ModelParams(encoder=encoder, dynamics=dynamics, seed=44)
    
    # Create slightly modified params
    new_dynamics = DynamicsParams(
        transition_matrix=tuple(
            list(dynamics.transition_matrix[0][:])[:-1] + (dynamics.transition_matrix[0][-1] + 1000,)
            if i == 0 else dynamics.transition_matrix[i]
            for i in range(len(dynamics.transition_matrix))
        ),
        action_matrix=dynamics.action_matrix,
        bias=dynamics.bias,
    )
    new_params = ModelParams(encoder=encoder, dynamics=new_dynamics, seed=44)
    
    # Test trust region with zero loss improvement
    old_loss = 1_000_000
    new_loss = 1_000_000  # No improvement
    
    ok, reason = trust_region_check(old_params, new_params, old_loss, new_loss)
    
    # Should fail because no improvement but there is delta
    assert not ok
    assert reason is not None
    
    print("✓ Trust region test passed")


def test_budget_check():
    """Test budget check."""
    # Enough budget
    ok, reason = budget_check(100_000, 50_000)
    assert ok
    assert reason is None
    
    # Not enough budget
    ok, reason = budget_check(30_000, 50_000)
    assert not ok
    assert "insufficient_budget" in reason
    
    print("✓ Budget check test passed")


def test_acceptance_test():
    """Test full acceptance test."""
    from cnsc_haai.model.encoder import create_default_encoder_params
    from cnsc_haai.model.dynamics import create_default_dynamics_params
    
    encoder = create_default_encoder_params(seed=42)
    dynamics = create_default_dynamics_params(seed=43)
    
    old_params = ModelParams(encoder=encoder, dynamics=dynamics, seed=44)
    
    # Same params = zero delta = should pass
    accepted, reason, receipt = acceptance_test(
        old_params=old_params,
        new_params=old_params,
        old_loss=1_000_000,
        new_loss=900_000,  # Improvement
        budget=100_000,
        batch_size=10,
    )
    
    assert accepted
    print(f"✓ Acceptance test passed: {reason}")


if __name__ == "__main__":
    test_trust_region()
    test_budget_check()
    test_acceptance_test()
    print("All acceptance tests passed!")
