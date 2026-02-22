"""
Unit tests for the SOC (Self-Organized Criticality) module.

Tests:
1. Norm bounds calculations
2. Verifier acceptance predicate
3. Q18 arithmetic correctness
"""

import pytest
import math
import random
from src.soc import (
    mat_inf_norm_q18,
    power_iteration_witness,
    compute_sigma,
    verify_renorm_criticality,
)
from src.soc.norm_bounds import Q18


class TestNormBounds:
    """Test deterministic norm bound calculations."""

    def test_mat_inf_norm_simple(self):
        """Test infinity norm for simple matrices."""
        # 2x2 matrix [[1, 2], [3, 4]]
        # Row sums: 3, 7 -> max = 7
        A = [[1, 2], [3, 4]]
        result = mat_inf_norm_q18(A)
        expected = int(7.0 * Q18)
        assert result == expected

    def test_mat_inf_norm_single_element(self):
        """Test infinity norm for 1x1 matrix."""
        A = [[5.0]]
        result = mat_inf_norm_q18(A)
        expected = int(5.0 * Q18)
        assert result == expected

    def test_mat_inf_norm_zeros(self):
        """Test infinity norm for zero matrix."""
        A = [[0, 0], [0, 0]]
        result = mat_inf_norm_q18(A)
        assert result == 0

    def test_mat_inf_norm_negative(self):
        """Test infinity norm with negative values."""
        A = [[-1, 2], [3, -4]]
        # Row sums: |-1| + |2| = 3, |3| + |-4| = 7 -> max = 7
        result = mat_inf_norm_q18(A)
        expected = int(7.0 * Q18)
        assert result == expected

    def test_mat_inf_norm_large(self):
        """Test infinity norm for larger matrix."""
        A = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        # Row sums: 6, 15, 24 -> max = 24
        result = mat_inf_norm_q18(A)
        expected = int(24.0 * Q18)
        assert result == expected


class TestComputeSigma:
    """Test sigma (operator criticality) calculations."""

    def test_compute_sigma_simple(self):
        """Test sigma = eta * norm * g with simple values."""
        # sigma = 0.5 * 2.0 * 1.5 = 1.5
        result = compute_sigma(
            norm=int(2.0 * Q18),
            eta_q18=int(0.5 * Q18),
            g_q18=int(1.5 * Q18)
        )
        expected = int(1.5 * Q18)
        assert result == expected

    def test_compute_sigma_unity(self):
        """Test sigma = 1.0 case."""
        # sigma = 1.0 * 1.0 * 1.0 = 1.0
        result = compute_sigma(
            norm=int(1.0 * Q18),
            eta_q18=int(1.0 * Q18),
            g_q18=int(1.0 * Q18)
        )
        expected = int(1.0 * Q18)
        assert result == expected

    def test_compute_sigma_small(self):
        """Test sigma < 1 case."""
        # sigma = 0.1 * 0.5 * 0.5 = 0.025
        result = compute_sigma(
            norm=int(0.1 * Q18),
            eta_q18=int(0.5 * Q18),
            g_q18=int(0.5 * Q18)
        )
        expected = int(0.025 * Q18)
        assert result == expected


class TestVerifier:
    """Test renorm criticality verifier."""

    def test_valid_renorm_accepts(self):
        """Test that valid renorm is accepted."""
        # Supercritical before: 2.0 * 0.75 * 1.0 = 1.5 > 1
        # Subcritical after: 1.0 * 0.75 * 1.0 = 0.75 < 1
        result = verify_renorm_criticality(
            norm_pre_q18=int(2.0 * Q18),
            norm_post_q18=int(1.0 * Q18),
            eta_q18=int(0.75 * Q18),
            g_q18=int(1.0 * Q18)
        )
        assert result.accepted is True

    def test_invalid_not_supercritical(self):
        """Test rejection when not supercritical before renorm."""
        # norm_pre * eta * g = 0.5 * 0.75 * 1.0 = 0.375 < 1
        result = verify_renorm_criticality(
            norm_pre_q18=int(0.5 * Q18),
            norm_post_q18=int(0.3 * Q18),
            eta_q18=int(0.75 * Q18),
            g_q18=int(1.0 * Q18)
        )
        assert result.accepted is False
        assert "sigma_pre" in str(result).lower()

    def test_invalid_no_reduction(self):
        """Test rejection when norm is not reduced."""
        # Same norm before and after
        result = verify_renorm_criticality(
            norm_pre_q18=int(1.0 * Q18),
            norm_post_q18=int(1.0 * Q18),
            eta_q18=int(0.75 * Q18),
            g_q18=int(1.5 * Q18)
        )
        assert result.accepted is False
        assert "norm" in str(result).lower()

    def test_invalid_still_supercritical(self):
        """Test rejection when still supercritical after renorm."""
        # norm_post * eta * g = 1.5 * 0.75 * 1.0 = 1.125 > 1
        result = verify_renorm_criticality(
            norm_pre_q18=int(2.0 * Q18),
            norm_post_q18=int(1.5 * Q18),
            eta_q18=int(0.75 * Q18),
            g_q18=int(1.0 * Q18)
        )
        assert result.accepted is False
        assert "sigma_post" in str(result).lower()

    def test_critical_boundary_post(self):
        """Test acceptance when post is exactly critical (sigma = 1)."""
        # norm_post * eta * g = 4/3 * 0.75 * 1.0 = 1.0
        # Using strict=False allows sigma_post == 1
        result = verify_renorm_criticality(
            norm_pre_q18=int(2.0 * Q18),
            norm_post_q18=int(int(4/3 * Q18)),
            eta_q18=int(0.75 * Q18),
            g_q18=int(1.0 * Q18),
            strict=False
        )
        # Should be accepted with strict=False
        assert result.accepted is True


class TestPowerIteration:
    """Test power iteration witness (diagnostic only)."""

    def test_power_iteration_basic(self):
        """Test power iteration on simple matrix."""
        A = [[2, 1], [1, 2]]
        result = power_iteration_witness(A, iterations=10, seed=42)
        # Largest eigenvalue of [[2,1],[1,2]] is 3
        assert 2.5 < result < 3.5

    def test_power_iteration_deterministic(self):
        """Test that seeded power iteration is deterministic."""
        A = [[2, 1], [1, 2]]
        result1 = power_iteration_witness(A, iterations=10, seed=123)
        result2 = power_iteration_witness(A, iterations=10, seed=123)
        assert result1 == result2


class TestQ18Arithmetic:
    """Test Q18 fixed-point arithmetic correctness."""

    def test_q18_constant(self):
        """Verify Q18 = 2^18."""
        assert Q18 == 262144

    def test_multiplication_consistency(self):
        """Test that multiplication gives consistent results."""
        # Test with various values
        a = 0.5
        b = 0.25
        c = 2.0
        
        # Compute (a * b * c) in Q18
        a_q18 = int(a * Q18)
        b_q18 = int(b * Q18)
        c_q18 = int(c * Q18)
        
        result = compute_sigma(a_q18, b_q18, c_q18)
        
        # Expected: 0.5 * 0.25 * 2.0 = 0.25
        expected = int(0.25 * Q18)
        assert result == expected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
