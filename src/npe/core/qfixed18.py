"""
NPE v1.0.1 QFixed18 Arithmetic Library.

Implements deterministic fixed-point arithmetic for NPE budget calculations:
- Q18 scaling (values are integers representing Q18 fixed-point)
- Deterministic rounding (UP for debits, DOWN for refunds)
- int64 bounds checking with overflow rejection
- No floats anywhere in the numeric path
"""

import math
from typing import Tuple

from npe.spec_constants import (
    Q18_SCALE,
    Q18_MIN,
    Q18_MAX,
    Q18_FRACTIONAL_MASK,
    RoundingMode,
)


# ============================================================================
# Core Q18 Operations
# ============================================================================

def q18_mul(a: int, b: int, rounding: RoundingMode = RoundingMode.DOWN) -> int:
    """
    Multiply two Q18 values.
    
    Args:
        a: First Q18 value (int64)
        b: Second Q18 value (int64)
        rounding: Rounding mode (UP or DOWN)
        
    Returns:
        Result of a * b in Q18 (scaled by 2^18)
        
    Raises:
        OverflowError: If result exceeds int64 bounds
    """
    # Use Python's arbitrary precision, then check bounds
    # result_full = a * b (full precision)
    # result = result_full / Q18_SCALE (remove scaling)
    
    result_full = a * b
    result = result_full // Q18_SCALE
    
    # Apply rounding
    if rounding == RoundingMode.UP:
        # Check for fractional part
        if (result_full & Q18_FRACTIONAL_MASK) != 0:
            # Has fractional part, round up (toward +infinity)
            if result >= 0:
                result += 1
            else:
                # For negative numbers, rounding UP means toward zero
                # But we want mathematical ceiling
                result = -((-result) + 1)
    # DOWN is floor division (default)
    
    # Check bounds
    if result < Q18_MIN or result > Q18_MAX:
        raise OverflowError(
            f"Q18 multiplication overflow: {a} * {b} = {result} "
            f"exceeds int64 range [{Q18_MIN}, {Q18_MAX}]"
        )
    
    return result


def q18_div(a: int, b: int, rounding: RoundingMode = RoundingMode.DOWN) -> int:
    """
    Divide two Q18 values.
    
    Args:
        a: Dividend Q18 value (int64)
        b: Divisor Q18 value (int64)
        rounding: Rounding mode (UP or DOWN)
        
    Returns:
        Result of a / b in Q18
        
    Raises:
        OverflowError: If result exceeds int64 bounds
        ValueError: If divisor is zero
    """
    if b == 0:
        raise ValueError("Division by zero")
    
    # Scale up before division to preserve precision
    # result_full = (a * Q18_SCALE) / b
    # Then remove scaling
    
    # For exact Q18 division, we scale by Q18_SCALE first
    result_full = a * Q18_SCALE
    result = result_full // b
    
    # Apply rounding
    if rounding == RoundingMode.UP:
        # Check for fractional part
        if (result_full % b) != 0:
            # Has fractional part, round up
            if result >= 0:
                result += 1
            else:
                # Negative: round toward +infinity (toward zero)
                result = -((-result) + 1)
    # DOWN is floor (default)
    
    # Check bounds
    if result < Q18_MIN or result > Q18_MAX:
        raise OverflowError(
            f"Q18 division overflow: {a} / {b} = {result} "
            f"exceeds int64 range [{Q18_MIN}, {Q18_MAX}]"
        )
    
    return result


def q18_add(a: int, b: int) -> int:
    """
    Add two Q18 values.
    
    Args:
        a: First Q18 value (int64)
        b: Second Q18 value (int64)
        
    Returns:
        Sum in Q18
        
    Raises:
        OverflowError: If result exceeds int64 bounds
    """
    result = a + b
    
    if result < Q18_MIN or result > Q18_MAX:
        raise OverflowError(
            f"Q18 addition overflow: {a} + {b} = {result} "
            f"exceeds int64 range [{Q18_MIN}, {Q18_MAX}]"
        )
    
    return result


def q18_sub(a: int, b: int) -> int:
    """
    Subtract two Q18 values.
    
    Args:
        a: Minuend Q18 value (int64)
        b: Subtrahend Q18 value (int64)
        
    Returns:
        Difference in Q18
        
    Raises:
        OverflowError: If result exceeds int64 bounds
    """
    result = a - b
    
    if result < Q18_MIN or result > Q18_MAX:
        raise OverflowError(
            f"Q18 subtraction overflow: {a} - {b} = {result} "
            f"exceeds int64 range [{Q18_MIN}, {Q18_MAX}]"
        )
    
    return result


def q18_clamp(value: int, min_val: int = Q18_MIN, max_val: int = Q18_MAX) -> int:
    """
    Clamp Q18 value to bounds.
    
    Args:
        value: Q18 value
        min_val: Minimum value (default: Q18_MIN)
        max_val: Maximum value (default: Q18_MAX)
        
    Returns:
        Clamped value
    """
    return max(min_val, min(max_val, value))


# ============================================================================
# Budget Calculations (Debits & Refunds)
# ============================================================================

def calculate_debit(kappa: int, cost: int) -> int:
    """
    Calculate debit using UPWARD rounding.
    
    Per spec: debit = ceil((kappa * cost) / 2^18)
    
    This represents the cost of using kappa amount of resources
    at a given cost level. Always rounds UP to ensure sufficient budget.
    
    Args:
        kappa: Q18 multiplier (e.g., resource usage)
        cost: Q18 cost per unit
        
    Returns:
        Debit amount in Q18 (rounded UP)
    """
    return q18_mul(kappa, cost, RoundingMode.UP)


def calculate_refund(rho: int, amount: int) -> int:
    """
    Calculate refund using DOWNWARD rounding.
    
    Per spec: refund = floor((rho * amount) / 2^18)
    
    This represents the refund for returning rho proportion of amount.
    Always rounds DOWN to ensure we don't over-refund.
    
    Args:
        rho: Q18 refund rate (e.g., 0.5 = 131072 Q18)
        amount: Q18 amount to refund from
        
    Returns:
        Refund amount in Q18 (rounded DOWN)
    """
    return q18_mul(rho, amount, RoundingMode.DOWN)


# ============================================================================
# Conversion Utilities
# ============================================================================

def int_to_q18(value: int) -> int:
    """
    Convert integer to Q18.
    
    Args:
        value: Integer value
        
    Returns:
        Q18 value (value * 2^18)
    """
    result = value * Q18_SCALE
    
    if result < Q18_MIN or result > Q18_MAX:
        raise OverflowError(
            f"Integer to Q18 overflow: {value} * {Q18_SCALE} = {result} "
            f"exceeds int64 range"
        )
    
    return result


def q18_to_int(value: int) -> int:
    """
    Convert Q18 to integer (discards fractional part).
    
    Args:
        value: Q18 value
        
    Returns:
        Integer value (floor of Q18)
    """
    return value // Q18_SCALE


def q18_to_float(value: int) -> float:
    """
    Convert Q18 to Python float (for display only, not for calculations).
    
    WARNING: Floats lose precision. Use only for debugging/display.
    
    Args:
        value: Q18 value
        
    Returns:
        Float approximation
    """
    return value / Q18_SCALE


def is_valid_q18(value: int) -> bool:
    """
    Check if value is valid Q18.
    
    Args:
        value: Value to check
        
    Returns:
        True if within Q18 range
    """
    return Q18_MIN <= value <= Q18_MAX


# ============================================================================
# Test Vector Helpers
# ============================================================================

def compute_test_vector(a: int, b: int) -> Tuple[int, int, int, int]:
    """
    Compute test vector for Q18 operations.
    
    Returns:
        Tuple of (mul_up, mul_down, div_up, div_down)
    """
    mul_up = q18_mul(a, b, RoundingMode.UP)
    mul_down = q18_mul(a, b, RoundingMode.DOWN)
    div_up = q18_div(a, b, RoundingMode.UP)
    div_down = q18_div(a, b, RoundingMode.DOWN)
    
    return mul_up, mul_down, div_up, div_down
