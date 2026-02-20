# Chain Hash Rule

**Receipt Chaining via Deterministic Hash Links**

| Field | Value |
|-------|-------|
| **Module** | 20_coh_kernel |
| **Section** | Chain Hash Rule |
| **Version** | 1.0.0 |

---

## 1. Chain Definition

Receipts form an immutable chain where each receipt references the previous one via hash links.

### 1.1 Chain Structure

```
ρ₀ (genesis) → ρ₁ → ρ₂ → ... → ρ_T
```

Each ρ_k links to ρ_{k-1}.

### 1.2 Chain Fields

| Field | Description |
|-------|-------------|
| **previous_receipt_id** | First 8 chars of previous receipt's hash |
| **previous_receipt_hash** | Full SHA-256 of previous receipt |
| **chain_hash** | Hash linking current to previous |

---

## 2. Chain Hash Computation

### 2.1 Genesis Receipt (ρ₀)

For the first receipt (no previous):

```
previous_receipt_id = "00000000"
previous_receipt_hash = "sha256:0000000000000000000000000000000000000000000000000000000000000000"
chain_hash = sha256(previous_receipt_id || receipt_id)
```

### 2.2 Subsequent Receipts (ρ_k for k > 0)

```
chain_hash(k) = sha256(
    previous_receipt_id(k) || 
    receipt_id(k)
)
```

### 2.3 Pseudocode

```python
def compute_chain_hash(receipt: Receipt) -> str:
    if receipt.previous_receipt_id == "00000000":
        # Genesis
        prev = "0000000000000000"
    else:
        prev = receipt.previous_receipt_id
    
    chain_input = prev + receipt.receipt_id
    return sha256(chain_input.encode()).hexdigest()
```

---

## 3. Chain Validation

### 3.1 Verification Rules

A receipt chain is valid if:

| Rule | Check |
|------|-------|
| **C1** | receipt.previous_receipt_id = receipt_id(previous receipt) |
| **C2** | receipt.chain_hash = sha256(prev_id || curr_id) |
| **C3** | receipt.previous_receipt_hash = sha256(canonical_bytes(previous)) |

### 3.2 Full Chain Validation

```python
def validate_chain(receipts: List[Receipt]) -> bool:
    # Check genesis
    if receipts[0].previous_receipt_id != "00000000":
        return False
    
    # Check each link
    for i in range(1, len(receipts)):
        curr = receipts[i]
        prev = receipts[i-1]
        
        # Check ID linkage
        if curr.previous_receipt_id != prev.receipt_id:
            return False
        
        # Check chain hash
        expected_chain = sha256(prev.receipt_id + curr.receipt_id)
        if curr.chain_hash != expected_chain:
            return False
    
    return True
```

---

## 4. Immutability Guarantees

### 4.1 Why Chain is Immutable

| Property | Guarantee |
|----------|-----------|
| **No Forward References** | Each receipt only knows its predecessor |
| **Hash Linkage** | Changing any receipt breaks the chain |
| **Deterministic** | Same receipts → same chain |

### 4.2 Tampering Detection

If an attacker modifies receipt ρ_k:

```
1. receipt_id(k) changes (hash changed)
2. ρ_{k+1}.previous_receipt_id now incorrect
3. ρ_{k+1}.chain_hash now incorrect
4. Chain validation fails
```

---

## 5. Chain Properties

### 5.1 Length

```
chain_length = number of receipts in chain
```

### 5.2 Total Risk Accumulation

From the chain, we can compute:

```
total_risk_increase = Σ delta_plus_q[i]
total_budget_consumed = budget_before(0) - budget_after(final)
```

### 5.3 Verification Efficiency

| Operation | Complexity |
|-----------|------------|
| **Single Receipt** | O(1) |
| **Full Chain** | O(n) where n = chain length |

---

## 6. Chain vs Merkle Tree

### 6.1 Chain (ATS)

Simple linked list:
- Each receipt links to one predecessor
- Verification is sequential
- Memory: O(n)

### 6.2 Merkle Tree (Alternative)

Binary tree structure:
- Each node links to two children
- Verification can be partial
- Memory: O(n), but different access pattern

ATS uses **chain** for simplicity and deterministic ordering.

---

## 7. Example

### 7.1 Receipt Chain

```
ρ₀: receipt_id = "a1b2c3d4"
    previous_receipt_id = "00000000"
    chain_hash = sha256("00000000" + "a1b2c3d4")

ρ₁: receipt_id = "e5f6g7h8"
    previous_receipt_id = "a1b2c3d4"
    chain_hash = sha256("a1b2c3d4" + "e5f6g7h8")

ρ₂: receipt_id = "i9j0k1l2"
    previous_receipt_id = "e5f6g7h8"
    chain_hash = sha256("e5f6g7h8" + "i9j0k1l2")
```

### 7.2 Validation

```python
# Verify ρ₁ links to ρ₀
assert ρ₁.previous_receipt_id == ρ₀.receipt_id  # "a1b2c3d4"

# Verify chain hash
expected = sha256("a1b2c3d4" + "e5f6g7h8")
assert ρ₁.chain_hash == expected
```

---

## 8. References

- [Receipt Identity](./receipt_identity.md)
- [Receipt Schema](./receipt_schema.md)
- [Canonical Serialization](./canonical_serialization.md)
- [RV Step Specification](./rv_step_spec.md)
