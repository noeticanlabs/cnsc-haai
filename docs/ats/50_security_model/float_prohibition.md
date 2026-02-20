# Float Prohibition

**Binary Floating-Point Ban in Consensus Domain**

| Field | Value |
|-------|-------|
| **Module** | 50_security_model |
| **Section** | Float Prohibition |
| **Version** | 1.0.0 |

---

## 1. Prohibition Statement

### 1.1 Binary Floating-Point Forbidden

The following types **MUST NOT** appear in consensus-critical code:

| Type | Status |
|------|--------|
| **float32** | FORBIDDEN |
| **float64** | FORBIDDEN |
| **bfloat16** | FORBIDDEN |
| **half** | FORBIDDEN |

### 1.2 Rationale

Binary floating-point introduces non-determinism due to:
- Platform-specific rounding
- FPU register precision variations
- Compiler optimization differences

---

## 2. The Float Problem

### 2.1 Non-Determinism Example

```python
# Python
x = 0.1 + 0.2
print(x)  # 0.30000000000000004

# Different platforms may get:
# 0.30000000000000004
# 0.29999999999999999
# 0.3
```

### 2.2 Why This Matters

```
In ATS, deterministic verification requires:
- Same input → Same risk value → Same verification result

If float introduces variance:
- Runtime computes: V(x) = 0.3
- Verifier computes: V(x) = 0.30000000000000004
- MISMATCH → REJECT
```

---

## 3. Allowed Numeric Types

### 3.1 QFixed (Recommended)

```
QFixed(18) = { n / 10^18 | n ∈ ℤ, n ≥ 0 }
```

Deterministic fixed-point with 18 decimal places.

### 3.2 Scaled Integer

```
ScaledInt = n × S where S = 10^18
```

Integer with fixed scale factor.

### 3.3 Integer

For whole numbers:
- int8, int16, int32, int64
- uint8, uint16, uint32, uint64

---

## 4. Conversion

### 4.1 Float to QFixed

```python
# WRONG
value = float(0.1)

# CORRECT - convert via string
value = QFixed.from_decimal_string("0.1")  # = 100000000000000000

# Or from integer
value = QFixed(1) // 10  # = 100000000000000000
```

### 4.2 Float Array to QFixed Array

```python
# WRONG
risks = [float(0.1), float(0.2)]

# CORRECT
risks = [QFixed(1) // 10, QFixed(2) // 10]
```

---

## 5. Detection

### 5.1 Code Scanning

```python
import ast

def check_no_floats(source_code):
    """Scan source for float literals."""
    tree = ast.parse(source_code)
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, float):
                raise ValueError(f"Float literal at line {node.lineno}")
        
        if isinstance(node, ast.Name):
            if node.id in ('float', 'float32', 'float64'):
                raise ValueError(f"Float type at line {node.lineno}")
```

### 5.2 Type Checking

```python
# Runtime type check
def compute_risk(state):
    if isinstance(state.value, float):
        raise TypeError("Float not allowed in risk computation")
    # ... compute with QFixed
```

---

## 6. References

- [Deterministic Numeric Domain](../20_coh_kernel/deterministic_numeric_domain.md)
- [Deterministic Replay Requirements](./deterministic_replay_requirements.md)
- [Risk Functional V](../10_mathematical_core/risk_functional_V.md)
