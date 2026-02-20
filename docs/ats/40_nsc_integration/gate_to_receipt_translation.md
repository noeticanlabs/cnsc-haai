# Gate to Receipt Translation

**Converting NSC Gates to ATS Receipts**

| Field | Value |
|-------|-------|
| **Module** | 40_nsc_integration |
| **Section** | Gate to Receipt Translation |
| **Version** | 1.0.0 |

---

## 1. Overview

NSC gates are the control flow primitives of the NSC VM. This document defines how gate evaluations translate to ATS receipts.

---

## 2. Gate Types

### 2.1 NSC Gate Types

| Gate | Description | ATS Implication |
|------|-------------|-----------------|
| **TypeGate** | Type checking | Validates type safety |
| **AffordanceGate** | Resource availability | Checks affordability |
| **CoherenceGate** | Coherence checking | Validates coherence |
| **PhaseGate** | Phase transitions | Marks episode boundaries |

### 2.2 Gate Execution

```
Gate Evaluation: (state, gate) → (decision, new_state, receipt)
```

---

## 3. Translation Mapping

### 3.1 Gate Decision to Receipt Decision

| NSC Decision | Receipt Decision | ATS Code |
|--------------|------------------|----------|
| PASS | PASS | ACCEPT |
| FAIL | FAIL | REJECT |
| WARN | WARN | ACCEPT (with warning) |
| SKIP | SKIP | ACCEPT (step skipped) |

### 3.2 Gate to Receipt Content

```python
def gate_to_receipt(gate_result: GateResult) -> Receipt:
    return Receipt(
        content={
            "step_type": "GATE_EVAL",
            "gate_type": gate_result.gate_type,
            "decision": gate_result.decision,
            "details": {
                "gate_name": gate_result.gate_name,
                "condition": gate_result.condition,
                "evaluation": gate_result.evaluation
            }
        },
        provenance={
            "source": "nsc-vm",
            "phase": "gate_evaluation"
        }
    )
```

---

## 4. Gate-Specific Translation

### 4.1 TypeGate

```json
{
  "content": {
    "step_type": "GATE_EVAL",
    "gate_type": "TYPE_GATE",
    "details": {
      "expected_type": "belief_vector",
      "actual_type": "belief_vector",
      "compatible": true
    },
    "decision": "PASS"
  }
}
```

### 4.2 AffordanceGate

```json
{
  "content": {
    "step_type": "GATE_EVAL",
    "gate_type": "AFFORDANCE_GATE",
    "details": {
      "resource": "memory",
      "required": 100,
      "available": 150,
      "affordable": true
    },
    "decision": "PASS"
  }
}
```

### 4.3 CoherenceGate

```json
{
  "content": {
    "step_type": "GATE_EVAL",
    "gate_type": "COHERENCE_GATE",
    "details": {
      "coherence_before": "920000000000000000",
      "coherence_after": "940000000000000000",
      "delta": "20000000000000000",
      "within_threshold": true
    },
    "decision": "PASS"
  }
}
```

---

## 5. Gate Failures

### 5.1 Failure Translation

| Gate Failure | Receipt Decision | Error Code |
|--------------|------------------|------------|
| Type mismatch | FAIL | `TYPE_VIOLATION` |
| Insufficient resources | FAIL | `AFFORDABILITY_VIOLATION` |
| Coherence too low | FAIL | `COHERENCE_VIOLATION` |
| Phase violation | FAIL | `PHASE_VIOLATION` |

### 5.2 Failure Receipt

```json
{
  "content": {
    "step_type": "GATE_EVAL",
    "gate_type": "AFFORDANCE_GATE",
    "decision": "FAIL",
    "details": {
      "resource": "budget",
      "required": "500000000000000000",
      "available": "300000000000000000",
      "error": "INSUFFICIENT_BUDGET"
    }
  },
  "signature": {
    "algorithm": "HMAC-SHA256",
    "signer": "gate-evaluator"
  }
}
```

---

## 6. References

- [NSC VM to ATS Bridge](./nsc_vm_to_ats_bridge.md)
- [NSC Specification - Gates and Rails](../spec/nsc/06_Gates_Rails_Receipts.md)
- [Receipt Schema](../20_coh_kernel/receipt_schema.md)
- [Rejection Reason Codes](../50_security_model/rejection_reason_codes.md)
