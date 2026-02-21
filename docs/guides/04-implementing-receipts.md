# Guide 04: Implementing Receipts

**Version**: 1.0.0
**Status**: DRAFT

---

## Overview

Receipts provide cryptographic records of reasoning steps. This guide explains how to implement receipt generation and verification.

---

## Receipt System Architecture

```
Receipt
├── ReceiptContent (step details)
├── ReceiptSignature (HMAC-SHA256)
└── ReceiptMetadata (timestamps, IDs)
```

---

## Creating Receipts

### Step 1: Define Receipt Content

```python
from cnhaai.core.receipts import ReceiptContent, ReceiptStepType, ReceiptDecision

content = ReceiptContent(
    step_type=ReceiptStepType.GATE_VALIDATION,
    input_state="state_hash_123",
    output_state="state_hash_456",
    decision=ReceiptDecision.PASS,
    details={
        "gate_name": "evidence_sufficiency",
        "threshold": 0.8,
        "actual": 0.9
    }
)
```

### Step 2: Create Receipt

```python
from cnhaai.core.receipts import Receipt, ReceiptSystem

receipt = Receipt(
    episode_id="episode_001",
    step_index=1,
    content=content,
    signer="system"
)
```

### Step 3: Sign Receipt

```python
receipt.sign(secret_key="your-secret-key")
print(receipt.signature)  # HMAC-SHA256 signature
```

---

## Receipt Verification

```python
from cnhaai.core.receipts import ReceiptSystem

system = ReceiptSystem()
is_valid = system.verify(receipt, secret_key="your-secret-key")
print(f"Receipt valid: {is_valid}")
```

---

## Receipt Types

| Type | Description |
|------|-------------|
| `GATE_VALIDATION` | Gate evaluation result |
| `PHASE_TRANSITION` | Phase change record |
| `RECOVERY_ACTION` | Recovery step record |
| `ABSTRACTION_CREATION` | New abstraction |
| `EPISODE_START` | Episode start marker |
| `EPISODE_END` | Episode end marker |

---

## Best Practices

1. **Immutability**: Once created, receipts cannot be modified
2. **Signatures**: Always sign receipts for integrity
3. **Chain**: Link receipts in a chain for traceability
4. **Storage**: Store receipts durably for audit

---

## Related Documents

- [Receipt System Theory](../spine/21-receipt-system.md)
- [Receipt Implementation](../spine/22-receipt-implementation.md)
- [Receipt Schema](../../schemas/receipt.schema.json)
