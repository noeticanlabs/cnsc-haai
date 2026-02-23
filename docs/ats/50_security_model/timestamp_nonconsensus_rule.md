# Timestamp Non-Consensus Rule

**Why Timestamps Are Excluded from Verification**

| Field | Value |
|-------|-------|
| **Module** | 50_security_model |
| **Section** | Timestamp Non-Consensus Rule |
| **Version** | 1.0.0 |

---

## 1. Rule Statement

> **Timestamps are not part of consensus. They may be present in receipts but are never verified.**

---

## 2. Rationale

### 2.1 Why Timestamps Are Problematic

| Issue | Description |
|-------|-------------|
| **Clock synchronization** | Different systems have different clocks |
| **NTP adjustments** | Clock can jump forward or backward |
| **No global time** | Distributed systems have no shared time |
| **Non-determinism** | Same execution could have different timestamps |

### 2.2 WhatATS Uses Instead

ATS uses **step indices** instead of timestamps:

```
Step 0 → Step 1 → Step 2 → ... → Step T
```

This provides deterministic ordering.

---

## 3. Timestamp Policy

### 3.1 What Timestamps Are

| Aspect | Policy |
|--------|--------|
| **In receipts** | Allowed (for display only) |
| **In verification** | Ignored |
| **In chain** | Not included |
| **In hash** | Not included |

### 3.2 Receipt Timestamps

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "metadata": {
    "created_for": "logging",
    "ignored_by": "verifier"
  }
}
```

The timestamp field exists for:
- Human debugging
- Log correlation
- External monitoring

It is **never** verified.

---

## 4. Ordering Without Timestamps

### 4.1 Step Index Ordering

Trajectory ordering is determined by:

```
Receipt[k].previous_receipt_id = Receipt[k-1].receipt_id
```

This creates a deterministic chain.

### 4.2 Chain as Order

```
ρ₀ → ρ₁ → ρ₂ → ... → ρ_T
```

The chain itself provides ordering:
- No timestamps needed
- No clock synchronization
- Deterministic

---

## 5. References

- [RV Step Specification](../20_coh_kernel/rv_step_spec.md)
- [Chain Hash Universal](../20_coh_kernel/chain_hash_universal.md)
- [Deterministic Replay Requirements](./deterministic_replay_requirements.md)
