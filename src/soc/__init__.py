"""
SOC (Self-Organized Criticality) spine implementation.

This module provides:
- Deterministic norm bound calculations
- Runtime verifier for renorm criticality
"""

from .norm_bounds import mat_inf_norm_q18, power_iteration_witness, compute_sigma
from .rv_verify_renorm_criticality import verify_renorm_criticality

__all__ = [
    "mat_inf_norm_q18",
    "power_iteration_witness",
    "compute_sigma",
    "verify_renorm_criticality",
]
