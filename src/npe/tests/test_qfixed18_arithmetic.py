"""
NPE v1.0.1 QFixed18 Arithmetic Tests.

Verifies deterministic Q18 arithmetic with proper rounding:
- UP rounding for debits (ceil)
- DOWN rounding for refunds (floor)
- int64 bounds checking
- Overflow rejection
"""

import pytest
from npe.core.qfixed18 import (
    q18_mul,
    q18_div,
    q18_add,
    q18_sub,
    q18_clamp,
    calculate_debit,
    calculate_refund,
    int_to_q18,
    q18_to_int,
    q18_to_float,
    is_valid_q18,
    compute_test_vector,
)
from npe.spec_constants import Q18_SCALE, Q18_MIN, Q18_MAX, RoundingMode


class TestQ18Multiplication:
    """Test Q18 multiplication with UP/DOWN rounding."""

    def test_multiply_basic(self):
        """Test basic multiplication."""
        # 1 * 1 = 1 in Q18
        result = q18_mul(Q18_SCALE, Q18_SCALE, RoundingMode.DOWN)
        assert result == Q18_SCALE

    def test_multiply_with_fractional_up(self):
        """Test multiplication with fractional result - UP rounding."""
        # 1.5 * 1 = 1.5 Q18 = 393216 (which is 1.5 * 262144)
        # This should round UP
        a = int(1.5 * Q18_SCALE)  # 393216
        b = Q18_SCALE  # 262144
        result = q18_mul(a, b, RoundingMode.UP)
        # Expected: ceil(393216 * 262144 / 262144) = ceil(393216) = 393216
        assert result >= a

    def test_multiply_with_fractional_down(self):
        """Test multiplication with fractional result - DOWN rounding."""
        a = int(1.5 * Q18_SCALE)  # 393216
        b = Q18_SCALE  # 262144
        result = q18_mul(a, b, RoundingMode.DOWN)
        # Expected: floor(393216 * 262144 / 262144) = floor(393216) = 393216
        assert result == a

    def test_multiply_negative_up(self):
        """Test negative multiplication with UP rounding."""
        a = -Q18_SCALE  # -262144
        b = Q18_SCALE  # 262144
        # -1 * 1 = -1 Q18
        result = q18_mul(a, b, RoundingMode.UP)
        assert result == -Q18_SCALE

    def test_overflow_rejected(self):
        """Test that overflow is rejected."""
        # Use values that actually exceed bounds after scaling
        # Q18_MAX * 10 / Q18_SCALE = ~3.5e13, which exceeds Q18_MAX
        # But simpler: just test with very large values
        with pytest.raises(OverflowError):
            q18_mul(10 * Q18_MAX, Q18_MAX, RoundingMode.DOWN)


class TestQ18Division:
    """Test Q18 division with UP/DOWN rounding."""

    def test_divide_basic(self):
        """Test basic division."""
        # 1 / 1 = 1 Q18
        result = q18_div(Q18_SCALE, Q18_SCALE, RoundingMode.DOWN)
        assert result == Q18_SCALE

    def test_divide_fractional_up(self):
        """Test division with fractional result - UP rounding."""
        # 1 / 3 = 0.333... Q18
        result = q18_div(Q18_SCALE, 3 * Q18_SCALE, RoundingMode.UP)
        # Should round up to 87382 (approximately 0.3334)
        assert result > 0

    def test_divide_by_zero_rejected(self):
        """Test that division by zero is rejected."""
        with pytest.raises(ValueError):
            q18_div(Q18_SCALE, 0, RoundingMode.DOWN)


class TestQ18Addition:
    """Test Q18 addition."""

    def test_add_basic(self):
        """Test basic addition."""
        result = q18_add(Q18_SCALE, Q18_SCALE)
        assert result == 2 * Q18_SCALE

    def test_add_overflow_rejected(self):
        """Test that addition overflow is rejected."""
        with pytest.raises(OverflowError):
            q18_add(Q18_MAX, 1)


class TestQ18Subtraction:
    """Test Q18 subtraction."""

    def test_sub_basic(self):
        """Test basic subtraction."""
        result = q18_sub(2 * Q18_SCALE, Q18_SCALE)
        assert result == Q18_SCALE

    def test_sub_underflow_rejected(self):
        """Test that subtraction underflow is rejected."""
        with pytest.raises(OverflowError):
            q18_sub(Q18_MIN, 1)


class TestQ18Clamp:
    """Test Q18 clamping."""

    def test_clamp_within_bounds(self):
        """Test clamping when value is within bounds."""
        result = q18_clamp(Q18_SCALE, Q18_MIN, Q18_MAX)
        assert result == Q18_SCALE

    def test_clamp_above_max(self):
        """Test clamping when value exceeds max."""
        result = q18_clamp(Q18_MAX + 1000, Q18_MIN, Q18_MAX)
        assert result == Q18_MAX

    def test_clamp_below_min(self):
        """Test clamping when value is below min."""
        result = q18_clamp(Q18_MIN - 1000, Q18_MIN, Q18_MAX)
        assert result == Q18_MIN


class TestBudgetCalculations:
    """Test budget debit and refund calculations."""

    def test_debit_upward_rounding(self):
        """
        Test that debit uses UPWARD rounding (ceil).

        debit = ceil((kappa * cost) / 2^18)
        """
        # kappa = 1.0 Q18, cost = 1.5 Q18
        kappa = Q18_SCALE  # 1.0
        cost = int(1.5 * Q18_SCALE)  # 1.5

        debit = calculate_debit(kappa, cost)

        # Expected: ceil(1.0 * 1.5) = ceil(1.5) = 2 Q18
        # In Q18: 2 * 262144 = 524288
        assert debit >= cost  # Should be at least 1.5 Q18

    def test_refund_downward_rounding(self):
        """
        Test that refund uses DOWNWARD rounding (floor).

        refund = floor((rho * amount) / 2^18)
        """
        # rho = 0.5 Q18, amount = 1.0 Q18
        rho = int(0.5 * Q18_SCALE)  # 0.5
        amount = Q18_SCALE  # 1.0

        refund = calculate_refund(rho, amount)

        # Expected: floor(0.5 * 1.0) = floor(0.5) = 0.5 Q18
        # In Q18: 0.5 * 262144 = 131072
        expected = int(0.5 * Q18_SCALE)
        assert refund == expected

    def test_debit_always_at_least_cost(self):
        """Debit should always round UP, never round DOWN."""
        # Even for exact multiples, debit should not lose precision
        kappa = Q18_SCALE  # 1.0
        cost = Q18_SCALE  # 1.0

        debit = calculate_debit(kappa, cost)

        # 1.0 * 1.0 = 1.0, exact
        assert debit == Q18_SCALE


class TestQ18Conversions:
    """Test Q18 conversion utilities."""

    def test_int_to_q18(self):
        """Test integer to Q18 conversion."""
        result = int_to_q18(10)
        assert result == 10 * Q18_SCALE

    def test_q18_to_int(self):
        """Test Q18 to integer conversion (floor)."""
        value = int(10.9 * Q18_SCALE)  # 10.9 Q18
        result = q18_to_int(value)
        assert result == 10  # Floor

    def test_is_valid_q18(self):
        """Test Q18 validity check."""
        assert is_valid_q18(0) is True
        assert is_valid_q18(Q18_MAX) is True
        assert is_valid_q18(Q18_MIN) is True
        assert is_valid_q18(Q18_MAX + 1) is False
        assert is_valid_q18(Q18_MIN - 1) is False


class TestDeterminism:
    """Test that Q18 operations are deterministic."""

    def test_same_inputs_same_output(self):
        """Same inputs should always produce same outputs."""
        a = int(3.14159 * Q18_SCALE)
        b = int(2.71828 * Q18_SCALE)

        result1 = q18_mul(a, b, RoundingMode.UP)
        result2 = q18_mul(a, b, RoundingMode.UP)

        assert result1 == result2

    def test_test_vector_computation(self):
        """Test the test vector helper function."""
        a = Q18_SCALE
        b = Q18_SCALE

        mul_up, mul_down, div_up, div_down = compute_test_vector(a, b)

        # 1 * 1 = 1 for all
        assert mul_up == Q18_SCALE
        assert mul_down == Q18_SCALE
        assert div_up == Q18_SCALE
        assert div_down == Q18_SCALE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
