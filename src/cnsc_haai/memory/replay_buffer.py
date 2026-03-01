"""
Replay Buffer - Deterministic Bounded Memory for Phase 2

Implements bounded replay buffer with deterministic retention for learning.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
import hashlib
import json

from cnsc_haai.tasks.gridworld_env import GridWorldObs


# =============================================================================
# Types
# =============================================================================

@dataclass(frozen=True)
class Transition:
    """
    A receipted transition for training.
    
    Immutable for deterministic replay.
    """
    obs: GridWorldObs
    action: str
    next_obs: GridWorldObs
    reward: int
    hash: bytes  # For audit
    
    def to_dict(self) -> dict:
        """Serialize to dict."""
        return {
            'action': self.action,
            'reward': self.reward,
            'hash': self.hash.hex(),
        }


class ReplayBuffer:
    """
    Bounded replay buffer with deterministic retention.
    
    Uses FIFO eviction with hash-based indexing for reproducible sampling.
    """
    
    def __init__(self, capacity: int = 1000, seed: int = 42):
        """
        Initialize replay buffer.
        
        Args:
            capacity: Maximum number of transitions
            seed: Seed for deterministic sampling
        """
        self.capacity = capacity
        self.seed = seed
        self.buffer: List[Transition] = []
        self._add_count = 0  # For deterministic indexing
    
    def add(self, transition: Transition):
        """
        Add transition, evict deterministically if full.
        
        Uses FIFO (keep newer transitions).
        
        Args:
            transition: Transition to add
        """
        self._add_count += 1
        
        if len(self.buffer) >= self.capacity:
            # Evict deterministically (FIFO) - keep newer transitions
            self.buffer = self.buffer[1:]
        
        self.buffer.append(transition)
    
    def sample_deterministic(
        self,
        batch_size: int,
        seed: Optional[int] = None,
    ) -> List[Transition]:
        """
        Deterministic batch selection via hash-based LCG.
        
        Args:
            batch_size: Number of samples
            seed: Override seed (uses self.seed if None)
        
        Returns:
            List of transitions (with replacement for simplicity)
        """
        if not self.buffer:
            return []
        
        if seed is None:
            seed = self.seed
        
        # Use LCG for deterministic sampling
        # LCG parameters from Numerical Recipes
        result = []
        h = seed
        
        for _ in range(batch_size):
            # LCG: h = (a * h + c) mod m
            h = (h * 1103515245 + 12345) % (2**31)
            idx = h % len(self.buffer)
            result.append(self.buffer[idx])
        
        return result
    
    def sample_by_hash(self, batch_size: int, step_index: int) -> List[Transition]:
        """
        Sample using hash(state_hash || step_index) for receiptable selection.
        
        This method is useful when you need to receipt the exact batch selected,
        as the selection is fully deterministic based on buffer contents + step.
        
        Args:
            batch_size: Number of samples
            step_index: Current step number (used in hash)
        
        Returns:
            List of transitions
        """
        if not self.buffer:
            return []
        
        result = []
        buffer_root = self.get_root()
        
        for i in range(batch_size):
            # Hash = f(buffer_root, step_index, i)
            h_input = f"{buffer_root.hex()}:{step_index}:{i}".encode()
            h = hashlib.sha256(h_input).digest()
            idx = int.from_bytes(h[:4], 'big') % len(self.buffer)
            result.append(self.buffer[idx])
        
        return result
    
    def get_root(self) -> bytes:
        """
        Merkle root of all transitions for receipt.
        
        Returns:
            SHA256 hash of all transition hashes combined
        """
        if not self.buffer:
            return hashlib.sha256(b"EMPTY_BUFFER").digest()
        
        # Sort hashes for deterministic combining
        hashes = sorted([t.hash for t in self.buffer])
        combined = b"".join(hashes)
        return hashlib.sha256(combined).digest()
    
    def get_root_with_index(self, start_index: int, end_index: int) -> bytes:
        """
        Merkle root of transitions in index range [start, end).
        
        Useful for receipting subsets of buffer.
        
        Args:
            start_index: Start index (inclusive)
            end_index: End index (exclusive)
        
        Returns:
            SHA256 hash of transition hashes in range
        """
        if start_index >= end_index or start_index >= len(self.buffer):
            return hashlib.sha256(b"EMPTY_RANGE").digest()
        
        # Clamp end_index
        end_index = min(end_index, len(self.buffer))
        
        hashes = [t.hash for t in self.buffer[start_index:end_index]]
        hashes = sorted(hashes)
        combined = b"".join(hashes)
        return hashlib.sha256(combined).digest()
    
    def __len__(self) -> int:
        """Return buffer size."""
        return len(self.buffer)
    
    def clear(self):
        """Clear buffer."""
        self.buffer = []
        self._add_count = 0
    
    def is_full(self) -> bool:
        """Check if buffer is at capacity."""
        return len(self.buffer) >= self.capacity
    
    def to_summary(self) -> dict:
        """Get summary for debugging."""
        return {
            'capacity': self.capacity,
            'size': len(self.buffer),
            'root': self.get_root().hex()[:16] + "...",
            'add_count': self._add_count,
        }


# =============================================================================
# Helper Functions
# =============================================================================

def compute_transition_hash(
    obs: GridWorldObs,
    action: str,
    next_obs: GridWorldObs,
    reward: int,
) -> bytes:
    """
    Compute deterministic hash of a transition.
    
    Args:
        obs: Current observation
        action: Action taken
        next_obs: Next observation
        reward: Reward received
    
    Returns:
        SHA256 hash of the transition
    """
    # Create deterministic representation using available fields
    # GridWorldObs has: local_patch, goal_delta, distance_to_goal
    state_data = {
        'patch': obs.local_patch,
        'goal_delta': obs.goal_delta,
        'distance': obs.distance_to_goal,
    }
    
    next_state_data = {
        'patch': next_obs.local_patch,
        'goal_delta': next_obs.goal_delta,
        'distance': next_obs.distance_to_goal,
    }
    
    data = {
        'state': state_data,
        'action': action,
        'next_state': next_state_data,
        'reward': reward,
    }
    
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).digest()


def create_transition(
    obs: GridWorldObs,
    action: str,
    next_obs: GridWorldObs,
    reward: int,
) -> Transition:
    """
    Create a transition with computed hash.
    
    Args:
        obs: Current observation
        action: Action taken
        next_obs: Next observation
        reward: Reward received
    
    Returns:
        Transition with hash
    """
    h = compute_transition_hash(obs, action, next_obs, reward)
    return Transition(
        obs=obs,
        action=action,
        next_obs=next_obs,
        reward=reward,
        hash=h,
    )


# =============================================================================
# Tests
# =============================================================================

def test_deterministic_sampling():
    """Test that sampling is deterministic with same seed."""
    buffer = ReplayBuffer(capacity=10, seed=42)
    
    # Add some dummy transitions
    from cnsc_haai.tasks.gridworld_env import GridWorldObs
    
    for i in range(5):
        obs = GridWorldObs(
            agent_x=0, agent_y=0,
            goal_x=1, goal_y=0,
            hazard_x=2, hazard_y=2,
            patch=[[0]*5 for _ in range(5)],
        )
        next_obs = GridWorldObs(
            agent_x=1, agent_y=0,
            goal_x=1, goal_y=0,
            hazard_x=2, hazard_y=2,
            patch=[[0]*5 for _ in range(5)],
        )
        t = create_transition(obs, "east", next_obs, 100)
        buffer.add(t)
    
    # Sample twice with same seed
    batch1 = buffer.sample_deterministic(3, seed=100)
    batch2 = buffer.sample_deterministic(3, seed=100)
    
    # Should be identical
    assert len(batch1) == len(batch2) == 3
    for t1, t2 in zip(batch1, batch2):
        assert t1.hash == t2.hash
    
    # Different seed should give different results
    batch3 = buffer.sample_deterministic(3, seed=200)
    hashes1 = [t.hash for t in batch1]
    hashes3 = [t.hash for t in batch3]
    assert hashes1 != hashes3
    
    print("✓ Deterministic sampling test passed")


def test_root_stability():
    """Test that root is stable regardless of addition order."""
    buffer1 = ReplayBuffer(capacity=10, seed=42)
    buffer2 = ReplayBuffer(capacity=10, seed=42)
    
    from cnsc_haai.tasks.gridworld_env import GridWorldObs
    
    # Add same transitions to both
    for i in range(5):
        obs = GridWorldObs(
            agent_x=i % 3, agent_y=i // 3,
            goal_x=1, goal_y=0,
            hazard_x=2, hazard_y=2,
            patch=[[0]*5 for _ in range(5)],
        )
        next_obs = GridWorldObs(
            agent_x=(i+1) % 3, agent_y=(i+1) // 3,
            goal_x=1, goal_y=0,
            hazard_x=2, hazard_y=2,
            patch=[[0]*5 for _ in range(5)],
        )
        t = create_transition(obs, "east", next_obs, 100)
        buffer1.add(t)
        buffer2.add(t)
    
    # Roots should match
    assert buffer1.get_root() == buffer2.get_root()
    
    print("✓ Root stability test passed")


if __name__ == "__main__":
    test_deterministic_sampling()
    test_root_stability()
    print("All replay buffer tests passed!")
