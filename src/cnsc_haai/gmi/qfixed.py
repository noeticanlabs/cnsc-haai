"""
QFixed6 - Deterministic Fixed-Point Arithmetic

This module provides integer-based fixed-point arithmetic for GMI.
No floats allowed - all computations use scaled integers.
"""

from __future__ import annotations
from dataclasses import dataclass

SCALE = 10**6  # QFixed6: integers represent value / 1e6


@dataclass(frozen=True)
class Q:
    """Immutable QFixed6 value - scaled integer representation."""
    v: int  # scaled integer

    @staticmethod
    def from_int(i: int) -> "Q":
        """Create Q from integer (scales by SCALE)."""
        return Q(i * SCALE)

    @staticmethod
    def from_scaled(v: int) -> "Q":
        """Create Q from already-scaled integer."""
        return Q(v)

    def add(self, other: "Q") -> "Q":
        """Addition - returns new Q with summed scaled values."""
        return Q(self.v + other.v)

    def sub(self, other: "Q") -> "Q":
        """Subtraction - returns new Q with difference."""
        return Q(self.v - other.v)

    def mul_q(self, other: "Q") -> "Q":
        """
        Multiplication of two Q values.
        (a/SCALE)*(b/SCALE) = (a*b)/SCALE^2 -> scaled: (a*b)/SCALE
        """
        return Q((self.v * other.v) // SCALE)

    def mul_int(self, k: int) -> "Q":
        """Multiply Q by integer constant."""
        return Q(self.v * k)

    def div_int(self, k: int) -> "Q":
        """Divide Q by integer constant (truncates toward 0)."""
        if k == 0:
            raise ZeroDivisionError("Q.div_int by 0")
        return Q(self.v // k)

    def le(self, other: "Q") -> bool:
        """Less-than-or-equal comparison."""
        return self.v <= other.v

    def lt(self, other: "Q") -> bool:
        """Strict less-than comparison."""
        return self.v < other.v

    def ge(self, other: "Q") -> bool:
        """Greater-than-or-equal comparison."""
        return self.v >= other.v

    def max0(self) -> "Q":
        """Return max(0, self) - used for ReLU-like operations."""
        return Q(self.v if self.v > 0 else 0)

    def min(self, other: "Q") -> "Q":
        """Return min(self, other)."""
        return Q(self.v if self.v < other.v else other.v)

    def max(self, other: "Q") -> "Q":
        """Return max(self, other)."""
        return Q(self.v if self.v > other.v else other.v)

    def __repr__(self) -> str:
        return f"Q({self.v})"
