"""
Deterministic Gridworld Environment for CLATL

A deterministic gridworld with:
- Walls (impassable)
- Hazards (unsafe states - violations if agent enters)
- Drifting goal (non-stationary objective)
- Partial observability (local patch)

All randomness is deterministic via seeded PRNG.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, List, Optional
import hashlib
import json

# Cell types
CELL_EMPTY = 0
CELL_WALL = 1
CELL_HAZARD = 2
CELL_GOAL = 3

# Actions
ACTIONS = ('N', 'S', 'E', 'W', 'Stay')


@dataclass(frozen=True)
class GridWorldState:
    """
    Grid world state - completely deterministic.
    
    All fields are immutable for receipt verification.
    """
    position: Tuple[int, int]      # Agent position (x, y)
    goal: Tuple[int, int]          # Current goal position
    grid: Tuple[Tuple[int, ...], ...]  # Immutable grid (0=empty, 1=wall, 2=hazard, 3=goal)
    t: int                          # Step counter
    drift_seed: int                 # Seed for deterministic goal drift
    
    def __post_init__(self):
        """Validate state."""
        if not isinstance(self.grid, tuple):
            # Convert list to tuple for immutability
            object.__setattr__(self, 'grid', tuple(tuple(row) for row in self.grid))


@dataclass(frozen=True)
class GridWorldObs:
    """
    Observation: local patch + goal beacon.
    
    Minimal observation - proposer receives (state, obs) to access full state.
    """
    local_patch: Tuple[Tuple[int, ...], ...]  # 5x5 view centered on agent
    goal_delta: Tuple[int, int]                # (dx, dy) to goal
    distance_to_goal: int                      # Manhattan distance


def create_gridworld(
    width: int,
    height: int,
    walls: List[Tuple[int, int]],
    hazards: List[Tuple[int, int]],
) -> Tuple[Tuple[int, ...], ...]:
    """
    Create a gridworld map.
    
    Args:
        width: Grid width
        height: Grid height
        walls: List of wall positions
        hazards: List of hazard positions
    
    Returns:
        Immutable grid tuple
    """
    grid = [[CELL_EMPTY for _ in range(width)] for _ in range(height)]
    
    for x, y in walls:
        if 0 <= x < width and 0 <= y < height:
            grid[y][x] = CELL_WALL
            
    for x, y in hazards:
        if 0 <= x < width and 0 <= y < height:
            grid[y][x] = CELL_HAZARD
    
    return tuple(tuple(row) for row in grid)


def create_initial_state(
    grid: Tuple[Tuple[int, ...], ...],
    start: Tuple[int, int],
    goal: Tuple[int, int],
    drift_seed: int = 42,
) -> GridWorldState:
    """
    Create initial state with seeded drift generator.
    
    Args:
        grid: The gridworld map
        start: Starting position
        goal: Initial goal position
        drift_seed: Seed for deterministic goal drift
    
    Returns:
        Initial GridWorldState
    """
    # Validate positions
    height = len(grid)
    width = len(grid[0]) if height > 0 else 0
    
    assert 0 <= start[0] < width, f"start[0] out of bounds: {start[0]}"
    assert 0 <= start[1] < height, f"start[1] out of bounds: {start[1]}"
    assert 0 <= goal[0] < width, f"goal[0] out of bounds: {goal[0]}"
    assert 0 <= goal[1] < height, f"goal[1] out of bounds: {goal[1]}"
    
    # Ensure start and goal are not on walls/hazards
    assert grid[start[1]][start[0]] != CELL_WALL, "Start cannot be on wall"
    assert grid[goal[1]][goal[0]] != CELL_WALL, "Goal cannot be on wall"
    
    return GridWorldState(
        position=start,
        goal=goal,
        grid=grid,
        t=0,
        drift_seed=drift_seed,
    )


def _apply_action(position: Tuple[int, int], action: str, grid: Tuple[Tuple[int, ...], ...]) -> Tuple[int, int]:
    """
    Apply action to position, checking for walls.
    
    Args:
        position: Current (x, y)
        action: Action to apply
        grid: The gridworld map
    
    Returns:
        New position (stays in place if wall)
    """
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
        if grid[new_pos[1]][new_pos[0]] != CELL_WALL:
            return new_pos
    
    # Hit wall or out of bounds - stay in place
    return position


def env_step(
    state: GridWorldState,
    action: str,
) -> Tuple[GridWorldState, int]:
    """
    Deterministic step function.
    
    Args:
        state: Current state
        action: Action to apply ('N', 'S', 'E', 'W', 'Stay')
    
    Returns:
        (next_state, reward)
        - reward: -1 per step, +100 for reaching goal, -50 for hazard (but should be prevented)
    """
    assert action in ACTIONS, f"Invalid action: {action}"
    
    # Apply action
    new_position = _apply_action(state.position, action, state.grid)
    
    # Check what we landed on
    cell = state.grid[new_position[1]][new_position[0]]
    
    # Compute reward
    if new_position == state.goal:
        reward = 100  # Reached goal!
    elif cell == CELL_HAZARD:
        reward = -50  # Hit hazard (should be prevented by governor)
    else:
        reward = -1  # Normal step cost
    
    # Update state
    new_state = GridWorldState(
        position=new_position,
        goal=state.goal,
        grid=state.grid,
        t=state.t + 1,
        drift_seed=state.drift_seed,
    )
    
    return new_state, reward


def get_observation(state: GridWorldState) -> GridWorldObs:
    """
    Get observation from state.
    
    Returns local 5x5 patch centered on agent plus goal beacon.
    
    Args:
        state: Current state
    
    Returns:
        GridWorldObs
    """
    x, y = state.position
    gx, gy = state.goal
    grid = state.grid
    
    height = len(grid)
    width = len(grid[0]) if height > 0 else 0
    
    # Build 5x5 local patch
    patch_size = 2  # 2 cells in each direction = 5x5 total
    patch = []
    
    for dy in range(-patch_size, patch_size + 1):
        row = []
        for dx in range(-patch_size, patch_size + 1):
            px, py = x + dx, y + dy
            if 0 <= px < width and 0 <= py < height:
                row.append(grid[py][px])
            else:
                row.append(CELL_WALL)  # Out of bounds = wall
        patch.append(tuple(row))
    
    # Goal delta (direction to goal)
    goal_delta = (gx - x, gy - y)
    
    # Manhattan distance
    distance = abs(gx - x) + abs(gy - y)
    
    return GridWorldObs(
        local_patch=tuple(patch),
        goal_delta=goal_delta,
        distance_to_goal=distance,
    )


class DeterministicDrift:
    """
    Deterministic goal drift generator.
    
    Uses linear congruential generator for reproducible sequences.
    """
    
    def __init__(self, seed: int):
        """Initialize with seed."""
        self._seed = seed
        self._state = seed
    
    def next_position(self, current_goal: Tuple[int, int], grid: Tuple[Tuple[int, ...], ...]) -> Tuple[int, int]:
        """
        Generate next goal position deterministically.
        
        Args:
            current_goal: Current goal position
            grid: The gridworld map
        
        Returns:
            New goal position
        """
        height = len(grid)
        width = len(grid[0]) if height > 0 else 0
        
        # LCG parameters (same as ANSI C)
        a = 1103515245
        c = 12345
        m = 2**31
        
        self._state = (a * self._state + c) % m
        
        # Generate new position that is reachable (not on wall/hazard)
        for _ in range(100):  # Max attempts
            new_x = (self._state % width)
            new_y = ((self._state // width) % height)
            
            cell = grid[new_y][new_x] if (0 <= new_x < width and 0 <= new_y < height) else CELL_WALL
            
            if cell == CELL_EMPTY:  # Only on empty cells
                return (new_x, new_y)
            
            # Try next
            self._state = (a * self._state + c) % m
        
        # Fallback: return current goal
        return current_goal


def drift_goal(state: GridWorldState, step: int) -> GridWorldState:
    """
    Drift the goal to a new position.
    
    Deterministic based on step and drift_seed.
    
    Args:
        state: Current state
        step: Current step number
    
    Returns:
        New state with drifted goal
    """
    # Create deterministic drift generator
    # Seed combines drift_seed and step for reproducibility
    combined_seed = (state.drift_seed * 1000000) + step
    drift_gen = DeterministicDrift(combined_seed)
    
    new_goal = drift_gen.next_position(state.goal, state.grid)
    
    # to Don't drift current position
    if new_goal == state.position:
        return state
    
    return GridWorldState(
        position=state.position,
        goal=new_goal,
        grid=state.grid,
        t=state.t,
        drift_seed=state.drift_seed,
    )


def hash_gridworld_state(state: GridWorldState) -> bytes:
    """
    Compute hash of gridworld state for receipts.
    
    Args:
        state: GridWorldState
    
    Returns:
        SHA256 hash bytes
    """
    data = {
        'position': list(state.position),
        'goal': list(state.goal),
        'grid': [list(row) for row in state.grid],
        't': state.t,
        'drift_seed': state.drift_seed,
    }
    serialized = json.dumps(data, sort_keys=True)
    return hashlib.sha256(serialized.encode()).digest()


# Standard gridworld layouts

def create_standard_grid(
    layout: str = "simple",
) -> Tuple[Tuple[Tuple[int, ...], ...], Tuple[int, int], Tuple[int, int]]:
    """
    Create a standard gridworld layout.
    
    Args:
        layout: Layout name ('simple', 'maze', 'hazard')
    
    Returns:
        (grid, start, goal)
    """
    if layout == "simple":
        grid = create_gridworld(10, 10, walls=[], hazards=[])
        return grid, (0, 0), (9, 9)
    
    elif layout == "maze":
        walls = [
            (3, 0), (3, 1), (3, 2), (3, 3),
            (3, 5), (3, 6), (3, 7), (3, 8), (3, 9),
            (6, 1), (6, 2), (6, 3), (6, 4), (6, 5),
            (6, 7), (6, 8), (6, 9),
        ]
        grid = create_gridworld(10, 10, walls=walls, hazards=[])
        return grid, (0, 0), (9, 9)
    
    elif layout == "hazard":
        hazards = [
            (2, 2), (2, 3), (2, 4),
            (5, 5), (5, 6), (5, 7),
            (7, 2), (7, 3),
        ]
        walls = [
            (4, 0), (4, 1), (4, 2),
        ]
        grid = create_gridworld(10, 10, walls=walls, hazards=hazards)
        return grid, (0, 0), (9, 9)
    
    else:
        raise ValueError(f"Unknown layout: {layout}")


# =============================================================================
# GridWorldEnv Wrapper Class (for compatibility)
# =============================================================================

class GridWorldEnv:
    """
    Wrapper class for gridworld environment.
    
    Provides a gym-like interface for the functional gridworld API.
    """
    
    def __init__(
        self,
        width: int = 10,
        height: int = 10,
        start_x: int = 0,
        start_y: int = 0,
        goal_x: int = 9,
        goal_y: int = 9,
        hazard_x: int = 5,
        hazard_y: int = 5,
        walls: list = None,
        hazards: list = None,
        max_steps: int = 100,
        seed: int = 42,
        enable_goal_drift: bool = False,
    ):
        """
        Initialize GridWorldEnv.
        
        Args:
            width: Grid width
            height: Grid height
            start_x: Starting X position
            start_y: Starting Y position
            goal_x: Goal X position
            goal_y: Goal Y position
            hazard_x: Hazard X position
            hazard_y: Hazard Y position
            walls: List of (x, y) wall positions
            hazards: List of (x, y) hazard positions
            max_steps: Maximum steps per episode
            seed: Random seed for determinism
            enable_goal_drift: Whether goal drifts
        """
        self.width = width
        self.height = height
        self.max_steps = max_steps
        self.seed = seed
        self.enable_goal_drift = enable_goal_drift
        
        # Build walls and hazards
        if walls is None:
            walls = []
        if hazards is None:
            hazards = [(hazard_x, hazard_y)]
        
        # Create grid
        self.grid = create_gridworld(width, height, walls=walls, hazards=hazards)
        
        # Create initial state
        self.initial_state = create_initial_state(
            grid=self.grid,
            start=(start_x, start_y),
            goal=(goal_x, goal_y),
            drift_seed=seed,
        )
        
        self._state = self.initial_state
        self._step_count = 0
    
    def reset(self) -> GridWorldObs:
        """Reset environment and return initial observation."""
        self._state = self.initial_state
        self._step_count = 0
        return get_observation(self._state)
    
    def step(self, action: str) -> tuple:
        """
        Take a step in the environment.
        
        Args:
            action: Action string ('north', 'south', 'east', 'west', 'stay')
        
        Returns:
            Tuple of (observation, reward, done, info)
        """
        # Map action string to action
        action_map = {
            'north': 'N',
            'south': 'S',
            'east': 'E',
            'west': 'W',
            'stay': 'Stay',
        }
        mapped_action = action_map.get(action, action)
        
        # Take step (returns only state and reward)
        next_state, reward = env_step(self._state, mapped_action)
        
        # Apply goal drift if enabled
        if self.enable_goal_drift:
            next_state = drift_goal(next_state, self._step_count)
        
        # Update state
        self._state = next_state
        self._step_count += 1
        
        # Check if done (goal reached)
        done = (next_state.position == next_state.goal)
        
        # Also check max steps
        if self._step_count >= self.max_steps:
            done = True
        
        # Get observation
        obs = get_observation(next_state)
        
        # Info
        info = {
            'state': next_state,
            'position': next_state.position,
            'goal': next_state.goal,
            'step': self._step_count,
        }
        
        return obs, reward, done, info
    
    @property
    def agent_x(self) -> int:
        """Get agent X position."""
        return self._state.position[0]
    
    @property
    def agent_y(self) -> int:
        """Get agent Y position."""
        return self._state.position[1]
    
    @property
    def goal_x(self) -> int:
        """Get goal X position."""
        return self._state.goal[0]
    
    @property
    def goal_y(self) -> int:
        """Get goal Y position."""
        return self._state.goal[1]
