# Coh Module Interface Contract

**Canonical Contract Between Coh Algebra and Verification Engines**

| Field | Value |
|-------|-------|
| **Document** | coh.module_contract |
| **Version** | 1.0.0 |
| **Status** | ACTIVE |
| **Layer** | L1 (Constitutional) |

---

## 1. Overview

This document defines the **canonical contract** between the Coh algebra (mathematical foundation) and any verification engine (ATS, discrete engine, PDE engine, etc.). It specifies:

- Receipt schema (canonical form)
- Verification API
- Reject codes
- Required test vectors

This is the **consensus constitution** — all engines must obey this contract.

---

## 2. Receipt Canonical Form

### 2.1 Core Identity Fields

Every Coh receipt MUST contain these fields:

```json
{
  "receipt_id": "sha256:...",
  "chain_digest": "sha256:...",
  "content": { ... },
  "metadata": { }
}
```

### 2.2 Field Definitions

| Field | Type | Description | Consensus Role |
|-------|------|-------------|----------------|
| `receipt_id` | string | **Content hash** - SHA-256 of canonicalized receipt content | Identifies the step content uniquely |
| `chain_digest` | string | **History hash** - SHA-256 of (prev_chain_digest, receipt_id) | Provides chain linkage |
| `content` | object | Step-specific data | Engine-dependent |
| `metadata` | object | Auxiliary data | Optional |

### 2.3 Critical Distinction

```
receipt_id ≠ chain_digest

receipt_id = hash(receipt_core)
           = hash(content + metadata)
           
chain_digest = hash(prev_chain_digest + receipt_id)
             = hash(history)
```

**Why this matters:**
- `receipt_id` is stable across chain reorganizations
- `chain_digest` changes if history changes
- Verification engines MUST treat these as separate concerns

---

## 3. Canonical Profile

### 3.1 Serialization

All receipts MUST be serialized using **JCS** (RFC 8785) for deterministic canonical form.

```python
# Canonical serialization pseudo-code
canonical_bytes = JCS.encode(receipt_core)
receipt_id = SHA256(domain_separator + canonical_bytes)
```

### 3.2 Domain Separators

| Context | Separator |
|---------|------------|
| Receipt ID | `COH_RECEIPT_ID_V1\n` |
| Chain Digest | `COH_CHAIN_DIGEST_V1\n` |
| Genesis | `COH_GENESIS_V1\n` |

### 3.3 Numeric Domain

All numeric values MUST use **QFixed** (fixed-point integer) representation.

- **NO floats** in consensus-critical fields
- Use 18-decimal precision: `1000000000000000000` = 1.0
- See: [`deterministic_numeric_domain.md`](docs/ats/20_coh_kernel/deterministic_numeric_domain.md)

---

## 4. Verification API

### 4.1 Core Functions

Every Coh verification engine MUST implement:

```python
def verify_receipt(receipt: Receipt) -> VerificationResult:
    """
    Returns: (is_valid, error_code, details)
    """
    
def compute_receipt_id(receipt_core: dict) -> str:
    """
    Computes content hash (receipt_id).
    """
    
def compute_chain_digest(prev_chain: str, receipt_id: str) -> str:
    """
    Computes history hash (chain_digest).
    """
    
def verify_chain_link(prev_receipt: Receipt, curr_receipt: Receipt) -> bool:
    """
    Verifies chain_digest consistency.
    """
```

### 4.2 Verification Pipeline

```
1. Parse receipt
   ↓
2. Verify receipt_id matches content
   ↓
3. Verify chain_digest links to previous
   ↓
4. Verify content semantics (engine-specific)
   ↓
5. Return (valid, error_code, details)
```

---

## 5. Reject Codes

### 5.1 Canonical Reject Codes

| Code | Name | Description |
|------|------|-------------|
| `R001` | INVALID_RECEIPT_ID | Content hash mismatch |
| `R002` | INVALID_CHAIN_LINK | History hash mismatch |
| `R003` | INVALID_SERIALIZATION | JCS canonical form violation |
| `R004` | INVALID_NUMERIC | Float or invalid number in consensus field |
| `R005` | INVALID_SIGNATURE | Cryptographic signature failure |
| `R006` | INVALID_CONTENT | Engine-specific content violation |
| `R007` | CHAIN_REORGANIZATION | Prev chain hash does not match |
| `R008` | GENESIS_REQUIRED | First receipt must have empty prev_chain |

### 5.2 Engine-Specific Codes

Engines MAY extend with additional codes in the `R1xx` range:

```
R100+ : ATS-specific
R200+ : Discrete engine-specific
R300+ : PDE engine-specific
```

---

## 6. Test Vectors

### 6.1 Genesis Receipt

```json
{
  "receipt_id": "sha256:5e884898da28047...",
  "chain_digest": "sha256:5e884898da28047...",
  "content": {
    "step_type": "GENESIS",
    "initial_state": "sha256:..."
  },
  "metadata": {
    "created_at": "2026-01-01T00:00:00Z"
  }
}
```

**Expected:**
- `receipt_id` = `hash(GENESIS_V1 + JCS(content))`
- `chain_digest` = `receipt_id` (genesis self-links)

### 6.2 Standard Receipt

```json
{
  "receipt_id": "sha256:a1b2c3d4e5f6...",
  "chain_digest": "sha256:deadbeef1234...",
  "content": {
    "step_type": "VM_EXECUTION",
    "risk_delta_q": "100000000000000000",
    "budget_delta_q": "-50000000000000000",
    "state_hash_before": "sha256:...",
    "state_hash_after": "sha256:..."
  },
  "metadata": {}
}
```

### 6.3 Chain Link Verification

```
Given:
  prev.chain_digest = "sha256:aaaa..."
  curr.content = { ... }
  curr.receipt_id = "sha256:bbbb..."
  
Expected:
  curr.chain_digest = SHA256(COH_CHAIN_DIGEST_V1\n + "sha256:aaaa..." + "sha256:bbbb...")
```

---

## 7. Extensibility

### 7.1 Versioning

- **Major version** (v1, v2): Breaking changes to this contract
- **Minor version** (v1.1, v1.2): Additive changes

### 7.2 Engine Registration

To add a new engine:

1. Register engine ID in metadata
2. Define engine-specific content schema
3. Define engine-specific reject codes (R1xx+)
4. Provide test vectors for each code path

---

## 8. References

- [Chain Hash Universal](../ats/20_coh_kernel/chain_hash_universal.md)
- [Chain Hash Rule (DEPRECATED)](../ats/20_coh_kernel/chain_hash_rule.md)
- [Deterministic Numeric Domain](../ats/20_coh_kernel/deterministic_numeric_domain.md)
- [Canonical Serialization](../ats/20_coh_kernel/canonical_serialization.md)
- [Receipt Schema](../ats/20_coh_kernel/receipt_schema.md)
- [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785) - JCS

---

## 9. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-02-23 | Initial canonical form |
