# Chain Hash Universal (v1.0.1)

**Universal Hashing with JCS + Domain Separation**

**REVISED**: 2026-02-23

| Field | Value |
|-------|-------|
| **Module** | 20_coh_kernel |
| **Section** | Chain Hash Universal |
| **Version** | 1.0.1 |
| **Status** | ACTIVE |

---

## 1. Overview

This spec defines the canonical hashing rules using JCS (RFC8785) for canonical serialization and domain separation. 

**CRITICAL**: This spec distinguishes between two different hash concepts:
- `receipt_id` - content-addressed identifier (no history)
- `chain_digest` - sequential history digest (includes previous)

---

## 2. Terminology Split

### 2.1 receipt_id (Content Hash)

A **content-addressed identifier** that uniquely identifies this receipt's content. Does NOT depend on previous state.

```
receipt_id(receipt_core) -> str:
    1. Serialize receipt_core using JCS (RFC8785)
    2. Prepend domain: COH_RECEIPT_ID_V1\n || serialized
    3. Hash: SHA256(domain || serialized)
    4. Return prefixed: "sha256:" || hex
```

### 2.2 chain_digest (History Hash)

A **sequential history digest** that depends on the previous chain state. Provides tamper-evident ordering.

```
chain_digest(prev_digest, receipt_id) -> str:
    1. Decode prev_digest (32 bytes) and receipt_id (32 bytes)
    2. Prepend domain: COH_CHAIN_DIGEST_V1\n || prev_digest || receipt_id
    3. Hash: SHA256(domain || prev || receipt_id)
    4. Return prefixed: "sha256:" || hex
```

---

## 3. Chain Hash v1 Specification (REVISED)

### 3.1 Domain Separators

| Purpose | Domain | Bytes |
|---------|--------|-------|
| receipt_id | `COH_RECEIPT_ID_V1\n` | 19 bytes |
| chain_digest | `COH_CHAIN_DIGEST_V1\n` | 20 bytes |
| Merkle leaf | `0x00` | 1 byte |
| Merkle internal | `0x01` | 1 byte |

### 3.2 receipt_id Algorithm

```
receipt_id = "sha256:" || SHA256(COH_RECEIPT_ID_V1 || JCS(receipt_core)).hex()
```

### 3.3 chain_digest Algorithm

```
chain_digest_next = "sha256:" || SHA256(COH_CHAIN_DIGEST_V1 || prev_digest || receipt_id).hex()
```

### 3.4 Genesis Receipt

For the first receipt (no previous):
```
prev_digest = "sha256:0000000000000000000000000000000000000000000000000000000000000000"
```

### 3.5 Receipt Core Structure

The receipt core must contain:
```json
{
  "receipt_id": "sha256:...",
  "chain_digest_prev": "sha256:...",
  "chain_digest_next": "sha256:...",
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

## 5. Migration from v1.0

### 5.1 v1.0 Format (DEPRECATED)
```
# Old - NOT a real chain (no prev dependency)
chain_hash = SHA256(COH_CHAIN_V1 || JCS(receipt_core))
receipt_id = chain_hash  # This was confused!
```

### 5.2 v1.0.1 Format (CURRENT)
```
# New - CLEAR DISTINCTION
receipt_id = SHA256(COH_RECEIPT_ID_V1 || JCS(receipt_core))
chain_digest_next = SHA256(COH_CHAIN_DIGEST_V1 || prev_digest || receipt_id)
```

### 5.3 Migration Notes

- v1.0 receipts remain valid but are DEPRECATED
- New receipts MUST use v1.0.1 format
- `receipt_id` is for content-addressing (indexing, dedup)
- `chain_digest` is for tamper-evident history
- Verify migration with test vectors

---

## 6. Test Vectors

See `compliance_tests/ats_slab/expected_chain_hashes.jsonl` for deterministic vectors.

---

## 7. Related Documents

- [RFC8785](https://www.rfc-editor.org/rfc/rfc8785) - JSON Canonicalization Scheme
- [Receipt Schema](receipt_schema.md)
- [Coh Merkle v1](coh.merkle.v1.md)
