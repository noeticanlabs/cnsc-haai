# Receipt Spec and Hash Chains

**Spec Version:** 1.0.0  
**Canonical Schema:** `schemas/receipt.schema.json`

## Overview

This document defines the receipt specification and hash chain mechanism for the GML (Governance Markup Language) layer. Receipts provide cryptographic evidence of reasoning steps, enabling auditability and replay verification.

## Receipt Schema (v1.0.0)

The canonical receipt schema is defined in [`schemas/receipt.schema.json`](../../schemas/receipt.schema.json). All implementations must conform to this schema.

### Core Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `version` | string | Yes | Schema version, must be "1.0.0" |
| `receipt_id` | string | Yes | 8-character hex identifier |
| `timestamp` | string | Yes | ISO 8601 UTC timestamp |
| `content` | object | Yes | Step content (see below) |
| `signature` | object | Yes | Cryptographic signature |
| `provenance` | object | Yes | Source and lineage information |

### Content Fields

| Field | Type | Description |
|-------|------|-------------|
| `step_type` | enum | PARSE, TYPE_CHECK, GATE_EVAL, PHASE_TRANSITION, VM_EXECUTION, COHERENCE_CHECK, TRACE_EVENT, CHECKPOINT, REPLAY, CUSTOM |
| `input_hash` | string | SHA-256 hash of input state |
| `output_hash` | string | SHA-256 hash of output state |
| `decision` | enum | PASS, FAIL, WARN, SKIP, PENDING |
| `details` | object | Step-specific metadata |
| `coherence_before` | number | Coherence score pre-step (0.0-1.0) |
| `coherence_after` | number | Coherence score post-step (0.0-1.0) |

### Chain Fields

| Field | Type | Description |
|-------|------|-------------|
| `previous_receipt_id` | string | ID of previous receipt in chain |
| `previous_receipt_hash` | string | Hash of previous receipt |
| `chain_hash` | string | Computed chain hash for this receipt |

## Hash Chain Mechanism

### Chain Structure

Receipts form a linked hash chain where each receipt references the previous one:

```
Genesis → R1 → R2 → R3 → ... → Rn
```

### Hash Computation

```python
def compute_receipt_hash(receipt):
    """Compute hash of receipt content."""
    data = json.dumps({
        "receipt_id": receipt.receipt_id,
        "content": receipt.content.to_dict(),
        "previous_receipt_hash": receipt.previous_receipt_hash,
    }, sort_keys=True)
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def compute_chain_hash(receipt, previous_chain_hash=None):
    """Compute chain hash linking to previous chain tip."""
    receipt_hash = compute_receipt_hash(receipt)
    if previous_chain_hash:
        data = json.dumps({
            "previous": previous_chain_hash,
            "current": receipt_hash,
        }, sort_keys=True)
    else:
        data = receipt_hash
    return hashlib.sha256(data.encode('utf-8')).hexdigest()
```

### Genesis Receipt

The first receipt in a chain has:
- `previous_receipt_hash`: `None`
- `previous_receipt_id`: `None`
- `chain_hash`: Computed without previous chain hash

## Signature Mechanism

### HMAC-SHA256 (Default)

```python
def sign_receipt(receipt, key):
    """Sign receipt content."""
    content_hash = receipt.content.compute_hash()
    signature = hmac.new(
        key.encode('utf-8'),
        content_hash.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature

def verify_signature(receipt, key):
    """Verify receipt signature."""
    content_hash = receipt.content.compute_hash()
    expected = hmac.new(
        key.encode('utf-8'),
        content_hash.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(receipt.signature.signature, expected)
```

### Alternative Algorithms

Supported algorithms:
- `HMAC-SHA256` (default, system use)
- `Ed25519` (recommended for external attestation)
- `ECDSA` (legacy compatibility)
- `RSA` (legacy compatibility)

## Replay Verification

### Determinism Guarantee

For deterministic replay, the following must match between original and replay receipts:
1. `content.step_type`
2. `content.decision`
3. `content.output_hash`

### Verification Process

```python
def verify_replay(original, replay):
    """Verify replay receipt matches original."""
    # Check step type
    if original.content.step_type != replay.content.step_type:
        return False, f"Step type mismatch"
    
    # Check decision
    if original.content.decision != replay.content.decision:
        return False, f"Decision mismatch"
    
    # Check output hash
    if original.content.output_hash != replay.content.output_hash:
        return False, "Output hash mismatch"
    
    return True, "Replay matches original"
```

## Error Codes

| Code | Meaning | Handling |
|------|---------|----------|
| `INVALID_SIGNATURE` | Signature verification failed | Reject receipt |
| `CHAIN_BREAK` | Previous receipt hash mismatch | Reject chain |
| `GENESIS_MISMATCH` | Chain root doesn't match expected | Reject chain |
| `REPLAY_MISMATCH` | Replay doesn't match original | Flag for review |

## Wire Format Example

```json
{
  "version": "1.0.0",
  "receipt_id": "a1b2c3d4",
  "timestamp": "2024-01-15T10:30:00Z",
  "episode_id": "e5f6g7h8",
  "content": {
    "step_type": "GATE_EVAL",
    "input_hash": "sha256:abc123...",
    "output_hash": "sha256:def456...",
    "decision": "PASS",
    "details": {"gate_type": "evidence_sufficiency"},
    "coherence_before": 0.92,
    "coherence_after": 0.94
  },
  "provenance": {
    "source": "nsc-vm",
    "phase": "execution"
  },
  "signature": {
    "algorithm": "HMAC-SHA256",
    "signer": "system-key-001",
    "signature": "base64signature..."
  },
  "previous_receipt_id": "9i8j7k6l",
  "previous_receipt_hash": "sha256:previous...",
  "chain_hash": "sha256:current..."
}
```

## Version Compatibility

| Schema Version | Code Version | Status |
|----------------|--------------|--------|
| 1.0.0 | 1.0.0+ | Current |
| 0.x.x | <1.0.0 | Deprecated |

## References

- Canonical Schema: [`schemas/receipt.schema.json`](../../schemas/receipt.schema.json)
- Implementation: [`src/cnsc/haai/gml/receipts.py`](../../src/cnsc/haai/gml/receipts.py)
- Theory: [`cnhaai/docs/spine/21-receipt-system.md`](../../cnhaai/docs/spine/21-receipt-system.md)
- Examples: [`cnhaai/docs/appendices/appendix-c-receipt-schema.md`](../../cnhaai/docs/appendices/appendix-c-receipt-schema.md)
