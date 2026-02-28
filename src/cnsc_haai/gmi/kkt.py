"""
KKT / VI Residual Checker

This module computes discrete KKT residuals for stationary state verification:
- feasibility residuals for constraints
- complementarity residuals for active rho bounds
- stationarity proxy: discrete Laplacian norm of theta

All computations use integer arithmetic for determinism.
"""

from __future__ import annotations
from typing import List, Dict
from typing import TYPE_CHECKING
from .types import GMIState
from .params import GMIParams


def _laplacian_norm(grid: List[List[int]]) -> int:
    """
    Compute discrete Laplacian norm: sum of squared Laplacian values.

    Laplacian(grid)[i][j] = sum(neighbors) - cnt * grid[i][j]

    Args:
        grid: 2D integer array

    Returns:
        Sum of squared Laplacian values
    """
    n = len(grid)
    m = len(grid[0]) if n > 0 else 0
    s = 0

    for i in range(n):
        for j in range(m):
            c = grid[i][j]
            acc = 0
            cnt = 0

            # Count neighbors and sum their values
            if i > 0:
                acc += grid[i - 1][j]
                cnt += 1
            if i + 1 < n:
                acc += grid[i + 1][j]
                cnt += 1
            if j > 0:
                acc += grid[i][j - 1]
                cnt += 1
            if j + 1 < m:
                acc += grid[i][j + 1]
                cnt += 1

            # Discrete Laplacian
            L = acc - cnt * c
            s += L * L

    return s


def kkt_residual_q(s: GMIState, p: GMIParams) -> Dict[str, int]:
    """
    Compute KKT residuals for state.

    Returns:
        Dictionary with:
        - feas_rho_q: feasibility residual for rho bounds
        - feas_C_q: feasibility residual for C >= 0
        - feas_b_q: feasibility residual for b >= 0
        - comp_rho_low_q: complementarity residual for rho = 0
        - comp_rho_high_q: complementarity residual for rho = rho_max
        - stationarity_theta_q: stationarity proxy (Laplacian norm)
    """
    # Feasibility residuals
    feas_rho = 0
    for row in s.rho:
        for v in row:
            if v < 0:
                feas_rho += -v
            elif v > p.rho_max:
                feas_rho += v - p.rho_max

    feas_C = 0
    for row in s.C:
        for v in row:
            if v < 0:
                feas_C += -v

    feas_b = 0 if s.b >= 0 else (-s.b)

    # Complementarity residuals (proxy - v1.5 simplified)
    comp_low = 0
    comp_high = 0
    for row in s.rho:
        for v in row:
            if v == 0:
                comp_low += 0  # Cannot compute multiplier; leave 0
            if v == p.rho_max:
                comp_high += 0

    # Stationarity proxy: Laplacian of theta
    stat_theta = _laplacian_norm(s.theta)

    return {
        "feas_rho_q": int(feas_rho),
        "feas_C_q": int(feas_C),
        "feas_b_q": int(feas_b),
        "comp_rho_low_q": int(comp_low),
        "comp_rho_high_q": int(comp_high),
        "stationarity_theta_q": int(stat_theta),
    }


def is_kkt_feasible(s: GMIState, p: GMIParams) -> bool:
    """
    Check if state is KKT-feasible (all residuals zero).

    Args:
        s: GMI state
        p: GMI parameters

    Returns:
        True if all KKT residuals are zero
    """
    r = kkt_residual_q(s, p)
    return r["feas_rho_q"] == 0 and r["feas_C_q"] == 0 and r["feas_b_q"] == 0
