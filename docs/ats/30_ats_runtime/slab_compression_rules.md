# Slab Compression Rules

**Receipt Aggregation and Compression**

| Field | Value |
|-------|-------|
| **Module** | 30_ats_runtime |
| **Section** | Slab Compression Rules |
| **Version** | 1.0.0 |

---

## 1. Overview

Slab compression allows aggregating multiple receipts into a single "slab" for efficient storage and transmission while maintaining verifiability.

---

## 2. Slab Definition

### 2.1 Slab Structure

```json
{
  "slab": {
    "version": "1.0.0",
    "slab_id": "slab001",
    "episode_id": "ep001",
    "first_receipt_id": "a1b2c3d4",
    "last_receipt_id": "i9j0k1l2",
    "receipt_count": 100,
    "initial_state_hash": "sha256:...",
    "final_state_hash": "sha256:...",
    "initial_budget": "1000000000000000000",
    "final_budget": "500000000000000000",
    "compressed_receipts": "base64:..."
  }
}
```

### 2.2 Slab Properties

| Property | Description |
|----------|-------------|
| **receipt_count** | Number of receipts in slab |
| **first_receipt_id** | First receipt in slab |
| **last_receipt_id** | Last receipt in slab |
| **compressed_receipts** | LZ4/FLATE compressed receipt list |

---

## 3. Compression Rules

### 3.1 Allowed Algorithms

| Algorithm | Use Case | Notes |
|-----------|----------|-------|
| **LZ4** | Fast compression | Default for runtime |
| **FLATE** | Max compression | For archival |
| **None** | Small slabs | For debugging |

### 3.2 Compression Format

```
compressed = algorithm(compressed_json_list)
```

Where `compressed_json_list` is:

```json
[
  {"receipt_id": "a1b2c3d4", "chain_hash": "..."},
  {"receipt_id": "e5f6g7h8", "chain_hash": "..."},
  ...
]
```

---

## 4. Verification with Slabs

### 4.1 Slab Verification

```python
def verify_slab(slab: Slab, expected_hash: str) -> bool:
    # Decompress
    receipts = decompress(slab.compressed_receipts)
    
    # Verify count
    if len(receipts) != slab.receipt_count:
        return False
    
    # Verify first/last
    if receipts[0].receipt_id != slab.first_receipt_id:
        return False
    if receipts[-1].receipt_id != slab.last_receipt_id:
        return False
    
    # Verify chain
    if not verify_chain(receipts):
        return False
    
    return True
```

### 4.2 Partial Verification

For large slabs, verify incrementally:

```python
def verify_slab_partial(slab: Slab, sample_size: int) -> bool:
    receipts = decompress(slab.compressed_receipts)
    
    # Verify random sample
    for i in random.sample(range(len(receipts)), sample_size):
        if not verify_receipt(receipts[i]):
            return False
    
    return True
```

---

## 5. Slab Boundaries

### 5.1 When to Create Slabs

| Trigger | Slab Size |
|---------|-----------|
| **Episode End** | All receipts in episode |
| **Size Limit** | 1MB default |
| **Time Limit** | Every 5 minutes |
| **Checkpoint** | Manual trigger |

### 5.2 Slab Metadata

Every slab includes:
- Episode identifier
- Time range
- Receipt count
- State hash range

---

## 6. References

- [Receipt Schema](../20_coh_kernel/receipt_schema.md)
- [Chain Hash Rule](../20_coh_kernel/chain_hash_rule.md)
- [Replay Verification](./replay_verification.md)
