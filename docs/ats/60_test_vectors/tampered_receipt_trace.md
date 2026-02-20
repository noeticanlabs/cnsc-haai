# Tampered Receipt Trace

**Test Vector: Detection of Receipt Tampering**

| Field | Value |
|-------|-------|
| **Module** | 60_test_vectors |
| **Vector** | Tampered Receipt |
| **Version** | 1.0.0 |

---

## 1. Test Description

This test verifies that the ATS detects tampered receipts by validating hash integrity.

---

## 2. Attack Scenario

### 2.1 Original Receipt

```json
{
  "receipt_id": "a1b2c3d4",
  "content": {
    "risk_before_q": "1000000000000000000",
    "risk_after_q": "800000000000000000",
    "budget_before_q": "1000000000000000000",
    "budget_after_q": "1000000000000000000"
  }
}
```

### 2.2 Tampered Receipt

Attacker modifies risk value:

```json
{
  "receipt_id": "a1b2c3d4",
  "content": {
    "risk_before_q": "1000000000000000000",
    "risk_after_q": "900000000000000000",  // CHANGED!
    "budget_before_q": "1000000000000000000",
    "budget_after_q": "1000000000000000000"
  }
}
```

---

## 3. Verification

### 3.1 Hash Validation

The verifier recomputes:

```
Original: sha256(canonical_bytes(receipt)) = a1b2c3d4...
Tampered: sha256(canonical_bytes(tampered)) = e5f6g7h8...

Mismatch detected!
```

### 3.2 Expected Result

```
REJECT(INVALID_RECEIPT_HASH)
Reason: Receipt hash doesn't match receipt_id
```

---

## 4. Verification Commands

```bash
python -m ats.verify --trajectory tampered_receipt.json

# Expected output:
# REJECT(INVALID_RECEIPT_HASH)
# Error: Receipt hash mismatch - receipt may have been tampered
```

---

## 5. Protection Mechanisms

### 5.1 Hash Integrity

| Mechanism | Protection |
|-----------|------------|
| SHA-256 | Cryptographic hash |
| First 8 chars | Receipt ID |
| Self-validation | Receipt proves its own integrity |

### 5.2 Chain Protection

Even if one receipt is tampered:
- Chain hash breaks
- Subsequent receipts invalidated

---

## 6. References

- [Receipt Identity](../20_coh_kernel/receipt_identity.md)
- [Chain Hash Rule](../20_coh_kernel/chain_hash_rule.md)
- [Rejection Reason Codes](../50_security_model/rejection_reason_codes.md)
