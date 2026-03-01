"""
Task Proposer for CLATL

Generates proposals with deterministic exploration bonus.
Implements: Score = -V_task + α(budget) * 1/sqrt(N(s) + 1)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
import hashlib
import json

# Import from tasks
from cnsc_haai.tasks.gridworld_env import (
    GridWorldState,
    GridWorldObs,
    ACTIONS,
    CELL_EMPTY,
)


# =============================================================================
# Proposal Types
# =============================================================================

@dataclass(frozen=True)
class TaskProposal:
    """
    Proposal for gridworld action.
    
    Immutable for deterministic receipt generation.
    """
    action: str                              # 'N', 'S', 'E', 'W', 'Stay'
    expected_next_position: Tuple[int, int] # Predicted next position
    V_task_proposal: int                    # Predicted task loss after action
    task_score: int                         # Score based on task (higher = better)
    exploration_bonus: int                  # Exploration bonus component
    
    def hash(self) -> bytes:
        """Compute hash of proposal for receipt."""
        data = {
            'action': self.action,
            'position': list(self.expected_next_position),
            'V_task': self.V_task_proposal,
            'score': self.task_score,
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).digest()


# =============================================================================
# Exploration Parameters
# =============================================================================

@dataclass
class ExplorationParams:
    """
    Parameters for deterministic exploration.
    
    Exploration is governed by remaining budget.
    """
    exploration_weight: int = 500_000  # QFixed: 0.5 - weight for exploration
    base_budget: int = 10_000_000      # QFixed: 10.0 - reference budget
    

# =============================================================================
# Visitation Memory
# =============================================================================

class VisitationMemory:
    """
    Tracks state visitation counts for deterministic exploration.
    
    Uses state position hash as key.
    """
    
    def __init__(self):
        self._counts: Dict[Tuple[int, int], int] = {}
    
    def get_count(self, position: Tuple[int, int]) -> int:
        """Get visitation count for position."""
        return self._counts.get(position, 0)
    
    def increment(self, position: Tuple[int, int]) -> int:
        """Increment count and return new count."""
        current = self._counts.get(position, 0)
        new_count = current + 1
        self._counts[position] = new_count
        return new_count
    
    def reset(self):
        """Reset memory."""
        self._counts.clear()


# =============================================================================
# Task Proposer
# =============================================================================

class TaskProposer:
    """
    Generates proposals for gridworld actions.
    
    Uses deterministic exploration bonus:
    Score = -V_task + α(b) * 1/sqrt(N(s) + 1)
    
    Where α(b) = min(b / base_budget, 1) - shrinks as budget depletes
    """
    
    def __init__(self, exploration_params: Optional[ExplorationParams] = None):
        self.exploration_params = exploration_params or ExplorationParams()
        self.memory = VisitationMemory()
    
    def propose(
        self,
        state: GridWorldState,
        obs: GridWorldObs,
        V_coh: int,
        memory: Optional[VisitationMemory] = None,
    ) -> List[TaskProposal]:
        """
        Generate proposal set with deterministic exploration bonus.
        
        Args:
            state: Current gridworld state (for position access)
            obs: Current observation
            V_coh: Current coherence Lyapunov value (for reference)
            memory: Visitation memory (uses internal if not provided)
        
        Returns:
            List of TaskProposal (immutable, receiptable)
        """
        mem = memory or self.memory
        
        # Compute exploration factor based on position
        # Note: We use position for exploration, not budget
        # (budget is enforced by governor)
        pos = state.position
        N = mem.get_count(pos)
        
        # Deterministic exploration: 1/sqrt(N + 1)
        # This gives more exploration for less-visited states
        visit_exploration = self._compute_visitation_bonus(N)
        
        # Generate proposals for all actions
        proposals = []
        
        for action in ACTIONS:
            # Compute expected next position
            next_pos = self._apply_action(state.position, action, state.grid)
            
            # Compute predicted task loss (distance from next position to goal)
            V_task = self._distance_to_goal(next_pos, state.goal)
            
            # Compute exploration bonus (deterministic based on visitation)
            # Note: exploration bonus decreases with more visits
            exploration = visit_exploration  # Same for all actions in same state
            
            # Score: task is NEGATIVE (lower distance = better)
            # We want HIGHER score = better, so negate
            task_score = -V_task * 1_000_000  # Scale to QFixed
            
            proposals.append(TaskProposal(
                action=action,
                expected_next_position=next_pos,
                V_task_proposal=V_task,
                task_score=task_score,
                exploration_bonus=exploration,
            ))
        
        return proposals
    
    def _apply_action(
        self,
        position: Tuple[int, int],
        action: str,
        grid: Tuple[Tuple[int, ...], ...],
    ) -> Tuple[int, int]:
        """Apply action to position, checking for walls."""
        x, y = position
        height = len(grid)
        width = len(grid[0]) if height > 0 else 0
        
        if action == 'N':
            new_pos = (x, y - 1)
        elif action == 'S':
            new_pos = (x, y + 1)
        elif action == 'E':
            new_pos = (x + 1, y)
        elif action == 'W':
            new_pos = (x - 1, y)
        elif action == 'Stay':
            new_pos = (x, y)
        else:
            new_pos = (x, y)
        
        # Check bounds and walls
        if 0 <= new_pos[0] < width and 0 <= new_pos[1] < height:
            if grid[new_pos[1]][new_pos[0]] != 1:  # Not a wall
                return new_pos
        
        return position
    
    def _distance_to_goal(
        self,
        position: Tuple[int, int],
        goal: Tuple[int, int],
    ) -> int:
        """Compute Manhattan distance to goal."""
        return abs(goal[0] - position[0]) + abs(goal[1] - position[1])
    
    def _compute_visitation_bonus(self, N: int) -> int:
        """
        Compute deterministic exploration bonus.
        
        Returns: QFixed integer
        """
        # 1/sqrt(N + 1)
        # N=0: 1.0, N=1: 0.707, N=3: 0.5, N=8: 0.333
        import math
        bonus = 1.0 / math.sqrt(N + 1)
        
        # Scale to QFixed
        return int(bonus * 1_000_000)
    
    def reset_memory(self):
        """Reset visitation memory between episodes."""
        self.memory.reset()


# =============================================================================
# Proposal Set Utilities
# =============================================================================

def build_proposalset_root(proposals: List[TaskProposal]) -> bytes:
    """
    Build Merkle root from proposal set.
    
    For deterministic receipt - commits to entire proposal set.
    
    Args:
        proposals: List of TaskProposal
    
    Returns:
        SHA256 hash as root commitment
    """
    if not proposals:
        return hashlib.sha256(b"EMPTY_PROPOSAL_SET").digest()
    
    # Sort proposals by action for deterministic ordering
    sorted_proposals = sorted(proposals, key=lambda p: p.action)
    
    # Hash each proposal
    leaves = [p.hash() for p in sorted_proposals]
    
    # Build simple Merkle tree (or just hash all for simplicity)
    # For small sets (5 proposals), just hash them together
    combined = b"".join(sorted(leaves))
    return hashlib.sha256(combined).digest()


def find_proposal_index(
    proposals: List[TaskProposal],
    selected: TaskProposal,
) -> int:
    """
    Find index of selected proposal in proposal set.
    
    Args:
        proposals: The full proposal set
        selected: The selected proposal
    
    Returns:
        Index of selected proposal
    """
    # Sort for consistent indexing
    sorted_proposals = sorted(proposals, key=lambda p: p.action)
    
    for i, p in enumerate(sorted_proposals):
        if p.action == selected.action:
            return i
    
    raise ValueError("Selected proposal not in proposal set")
