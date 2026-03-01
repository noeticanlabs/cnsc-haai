"""
Memory Module - Replay Buffer

Implements bounded replay buffer with deterministic retention for Phase 2.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Optional
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
    
    For Phase 2, implements FIFO retention with hash-based pruning.
    """
    
    def __init__(self, capacity: int = 1000, retention_policy: str = "fifo"):
        """
        Initialize replay buffer.
        
        Args:
            capacity: Maximum number of transitions
            retention_policy: "fifo" or "priority" (future)
        """
        self.capacity = capacity
        self.retention_policy = retention_policy
        self.buffer: List[Transition] = []
    
    def add(self, transition: Transition):
        """
        Add transition, evict deterministically if full.
        
        Args:
            transition: Transition to add
        """
        if len(self.buffer) >= self.capacity:
            # Evict deterministically (FIFO)
            # Keep newer transitions (higher index)
            self.buffer = self.buffer[1:]
        
        self.buffer.append(transition)
    
    def sample_deterministic(
        self,
        batch_size: int,
        seed: int,
    ) -> List[Transition]:
        """
        Deterministic batch selection via hash-based indexing.
        
        Args:
            batch_size: Number of samples
            seed: Random seed for reproducibility
        
        Returns:
            List of transitions
        """
        if not self.buffer:
            return []
        
        # Generate deterministic indices
        indices = []
        h = seed
        
        for _ in range(batch_size):
            h = (h * 1103515245 + 12345) % (2**31)
            idx = h % len(self.buffer)
            indices.append(idx)
        
        # Return selected transitions
        return [self.buffer[i] for i in indices]
    
    def get_root(self) -> bytes:
        """
        Merkle root of all transitions for receipt.
        
        Returns:
            SHA256 hash of all transition hashes
        """
        if not self.buffer:
            return hashlib.sha256(b"EMPTY_BUFFER").digest()
        
        # Sort hashes for deterministic combining
        hashes = sorted([t.hash for t in self.buffer])
        combined = b"".join(hashes)
        return hashlib.sha256(combined).digest()
    
    def __len__(self) -> int:
        """Return buffer size."""
        return len(self.buffer)
    
    def clear(self):
        """Clear buffer."""
        self.buffer = []


# =============================================================================
# Helper Functions
# =============================================================================

def create_transition(
    obs: GridWorldObs,
    action: str,
    next_obs: GridWorldObs,
    reward: int,
) -> Transition:
    """
    Create a receipted transition.
    
    Args:
        obs: Current observation
        action: Action taken
        next_obs: Next observation
        reward: Reward received
    
    Returns:
        Transition with hash
    """
    # Create deterministic hash
    data = {
        'obs_distance': obs.distance_to_goal,
        'obs_delta': list(obs.goal_delta),
        'action': action,
        'next_distance': next_obs.distance_to_goal,
        'next_delta': list(next_obs.goal_delta),
        'reward': reward,
    }
    serialized = json.dumps(data, sort_keys=True)
    h = hashlib.sha256(serialized.encode()).digest()
    
    return Transition(
        obs=obs,
        action=action,
        next_obs=next_obs,
        reward=reward,
        hash=h,
    )
