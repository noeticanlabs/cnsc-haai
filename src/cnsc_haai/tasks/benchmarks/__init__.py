"""
Benchmark Tasks for Phase 3 Planning

These environments require multi-step lookahead planning:
- Key-Door Maze: Requires getting key before door
- Delayed Corridor: Short path has hazards, long path is safe
- Beacon Lag: POMDP with delayed/noisy beacon
"""

from .key_door_maze import KeyDoorMaze, create_key_door_maze
from .delayed_corridor import DelayedCorridor, create_delayed_corridor
from .beacon_lag import BeaconLag, create_beacon_lag

__all__ = [
    "KeyDoorMaze",
    "create_key_door_maze",
    "DelayedCorridor", 
    "create_delayed_corridor",
    "BeaconLag",
    "create_beacon_lag",
]
