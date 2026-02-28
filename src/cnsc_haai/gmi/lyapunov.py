"""
Lyapunov Functional (Quantized)

This module implements the quantized Lyapunov functional V_q:
- Computable without floats (integer arithmetic)
- Monotone under governed step (enforced by rejection)
- Uses barrier term for absorption at b=0

V = w_theta * |grad(theta)|^2 + w_C * |C|^2 + w_budget * barrier(b)

Barrier uses absorption semantics: penalize low budget.
"""

from __future__ import annotations
from typing import List
from .types import GMIState
from .params import GMIParams


def _grad_energy(grid: List[List[int]]) -> int:
    """
    Compute gradient energy: sum of squared forward differences.
    
    |grad(grid)|^2 = sum of ((grid[i+1][j] - grid[i][j])^2 + (grid[i][j+1] - grid[i][j])^2)
    
    Args:
        grid: 2D integer array
        
    Returns:
        Integer gradient energy
    """
    n = len(grid)
    m = len(grid[0]) if n > 0 else 0
    s = 0
    for i in range(n):
        for j in range(m):
            if i + 1 < n:
                d = grid[i + 1][j] - grid[i][j]
                s += d * d
            if j + 1 < m:
                d = grid[i][j + 1] - grid[i][j]
                s += d * d
    return s


def _l2_energy(grid: List[List[int]]) -> int:
    """
    Compute L2 energy: sum of squared values.
    
    |grid|^2 = sum of grid[i][j]^2
    
    Args:
        grid: 2D integer array
        
    Returns:
        Integer L2 energy
    """
    s = 0
    for row in grid:
        for v in row:
            s += v * v
    return s


def V_extended_q(s: GMIState, p: GMIParams) -> int:
    """
    Compute quantized Lyapunov functional.
    
    V = w_grad_theta * |grad(theta)|^2 + w_C * |C|^2 + w_budget * barrier(b)
    
    Args:
        s: GMI state
        p: GMI parameters
        
    Returns:
        Lyapunov value as scaled integer (QFixed)
    """
    # Gradient energy of theta
    grad_theta = _grad_energy(s.theta)
    
    # L2 energy of curvature C
    C_l2 = _l2_energy(s.C)
    
    # Barrier: penalize low budget (absorption semantics)
    # barrier(b) = max(0, B_min - b) where B_min = 0 in v1.5
    B_min_q = 0
    barrier = (B_min_q - s.b) if s.b < B_min_q else 0
    
    # Compute weighted sum
    Vq = (
        p.w_grad_theta_q * grad_theta +
        p.w_C_q * C_l2 +
        p.w_budget_barrier_q * barrier
    )
    
    return int(Vq)


def dV_accepted(dV: int) -> bool:
    """
    Check if delta-V is acceptable (non-positive).
    
    Args:
        dV: Delta Lyapunov value (scaled)
        
    Returns:
        True if dV <= 0 (accepted), False if dV > 0 (rejected)
    """
    return dV <= 0
