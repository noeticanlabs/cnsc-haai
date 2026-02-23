# Receipt Identity

**Deterministic Receipt Identifier Generation**

| Field | Value |
|-------|-------|
| **Module** | 20_coh_kernel |
| **Section** | Receipt Identity |
| **Version** | 1.0.0 |

---

## 1. Receipt ID Definition

### 1.1 No UUIDs Allowed

In the consensus domain, **UUIDs are forbidden**. They introduce non-determinism.

### 1.2 Receipt ID Computation

The receipt ID is the **first 8 characters** of the SHA-256 hash of the canonical receipt bytes:

```
receipt_id = first8(sha256(canonical_bytes(receipt)))
```

### 1.3 Format

| Property | Value |
|----------|-------|
| **Length** | 8 characters |
| **Characters** | Lowercase hexadecimal (0-9, a-f) |
| **Example** | `a1b2c3d4` |

---

## 2. Computation Process

### 2.1 Step-by-Step

```
1. Serialize receipt to canonical bytes
   → canonical_bytes(receipt)

2. Compute SHA-256 hash
   → sha256(canonical_bytes(receipt))

3. Convert to hexadecimal
   → 64-character hex string

4. Take first 8 characters
   → receipt_id (8 characters)
```

### 2.2 Pseudocode

```python
def compute_receipt_id(receipt: Receipt) -> str:
    # Step 1: Canonical bytes
    canonical = canonical_bytes(receipt)
    
    # Step 2: SHA-256 hash
    hash_bytes = sha256(canonical)
    
    # Step 3: Hex encoding
    hex_string = hash_bytes.hex()
    
    # Step 4: First 8 characters
    receipt_id = hex_string[:8]
    
    return receipt_id
```

---

## 3. Determinism Guarantees

### 3.1 Why This Works

| Property | Guarantee |
|----------|-----------|
| **Deterministic** | Same receipt → same ID |
| **Unique** | Different receipts → different IDs (collision probability: 2^-32) |
| **No Randomness** | No UUIDs, no timestamps in ID |

### 3.2 Collision Resistance

```
Probability of collision for 2^n receipts: ≈ n² / 2^32

For 1 million receipts: ≈ 10^-10 (negligible)
```

---

## 4. Receipt ID in Verification

### 4.1 Self-Referential Validation

The receipt ID is computed **from** the receipt, but the receipt contains **the ID**. This is validated as:

```python
def verify_receipt_id(receipt: Receipt) -> bool:
    # Recompute ID
    computed_id = compute_receipt_id(receipt)
    
    # Compare with stored ID
    return computed_id == receipt.receipt_id
```

### 4.2 First Receipt (Genesis)

For the first receipt in a trajectory (no previous receipt):

```
previous_receipt_id = "00000000"
previous_receipt_hash = "sha256:0000000000000000..."
```

---

## 5. Examples

### 5.1 Example Receipt

```json
{
  "version": "1.0.0",
  "receipt_id": "a1b2c3d4",
  "content": {
    "step_type": "VM_EXECUTION",
    "risk_before_q": "1000000000000000000",
    "risk_after_q": "800000000000000000",
    "delta_plus_q": "0",
    "budget_before_q": "1000000000000000000",
    "budget_after_q": "1000000000000000000",
    "kappa_q": "1000000000000000000",
    "state_hash_before": "sha256:abc123...",
    "state_hash_after": "sha256:def456...",
    "decision": "PASS"
  }
}
```

### 5.2 ID Verification

```python
# Canonical bytes (simplified)
canonical = b'RCEI\x01\x00\x00{"version":"1.0.0",...}'

# SHA-256
hash = sha256(canonical)
# = a1b2c3d4e5f6... (64 hex chars)

# First 8 chars = receipt_id
receipt_id = "a1b2c3d4"
```

---

## 6. Chain Link

Receipts form a chain via:

```
receipt_id(k) = first8(sha256(canonical_bytes(receipt_k)))
chain_digest(k) = sha256(chain_digest(k-1) || receipt_id(k))
```

See [Chain Hash Universal](./chain_hash_universal.md) for details.

---

## 7. References

- [Receipt Schema](./receipt_schema.md)
- [Chain Hash Universal](./chain_hash_universal.md)
- [Canonical Serialization](./canonical_serialization.md)
- [RV Step Specification](./rv_step_spec.md)
