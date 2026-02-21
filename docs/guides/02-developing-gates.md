# Guide 02: Developing Gates

**Version**: 1.0.0
**Status**: DRAFT

---

## Overview

Gates are runtime constraints that validate transitions between states. This guide explains how to implement custom gates in CNHAAI.

---

## Gate Types

| Type | Purpose |
|------|---------|
| `EVIDENCE_SUFFICIENCY` | Validates evidence quality |
| `COHERENCE_CHECK` | Validates coherence |
| `RECONSTRUCTION_BOUND` | Validates reconstruction limits |
| `CONTRADICTION` | Detects contradictions |
| `SCOPE` | Validates scope boundaries |
| `TEMPORAL` | Validates temporal consistency |

---

## Gate Decisions

| Decision | Meaning |
|----------|---------|
| `PASS` | Condition satisfied, proceed |
| `FAIL` | Condition violated, block |
| `WARN` | Condition marginal, proceed with warning |
| `SKIP` | Gate not applicable, skip |

---

## Implementing a Gate

### Step 1: Extend the Gate Base Class

```python
from cnhaai.core.gates import Gate, GateType, GateResult, GateDecision

class CustomEvidenceGate(Gate):
    """Custom gate for evidence validation."""
    
    def __init__(self, threshold: float = 0.8):
        super().__init__(
            gate_type=GateType.EVIDENCE_SUFFICIENCY,
            name="custom_evidence_gate",
            description="Validates evidence meets minimum threshold",
            threshold=threshold
        )
    
    def evaluate(self, context: Dict[str, Any], state: Dict[str, Any]) -> GateResult:
        """Evaluate the gate."""
        # Your logic here
        evidence = context.get("evidence", [])
        
        if len(evidence) >= self.threshold:
            return GateResult(
                decision=GateDecision.PASS,
                gate_type=self.gate_type,
                message="Evidence threshold met",
                details={"count": len(evidence)}
            )
        else:
            return GateResult(
                decision=GateDecision.FAIL,
                gate_type=self.gate_type,
                message="Insufficient evidence",
                details={"count": len(evidence), "required": self.threshold}
            )
```

### Step 2: Register with Gate Manager

```python
from cnhaai.core.gates import GateManager

manager = GateManager()
manager.register_gate(CustomEvidenceGate(threshold=0.7))
```

### Step 3: Evaluate in Context

```python
context = {"evidence": ["source1", "source2", "source3"]}
state = {"current_phase": "reasoning"}

result = manager.evaluate_all(context, state)
```

---

## Best Practices

1. **Idempotency**: Gates should produce same result for same input
2. **Determinism**: No random behavior
3. **Clarity**: Clear pass/fail criteria
4. **Logging**: Include informative messages

---

## Related Documents

- [Gate Theory](../spine/15-gate-theory.md)
- [Gate Implementation](../spine/16-gate-implementation.md)
- [Receipt System](../spine/21-receipt-system.md)
