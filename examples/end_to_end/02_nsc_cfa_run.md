# Example 02: NSC CFA Run

**Purpose**: Demonstrate NSC execution with Control Flow Automaton (CFA)

---

## Overview

NSC (Neural State Controller) executes GHLL with CFA phases that enforce PoC constraints.

---

## Running NSC Program

```python
from cnsc.haai.nsc.cfa import CFAExecutor
from cnsc.haai.nsc.ir import NSCProgram

# Create NSC program
program = NSCProgram.from_ghll(ast)

# Create executor
executor = CFAExecutor()

# Run with CFA
result = executor.execute(program)

print(f"Result: {result.value}")
print(f"Receipts: {len(result.receipts)}")
```

---

## CFA Phases

| Phase | Purpose |
|-------|---------|
| ACQUISITION | Gather evidence |
| CONSTRUCTION | Build abstractions |
| REASONING | Use abstractions |
| VALIDATION | Verify results |
| RECOVERY | Repair degradation |

---

## Running the Example

```bash
python -c "
from cnsc.haai.nsc.cfa import CFAExecutor

executor = CFAExecutor()
# ... load and run program
print('CFA executed successfully')
"
```

---

## Related Documents

- [NSC Goals and Invariants](../../spec/nsc/00_NSC_Goals_and_Invariants.md)
- [CFA Flow Automaton](../../spec/nsc/05_CFA_Flow_Automaton.md)
