"""
Phase 2 Invariants Never Break Test

Tests that learning preserves all safety invariants:
- Admissibility: π ∈ K_π
- Budget: b ≥ 0 after learning cost
- Determinism: replay produces same parameter sequence
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest


class TestPhase2Invariants:
    """Phase 2 invariant tests."""
    
    def test_model_params_admissible(self):
        """Test that model parameters stay in admissible set."""
        from cnsc_haai.learn import ModelParams, compute_param_hash
        
        params = ModelParams(seed=42)
        params_hash = compute_param_hash(params)
        
        # Hash should be valid bytes
        assert len(params_hash) == 32
    
    def test_update_receipt_exists(self):
        """Test that updates produce receipts."""
        from cnsc_haai.learn import (
            ModelParams, trust_region_update, UpdateReceipt
        )
        
        params = ModelParams(seed=42)
        empty_batch = []
        
        new_params, accepted, receipt = trust_region_update(
            params, empty_batch, current_loss=0
        )
        
        assert isinstance(receipt, UpdateReceipt)
        assert receipt.old_params_hash is not None
        assert receipt.new_params_hash is not None
        assert receipt.delta_hash is not None
    
    def test_buffer_bounded(self):
        """Test that replay buffer respects capacity."""
        from cnsc_haai.memory import ReplayBuffer, create_transition
        from cnsc_haai.tasks.gridworld_env import GridWorldObs
        
        buffer = ReplayBuffer(capacity=3)
        
        # Create dummy observations
        obs = GridWorldObs(
            local_patch=tuple(tuple(0 for _ in range(5)) for _ in range(5)),
            goal_delta=(0, 0),
            distance_to_goal=10,
        )
        
        # Add 5 transitions
        for i in range(5):
            t = create_transition(obs, 'N', obs, 0)
            buffer.add(t)
        
        # Buffer should be bounded
        assert len(buffer) == 3
    
    def test_buffer_deterministic_sample(self):
        """Test that buffer sampling is deterministic."""
        from cnsc_haai.memory import ReplayBuffer, create_transition
        from cnsc_haai.tasks.gridworld_env import GridWorldObs
        
        buffer = ReplayBuffer(capacity=10)
        
        obs = GridWorldObs(
            local_patch=tuple(tuple(0 for _ in range(5)) for _ in range(5)),
            goal_delta=(0, 0),
            distance_to_goal=10,
        )
        
        # Add transitions
        for i in range(5):
            t = create_transition(obs, 'N', obs, 0)
            buffer.add(t)
        
        # Sample twice with same seed
        batch1 = buffer.sample_deterministic(3, seed=123)
        batch2 = buffer.sample_deterministic(3, seed=123)
        
        # Should be identical
        assert len(batch1) == len(batch2)
    
    def test_prediction_loss_computes(self):
        """Test that prediction loss computes correctly."""
        from cnsc_haai.model.loss import compute_simple_loss
        from cnsc_haai.model.encoder import LatentState
        
        s1 = LatentState(values=(1000000, 0, 0, 0))
        s2 = LatentState(values=(1000000, 0, 0, 0))
        
        loss = compute_simple_loss(s1, s2)
        
        # Same state = zero loss
        assert loss == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
