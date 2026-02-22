"""
Deterministic norm bound utilities for SOC spine.

Provides:
- Safe upper bound for matrix norms (deterministic, verifier-safe)
- Optional power iteration witness for diagnostics only

Uses pure Python - no numpy dependency required.
"""

from typing import Union, Optional, List
import math
import random

# Q18 fixed-point scaling factor
Q18 = 1 << 18  # 2^18 = 262144


def mat_inf_norm_q18(A: Union[List[List[float]], List[List[int]]]) -> int:
    """
    Compute safe upper bound for matrix norm: ||A||_inf (row sum norm).
    
    This is the maximum absolute row sum:
        ||A||_inf = max_i (sum_j |A_ij|)
    
    This provides a deterministic, verifier-safe upper bound for the
    operator norm that works for any matrix (symmetric or not).
    
    Args:
        A: Matrix as nested list of floats/ints
        
    Returns:
        Integer: Q18 fixed-point representation of ||A||_inf
        
    Example:
        >>> A = [[1, 2], [3, 4]]
        >>> mat_inf_norm_q18(A)
        1835008  # max(1+2, 3+4) = 7 * 262144
    """
    if not A:
        return 0
    
    max_row_sum = 0.0
    for row in A:
        row_sum = sum(abs(val) for val in row)
        if row_sum > max_row_sum:
            max_row_sum = row_sum
    
    # Convert to Q18 fixed-point
    return int(max_row_sum * Q18)


def mat_2_norm_q18(A: Union[List[List[float]], List[List[int]]]) -> int:
    """
    Compute spectral norm ||A||_2 (largest singular value).
    
    For symmetric matrices, this equals the largest absolute eigenvalue.
    This is a tighter bound than infinity norm but requires SVD.
    
    Note: This is NOT deterministic in the presence of floating-point
    numerics, but is provided for reference. The verifier should use
    mat_inf_norm_q18 for guaranteed safety.
    
    Args:
        A: Matrix as nested list
        
    Returns:
        Integer: Q18 fixed-point representation of ||A||_2
    """
    # For pure Python, fall back to power iteration
    # This is approximate - use mat_inf_norm_q18 for safe verification
    try:
        import numpy as np
        A_np = np.array(A, dtype=float)
        singular_values = np.linalg.svd(A_np, compute_uv=False)
        spec_norm = singular_values[0]
        return int(spec_norm * Q18)
    except ImportError:
        # Fall back to rough estimate using infinity norm
        # ||A||_2 <= ||A||_F <= sqrt(n) * ||A||_2
        # Using Gershgorin bound as overestimate
        inf_norm = mat_inf_norm_q18(A) / Q18
        n = len(A)
        if n > 0:
            return int(inf_norm * math.sqrt(n) * Q18)
        return 0


def mat_fro_norm_q18(A: Union[List[List[float]], List[List[int]]]) -> int:
    """
    Compute Frobenius norm ||A||_F = sqrt(sum_ij |A_ij|^2).
    
    This provides ||A||_2 <= ||A||_F <= sqrt(n) * ||A||_2
    
    Args:
        A: Matrix as nested list
        
    Returns:
        Integer: Q18 fixed-point representation of ||A||_F
    """
    sum_squares = 0.0
    for row in A:
        for val in row:
            sum_squares += val * val
    
    fro_norm = math.sqrt(sum_squares)
    
    # Convert to Q18 fixed-point
    return int(fro_norm * Q18)


def power_iteration_witness(
    A: Union[List[List[float]], List[List[int]]],
    iterations: int = 10,
    seed: Optional[int] = None
) -> float:
    """
    Estimate spectral radius via power iteration.
    
    WARNING: This is for DIAGNOSTIC PURPOSES ONLY. The verifier is NOT
    required to trust this witness. Use mat_inf_norm_q18 for safe,
    deterministic verification.
    
    The power iteration provides an estimate of the dominant eigenvalue
    (spectral radius for non-negative matrices), but:
    - Converges slowly if there's a gap
    - May converge to wrong vector if multiple dominant eigenvalues
    - Depends on random initialization (unless seeded)
    
    Args:
        A: Matrix as nested list
        iterations: Number of power iteration steps
        seed: Random seed for reproducibility (if None, uses random)
        
    Returns:
        float: Estimated spectral radius (not Q18 scaled)
    """
    n = len(A)
    if n == 0:
        return 0.0
    
    # Initialize random vector
    if seed is not None:
        random.seed(seed)
    v = [random.random() for _ in range(n)]
    
    # Normalize
    v_norm = math.sqrt(sum(x * x for x in v))
    v = [x / v_norm for x in v]
    
    # Power iteration
    for _ in range(iterations):
        # v = A @ v
        Av = [0.0] * n
        for i in range(n):
            for j in range(n):
                Av[i] += A[i][j] * v[j]
        
        # Normalize
        v_norm = math.sqrt(sum(x * x for x in Av))
        if v_norm > 0:
            v = [x / v_norm for x in Av]
    
    # Rayleigh quotient as estimate: (v^T A v) / (v^T v)
    # Since v is normalized, v^T v = 1
    Av = [0.0] * n
    for i in range(n):
        for j in range(n):
            Av[i] += A[i][j] * v[j]
    
    witness = sum(v[i] * Av[i] for i in range(n))
    
    return witness


def compute_sigma(
    norm: int,
    eta_q18: int,
    g_q18: int
) -> int:
    """
    Compute operator criticality sigma = eta * norm * g.
    
    All inputs and output are in Q18 fixed-point format.
    
    When multiplying three Q18 values, result is Q54.
    To convert back to Q18, divide by Q18^2 (2^36).
    
    Args:
        norm: Matrix norm bound (Q18)
        eta_q18: Prox contractivity factor (Q18)
        g_q18: NPE gain factor (Q18)
        
    Returns:
        Integer: sigma in Q18 fixed-point
    """
    # Multiply three Q18 values: result is Q54
    # Convert back to Q18: divide by Q18^2 = 2^36
    Q36 = 1 << 36
    result = (norm * eta_q18 * g_q18) // Q36
    return result


def compute_eta(mu: float, c: float, B: int) -> int:
    """
    Compute prox contractivity factor eta = 1 / (1 + mu * c * B).
    
    Args:
        mu: Prox parameter
        c: Constant
        B: Budget (integer)
        
    Returns:
        Integer: eta in Q18 fixed-point
    """
    denominator = 1.0 + mu * c * float(B)
    eta_float = 1.0 / denominator
    return int(eta_float * Q18)


# =============================================================================
# Quick reference for verifiers
# =============================================================================

"""
VERIFIER QUICK REFERENCE:

For safe verification, use ONLY:
    norm = mat_inf_norm_q18(A)  # Returns Q18

Optional diagnostics (NOT required to trust):
    spec_radius = power_iteration_witness(A)

Acceptance predicate:
    norm_post < norm_pre
    eta * norm_pre * g > Q18    # sigma > 1
    eta * norm_post * g <= Q18  # sigma <= 1
"""
