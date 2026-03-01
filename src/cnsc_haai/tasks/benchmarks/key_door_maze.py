"""
Key-Door Maze - Benchmark Requiring Subgoal Planning

Environment:
- Start position
- Key (must be collected first)
- Door (blocks goal until key collected)
- Goal (behind door)
- Hazards (create dead-ends that greedy agents choose)

Why it forces planning:
- Reactive agents go directly to goal and get blocked by door
- Planner must plan to get key first, then go to goal
- Goal shifts slightly after door opens (requires re-planning)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, List, Optional, Dict
import hashlib
import random


# =============================================================================
# Cell Types
# =============================================================================

class CellType:
    EMPTY = 0
    WALL = 1
    START = 2
    KEY = 3
    DOOR = 4
    GOAL = 5
    HAZARD = 6


# =============================================================================
# Key-Door Maze State
# =============================================================================

@dataclass(frozen=True)
class KeyDoorMazeState:
    """
    State for Key-Door Maze.
    """
    position: Tuple[int, int]        # Current position (row, col)
    has_key: bool                    # Whether key has been collected
    door_open: bool                  # Whether door is open
    goal_position: Tuple[int, int]   # Current goal position
    key_position: Tuple[int, int]     # Key position
    door_position: Tuple[int, int]    # Door position
    step_count: int                  # Steps taken
    
    def is_goal_reached(self) -> bool:
        """Check if goal is reached."""
        return self.position == self.goal_position


@dataclass
class KeyDoorMaze:
    """
    Key-Door Maze environment.
    
    Requires multi-step lookahead to:
    1. Get the key first
    2. Open the door (automatic when at key position + door position adjacent)
    3. Go to goal
    """
    # Required fields
    width: int
    height: int
    start_position: Tuple[int, int]
    key_position: Tuple[int, int]
    door_position: Tuple[int, int]
    goal_position: Tuple[int, int]
    hazard_positions: Tuple[Tuple[int, int], ...]
    walls: Tuple[Tuple[int, int], ...]
    
    # Mutable state - default to None, initialize in __post_init__
    _state: KeyDoorMazeState = None
    
    def __post_init__(self):
        """Initialize the maze."""
        if self._state is None:
            self._state = KeyDoorMazeState(
            position=self.start_position,
            has_key=False,
            door_open=False,
            goal_position=self.goal_position,
            key_position=self.key_position,
            door_position=self.door_position,
            step_count=0,
        )
    
    @property
    def state(self) -> KeyDoorMazeState:
        """Get current state."""
        return self._state
    
    def get_obs(self) -> Dict:
        """Get observation (for partial observability if needed)."""
        return {
            "position": self._state.position,
            "has_key": self._state.has_key,
            "door_open": self._state.door_open,
            "goal": self._state.goal_position,
            "hazards": list(self.hazard_positions),
            "walls": list(self.walls),
        }
    
    def step(self, action: str) -> Tuple[KeyDoorMazeState, int, bool]:
        """
        Take a step in the maze.
        
        Args:
            action: One of "N", "S", "E", "W", "Stay"
        
        Returns:
            (new_state, reward, done)
        """
        row, col = self._state.position
        new_row, new_col = row, col
        
        # Compute new position
        if action == "N":
            new_row = max(0, row - 1)
        elif action == "S":
            new_row = min(self.height - 1, row + 1)
        elif action == "E":
            new_col = min(self.width - 1, col + 1)
        elif action == "W":
            new_col = max(0, col - 1)
        # Stay: no change
        
        new_position = (new_row, new_col)
        
        # Check for wall collision
        if new_position in self.walls:
            new_position = (row, col)  # Stay in place
        
        # Check for hazard - restart at start
        if new_position in self.hazard_positions:
            new_position = self.start_position
            self._state = KeyDoorMazeState(
                position=new_position,
                has_key=False,  # Lose key on hazard
                door_open=False,
                goal_position=self.goal_position,
                key_position=self.key_position,
                door_position=self.door_position,
                step_count=self._state.step_count + 1,
            )
            return self._state, -100, False
        
        # Check for key collection
        has_key = self._state.has_key
        if new_position == self.key_position:
            has_key = True
        
        # Check for door interaction
        door_open = self._state.door_open
        if has_key and (
            new_position == self.door_position or
            self._is_adjacent(new_position, self.door_position)
        ):
            door_open = True
        
        # Check if door blocks path
        if not door_open and new_position == self.door_position:
            # Door blocks - stay in place
            new_position = (row, col)
        
        # Check for goal
        goal_reached = new_position == self.goal_position
        
        # Compute reward
        reward = -1  # Step cost
        if goal_reached:
            reward += 100
        
        # Update state
        self._state = KeyDoorMazeState(
            position=new_position,
            has_key=has_key,
            door_open=door_open,
            goal_position=self.goal_position,
            key_position=self.key_position,
            door_position=self.door_position,
            step_count=self._state.step_count + 1,
        )
        
        return self._state, reward, goal_reached
    
    def _is_adjacent(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> bool:
        """Check if two positions are adjacent."""
        r1, c1 = pos1
        r2, c2 = pos2
        return abs(r1 - r2) + abs(c1 - c2) == 1
    
    def reset(self) -> KeyDoorMazeState:
        """Reset to initial state."""
        self._state = KeyDoorMazeState(
            position=self.start_position,
            has_key=False,
            door_open=False,
            goal_position=self.goal_position,
            key_position=self.key_position,
            door_position=self.door_position,
            step_count=0,
        )
        return self._state
    
    def get_hazard_positions(self) -> List[Tuple[int, int]]:
        """Get hazard positions for planner."""
        return list(self.hazard_positions)
    
    def get_grid_bounds(self) -> Tuple[int, int]:
        """Get grid bounds."""
        return (self.height, self.width)
    
    def render(self) -> str:
        """Render the maze as ASCII."""
        grid = [[" " for _ in range(self.width)] for _ in range(self.height)]
        
        # Add walls
        for (r, c) in self.walls:
            grid[r][c] = "#"
        
        # Add hazards
        for (r, c) in self.hazard_positions:
            grid[r][c] = "X"
        
        # Add special cells
        r, c = self.key_position
        grid[r][c] = "K"
        
        r, c = self.door_position
        if not self._state.door_open:
            grid[r][c] = "D"
        else:
            grid[r][c] = "d"  # Open door
        
        r, c = self.goal_position
        grid[r][c] = "G"
        
        # Add player
        r, c = self._state.position
        grid[r][c] = "@"
        
        return "\n".join("".join(row) for row in grid)


# =============================================================================
# Factory Functions
# =============================================================================

def create_key_door_maze(
    width: int = 8,
    height: int = 8,
    seed: int = 42,
) -> KeyDoorMaze:
    """
    Create a Key-Door Maze.
    
    Layout:
    ########
    #S    K#
    # ###  #
    # #    #
    # # ####
    # #    #
    #   D  G
    ########
    """
    random.seed(seed)
    
    # Define positions
    start = (1, 1)
    key = (1, 6)
    door = (6, 4)
    goal = (6, 6)
    
    # Create walls
    walls = []
    for r in range(height):
        walls.append((r, 0))
        walls.append((r, width - 1))
    for c in range(width):
        walls.append((0, c))
        walls.append((height - 1, c))
    
    # Interior walls
    walls.extend([
        (2, 2), (2, 3), (2, 4),
        (3, 2),
        (4, 2), (4, 3), (4, 4), (4, 5),
        (5, 2),
    ])
    
    # Hazards (dead-ends)
    hazards = [
        (1, 3),
        (3, 4),
        (5, 4),
    ]
    
    maze = KeyDoorMaze(
        width=width,
        height=height,
        start_position=start,
        key_position=key,
        door_position=door,
        goal_position=goal,
        hazard_positions=tuple(hazards),
        walls=tuple(walls),
    )
    
    return maze


# =============================================================================
# Testing
# =============================================================================

if __name__ == "__main__":
    maze = create_key_door_maze()
    print("Initial state:")
    print(maze.render())
    print()
    
    # Test: Try to go directly to goal (will fail)
    actions = ["E", "E", "E", "E", "E"]
    for a in actions:
        state, reward, done = maze.step(a)
        print(f"Action: {a}")
        print(maze.render())
        print(f"Reward: {reward}, Done: {done}")
        print()
        if done:
            break
