# Receipt Schema

**ATS Receipt Structure for Step Verification**

| Field | Value |
|-------|-------|
| **Module** | 20_coh_kernel |
| **Section** | Receipt Schema |
| **Version** | 1.0.0 |

---

## 1. Receipt Overview

A receipt is a cryptographic record that proves a step is admissible. Every state transition must produce a receipt that can be independently verified.

---

## 2. Schema Structure

### 2.1 Top-Level Fields

```json
{
  "version": "1.0.0",
  "receipt_id": "a1b2c3d4",
  "timestamp": "2024-01-15T10:30:00Z",
  "episode_id": "e5f6g7h8",
  "content": { ... },
  "provenance": { ... },
  "signature": { ... },
  "previous_receipt_id": "9i8j7k6l",
  "previous_receipt_hash": "sha256:...",
  "chain_hash": "sha256:...",
  "metadata": { }
}
```

### 2.2 Required Fields

| Field | Type | Description |
|-------|------|-------------|
| **version** | string | Schema version (must be "1.0.0") |
| **receipt_id** | string | 8-character hex identifier |
| **content** | object | Step content (required) |
| **signature** | object | Cryptographic signature (required) |

---

## 3. Content Fields (Consensus-Critical)

### 3.1 Risk and Budget Fields

These fields are **required for ATS verification**:

```json
{
  "content": {
    "step_type": "VM_EXECUTION",
    
    "risk_before_q": "1000000000000000000",
    "risk_after_q": "800000000000000000",
    "delta_plus_q": "0",
    
    "budget_before_q": "1000000000000000000",
    "budget_after_q": "1000000000000000000",
    "kappa_q": "1000000000000000000",
    
    "state_hash_before": "sha256:0123456789abcdef...",
    "state_hash_after": "sha256:fedcba9876543210...",
    
    "input_hash": "sha256:...",
    "output_hash": "sha256:...",
    "decision": "PASS"
  }
}
```

### 3.2 Field Descriptions

| Field | QFixed(18) | Description |
|-------|------------|-------------|
| **risk_before_q** | Required | V(x_k) before step |
| **risk_after_q** | Required | V(x_{k+1}) after step |
| **delta_plus_q** | Required | max(0, risk_after - risk_before) |
| **budget_before_q** | Required | B_k before step |
| **budget_after_q** | Required | B_{k+1} after step |
| **kappa_q** | Required | κ constant for this ATS |

### 3.3 State Hash Fields

| Field | Format | Description |
|-------|--------|-------------|
| **state_hash_before** | sha256:hex | sha256(canonical_bytes(x_k)) |
| **state_hash_after** | sha256:hex | sha256(canonical_bytes(x_{k+1})) |

---

## 4. Provenance Fields

```json
{
  "provenance": {
    "source": "nsc-vm",
    "phase": "execution",
    "span": {
      "start": 100,
      "end": 200
    },
    "action_type": "BELIEF_UPDATE"
  }
}
```

---

## 5. Signature Fields

```json
{
  "signature": {
    "algorithm": "HMAC-SHA256",
    "signer": "system-key-001",
    "signature": "base64:..."
  }
}
```

---

## 6. Chain Fields

```json
{
  "previous_receipt_id": "9i8j7k6l",
  "previous_receipt_hash": "sha256:...",
  "chain_hash": "sha256:..."
}
```

---

## 7. ATS Extension Fields

For ATS-specific verification, receipts include these additional fields:

### 7.1 Extended Schema

```json
{
  "content": {
    "ats_extension": {
      "action_algebra_type": "BELIEF_UPDATE",
      "state_components": ["belief", "memory", "plan", "policy", "io"],
      "determinism_proof": "sha256:...",
      "vm_checkpoint_id": "checkpoint-001"
    }
  }
}
```

### 7.2 Field Requirements

| Field | Required | Description |
|-------|----------|-------------|
| **action_algebra_type** | Yes | Type of action from algebra |
| **state_components** | Yes | Which components changed |
| **determinism_proof** | No | Proof of deterministic execution |
| **vm_checkpoint_id** | No | VM checkpoint reference |

---

## 8. Validation Rules

### 8.1 Receipt Validation

A receipt is valid if:

1. All required fields present
2. All QFixed fields contain valid decimal strings
3. State hashes match recomputed values
4. Chain hash is consistent
5. Signature verifies (if present)

### 8.2 Rejection Codes

| Code | Description |
|------|-------------|
| `MISSING_REQUIRED_FIELD` | Required field absent |
| `INVALID_QFIXED` | QFixed format invalid |
| `STATE_HASH_MISMATCH` | Hash recompute fails |
| `CHAIN_BROKEN` | Receipt chain invalid |

---

## 9. Schema Versioning

### 9.1 Version String

Format: `major.minor.patch`

| Version | Status |
|---------|--------|
| 1.0.0 | Current |
| 0.x.x | Deprecated |

---

## 10. References

- [ATS Definition](../00_identity/ats_definition.md)
- [Canonical Serialization](./canonical_serialization.md)
- [Receipt Identity](./receipt_identity.md)
- [Chain Hash Rule](./chain_hash_rule.md)
- [RV Step Specification](./rv_step_spec.md)
