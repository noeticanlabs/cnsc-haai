"""
Deterministic Numeric Domain - QFixed(18) Implementation

This module implements fixed-point arithmetic for consensus-critical computation.
All arithmetic is deterministic and platform-independent.

Per docs/ats/20_coh_kernel/deterministic_numeric_domain.md:
- QFixed(18) = { n / 10^18 | n ∈ ℤ, n ≥ 0 }
- No floats allowed in consensus-critical paths
- All operations must be deterministic

===============================================================================
UNIT CONVENTIONS (Per Gap E)
===============================================================================

- V (risk) measured in "risk micro-units" = 1 QFixed unit
- B (budget) measured in "budget micro-units" = 1 QFixed unit
- κ (kappa) maps risk → budget with fixed scale

Allowed κ range:
- MIN_KAPPA = 1 (minimum stiffness)
- MAX_KAPPA = 1000 (maximum stiffness)
- DEFAULT_KAPPA = 1 (default stiffness)

These are INVARIANT under rescaling - the kernel enforces them directly.
"""

from __future__ import annotations

# Scale factor: 10^18
SCALE = 10**18
SCALE_BITS = 60  # 2^60 ≈ 10^18

# Maximum integer value
# Per deterministic_numeric_domain.md: QFixed(18) range is [0, 10^18 - 1]
# Using MAX_INT = 10^7 to keep internal values manageable while allowing
# values up to 10,000,000.0 in QFixed(18) representation
MAX_INT = 10**7  # 10 million
MAX_VALUE = MAX_INT * SCALE  # Maximum internal value

# Unit conventions (Per Gap E: κ unit conventions)
MIN_KAPPA = 1  # Minimum κ
MAX_KAPPA = 1000  # Maximum κ
DEFAULT_KAPPA = 1  # Default κ


class QFixedOverflow(Exception):
    """Raised when QFixed operation overflows."""

    pass


class QFixedUnderflow(Exception):
    """Raised when QFixed operation underflows."""

    pass


class QFixedInvalid(Exception):
    """Raised when QFixed value is invalid (negative, NaN, etc.)."""

    pass


class QFixed:
    """
    Deterministic fixed-point number with 18 decimal places.

    Internal representation: int storing value * SCALE

    Valid range: [0, MAX_VALUE] = [0.0, MAX_INT] in QFixed(18)

    Examples:
        QFixed(0)           = 0.0
        QFixed(500000000000000000) = 0.5
        QFixed(1000000000000000000) = 1.0
        QFixed.from_int(1)  = 1.0 = 10^18
        QFixed.from_str("0.1") = 0.1 = 10^17
    """

    __slots__ = ("value",)

    # Class-level constants
    ZERO = None  # Will be set after class definition
    ONE = None  # Will be set after class definition

    def __init__(self, value: int):
        """
        Create QFixed from internal scaled value (0 to MAX_VALUE inclusive).

        IMPORTANT: In consensus paths, negative and overflow values cause explicit
        rejection via exceptions rather than silent saturation/flooring.
        """
        if value < 0:
            raise QFixedInvalid(f"Negative values forbidden in consensus: {value}")
        # Explicit overflow rejection (not silent capping)
        if value > MAX_VALUE:
            raise QFixedOverflow(f"Value exceeds MAX_VALUE in consensus: {value} > {MAX_VALUE}")
        self.value = value

    @classmethod
    def _init_class_constants(cls):
        """Initialize class constants after class is fully defined."""
        cls.ZERO = cls(0)
        cls.ONE = cls(SCALE)

    def __repr__(self) -> str:
        return f"QFixed({self.value})"

    def compute_delta(self, other: QFixed) -> QFixedDelta:
        """
        Compute signed delta between two QFixed values.

        Returns a QFixedDelta that preserves sign information, allowing correct
        budget law enforcement without silent negative→zero conversion.

        This is the preferred method for budget law computation.

        Args:
            other: The QFixed value to compare against.

        Returns:
            QFixedDelta with sign information preserved (can be negative).

        Example:
            >>> r_before = QFixed.from_int(1)   # 1.0
            >>> r_after = QFixed.from_int(2)    # 2.0 (increased)
            >>> delta = r_after.compute_delta(r_before)
            >>> delta.is_positive()
            True
            >>> delta.plus()  # max(0, delta) for budget law
            QFixed(1000000000000000000)
        """
        return QFixedDelta(self.value - other.value)  # Can be negative!

    def __str__(self) -> str:
        # Convert to decimal string
        if self.value == 0:
            return "0"
        integer = self.value // SCALE
        fractional = self.value % SCALE
        fractional_str = str(fractional).rjust(18, "0")
        return f"{integer}.{fractional_str}"

    # Comparison operators
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, QFixed):
            return NotImplemented
        return self.value == other.value

    def __hash__(self) -> int:
        return hash(self.value)

    def __lt__(self, other: QFixed) -> bool:
        if not isinstance(other, QFixed):
            return NotImplemented
        return self.value < other.value

    def __le__(self, other: QFixed) -> bool:
        return self == other or self < other

    def __gt__(self, other: QFixed) -> bool:
        if not isinstance(other, QFixed):
            return NotImplemented
        return self.value > other.value

    def __ge__(self, other: QFixed) -> bool:
        return self == other or self > other

    # Arithmetic operators
    def __add__(self, other: QFixed) -> QFixed:
        """Add two QFixed numbers.

        Per deterministic numeric domain spec: overflow causes step REJECTION.
        This raises QFixedOverflow instead of silently capping.
        """
        if not isinstance(other, QFixed):
            return NotImplemented
        result = self.value + other.value
        # Raise on overflow (per spec)
        if result > MAX_VALUE:
            raise QFixedOverflow(f"Overflow in QFixed addition: {self} + {other} exceeds MAX_VALUE")
        return QFixed(result)

    def __sub__(self, other: QFixed) -> QFixed:
        """
        Subtraction for consensus paths.

        NOTE: For budget law, use compute_delta() instead to get signed result.
        This method raises an exception for negative results (consensus paths).
        For non-consensus paths that need flooring, use sub_raw() method.
        """
        if not isinstance(other, QFixed):
            return NotImplemented
        result = self.value - other.value
        # Raise exception for negative results (consensus-appropriate behavior)
        if result < 0:
            raise QFixedInvalid(f"Negative result not allowed in consensus: {self} - {other}")
        return QFixed(result)

    def __mul__(self, other: QFixed) -> QFixed:
        """Multiply two QFixed numbers.

        Per deterministic numeric domain spec: overflow causes step REJECTION.
        This raises QFixedOverflow instead of silently capping.
        """
        if not isinstance(other, QFixed):
            return NotImplemented
        # Use integer division by SCALE to get result
        result = (self.value * other.value) // SCALE
        # Raise on overflow (per spec)
        if result > MAX_VALUE:
            raise QFixedOverflow(
                f"Overflow in QFixed multiplication: {self} * {other} exceeds MAX_VALUE"
            )
        return QFixed(result)

    def __truediv__(self, other: QFixed) -> QFixed:
        """Divide two QFixed numbers.

        Per deterministic numeric domain spec: overflow causes step REJECTION.
        This raises QFixedOverflow instead of silently capping.
        """
        if not isinstance(other, QFixed):
            return NotImplemented
        if other.value == 0:
            raise QFixedUnderflow("Division by zero")
        # Multiply by SCALE to maintain precision
        result = (self.value * SCALE) // other.value
        # Raise on overflow (per spec)
        if result > MAX_VALUE:
            raise QFixedOverflow(f"Overflow in QFixed division: {self} / {other} exceeds MAX_VALUE")
        if result > MAX_VALUE:
            result = MAX_VALUE
        return QFixed(result)

    def __radd__(self, other: QFixed) -> QFixed:
        return self.__add__(other)

    def __rsub__(self, other: QFixed) -> QFixed:
        """
        Reverse subtraction: other - self

        For consensus paths, raises exception for negative results.
        """
        if not isinstance(other, QFixed):
            return NotImplemented
        result = other.value - self.value
        if result < 0:
            raise QFixedInvalid(f"Negative result not allowed in consensus: {other} - {self}")
        return QFixed(result)

    def __rmul__(self, other: QFixed) -> QFixed:
        return self.__mul__(other)

    def __rtruediv__(self, other: QFixed) -> QFixed:
        """Reverse division: other / self"""
        if not isinstance(other, QFixed):
            return NotImplemented
        if self.value == 0:
            raise QFixedUnderflow("Division by zero")
        result = (other.value * SCALE) // self.value
        if result > MAX_VALUE:
            result = MAX_VALUE
        return QFixed(result)

    # Unary operators
    def __neg__(self) -> QFixed:
        """Negation (returns ZERO since we don't support negatives)."""
        return QFixed(0)

    def __pos__(self) -> QFixed:
        """Positive (returns self)."""
        return self

    def __abs__(self) -> QFixed:
        """Absolute value (returns self since we don't support negatives)."""
        return self

    # Class methods for construction
    @classmethod
    def from_int(cls, n: int) -> QFixed:
        """Create QFixed from integer n (represents n.0)."""
        value = n * SCALE
        # Cap at MAX_VALUE, floor at 0
        if value > MAX_VALUE:
            value = MAX_VALUE
        elif value < 0:
            value = 0
        return cls(value)

    @classmethod
    def from_decimal(cls, integer: int, fractional: int = 0, fractional_digits: int = 18) -> QFixed:
        """Create QFixed from integer and fractional parts."""
        if integer < 0:
            raise QFixedInvalid(f"Negative values forbidden: {integer}")
        # Scale the fractional part to 18 digits
        if fractional_digits < 18:
            fractional = fractional * (10 ** (18 - fractional_digits))
        elif fractional_digits > 18:
            fractional = fractional // (10 ** (fractional_digits - 18))
        value = integer * SCALE + fractional
        if value > MAX_VALUE:
            value = MAX_VALUE
        return cls(value)

    @classmethod
    def from_str(cls, s: str) -> QFixed:
        """Create QFixed from string like '0.1' or '1.5'."""
        if "." in s:
            integer_str, fractional_str = s.split(".")
            # Pad or truncate fractional to 18 digits
            if len(fractional_str) < 18:
                fractional_str = fractional_str.ljust(18, "0")
            else:
                fractional_str = fractional_str[:18]
            return cls.from_decimal(int(integer_str), int(fractional_str), 18)
        else:
            return cls.from_int(int(s))

    @classmethod
    def safe_from_float(cls, f: float) -> QFixed:
        """Create QFixed from float (for testing only - not deterministic!)."""
        if f < 0:
            raise QFixedInvalid(f"Negative values forbidden: {f}")
        # Multiply by SCALE and convert to int
        value = int(f * SCALE)
        if value > MAX_VALUE:
            value = MAX_VALUE
        return cls(value)

    # Instance methods
    def is_zero(self) -> bool:
        """Check if value is zero."""
        return self.value == 0

    def is_one(self) -> bool:
        """Check if value equals 1.0."""
        return self.value == SCALE

    def to_int(self) -> int:
        """Convert to integer (truncates fractional part)."""
        return self.value // SCALE

    def to_float(self) -> float:
        """Convert to float (for testing only - not deterministic!)."""
        return self.value / SCALE

    def to_raw(self) -> int:
        """Return raw internal value (for serialization)."""
        return self.value

    def to_json(self) -> dict:
        """Serialize to JSON-compatible format."""
        return {"value": self.value, "scale": SCALE, "repr": str(self)}

    @classmethod
    def from_value(cls, n: int) -> QFixed:
        """Create QFixed from integer value (alias for from_int)."""
        return cls.from_int(n)

    # Arithmetic operations that return raw values for compatibility
    def add_raw(self, other: QFixed) -> int:
        """Add and return raw internal value (capped)."""
        result = self.value + other.value
        if result > MAX_VALUE:
            result = MAX_VALUE
        return result

    def sub_raw(self, other: QFixed) -> int:
        """Subtract and return raw internal value (floored at 0)."""
        result = self.value - other.value
        if result < 0:
            result = 0
        return result


# Initialize class constants
QFixed._init_class_constants()


class QFixedDelta:
    """
    Signed delta for proper budget law computation.

    This class exists because QFixed disallows negative values (for consensus safety),
    but the budget law needs to know the sign of risk deltas.

    Per docs/ats/10_mathematical_core/budget_law.md:
    - If ΔV ≤ 0: B_next = B_prev (budget preserved)
    - If ΔV > 0: B_next = B_prev - κ × ΔV (budget consumed)
    """

    __slots__ = ("raw_delta",)

    def __init__(self, raw_delta: int):
        """
        Create a signed delta from raw integer difference.

        Args:
            raw_delta: Can be negative, zero, or positive.
        """
        self.raw_delta = raw_delta

    def is_positive(self) -> bool:
        """Return True if delta > 0."""
        return self.raw_delta > 0

    def is_negative(self) -> bool:
        """Return True if delta < 0."""
        return self.raw_delta < 0

    def is_zero(self) -> bool:
        """Return True if delta == 0."""
        return self.raw_delta == 0

    def sign(self) -> int:
        """Return -1, 0, or 1."""
        if self.raw_delta > 0:
            return 1
        elif self.raw_delta < 0:
            return -1
        return 0

    def plus(self) -> QFixed:
        """
        Return max(0, delta) for budget law.

        This is ΔV⁺ in the budget law formula.
        """
        return QFixed(max(0, self.raw_delta))

    def abs_value(self) -> QFixed:
        """Return absolute value as QFixed."""
        return QFixed(abs(self.raw_delta))

    def __repr__(self) -> str:
        return f"QFixedDelta({self.raw_delta})"

    def __str__(self) -> str:
        return f"Δ={self.raw_delta / SCALE:+.18f}"


def qfixed_cmp(a: QFixed, b: QFixed) -> int:
    """Compare two QFixed numbers. Returns -1, 0, or 1."""
    if a < b:
        return -1
    elif a > b:
        return 1
    else:
        return 0


def compute_signed_delta(a: QFixed, b: QFixed) -> QFixedDelta:
    """
    Compute signed delta between two QFixed values.

    This is the CORRECT way to compute ΔV for budget law verification,
    as it preserves sign information that QFixed subtraction loses.

    Args:
        a: Ending value (e.g., risk_after)
        b: Starting value (e.g., risk_before)

    Returns:
        QFixedDelta with sign information preserved.

    Example:
        >>> r_before = QFixed(1000000000000000000)  # 1.0
        >>> r_after = QFixed(500000000000000000)   # 0.5 (decreased)
        >>> delta = compute_signed_delta(r_after, r_before)
        >>> delta.is_positive()
        False
        >>> delta.is_negative()
        True
        >>> delta.plus()  # max(0, delta)
        QFixed(0)
    """
    return QFixedDelta(a.value - b.value)


# =============================================================================
# Per Gap I: Tensor Composition Semantics
# =============================================================================

"""
TENSOR COMPOSITION LAWS (Per Gap I)

For parallel subsystems S₁ ⊗ S₂:

### Budget Additivity
B_total = B₁ + B₂  (simple addition)

### Risk... NOT additive!
V_total ≠ V₁ + V₂  (risk is not a resource)

Instead:
- If independent: V_total = max(V₁, V₂)
- If interacting: V_total requires interaction matrix

### Counterexample

Cartesian product X × Y fails because:
- (x₁, y₁) and (x₂, y₂) can have individual risk < threshold
- But (x₁, y₂) can have combined risk >> threshold
- Therefore no simple product law exists

For ATS v1: Only support sequential composition (⊕), not tensor (⊗)
"""
