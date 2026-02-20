# Coh Merkle v1

**Merkle Tree Specification for ATS Receipts**

| Field | Value |
|-------|-------|
| **Module** | 20_coh_kernel |
| **Section** | Coh Merkle |
| **Version** | 1.0.0 |
| **Status** | ACTIVE |

---

## 1. Overview

This spec defines the Merkle tree construction for ATS receipts, enabling efficient verification and inclusion proofs.

---

## 2. Merkle Tree Specification

### 2.1 Hash Function

- **Algorithm**: SHA256
- **Output**: 32 bytes (raw)

### 2.2 Node Types

| Type | Prefix | Description |
|------|--------|-------------|
| Leaf | `0x01` | Data node |
| Internal | `0x01` | Hash of children |

### 2.3 Leaf Hash

```
leaf_hash = SHA256(0x01 || leaf_bytes)
```

Where `leaf_bytes` is the JCS canonical bytes of the leaf data.

### 2.4 Internal Hash

```
internal_hash(L, R) = SHA256(0x01 || L || R)
```

### 2.5 Odd Node Handling

When an odd number of children exists at any level:
- Duplicate the last node to make it even

---

## 3. Tree Construction

### 3.1 Algorithm

```
function build_merkle(leaves):
    if len(leaves) == 0:
        return empty_hash
    
    if len(leaves) == 1:
        return leaf_hash(leaves[0])
    
    # Build level
    next_level = []
    for i in range(0, len(leaves), 2):
        left = leaves[i]
        right = leaves[i+1] if i+1 < len(leaves) else left
        next_level.append(internal_hash(left, right))
    
    return build_merkle(next_level)
```

### 3.2 Root Calculation

The root is the final hash after all levels are computed.

---

## 4. Inclusion Proof

### 4.1 Proof Structure

```json
{
  "leaf_index": 5,
  "root_hash": "sha256:...",
  "proof": [
    {"side": "left", "hash": "sha256:..."},
    {"side": "right", "hash": "sha256:..."}
  ]
}
```

### 4.2 Verification

```
function verify_inclusion(leaf, proof, root):
    current = leaf_hash(leaf)
    
    for step in proof:
        if step.side == "left":
            current = internal_hash(step.hash, current)
        else:
            current = internal_hash(current, step.hash)
    
    return current == root
```

---

## 5. Micro Leaf Codec

### 5.1 Codec ID

```
coh.micro.codec.ats_receipt_core.v1
```

### 5.2 Encoding

Leaf bytes = JCS UTF-8 of the stripped micro receipt core:

```python
def encode_micro_leaf(receipt_core) -> bytes:
    """Strip receipt to core, serialize with JCS UTF-8."""
    core = strip_to_core(receipt_core)
    return jcs_canonical_bytes(core)
```

---

## 6. Test Vectors

See `compliance_tests/ats_slab/expected_merkle_root.txt` for deterministic vectors.

---

## 7. Related Documents

- [Chain Hash Universal](chain_hash_universal.md)
- [Slab Compression Rules](slab_compression_rules.md)
- [RFC8785](https://www.rfc-editor.org/rfc/rfc8785)
