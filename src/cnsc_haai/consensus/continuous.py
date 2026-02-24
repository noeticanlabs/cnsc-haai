"""
Continuous Trajectory Module

Provides continuous trajectory interface wrapping discrete step engine.
Per docs/ats/10_mathematical_core/continuous_manifold_flow.md

This module wraps the discrete ATS step engine to provide continuous-time
trajectories while maintaining determinism (no floating serialization).
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

# Use QFixed for all numeric values (no floats)
QFIXED_SCALE = 10**18  # 18 decimal places

# =============================================================================
# CANONICAL STEPPING POLICY
# =============================================================================
# 
# This is the ONLY legal way to convert continuous time (dt) to discrete steps.
# All nodes must use this policy for consensus to be achievable.
#
# Policy: DISCRETE_MICRO_STEPS
#   - 1:1 mapping: dt_q units = dt_q steps
#   - Each step represents 1 QFixed unit of time
#   - Rounding: floor (dt_q // STEP_UNIT_Q)
#
# CANONICAL CONSTANTS
CANONICAL_STEPPING_POLICY = "DISCRETE_MICRO_STEPS"
CANONICAL_STEP_UNIT_Q = QFIXED_SCALE  # 1 step = 10^18 QFixed (1 second)
MAX_STEPS_PER_ADVANCE = 10000  # Prevent runaway loops


# =============================================================================
# PUBLIC CANONICAL STEPPING API
# =============================================================================

def compute_canonical_steps(dt_q: int) -> int:
    """
    Compute the number of canonical micro-steps for a given dt.
    
    This is the ONLY public API for converting continuous time to discrete steps.
    All nodes must use this function for consensus to be achievable.
    
    Policy: DISCRETE_MICRO_STEPS
    - 1:1 mapping: dt_q units = dt_q steps
    - Rounding: floor (dt_q // CANONICAL_STEP_UNIT_Q)
    
    Args:
        dt_q: Time delta in QFixed format
        
    Returns:
        Number of canonical micro-steps
        
    Raises:
        ValueError: If dt_q would require more than MAX_STEPS_PER_ADVANCE steps
    """
    if dt_q <= 0:
        return 0
    
    steps = dt_q // CANONICAL_STEP_UNIT_Q
    
    if steps > MAX_STEPS_PER_ADVANCE:
        raise ValueError(
            f"dt_q={dt_q} would require {steps} steps, exceeding maximum "
            f"of {MAX_STEPS_PER_ADVANCE}. Use smaller dt or chunked advancement."
        )
    
    return steps


class TrajectoryState(Enum):
    """States of a continuous trajectory."""
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"


@dataclass
class TrajectoryPoint:
    """
    A single point in a continuous trajectory.
    
    All values are stored as QFixed integers (scaled by 10^18).
    """
    step_index: int
    state_hash: str
    budget_q: int  # QFixed scaled
    risk_q: int  # QFixed scaled
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_index": self.step_index,
            "state_hash": self.state_hash,
            "budget_q": str(self.budget_q),
            "risk_q": str(self.risk_q),
            "timestamp": self.timestamp,
        }


@dataclass
class ContinuousTrajectory:
    """
    Continuous trajectory wrapper around discrete step engine.
    
    Provides:
    - advance(dt) that uses stable discrete steps
    - Projects onto admissible set K(A)
    - Emits micro receipts into slab buffer
    """
    
    def __init__(
        self,
        initial_state: Dict[str, Any],
        initial_budget_q: int,
        step_engine: Optional[Callable] = None,
        slab_buffer: Optional[Any] = None,
    ):
        """
        Initialize continuous trajectory.
        
        Args:
            initial_state: Initial cognitive state
            initial_budget_q: Initial budget (QFixed scaled)
            step_engine: Function that executes one discrete step
            slab_buffer: Buffer for accumulating micro receipts
        """
        self._x_state = initial_state  # Cognitive state dict (for step engine)
        self._budget_q = initial_budget_q
        self._step_engine = step_engine
        self._slab_buffer = slab_buffer
        
        self._trajectory: List[TrajectoryPoint] = []
        self._step_index = 0
        self._traj_state = TrajectoryState.IDLE  # Trajectory state enum (separate from _x_state)
    
    def start(self) -> None:
        """Start the trajectory."""
        self._traj_state = TrajectoryState.RUNNING
    
    def pause(self) -> None:
        """Pause the trajectory."""
        self._traj_state = TrajectoryState.PAUSED
    
    def resume(self) -> None:
        """Resume the trajectory."""
        self._traj_state = TrajectoryState.RUNNING
    
    def advance(self, dt_q: int) -> Optional[Dict[str, Any]]:
        """
        Advance trajectory by dt (delta time).
        
        Internally uses stable discrete steps. The dt is in QFixed format.
        
        Args:
            dt_q: Delta time in QFixed format
            
        Returns:
            Micro receipt if step was executed, None otherwise
        """
        if self._traj_state != TrajectoryState.RUNNING:
            return None
        
        # Convert dt to discrete steps
        # Each discrete step represents a fixed time unit
        discrete_steps = self._compute_discrete_steps(dt_q)
        
        receipt = None
        for _ in range(discrete_steps):
            receipt = self._execute_step()
            if receipt is None:
                # Step rejected - stop trajectory
                self._traj_state = TrajectoryState.COMPLETED
                break
        
        return receipt
    
    def _compute_discrete_steps(self, dt_q: int) -> int:
        """
        Convert continuous time delta to discrete steps using CANONICAL stepping policy.
        
        This is the ONLY legal way to convert dt to discrete steps per the consensus
        stepping policy. All nodes must use this exact method for deterministic receipts.
        
        Policy: DISCRETE_MICRO_STEPS
        - 1:1 mapping: dt_q units = dt_q steps
        - Rounding: floor (dt_q // CANONICAL_STEP_UNIT_Q)
        
        Args:
            dt_q: Delta time in QFixed format
            
        Returns:
            Number of discrete steps (capped by MAX_STEPS_PER_ADVANCE)
            
        Raises:
            ValueError: If dt_q exceeds MAX_STEPS_PER_ADVANCE
        """
        if dt_q < CANONICAL_STEP_UNIT_Q:
            return 0
        
        steps = dt_q // CANONICAL_STEP_UNIT_Q
        
        if steps > MAX_STEPS_PER_ADVANCE:
            raise ValueError(
                f"dt_q={dt_q} would require {steps} steps, exceeding maximum "
                f"of {MAX_STEPS_PER_ADVANCE}. Use smaller dt or chunked advancement."
            )
        
        return steps
    
    def _execute_step(self) -> Optional[Dict[str, Any]]:
        """
        Execute a single discrete step.
        
        Returns:
            Micro receipt if step accepted, None if rejected
        """
        if self._step_engine is None:
            return None
        
        # Execute the step
        try:
            result = self._step_engine(
                state=self._x_state,
                budget_q=self._budget_q,
                step_index=self._step_index,
            )
            
            if result is None:
                return None
            
            # Unpack result
            new_state = result.get("state")
            new_budget_q = result.get("budget_q", self._budget_q)
            risk_q = result.get("risk_q", 0)
            receipt = result.get("receipt")
            
            # Update cognitive state (not trajectory state)
            self._x_state = new_state
            self._budget_q = new_budget_q
            
            # Record trajectory point
            point = TrajectoryPoint(
                step_index=self._step_index,
                state_hash=receipt.get("state_hash_after", "") if receipt else "",
                budget_q=self._budget_q,
                risk_q=risk_q,
                timestamp=receipt.get("timestamp", "") if receipt else "",
            )
            self._trajectory.append(point)
            
            self._step_index += 1
            
            # Add to slab buffer if provided
            if self._slab_buffer and receipt:
                self._slab_buffer.add_micro_receipt(receipt)
            
            return receipt
            
        except Exception:
            return None
    
    def project_to_admissible(self) -> Dict[str, Any]:
        """
        Project current state onto admissible set K(A).
        
        Returns:
            Projected state
        """
        # This is a placeholder - in practice, this would
        # project the state onto the admissible set
        return self._x_state
    
    def get_trajectory(self) -> List[TrajectoryPoint]:
        """Get the full trajectory."""
        return self._trajectory
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current cognitive state."""
        return self._x_state
    
    def get_current_budget_q(self) -> int:
        """Get current budget (QFixed)."""
        return self._budget_q
    
    def get_step_index(self) -> int:
        """Get current step index."""
        return self._step_index
    
    def get_state(self) -> TrajectoryState:
        """Get trajectory state."""
        return self._traj_state


class ContinuousSolver:
    """
    Continuous solver that wraps discrete step engine.
    
    Ensures determinism by:
    - Using QFixed for all numeric values
    - No floating-point serialization in receipts
    - Deterministic step ordering
    """
    
    def __init__(
        self,
        step_engine: Callable,
        admissible_projection: Optional[Callable] = None,
    ):
        """
        Initialize continuous solver.
        
        Args:
            step_engine: Function that executes one discrete step
            admissible_projection: Function to project to admissible set
        """
        self._step_engine = step_engine
        self._admissible_projection = admissible_projection or (lambda s: s)
    
    def solve(
        self,
        initial_state: Dict[str, Any],
        initial_budget_q: int,
        max_steps: int = 1000,
        target_risk_q: Optional[int] = None,
    ) -> ContinuousTrajectory:
        """
        Solve a continuous trajectory.
        
        Args:
            initial_state: Initial cognitive state
            initial_budget_q: Initial budget (QFixed)
            max_steps: Maximum discrete steps
            target_risk_q: Target risk threshold (QFixed)
            
        Returns:
            ContinuousTrajectory with results
        """
        trajectory = ContinuousTrajectory(
            initial_state=initial_state,
            initial_budget_q=initial_budget_q,
            step_engine=self._step_engine,
        )
        
        trajectory.start()
        
        for _ in range(max_steps):
            # Check if target risk reached
            if target_risk_q is not None:
                current_risk = trajectory._trajectory[-1].risk_q if trajectory._trajectory else 0
                if current_risk <= target_risk_q:
                    break
            
            # Execute step (dt = 1.0 in QFixed)
            receipt = trajectory.advance(QFIXED_SCALE)
            
            if receipt is None:
                break
            
            # Check budget
            if trajectory.get_current_budget_q() <= 0:
                break
        
        trajectory._state = TrajectoryState.COMPLETED
        
        return trajectory


# Utility functions

def qfixed_to_int(qfixed: int) -> int:
    """Convert QFixed to integer."""
    return qfixed // QFIXED_SCALE


def int_to_qfixed(value: int) -> int:
    """Convert integer to QFixed."""
    return value * QFIXED_SCALE


def qfixed_div(a: int, b: int) -> int:
    """Divide two QFixed numbers."""
    return (a * QFIXED_SCALE) // b


def qfixed_mul(a: int, b: int) -> int:
    """Multiply two QFixed numbers."""
    return (a * b) // QFIXED_SCALE
