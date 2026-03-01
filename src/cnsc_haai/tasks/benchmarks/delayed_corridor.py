"""
Delayed Corridor - Benchmark Requiring Hazard Anticipation

Environment:
- Two corridors: short (ends in hazard trap) vs long (safe)
- Short path: 3 steps but leads to hazard
- Long path: 10 steps but safe

Why it forces planning:
- Reactive agents take short path and repeatedly hit hazard trap
- Planner must anticipate future hazard, choose long path
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, List, Optional, Dict
import hashlib
import random


# =============================================================================
# Delayed Corridor State
# =============================================================================

@dataclass(frozen=True)
class DelayedCorridorState:
    """
    State for Delayed Corridor.
    """
    position: int              # Position in corridor (0 = start)
    corridor_choice: int      # 0 = not chosen, 1 = short, 2 = long
    step_count: int            # Steps taken
    hazard_hits: int           # Times hit hazard
    
    def is_at_end(self) -> bool:
        """Check if at end of corridor."""
        return self.position < 0  # Negative = at hazard


@dataclass
class DelayedCorridor:
    """
    Delayed Corridor environment.
    
    Two corridors:
    - Short (3 steps): leads to hazard
    - Long (10 steps): leads to goal
    
    Reactive agents will keep taking short path and hitting hazard.
    Planner must choose long path.
    """
    # Mutable state - must come before fields with defaults
    _state: DelayedCorridorState = None
    
    # Configuration fields with defaults
    corridor_length_short: int = 3
    corridor_length_long: int = 10
    
    def __post_init__(self):
        """Initialize the corridor."""
        if self._state is None:
            self._state = DelayedCorridorState(
            position=0,
            corridor_choice=0,
            step_count=0,
            hazard_hits=0,
        )
    
    @property
    def state(self) -> DelayedCorridorState:
        """Get current state."""
        return self._state
    
    def get_obs(self) -> Dict:
        """Get observation."""
        return {
            "position": self._state.position,
            "corridor_choice": self._state.corridor_choice,
            "step_count": self._state.step_count,
            "hazard_hits": self._state.hazard_hits,
        }
    
    def step(self, action: str) -> Tuple[DelayedCorridorState, int, bool]:
        """
        Take a step in the corridor.
        
        Actions:
        - "EnterShort": Choose short corridor
        - "EnterLong": Choose long corridor
        - "Forward": Move forward in chosen corridor
        - "Stay": Stay in place
        
        Returns:
            (new_state, reward, done)
        """
        reward = -1  # Step cost
        done = False
        hazard_hits = self._state.hazard_hits
        
        if action == "EnterShort":
            # Choose short corridor
            new_state = DelayedCorridorState(
                position=1,  # Start of short corridor
                corridor_choice=1,
                step_count=self._state.step_count + 1,
                hazard_hits=self._state.hazard_hits,
            )
            self._state = new_state
            return self._state, reward, done
        
        elif action == "EnterLong":
            # Choose long corridor
            new_state = DelayedCorridorState(
                position=1,  # Start of long corridor
                corridor_choice=2,
                step_count=self._state.step_count + 1,
                hazard_hits=self._state.hazard_hits,
            )
            self._state = new_state
            return self._state, reward, done
        
        elif action == "Forward":
            # Move forward
            new_pos = self._state.position + 1
            
            # Check if reached end
            if self._state.corridor_choice == 1:
                # Short corridor - hazard at end
                if new_pos >= self.corridor_length_short:
                    # Hit hazard!
                    reward = -100
                    hazard_hits += 1
                    # Reset to start
                    new_state = DelayedCorridorState(
                        position=0,
                        corridor_choice=0,
                        step_count=self._state.step_count + 1,
                        hazard_hits=hazard_hits,
                    )
                    self._state = new_state
                    return self._state, reward, done
            elif self._state.corridor_choice == 2:
                # Long corridor - goal at end
                if new_pos >= self.corridor_length_long:
                    # Reached goal!
                    reward += 100
                    done = True
            
            new_state = DelayedCorridorState(
                position=new_pos,
                corridor_choice=self._state.corridor_choice,
                step_count=self._state.step_count + 1,
                hazard_hits=hazard_hits,
            )
            self._state = new_state
            return self._state, reward, done
        
        elif action == "Stay":
            # Stay in place
            new_state = DelayedCorridorState(
                position=self._state.position,
                corridor_choice=self._state.corridor_choice,
                step_count=self._state.step_count + 1,
                hazard_hits=self._state.hazard_hits,
            )
            self._state = new_state
            return self._state, reward, done
        
        # Unknown action - stay
        return self._state, reward, done
    
    def reset(self) -> DelayedCorridorState:
        """Reset to initial state."""
        self._state = DelayedCorridorState(
            position=0,
            corridor_choice=0,
            step_count=0,
            hazard_hits=0,
        )
        return self._state
    
    def get_hazard_positions(self) -> List[Tuple[int, int]]:
        """Get hazard positions (end of short corridor)."""
        # In this simple version, hazards are "virtual" - at end of short corridor
        return []
    
    def get_grid_bounds(self) -> Tuple[int, int]:
        """Get grid bounds."""
        return (1, max(self.corridor_length_short, self.corridor_length_long) + 1)
    
    def render(self) -> str:
        """Render the corridor as ASCII."""
        choice = self._state.corridor_choice
        
        if choice == 0:
            # At entrance
            return ">>> [Short/Long] <<<"
        elif choice == 1:
            # In short corridor
            pos = self._state.position
            path = ">" * pos + "@" + "X" * (self.corridor_length_short - pos - 1)
            return f"SHORT: {path}"
        elif choice == 2:
            # In long corridor
            pos = self._state.position
            path = ">" * pos + "@" + "G" * (self.corridor_length_long - pos - 1)
            return f"LONG:  {path}"
        
        return "???"


# =============================================================================
# Factory Functions
# =============================================================================

def create_delayed_corridor(
    short_length: int = 3,
    long_length: int = 10,
    seed: int = 42,
) -> DelayedCorridor:
    """
    Create a Delayed Corridor benchmark.
    """
    random.seed(seed)
    
    return DelayedCorridor(
        corridor_length_short=short_length,
        corridor_length_long=long_length,
    )


# =============================================================================
# Testing
# =============================================================================

if __name__ == "__main__":
    corridor = create_delayed_corridor()
    print("Initial state:")
    print(corridor.render())
    print()
    
    # Test: Keep taking short path (will hit hazard repeatedly)
    print("Testing reactive behavior (short path):")
    for _ in range(5):
        corridor.reset()
        corridor.step("EnterShort")
        for _ in range(10):
            state, reward, done = corridor.step("Forward")
            print(f"Position: {state.position}, Reward: {reward}, Done: {done}")
            if done:
                break
        print(f"Hazard hits so far: {state.hazard_hits}")
    print()
    
    # Test: Take long path
    print("Testing long path:")
    corridor.reset()
    corridor.step("EnterLong")
    for _ in range(15):
        state, reward, done = corridor.step("Forward")
        print(f"Position: {state.position}, Reward: {reward}, Done: {done}")
        if done:
            print("Success!")
            break
