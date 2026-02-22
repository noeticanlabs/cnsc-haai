"""
Reference verifier implementation for renorm criticality verification.

This module implements the exact acceptance predicate for renormalization
criticality boundary crossing events as specified in the runtime trigger spec.

Acceptance requires ALL of:
1. norm_post < norm_pre (actual norm reduction)
2. sigma_pre > 1 (supercritical before renorm)
3. sigma_post <= 1 (critical/subcritical after renorm)
"""

from dataclasses import dataclass
from typing import Tuple, Optional
from .norm_bounds import Q18, compute_sigma

# Fixed-point representation of 1.0 in Q18
ONE_Q18 = Q18  # 2^18 = 262144


@dataclass
class RenormVerificationResult:
    """Result of renorm criticality verification."""
    accepted: bool
    sigma_pre_q18: int
    sigma_post_q18: int
    norm_pre_q18: int
    norm_post_q18: int
    eta_q18: int
    g_q18: int
    
    def __str__(self) -> str:
        status = "ACCEPTED" if self.accepted else "REJECTED"
        lines = [
            f"Verification Result: {status}",
            f"  norm_pre: {self.norm_pre_q18} (Q18)",
            f"  norm_post: {self.norm_post_q18} (Q18)",
            f"  eta: {self.eta_q18} (Q18)",
            f"  g: {self.g_q18} (Q18)",
            f"  sigma_pre: {self.sigma_pre_q18} (Q18) = {self.sigma_pre_q18 / Q18:.4f}",
            f"  sigma_post: {self.sigma_post_q18} (Q18) = {self.sigma_post_q18 / Q18:.4f}",
        ]
        
        if not self.accepted:
            # Add failure reasons
            failures = []
            if self.norm_post_q18 >= self.norm_pre_q18:
                failures.append("norm_post >= norm_pre (no reduction)")
            if self.sigma_pre_q18 <= ONE_Q18:
                failures.append(f"sigma_pre ({self.sigma_pre_q18 / Q18:.4f}) <= 1.0")
            if self.sigma_post_q18 > ONE_Q18:
                failures.append(f"sigma_post ({self.sigma_post_q18 / Q18:.4f}) > 1.0")
            lines.append(f"  Failures: {', '.join(failures)}")
        
        return "\n".join(lines)


def verify_renorm_criticality(
    norm_pre_q18: int,
    norm_post_q18: int,
    eta_q18: int,
    g_q18: int,
    strict: bool = True
) -> RenormVerificationResult:
    """
    Verify a renormalization criticality event.
    
    Implements the exact acceptance predicate:
        1. norm_post < norm_pre (must reduce norm)
        2. eta * norm_pre * g > 1 (supercritical before)
        3. eta * norm_post * g <= 1 (critical/subcritical after)
    
    Args:
        norm_pre_q18: Graph norm before renormalization (Q18 fixed-point)
        norm_post_q18: Graph norm after renormalization (Q18 fixed-point)
        eta_q18: Repair/eta factor (Q18 fixed-point)
        g_q18: NPE gain factor (Q18 fixed-point)
        strict: If True, reject if sigma_post == 1 (must be < 1)
                If False, allow sigma_post == 1 (critical is acceptable)
    
    Returns:
        RenormVerificationResult with acceptance decision and details
    """
    # Compute sigma values
    sigma_pre_q18 = compute_sigma(norm_pre_q18, eta_q18, g_q18)
    sigma_post_q18 = compute_sigma(norm_post_q18, eta_q18, g_q18)
    
    # Check acceptance predicates
    condition_1_norm_reduced = norm_post_q18 < norm_pre_q18
    condition_2_supercritical_pre = sigma_pre_q18 > ONE_Q18
    condition_3_subcritical_post = (
        sigma_post_q18 < ONE_Q18 if strict else sigma_post_q18 <= ONE_Q18
    )
    
    accepted = (
        condition_1_norm_reduced and
        condition_2_supercritical_pre and
        condition_3_subcritical_post
    )
    
    return RenormVerificationResult(
        accepted=accepted,
        sigma_pre_q18=sigma_pre_q18,
        sigma_post_q18=sigma_post_q18,
        norm_pre_q18=norm_pre_q18,
        norm_post_q18=norm_post_q18,
        eta_q18=eta_q18,
        g_q18=g_q18
    )


def verify_simple(
    norm_pre: float,
    norm_post: float,
    eta: float,
    g: float
) -> Tuple[bool, str]:
    """
    Simple verification using floating point (for testing/debugging).
    
    Note: For production verification, use verify_renorm_criticality
    with Q18 fixed-point arithmetic to avoid floating-point ambiguity.
    
    Args:
        norm_pre: Pre-renorm norm (floating point)
        norm_post: Post-renorm norm (floating point)
        eta: Prox contractivity factor (floating point)
        g: NPE gain factor (floating point)
    
    Returns:
        Tuple of (accepted: bool, reason: str)
    """
    sigma_pre = eta * norm_pre * g
    sigma_post = eta * norm_post * g
    
    if norm_post >= norm_pre:
        return False, f"norm_post ({norm_post}) >= norm_pre ({norm_pre})"
    
    if sigma_pre <= 1.0:
        return False, f"sigma_pre ({sigma_pre}) <= 1.0 (not supercritical)"
    
    if sigma_post > 1.0:
        return False, f"sigma_post ({sigma_post}) > 1.0 (not subcritical)"
    
    return True, "accepted"


# =============================================================================
# Example usage and test cases
# =============================================================================

def example_valid_renorm():
    """Example of a valid renorm event."""
    # Pre-renorm: supercritical state
    norm_pre = 2.0
    eta = 0.001
    g = 1.2
    sigma_pre = eta * norm_pre * g  # 0.0024
    
    # Post-renorm: subcritical state
    norm_post = 1.0
    sigma_post = eta * norm_post * g  # 0.0012
    
    # Convert to Q18
    norm_pre_q18 = int(norm_pre * Q18)
    norm_post_q18 = int(norm_post * Q18)
    eta_q18 = int(eta * Q18)
    g_q18 = int(g * Q18)
    
    result = verify_renorm_criticality(
        norm_pre_q18=norm_pre_q18,
        norm_post_q18=norm_post_q18,
        eta_q18=eta_q18,
        g_q18=g_q18
    )
    
    print("=== Valid Renorm Example ===")
    print(result)
    print()


def example_invalid_not_supercritical():
    """Example of invalid renorm: not supercritical before."""
    norm_pre = 0.5
    norm_post = 0.3
    eta = 0.001
    g = 1.2
    sigma_pre = eta * norm_pre * g  # 0.0006
    
    norm_pre_q18 = int(norm_pre * Q18)
    norm_post_q18 = int(norm_post * Q18)
    eta_q18 = int(eta * Q18)
    g_q18 = int(g * Q18)
    
    result = verify_renorm_criticality(
        norm_pre_q18=norm_pre_q18,
        norm_post_q18=norm_post_q18,
        eta_q18=eta_q18,
        g_q18=g_q18
    )
    
    print("=== Invalid: Not Supercritical Before ===")
    print(result)
    print()


def example_invalid_no_reduction():
    """Example of invalid renorm: no norm reduction."""
    norm_pre = 1.0
    norm_post = 1.0  # Same as pre!
    eta = 0.5
    g = 3.0
    sigma_pre = eta * norm_pre * g  # 1.5 (> 1)
    sigma_post = eta * norm_post * g  # 1.5 (> 1)
    
    norm_pre_q18 = int(norm_pre * Q18)
    norm_post_q18 = int(norm_post * Q18)
    eta_q18 = int(eta * Q18)
    g_q18 = int(g * Q18)
    
    result = verify_renorm_criticality(
        norm_pre_q18=norm_pre_q18,
        norm_post_q18=norm_post_q18,
        eta_q18=eta_q18,
        g_q18=g_q18
    )
    
    print("=== Invalid: No Norm Reduction ===")
    print(result)
    print()


if __name__ == "__main__":
    example_valid_renorm()
    example_invalid_not_supercritical()
    example_invalid_no_reduction()
