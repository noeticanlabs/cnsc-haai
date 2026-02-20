# Deterministic Numeric Domain

**Fixed-Point Arithmetic for Consensus-Critical Computation**

| Field | Value |
|-------|-------|
| **Module** | 20_coh_kernel |
| **Section** | Deterministic Numeric Domain |
| **Version** | 1.0.0 |

---

## 1. Domain Definition

The ATS uses **fixed-point arithmetic** to ensure deterministic numeric computation across all platforms.

### 1.1 Primary Domain: QFixed(18)

```
QFixed(18) = { n / 10^18 | n ∈ ℤ, n ≥ 0 }
```

| Property | Value |
|----------|-------|
| **Precision** | 18 decimal places |
| **Range** | [0, 10^18 - 1] |
| **Storage** | 64-bit unsigned integer |

### 1.2 Alternative: Scaled Integer

```
ScaledInt = { n × S | n ∈ ℤ, n ≥ 0 }
```

| Property | Value |
|----------|-------|
| **Scale** | S = 10^18 |
| **Storage** | 64-bit signed integer |

---

## 2. Prohibited Types

### 2.1 Binary Floating-Point Forbidden

The following types **MUST NOT** appear in consensus-critical code:

| Type | Reason |
|------|--------|
| **float32** | IEEE 754 rounding varies by platform |
| **float64** | Precision loss across implementations |
| **bfloat16** | Non-deterministic edge cases |

### 2.2 Why No Floats

```python
# WRONG - float addition is non-deterministic
x = 0.1 + 0.2
# x may be 0.30000000000000004 or 0.29999999999999999

# CORRECT - fixed-point arithmetic
x = QFixed(1) / 10 + QFixed(2) / 10
# x is exactly 3/10 = 300000000000000000 in QFixed(18)
```

---

## 3. Operations

### 3.1 Arithmetic Operations

| Operation | QFixed(18) | ScaledInt |
|-----------|------------|-----------|
| **Addition** | (a + b) | (a + b) / S |
| **Subtraction** | (a - b) | (a - b) / S |
| **Multiplication** | (a × b) / 10^18 | (a × b) / S |
| **Division** | (a × 10^18) / b | (a × S) / b |

### 3.2 Comparison Operations

| Operation | Implementation |
|-----------|----------------|
| **a < b** | a.compare(b) < 0 |
| **a ≤ b** | a.compare(b) ≤ 0 |
| **a = b** | a.compare(b) = 0 |
| **a > b** | a.compare(b) > 0 |
| **a ≥ b** | a.compare(b) ≥ 0 |

### 3.3 Rounding Rules

| Scenario | Rule |
|----------|------|
| **Division** | Truncate toward zero |
| **Multiplication** | Truncate toward zero |
| **Addition/Subtraction** | Exact (no rounding) |

---

## 4. Overflow Handling

### 4.1 Overflow Behavior

| Condition | Behavior |
|-----------|----------|
| **Addition Overflow** | REJECT step |
| **Subtraction Underflow** | Treat as 0 |
| **Multiplication Overflow** | REJECT step |
| **Division by Zero** | REJECT step |

### 4.2 Detection

```python
def safe_add(a, b):
    result = a + b
    if result > MAX_QFIXED:
        return ERROR_OVERFLOW
    return result

def safe_mul(a, b):
    result = (a * b) >> SCALE_BITS
    if result > MAX_QFIXED:
        return ERROR_OVERFLOW
    return result
```

---

## 5. Canonical Formatting

### 5.1 Serialization

QFixed values serialize to canonical decimal strings:

```json
{
  "risk_before_q": "1000000000000000000",
  "budget_after_q": "500000000000000000"
}
```

### 5.2 No Scientific Notation

```
CORRECT:   "1000000000000000000"
INCORRECT: "1e18"
```

### 5.3 Leading Zeros

```
CORRECT:   "000000000100000000"
INCORRECT: "100000000"
```

---

## 6. Constants

### 6.1 Common Constants in QFixed(18)

| Constant | QFixed(18) | Hex |
|----------|-------------|-----|
| **0** | 0 | 0x0 |
| **1** | 10^18 | 0x3B9ACA0000000000 |
| **-1** | N/A | N/A (negative forbidden) |
| **MAX** | 10^18 - 1 | 0x3B9ACAFFFFFFFFFFFF |

---

## 7. Implementation Reference

### 7.1 Python Implementation

```python
class QFixed:
    SCALE = 10**18
    
    def __init__(self, value: int):
        if value < 0:
            raise ValueError("Negative values forbidden")
        if value > self.SCALE - 1:
            raise ValueError("Overflow")
        self.value = value
    
    @classmethod
    def from_int(cls, n: int) -> 'QFixed':
        return cls(n * cls.SCALE)
    
    def __add__(self, other: 'QFixed') -> 'QFixed':
        result = self.value + other.value
        if result >= self.SCALE:
            raise OverflowError("Addition overflow")
        return QFixed(result)
    
    def __mul__(self, other: 'QFixed') -> 'QFixed':
        result = (self.value * other.value) // self.SCALE
        return QFixed(result)
    
    def __str__(self) -> str:
        return str(self.value)
```

---

## 8. References

- [Coh Kernel Scope](../00_identity/coh_kernel_scope.md)
- [Risk Functional V](../10_mathematical_core/risk_functional_V.md)
- [Budget Law](../10_mathematical_core/budget_law.md)
- [RV Step Specification](./rv_step_spec.md)
