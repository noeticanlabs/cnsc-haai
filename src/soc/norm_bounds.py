"""
Deterministic norm bound utilities for SOC spine.

Provides:
- Safe upper bound for matrix norms (deterministic, verifier-safe)
- Optional power iteration witness for diagnostics only

Uses pure Python with Q18 fixed-point arithmetic from npe.core.qfixed18.

IMPORTANT: All verifier-critical functions use Q18 integer arithmetic only.
No floats in the computation path - see docs/ats/20_coh_kernel/deterministic_numeric_domain.md
"""

from typing import Union, Optional, List
import math
import random

# Import Q18 constants from spec_constants
from npe.spec_constants import Q18_SCALE

# Q18 fixed-point scaling factor (same as Q18_SCALE = 2^18 = 262144)
Q18 = Q18_SCALE

# For backward compatibility - deprecated, use npe.core.qfixed18 functions
Q18_DEPRECATED = Q18


def mat_inf_norm_q18(A: List[List[int]]) -> int:
    """
    Compute safe upper bound for matrix norm: ||A||_inf (row sum norm).
    
    This is the maximum absolute row sum:
        ||A||_inf = max_i (sum_j |A_ij|)
    
    This provides a deterministic, verifier-safe upper bound for the
    operator norm that works for any matrix (symmetric or not).
    
    Args:
        A: Matrix as nested list of Q18 integers (already scaled)
           Each element should be in Q18 format, e.g., 262144 = 1.0
        
    Returns:
        Integer: Q18 fixed-point representation of ||A||_inf
        
    Example:
        >>> A = [[262144, 524288], [786432, 1048576]]  # [1, 2], [3, 4] in Q18
        >>> mat_inf_norm_q18(A)
        1835008  # max(1+2, 3+4) = 7 * 262144
    """
    if not A:
        return 0
    
    # Pure integer arithmetic - no floats
    max_row_sum = 0
    for row in A:
        row_sum = sum(abs(val) for val in row)
        if row_sum > max_row_sum:
            max_row_sum = row_sum
    
    # Already in Q18 format, no conversion needed
    return max_row_sum


def mat_2_norm_q18(A: List[List[int]]) -> int:
    """
    Compute spectral norm ||A||_2 (largest singular value).
    
    For symmetric matrices, this equals the largest absolute eigenvalue.
    This is a tighter bound than infinity norm but requires SVD.
    
    WARNING: This function is for DIAGNOSTIC PURPOSES ONLY.
    It uses floating-point internally and is NOT deterministic.
    The verifier MUST use mat_inf_norm_q18 for guaranteed safety.
    
    Args:
        A: Matrix as nested list of Q18 integers
        
    Returns:
        Integer: Q18 fixed-point representation of ||A||_2 (approximate)
    """
    # For pure Python, fall back to power iteration
    # This is approximate - use mat_inf_norm_q18 for safe verification
    try:
        import numpy as np
        # Convert Q18 integers to floats for numpy - loses determinism!
        A_np = np.array([[v / Q18 for v in row] for row in A], dtype=float)
        singular_values = np.linalg.svd(A_np, compute_uv=False)
        spec_norm = singular_values[0]
        return int(spec_norm * Q18)
    except ImportError:
        # Fall back to infinity norm as safe upper bound
        return mat_inf_norm_q18(A)


def mat_fro_norm_q18(A: List[List[int]]) -> int:
    """
    Compute Frobenius norm ||A||_F = sqrt(sum_ij |A_ij|^2).
    
    This provides ||A||_2 <= ||A||_F <= sqrt(n) * ||A||_2
    
    IMPORTANT: This is an UPPER BOUND approximation for diagnostics only.
    For deterministic verification, use mat_inf_norm_q18.
    
    Args:
        A: Matrix as nested list of Q18 integers
        
    Returns:
        Integer: Q18 fixed-point approximation of ||A||_F (upper bound)
    """
    # Sum of squares - each val^2 in Q36
    sum_squares_q36 = 0
    for row in A:
        for val in row:
            sum_squares_q36 += val * val
    
    # Upper bound: sqrt(sum_squares_q36) is in Q18
    # Use integer sqrt for deterministic upper bound
    sqrt_val = math.isqrt(sum_squares_q36)
    
    # This is an upper bound in Q18
    # Note: This is a rough approximation, use mat_inf_norm_q18 for safety
    return sqrt_val


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


def compute_eta_q18(mu_q18: int, c_q18: int, B: int) -> int:
    """
    Compute prox contractivity factor eta = 1 / (1 + mu * c * B).
    
    All values in Q18 fixed-point format for deterministic computation.
    Uses pure integer arithmetic - no floats.
    
    Formula: eta = 1 / (1 + mu * c * B)
    
    In Q18:
    - mu_q18, c_q18 are in Q18 (scaled by 2^18)
    - B is integer
    - mu * c * B in Q18: (mu_q18 * c_q18 * B) / Q18
    
    Args:
        mu_q18: Prox parameter in Q18 format
        c_q18: Constant in Q18 format
        B: Budget (integer)
        
    Returns:
        Integer: eta in Q18 fixed-point
        
    Example:
        >>> compute_eta_q18(262144, 262144, 1000)  # mu=1.0, c=1.0, B=1000
        259003  # approximately 0.987
    """
    # Compute mu * c in Q18: (mu_q18 * c_q18) / Q18
    mu_c = (mu_q18 * c_q18) // Q18
    
    # Compute mu * c * B in Q18
    mu_c_B = mu_c * B
    
    # Compute denominator: 1 + mu * c * B
    # 1 in Q18 is Q18, so we add Q18 to mu_c_B
    denominator_q18 = Q18 + mu_c_B
    
    # Compute eta = 1 / denominator = Q18 / denominator_q18
    # eta in Q18 = (Q18 * Q18) / denominator_q18
    eta_q18 = (Q18 * Q18) // denominator_q18
    
    return eta_q18


# Legacy function - DEPRECATED, use compute_eta_q18
def compute_eta(mu: float, c: float, B: int) -> int:
    """
    DEPRECATED: Compute prox contractivity factor eta.
    
    This function uses float arithmetic and is NOT deterministic.
    Use compute_eta_q18 instead for verifier-critical code.
    
    Args:
        mu: Prox parameter (float)
        c: Constant (float)
        B: Budget (integer)
        
    Returns:
        Integer: eta in Q18 fixed-point
    """
    import warnings
    warnings.warn(
        "compute_eta uses float arithmetic and is not deterministic. "
        "Use compute_eta_q18 for verifier-critical code.",
        DeprecationWarning
    )
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
