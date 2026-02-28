"""
GMI Core Types

Immutable dataclasses for GMI state, actions, and receipts.
All numeric fields are integers (no floats).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any, List


@dataclass(frozen=True)
class GMIState:
    """
    GMI system state.
    
    All arrays are represented as nested lists of integers (no floats).
    All values are in integer domain for determinism.
    """
    rho: List[List[int]]      # density in [0, rho_max] integer domain
    theta: List[List[int]]    # phase potential integer domain
    C: List[List[int]]        # curvature in [0, +inf) integer domain
    b: int                   # budget in QFixed scaled integer
    t: int                   # integer time step

    def __post_init__(self):
        """Validate state structure."""
        if not isinstance(self.rho, list) or not self.rho:
            raise ValueError("rho must be non-empty list")
        if not isinstance(self.theta, list) or not self.theta:
            raise ValueError("theta must be non-empty list")
        if not isinstance(self.C, list) or not self.C:
            raise ValueError("C must be non-empty list")


@dataclass(frozen=True)
class GMIAction:
    """
    GMI action - minimal action set for proposing drift.
    
    Delta fields represent integer domain changes.
    """
    drho: List[List[int]]                    # density delta
    dtheta: List[List[int]]                  # phase potential delta
    u_glyph: Optional[List[List[int]]] = None  # optional external glyph forcing

    def __post_init__(self):
        """Validate action structure."""
        if not isinstance(self.drho, list) or not self.drho:
            raise ValueError("drho must be non-empty list")
        if not isinstance(self.dtheta, list) or not self.dtheta:
            raise ValueError("dtheta must be non-empty list")


@dataclass(frozen=True)
class GMIStepReceipt:
    """
    GMI step receipt - cryptographic record of state transition.
    
    Contains all information needed for replay verification and audit.
    """
    version: str
    prev_state_hash: bytes
    next_state_hash: bytes
    chain_prev: bytes
    chain_next: bytes

    V_prev_q: int          # Lyapunov value before step (scaled)
    V_next_q: int          # Lyapunov value after step (scaled)
    dV_q: int              # Delta V (scaled)

    b_prev_q: int          # Budget before step (scaled)
    b_next_q: int          # Budget after step (scaled)
    db_q: int              # Budget delta (scaled)

    projected: bool        # Whether projection was applied
    reject_code: Optional[str]  # None if accepted, else rejection reason
    witness: Dict[str, Any]    # Active sets, multipliers, norms

    def is_accepted(self) -> bool:
        """Check if step was accepted."""
        return self.reject_code is None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "version": self.version,
            "prev_state_hash": self.prev_state_hash.hex(),
            "next_state_hash": self.next_state_hash.hex(),
            "chain_prev": self.chain_prev.hex(),
            "chain_next": self.chain_next.hex(),
            "V_prev_q": self.V_prev_q,
            "V_next_q": self.V_next_q,
            "dV_q": self.dV_q,
            "b_prev_q": self.b_prev_q,
            "b_next_q": self.b_next_q,
            "db_q": self.db_q,
            "projected": self.projected,
            "reject_code": self.reject_code,
            "witness": self.witness,
        }
