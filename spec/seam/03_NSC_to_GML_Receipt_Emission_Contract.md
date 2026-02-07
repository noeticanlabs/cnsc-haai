# NSC to GML Receipt Emission Contract

**Spec Version:** 1.0.0  
**Seam:** NSC → GML  
**Status:** Canonical

## Overview

This contract defines the rules for emitting GML receipts during NSC execution. Every execution step produces a receipt for auditability.

## Preconditions

| # | Condition | Description |
|---|-----------|-------------|
| 1 | Valid VM state | VM must be in a valid state |
| 2 | Bytecode loaded | Program bytecode must be loaded |
| 3 | Gate policy | Gate policy must be defined |
| 4 | Receipt system initialized | ReceiptSystem must be initialized |

## Receipt Emission Triggers

| Event | Step Type | When Emitted |
|-------|-----------|--------------|
| Instruction execute | VM_EXECUTION | After each instruction |
| Gate evaluation | GATE_EVAL | After each gate check |
| Phase transition | PHASE_TRANSITION | When phase changes |
| Checkpoint | CHECKPOINT | At defined checkpoints |
| Error | VM_EXECUTION | On exception |

## Receipt Content

### Per-Instruction Receipt

```json
{
  "content": {
    "step_type": "VM_EXECUTION",
    "input_hash": "sha256:state_before",
    "output_hash": "sha256:state_after",
    "decision": "PASS",
    "details": {
      "pc": 42,
      "opcode": "LOAD_CONST",
      "operand": 255,
      "stack_before": ["value1", "value2"],
      "stack_after": ["value1", "value2", 255]
    }
  }
}
```

### Gate Evaluation Receipt

```json
{
  "content": {
    "step_type": "GATE_EVAL",
    "input_hash": "sha256:state",
    "output_hash": "sha256:state",
    "decision": "PASS",
    "details": {
      "gate_name": "evidence_sufficiency",
      "gate_type": "hard",
      "threshold": 0.8,
      "measured": 0.95,
      "violations": []
    }
  }
}
```

## Wire Format

### Input (VM State)

```json
{
  "pc": 42,
  "stack": [1, 2, 3],
  "registers": {"x": 255, "y": 0},
  "coherence": 0.92,
  "phase": "execution"
}
```

### Output (Receipt)

```json
{
  "version": "1.0.0",
  "receipt_id": "a1b2c3d4",
  "timestamp": "2024-01-15T10:30:00Z",
  "episode_id": "e5f6g7h8",
  "content": {...},
  "provenance": {
    "source": "nsc-vm",
    "phase": "execution"
  },
  "signature": {
    "algorithm": "HMAC-SHA256",
    "signer": "vm-key-001",
    "signature": "base64..."
  },
  "previous_receipt_id": "9i8j7k6l",
  "chain_hash": "sha256:..."
}
```

## Error Codes

| Code | Meaning | Handling |
|------|---------|----------|
| `SIGNATURE_FAILED` | Receipt signature invalid | Log error, continue |
| `CHAIN_BREAK` | Previous receipt not found | Create new chain |
| `RECEIPT_OVERFLOW` | Too many receipts | Flush to storage |

## Example

```python
from cnsc.haai.gml.receipts import ReceiptSystem, ReceiptStepType, ReceiptDecision

def execute_with_receipts(vm: VM, receipts: ReceiptSystem):
    """Execute VM with receipt emission."""
    
    while not vm.halted:
        pc = vm.pc
        opcode = vm.fetch_bytecode(pc)
        
        # Execute instruction
        result = vm.execute_step()
        
        # Evaluate gates
        gate_decisions = evaluate_gates(vm.gate_policy, vm.state)
        
        # Emit receipt
        receipt = receipts.emit_receipt(
            step_type=ReceiptStepType.VM_EXECUTION,
            source="nsc-vm",
            input_data={"pc": pc, "opcode": opcode},
            output_data={"result": result, "gates": gate_decisions},
            decision=ReceiptDecision.PASS if all(d == "PASS" for d in gate_decisions) else ReceiptDecision.FAIL,
            phase=vm.state.phase,
        )
        
        print(f"Receipt {receipt.receipt_id}: step_type={receipt.content.step_type.name}")
    
    return receipts
```

## Version Compatibility

| NSC Version | GML Version | Status |
|-------------|-------------|--------|
| 1.0.0 | 1.0.0 | Required |
| 1.0.0 | 1.1.0 | Compatible |

## See Also

- Implementation: [`src/cnsc/haai/gml/receipts.py`](../../src/cnsc/haai/gml/receipts.py)
- Receipt Schema: [`schemas/receipt.schema.json`](../../schemas/receipt.schema.json)
- VM: [`src/cnsc/haai/nsc/vm.py`](../../src/cnsc/haai/nsc/vm.py)
