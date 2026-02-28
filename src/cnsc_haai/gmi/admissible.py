"""
Admissibility Set and Projection

This module implements:
- in_K: Check if state is in convex admissibility set K
- project_K: Deterministic projection to K with witness data
"""

from __future__ import annotations
from typing import Tuple, Dict, Any, List
from .types import GMIState
from .params import GMIParams


def in_K(s: GMIState, p: GMIParams) -> bool:
    """
    Check if state is in admissibility set K.

    K requires:
    - b >= 0 (non-negative budget)
    - rho in [0, rho_max] for all cells
    - C >= 0 for all cells (non-negative curvature)

    Args:
        s: GMI state to check
        p: GMI parameters

    Returns:
        True if state is in K, False otherwise
    """
    # Budget must be non-negative
    if s.b < 0:
        return False

    # Check rho bounds
    for row in s.rho:
        for v in row:
            if v < 0 or v > p.rho_max:
                return False

    # Check C non-negative
    for row in s.C:
        for v in row:
            if v < 0:
                return False

    return True


def project_K(s: GMIState, p: GMIParams) -> Tuple[GMIState, Dict[str, Any]]:
    """
    Deterministic projection to convex box constraints.

    Projection rules:
    - rho: clamp to [0, rho_max]
    - C: clamp to [0, +inf) (just clamp negatives to 0)
    - b: clamp to [0, +inf)

    Args:
        s: GMI state to project
        p: GMI parameters

    Returns:
        Tuple of (projected state, witness dict with active set info)
    """
    witness: Dict[str, Any] = {
        "rho_active_low": [],
        "rho_active_high": [],
        "C_active_low": [],
        "b_clamped": False,
    }

    # Project rho: clamp to [0, rho_max]
    rho2: List[List[int]] = []
    for i, row in enumerate(s.rho):
        rr: List[int] = []
        for j, v in enumerate(row):
            if v < 0:
                witness["rho_active_low"].append([i, j])
                rr.append(0)
            elif v > p.rho_max:
                witness["rho_active_high"].append([i, j])
                rr.append(p.rho_max)
            else:
                rr.append(v)
        rho2.append(rr)

    # Project C: clamp negatives to 0
    C2: List[List[int]] = []
    for i, row in enumerate(s.C):
        rr: List[int] = []
        for j, v in enumerate(row):
            if v < 0:
                witness["C_active_low"].append([i, j])
                rr.append(0)
            else:
                rr.append(v)
        C2.append(rr)

    # Project budget: clamp negatives to 0
    b2 = s.b if s.b > 0 else 0
    if s.b != b2:
        witness["b_clamped"] = True

    s2 = GMIState(
        rho=rho2,
        theta=s.theta,  # theta not projected
        C=C2,
        b=b2,
        t=s.t,
    )

    return s2, witness
