# Canonical Serialization

**Deterministic Byte Representation for All ATS Types**

| Field | Value |
|-------|-------|
| **Module** | 20_coh_kernel |
| **Section** | Canonical Serialization |
| **Version** | 1.0.0 |

---

## 1. Serialization Principles

### 1.1 Determinism Requirement

Canonical serialization ensures:
- Same object → same bytes (always)
- Different objects → different bytes (with overwhelming probability)
- Platform-independent output

### 1.2 Key Rules

| Rule | Description |
|------|-------------|
| **R1** | Fixed byte order (big-endian) |
| **R2** | Sorted dictionary keys |
| **R3** | Type tags included |
| **R4** | Schema version included |
| **R5** | No whitespace variation |

---

## 2. Data Type Serialization

### 2.1 Integer Types

```python
# Signed integers: 2's complement, big-endian
def serialize_int(n: int, bytes: int) -> bytes:
    return n.to_bytes(bytes, byteorder='big', signed=True)

# Unsigned integers: big-endian
def serialize_uint(n: int, bytes: int) -> bytes:
    return n.to_bytes(bytes, byteorder='big', signed=False)
```

### 2.2 String Types

```python
# All strings: UTF-8 encoding
def serialize_string(s: str) -> bytes:
    return s.encode('utf-8')
```

### 2.3 Boolean Types

```python
# Boolean: single byte
TRUE  = b'\x01'
FALSE = b'\x00'
```

### 2.4 Null Types

```python
# Null: single byte
NULL = b'\x00'
```

---

## 3. Collection Serialization

### 3.1 Dictionary (Object)

Keys are **sorted lexicographically**:

```python
def serialize_dict(d: dict) -> bytes:
    result = b''
    for key in sorted(d.keys()):
        result += serialize_string(key)
        result += serialize_value(d[key])
    return result
```

**Example:**
```python
{"b": 1, "a": 2}  →  serialize("a") + serialize(2) + serialize("b") + serialize(1)
```

### 3.2 List (Array)

Order **preserved as-is**:

```python
def serialize_list(l: list) -> bytes:
    result = b''
    for item in l:
        result += serialize_value(item)
    return result
```

### 3.3 Sets

Converted to **sorted list**:

```python
def serialize_set(s: set) -> bytes:
    return serialize_list(sorted(s))
```

---

## 4. Envelope Format

### 4.1 Type Tag

Every serialized value includes a type tag:

```
┌─────────────────────────────────────────────┐
│  Type Tag (4 bytes)  │  Version (4 bytes)  │
├─────────────────────────────────────────────┤
│              Payload (variable)              │
└─────────────────────────────────────────────┘
```

### 4.2 Type Tags

| Type | Tag (hex) |
|------|-----------|
| **State** | 0x53544154 ("STAT") |
| **Action** | 0x41435447 ("ACTG") |
| **Receipt** | 0x52434549 ("RCEI") |
| **Budget** | 0x42444745 ("BDGE") |
| **Risk** | 0x524B5350 ("RKSP") |

### 4.3 Version Format

```
Version = major << 16 | minor << 8 | patch
```

Example: v1.0.0 → 0x010000

---

## 5. Complete Serialization

### 5.1 State Serialization

```python
def canonical_bytes(state: State) -> bytes:
    envelope = b'STAT\x01\x00\x00'  # Type + v1.0.0
    
    # Components in fixed order
    envelope += serialize_dict(state.belief)      # X_belief
    envelope += serialize_list(state.memory)       # X_memory
    envelope += serialize_list(state.plan)         # X_plan
    envelope += serialize_dict(state.policy)        # X_policy
    envelope += serialize_dict(state.io)            # X_io
    
    return envelope
```

### 5.2 Receipt Serialization

```python
def canonical_bytes(receipt: Receipt) -> bytes:
    envelope = b'RCEI\x01\x00\x00'  # Type + v1.0.0
    
    # Fields in canonical order
    envelope += serialize_string(receipt.version)
    envelope += serialize_string(receipt.receipt_id)
    envelope += serialize_string(receipt.timestamp)
    envelope += serialize_string(receipt.episode_id)
    envelope += serialize_dict(receipt.content)
    envelope += serialize_dict(receipt.provenance)
    envelope += serialize_dict(receipt.signature)
    envelope += serialize_string(receipt.previous_receipt_id)
    envelope += serialize_string(receipt.previous_receipt_hash)
    envelope += serialize_string(receipt.chain_hash)
    envelope += serialize_dict(receipt.metadata)
    
    return envelope
```

---

## 6. Hash Computation

### 6.1 State Hash

```python
def state_hash(state: State) -> str:
    return sha256(canonical_bytes(state)).hexdigest()
```

### 6.2 Receipt Hash

```python
def receipt_hash(receipt: Receipt) -> str:
    return sha256(canonical_bytes(receipt)).hexdigest()
```

---

## 7. Canonical Examples

### 7.1 Identical States

```python
# These produce identical bytes:
state1 = {"a": 1, "b": 2}
state2 = {"b": 2, "a": 1}

canonical_bytes(state1) == canonical_bytes(state2)  # True
```

### 7.2 Floating-Point Rejection

```python
# This is INVALID in ATS:
{"risk": 0.1}

# Must use QFixed:
{"risk": "100000000000000000"}
```

---

## 8. References

- [State Space](../10_mathematical_core/state_space.md)
- [Deterministic Numeric Domain](./deterministic_numeric_domain.md)
- [Receipt Schema](./receipt_schema.md)
- [Chain Hash Rule](./chain_hash_rule.md)
