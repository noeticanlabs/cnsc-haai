"""
Deterministic Numeric Domain - QFixed(18) Implementation

This module implements fixed-point arithmetic for consensus-critical computation.
All arithmetic is deterministic and platform-independent.

Per docs/ats/20_coh_kernel/deterministic_numeric_domain.md:
- QFixed(18) = { n / 10^18 | n ∈ ℤ, n ≥ 0 }
- No floats allowed in consensus-critical paths
- All operations must be deterministic
"""

from __future__ import annotations


# Scale factor: 10^18
SCALE = 10**18
SCALE_BITS = 60  # 2^60 ≈ 10^18

# Maximum integer value (allows values up to MAX_INT in QFixed representation)
MAX_INT = 10000  # Allows up to 10000.0 in QFixed(18)
MAX_VALUE = MAX_INT * SCALE  # Maximum internal value


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
    
    __slots__ = ('value',)
    
    # Class-level constants
    ZERO = None  # Will be set after class definition
    ONE = None   # Will be set after class definition
    
    def __init__(self, value: int):
        """Create QFixed from internal scaled value (0 to MAX_VALUE inclusive)."""
        if value < 0:
            raise QFixedInvalid(f"Negative values forbidden: {value}")
        # Cap at MAX_VALUE to prevent overflow
        if value > MAX_VALUE:
            value = MAX_VALUE
        self.value = value
    
    @classmethod
    def _init_class_constants(cls):
        """Initialize class constants after class is fully defined."""
        cls.ZERO = cls(0)
        cls.ONE = cls(SCALE)
    
    def __repr__(self) -> str:
        return f"QFixed({self.value})"
    
    def __str__(self) -> str:
        # Convert to decimal string
        if self.value == 0:
            return "0"
        integer = self.value // SCALE
        fractional = self.value % SCALE
        fractional_str = str(fractional).rjust(18, '0')
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
        """Add two QFixed numbers, capping at MAX_VALUE on overflow."""
        if not isinstance(other, QFixed):
            return NotImplemented
        result = self.value + other.value
        # Cap at MAX_VALUE instead of raising
        if result > MAX_VALUE:
            result = MAX_VALUE
        return QFixed(result)
    
    def __sub__(self, other: QFixed) -> QFixed:
        """Subtract two QFixed numbers, flooring at 0."""
        if not isinstance(other, QFixed):
            return NotImplemented
        result = self.value - other.value
        # Floor at 0 (no negative values allowed)
        if result < 0:
            result = 0
        return QFixed(result)
    
    def __mul__(self, other: QFixed) -> QFixed:
        """Multiply two QFixed numbers."""
        if not isinstance(other, QFixed):
            return NotImplemented
        # Use integer division by SCALE to get result
        result = (self.value * other.value) // SCALE
        # Cap at MAX_VALUE
        if result > MAX_VALUE:
            result = MAX_VALUE
        return QFixed(result)
    
    def __truediv__(self, other: QFixed) -> QFixed:
        """Divide two QFixed numbers."""
        if not isinstance(other, QFixed):
            return NotImplemented
        if other.value == 0:
            raise QFixedUnderflow("Division by zero")
        # Multiply by SCALE to maintain precision
        result = (self.value * SCALE) // other.value
        # Cap at MAX_VALUE
        if result > MAX_VALUE:
            result = MAX_VALUE
        return QFixed(result)
    
    def __radd__(self, other: QFixed) -> QFixed:
        return self.__add__(other)
    
    def __rsub__(self, other: QFixed) -> QFixed:
        """Reverse subtraction: other - self"""
        if not isinstance(other, QFixed):
            return NotImplemented
        result = other.value - self.value
        if result < 0:
            result = 0
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
        if '.' in s:
            integer_str, fractional_str = s.split('.')
            # Pad or truncate fractional to 18 digits
            if len(fractional_str) < 18:
                fractional_str = fractional_str.ljust(18, '0')
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


def qfixed_cmp(a: QFixed, b: QFixed) -> int:
    """Compare two QFixed numbers. Returns -1, 0, or 1."""
    if a < b:
        return -1
    elif a > b:
        return 1
    else:
        return 0
