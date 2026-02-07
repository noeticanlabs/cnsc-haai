# Seam Principles

**Spec Version:** 1.0.0  
**Status:** Canonical

## Overview

Seams are the boundaries between architectural layers in the CNHAAI system. Each seam defines a contract that ensures:
1. **Semantic preservation** across layer transitions
2. **Deterministic behavior** for replayability
3. **Auditability** through receipt emission

## Seam Definitions

| Seam | From | To | Purpose |
|------|------|-----|---------|
| GLLL→GHLL | GLLL (Integrity) | GHLL (Meaning) | Glyph decoding to semantic atoms |
| GHLL→NSC | GHLL (Meaning) | NSC (Execution) | High-level to intermediate representation |
| NSC→GML | NSC (Execution) | GML (Forensics) | Execution traces to receipts |

## Core Principles

### 1. Semantic Preservation

Every transformation across a seam must preserve meaning. This is enforced through:
- **Binding validation** at GLLL→GHLL
- **Type preservation** at GHLL→NSC
- **Trace completeness** at NSC→GML

### 2. Determinism

All seam operations must be deterministic:
- Same input → same output
- Same input → same receipts
- Replay must match original execution

### 3. Auditability

Every seam crossing produces a receipt:
- Input hash captured
- Output hash computed
- Transformation verified

## Invariants

All seams must maintain these invariants:

```
∀ s ∈ seams:
  1. input_hash = H(input)
  2. output_hash = H(output)
  3. receipt_chain = [...prev_receipt, current_receipt]
  4. H(receipt) ∈ receipt_chain
```

## Error Handling

| Error Category | Handling Strategy |
|----------------|-------------------|
| **Invalid input** | Reject with error receipt |
| **Transformation failure** | Abort with error receipt |
| **Non-determinism detected** | Flag for review |

## Version Compatibility

| Seam | Min Version | Max Version | Notes |
|------|-------------|-------------|-------|
| GLLL→GHLL | 1.0.0 | 1.0.0 | Stable |
| GHLL→NSC | 1.0.0 | 1.0.0 | Stable |
| NSC→GML | 1.0.0 | 1.0.0 | Stable |

## See Also

- Implementation: [`src/cnsc/haai/glll/mapping.py`](../../src/cnsc/haai/glll/mapping.py)
- Seam contracts: [`spec/seam/`](../../spec/seam/)
- Receipt schema: [`schemas/receipt.schema.json`](../../schemas/receipt.schema.json)
