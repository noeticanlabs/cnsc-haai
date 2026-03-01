"""
Beacon Lag - POMDP Benchmark with Delayed/Noisy Beacon

Environment:
- Goal beacon that is delayed and noisy
- Agent must infer true goal position from dynamics
- Partial observability

Why it forces planning:
- Reactive agents dither (random walk) due to noisy beacon
- Planner integrates belief-like behavior via model, anticipates true goal
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, List, Optional, Dict
import hashlib
import random


# =============================================================================
# Beacon Lag State
# =============================================================================

@dataclass(frozen=True)
class BeaconLagState:
    """
    State for Beacon Lag.
    """
    position: Tuple[int, int]    # Current position
    beacon_noisy: Tuple[int, int]  # Noisy beacon reading
    true_goal: Tuple[int, int]     # True goal position
    step_count: int               # Steps taken
    
    def is_at_goal(self) -> bool:
        """Check if at goal."""
        return self.position == self.true_goal


@dataclass
class BeaconLag:
    """
    Beacon Lag environment - POMDP with delayed/noisy beacon.
    
    The beacon provides noisy information about goal direction.
    The agent must use the model to infer true goal and plan accordingly.
    """
    # Required fields first
    width: int
    height: int
    start_position: Tuple[int, int]
    true_goal: Tuple[int, int]
    
    # Mutable state - must come before fields with defaults
    _state: BeaconLagState = None
    _beacon_history: List[Tuple[int, int]] = None
    
    # Configuration fields with defaults
    noise_std: int = 2           # Beacon noise standard deviation
    beacon_delay: int = 2         # Steps before beacon updates
    
    def __post_init__(self):
        """Initialize the environment."""
        if self._beacon_history is None:
            self._beacon_history = []
        if self._state is None:
            self._state = BeaconLagState(
            position=self.start_position,
            beacon_noisy=self._get_beacon_reading(self.start_position),
            true_goal=self.true_goal,
            step_count=0,
        )
    
    @property
    def state(self) -> BeaconLagState:
        """Get current state."""
        return self._state
    
    def _get_beacon_reading(self, position: Tuple[int, int]) -> Tuple[int, int]:
        """Get noisy beacon reading."""
        row, col = self.true_goal
        
        # Add noise
        noise_row = random.gauss(0, self.noise_std)
        noise_col = random.gauss(0, self.noise_std)
        
        return (
            int(row + noise_row),
            int(col + noise_col),
        )
    
    def get_obs(self) -> Dict:
        """Get observation (POMDP - no direct goal position)."""
        return {
            "position": self._state.position,
            "beacon": self._state.beacon_noisy,
            "step_count": self._state.step_count,
        }
    
    def step(self, action: str) -> Tuple[BeaconLagState, int, bool]:
        """
        Take a step.
        
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
        
        new_position = (new_row, new_col)
        
        # Update beacon with delay
        beacon = self._state.beacon_noisy
        if self._state.step_count >= self.beacon_delay:
            beacon = self._get_beacon_reading(new_position)
        
        # Check for goal
        goal_reached = new_position == self.true_goal
        
        # Compute reward
        # Negative distance to goal
        dist = abs(new_row - self.true_goal[0]) + abs(new_col - self.true_goal[1])
        reward = -dist
        
        if goal_reached:
            reward += 100
        
        # Update state
        self._state = BeaconLagState(
            position=new_position,
            beacon_noisy=beacon,
            true_goal=self.true_goal,
            step_count=self._state.step_count + 1,
        )
        
        return self._state, reward, goal_reached
    
    def reset(self) -> BeaconLagState:
        """Reset to initial state."""
        self._state = BeaconLagState(
            position=self.start_position,
            beacon_noisy=self._get_beacon_reading(self.start_position),
            true_goal=self.true_goal,
            step_count=0,
        )
        return self._state
    
    def get_hazard_positions(self) -> List[Tuple[int, int]]:
        """Get hazard positions (none in this benchmark)."""
        return []
    
    def get_grid_bounds(self) -> Tuple[int, int]:
        """Get grid bounds."""
        return (self.height, self.width)
    
    def render(self) -> str:
        """Render as ASCII."""
        grid = [[" " for _ in range(self.width)] for _ in range(self.height)]
        
        # Add goal (hidden)
        gr, gc = self.true_goal
        # Don't show true goal
        
        # Add player
        pr, pc = self._state.position
        grid[pr][pc] = "@"
        
        # Add beacon indicator
        br, bc = self._beacon_history[-1] if self._beacon_history else (pr, pc)
        
        result = "\n".join("".join(row) for row in grid)
        result += f"\nBeacon: ({br}, {bc})"
        result += f"\nTrue Goal: ({gr}, {gc})"
        
        return result


# =============================================================================
# Factory Functions
# =============================================================================

def create_beacon_lag(
    width: int = 10,
    height: int = 10,
    noise_std: int = 2,
    beacon_delay: int = 2,
    seed: int = 42,
) -> BeaconLag:
    """
    Create a Beacon Lag benchmark.
    """
    random.seed(seed)
    
    return BeaconLag(
        width=width,
        height=height,
        start_position=(1, 1),
        true_goal=(8, 8),
        noise_std=noise_std,
        beacon_delay=beacon_delay,
    )


# =============================================================================
# Testing
# =============================================================================

if __name__ == "__main__":
    env = create_beacon_lag(noise_std=2)
    print("Initial state:")
    print(env.render())
    print()
    
    # Random walk (reactive baseline)
    print("Testing random walk:")
    for _ in range(20):
        actions = ["N", "S", "E", "W"]
        action = random.choice(actions)
        state, reward, done = env.step(action)
        print(f"Action: {action}, Pos: {state.position}, Reward: {reward}, Done: {done}")
        if done:
            print("Success!")
            break
