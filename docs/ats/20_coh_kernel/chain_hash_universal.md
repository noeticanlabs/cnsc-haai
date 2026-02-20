# Chain Hash Universal (v1)

**Universal Chain Hashing with JCS + Domain Separation**

| Field | Value |
|-------|-------|
| **Module** | 20_coh_kernel |
| **Section** | Chain Hash Universal |
| **Version** | 1.0.0 |
| **Status** | ACTIVE |

---

## 1. Overview

This spec defines the universal chain hash rule using JCS (RFC8785) for canonical serialization and domain separation for universal compatibility.

---

## 2. Chain Hash v1 Specification

### 2.1 Domain Separator

```
COH_CHAIN_V1\n
```

This 12-byte domain separator ensures chain hashes are unique to this version.

### 2.2 Chain Hash Algorithm

```
chain_hash(prev_chain_hash_raw32, receipt_core) -> bytes32:
    1. Serialize receipt_core using JCS (RFC8785)
    2. Prepend domain separator: domain || serialized
    3. Double-hash: SHA256(SHA256(domain || serialized))
    4. Return raw 32 bytes
```

### 2.3 Genesis Receipt

For the first receipt (no previous):
```
prev_chain_hash = 32 zero bytes
```

### 2.4 Receipt Core Structure

The receipt core must contain:
```json
{
  "receipt_id": "sha256:...",
  "step_index": 1,
  "timestamp": "2026-02-20T12:00:00Z",
  "content": { ... }
}
```

---

## 3. Digest Format

### 3.1 Prefix Convention

All SHA256 digests in JSON use the `sha256:` prefix:
```json
{
  "receipt_id": "sha256:a1b2c3d4e5f6...",
  "chain_hash": "sha256:..."
}
```

### 3.2 Internal Processing

When computing hashes internally:
1. Decode `sha256:` prefix to raw 32 bytes
2. Use raw bytes for computation
3. Re-encode with prefix for storage

---

## 4. Implementation

```python
import hashlib

DOMAIN_SEPARATOR = b"COH_CHAIN_V1\n"

def jcs_canonical_bytes(obj) -> bytes:
    """RFC8785 canonical serialization."""
    # ... implementation
    pass

def chain_hash(prev_chain_hash: bytes, receipt_core: dict) -> bytes:
    """Compute chain hash v1."""
    # 1. JCS serialize
    serialized = jcs_canonical_bytes(receipt_core)
    
    # 2. Prepend domain
    to_hash = DOMAIN_SEPARATOR + serialized
    
    # 3. Double hash
    return hashlib.sha256(hashlib.sha256(to_hash).digest()).digest()
```

---

## 5. Migration from v0

### 5.1 Old Format (DEPRECATED)
```
chain_hash = sha256(prev_id || curr_id)
```

### 5.2 New Format (v1)
```
chain_hash = sha256(sha256(COH_CHAIN_V1 || JCS(receipt_core)))
```

### 5.3 Migration Notes

- v0 receipts remain valid but should be migrated
- New receipts MUST use v1
- Verify migration with test vectors

---

## 6. Test Vectors

See `compliance_tests/ats_slab/expected_chain_hashes.jsonl` for deterministic vectors.

---

## 7. Related Documents

- [RFC8785](https://www.rfc-editor.org/rfc/rfc8785) - JSON Canonicalization Scheme
- [Receipt Schema](receipt_schema.md)
- [Coh Merkle v1](coh.merkle.v1.md)
