"""
Batching - Deterministic Batch Selection for Learning

Provides deterministic batch selection for replay buffer with receiptable indices.
"""

from __future__ import annotations
from typing import List, Tuple, Optional
import hashlib

from cnsc_haai.memory.replay_buffer import ReplayBuffer, Transition


# =============================================================================
# Deterministic Batch Selection
# =============================================================================

def select_batch_deterministic(
    buffer: ReplayBuffer,
    batch_size: int,
    seed: int,
) -> List[Transition]:
    """
    Select batch using deterministic LCG-based indexing.
    
    Args:
        buffer: Replay buffer to sample from
        batch_size: Number of transitions to select
        seed: Seed for deterministic sampling
    
    Returns:
        List of selected transitions
    """
    return buffer.sample_deterministic(batch_size, seed)


def select_batch_by_hash(
    buffer: ReplayBuffer,
    batch_size: int,
    step_index: int,
) -> Tuple[List[Transition], List[int]]:
    """
    Select batch using hash-based indexing for receiptable selection.
    
    Returns both the transitions and their indices for receipting.
    
    Args:
        buffer: Replay buffer to sample from
        batch_size: Number of transitions to select
        step_index: Current step number (used in hash)
    
    Returns:
        Tuple of (transitions, indices)
    """
    if not buffer.buffer:
        return [], []
    
    indices = []
    result = []
    buffer_root = buffer.get_root()
    
    for i in range(batch_size):
        # Hash = f(buffer_root, step_index, i)
        h_input = f"{buffer_root.hex()}:{step_index}:{i}".encode()
        h = hashlib.sha256(h_input).digest()
        idx = int.from_bytes(h[:4], 'big') % len(buffer.buffer)
        indices.append(idx)
        result.append(buffer.buffer[idx])
    
    return result, indices


def compute_batch_root(
    transitions: List[Transition],
) -> bytes:
    """
    Compute Merkle root of a batch of transitions.
    
    Args:
        transitions: List of transitions
    
    Returns:
        SHA256 hash of all transition hashes
    """
    if not transitions:
        return hashlib.sha256(b"EMPTY_BATCH").digest()
    
    hashes = sorted([t.hash for t in transitions])
    combined = b"".join(hashes)
    return hashlib.sha256(combined).digest()


def select_batch_with_receipt(
    buffer: ReplayBuffer,
    batch_size: int,
    step_index: int,
    seed: int,
) -> Tuple[List[Transition], bytes, List[int]]:
    """
    Select batch and compute receipt data.
    
    This combines hash-based selection (for receiptability) with
    seed-based selection (for determinism).
    
    Args:
        buffer: Replay buffer
        batch_size: Number of transitions
        step_index: Current step (for hash)
        seed: Seed for deterministic selection
    
    Returns:
        Tuple of (transitions, batch_root, indices)
    """
    # Use hash-based selection for receiptability
    transitions, indices = select_batch_by_hash(buffer, batch_size, step_index)
    
    # Compute batch root for receipt
    batch_root = compute_batch_root(transitions)
    
    return transitions, batch_root, indices


# =============================================================================
# Batch Statistics
# =============================================================================

def compute_batch_statistics(
    batch: List[Transition],
) -> dict:
    """
    Compute statistics about a batch.
    
    Args:
        batch: List of transitions
    
    Returns:
        Dictionary with batch statistics
    """
    if not batch:
        return {
            'size': 0,
            'total_reward': 0,
            'avg_reward': 0,
        }
    
    total_reward = sum(t.reward for t in batch)
    return {
        'size': len(batch),
        'total_reward': total_reward,
        'avg_reward': total_reward // len(batch),
    }


# =============================================================================
# Tests
# =============================================================================

def test_deterministic_batch():
    """Test that batch selection is deterministic."""
    from cnsc_haai.tasks.gridworld_env import GridWorldObs
    from cnsc_haai.memory.replay_buffer import create_transition
    
    buffer = ReplayBuffer(capacity=100, seed=42)
    
    # Add transitions
    for i in range(10):
        obs = GridWorldObs(
            agent_x=i, agent_y=0,
            goal_x=1, goal_y=0,
            hazard_x=5, hazard_y=5,
            patch=[[0]*5 for _ in range(5)],
        )
        next_obs = GridWorldObs(
            agent_x=i+1, agent_y=0,
            goal_x=1, goal_y=0,
            hazard_x=5, hazard_y=5,
            patch=[[0]*5 for _ in range(5)],
        )
        t = create_transition(obs, "east", next_obs, 100)
        buffer.add(t)
    
    # Sample twice with same seed
    batch1 = select_batch_deterministic(buffer, 5, seed=100)
    batch2 = select_batch_deterministic(buffer, 5, seed=100)
    
    # Should be identical
    assert len(batch1) == len(batch2) == 5
    for t1, t2 in zip(batch1, batch2):
        assert t1.hash == t2.hash
    
    print("✓ Deterministic batch test passed")


def test_hash_based_batch():
    """Test hash-based batch selection."""
    from cnsc_haai.tasks.gridworld_env import GridWorldObs
    from cnsc_haai.memory.replay_buffer import create_transition
    
    buffer = ReplayBuffer(capacity=100, seed=42)
    
    # Add transitions
    for i in range(10):
        obs = GridWorldObs(
            agent_x=i, agent_y=0,
            goal_x=1, goal_y=0,
            hazard_x=5, hazard_y=5,
            patch=[[0]*5 for _ in range(5)],
        )
        next_obs = GridWorldObs(
            agent_x=i+1, agent_y=0,
            goal_x=1, goal_y=0,
            hazard_x=5, hazard_y=5,
            patch=[[0]*5 for _ in range(5)],
        )
        t = create_transition(obs, "east", next_obs, 100)
        buffer.add(t)
    
    # Sample with hash-based method
    batch, indices = select_batch_by_hash(buffer, 5, step_index=100)
    
    assert len(batch) == 5
    assert len(indices) == 5
    
    # Sample again with same step_index - should be identical
    batch2, indices2 = select_batch_by_hash(buffer, 5, step_index=100)
    assert indices == indices2
    
    # Different step_index should give different results
    batch3, indices3 = select_batch_by_hash(buffer, 5, step_index=200)
    assert indices != indices3
    
    print("✓ Hash-based batch test passed")


if __name__ == "__main__":
    test_deterministic_batch()
    test_hash_based_batch()
    print("All batching tests passed!")
