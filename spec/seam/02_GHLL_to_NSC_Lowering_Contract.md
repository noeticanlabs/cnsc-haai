# GHLL to NSC Lowering Contract

**Spec Version:** 1.0.0  
**Seam:** GHLL → NSC  
**Status:** Canonical

## Overview

This contract defines the lowering rules for converting GHLL AST to NSC Intermediate Representation (IR). Lowering preserves:
- **Provenance spans** for traceability
- **Semantic atoms** for meaning preservation
- **Type information** for type safety

## Preconditions

| # | Condition | Description |
|---|-----------|-------------|
| 1 | Valid AST | AST must be parseable and type-checked |
| 2 | Resolved symbols | All identifiers must be resolved |
| 3 | No unbound references | All variable references must exist |
| 4 | Well-typed expressions | All expressions must have inferred types |

## Lowering Rules

### Rule 1: Variable Declaration

```
GHLL: let x: int = 42;
NSC:  [LOAD_CONST 42, STORE x]
```

### Rule 2: Binary Operations

```
GHLL: x + y
NSC:  [LOAD x, LOAD y, ADD]
```

### Rule 3: Conditionals

```
GHLL: if x > y then A else B endif
NSC:  [LOAD x, LOAD y, GT, IF_FALSE else_block, A, JUMP endif, else_block, B, endif_block]
```

### Rule 4: Loops

```
GHLL: while x > 0 do x = x - 1 endwhile
NSC:  [loop_header, LOAD x, LOAD 0, GT, IF_FALSE exit, LOAD x, LOAD 1, SUB, STORE x, JUMP loop_header, exit_block]
```

## Wire Format

### Input (GHLL AST)

```json
{
  "ast": {
    "type": "Program",
    "body": [...]
  },
  "types": {"x": "int", "y": "int"},
  "provenance": {
    "source_file": "example.ghll",
    "span": {"start": 0, "end": 100}
  }
}
```

### Output (NSC IR)

```json
{
  "ir": {
    "type": "NSCProgram",
    "functions": [...],
    "bytecode": [0x01, 0x2A, ...]
  },
  "provenance": {
    "source": "ghll-nsc-lowerer",
    "input_spans": [...],
    "output_offsets": [...]
  }
}
```

## Error Codes

| Code | Meaning | Handling |
|------|---------|----------|
| `UNBOUND_VARIABLE` | Reference to undefined variable | Type error |
| `TYPE_MISMATCH` | Operator applied to wrong type | Type error |
| `INVALID_AST` | Malformed AST structure | Parse error |
| `SPAN_MISSING` | Missing provenance span | Warning, use default |

## Example

### Input GHLL

```ghll
let x: int = 42;
let y: int = x + 10;
if x > y then
    return 1;
else
    return 0;
endif;
```

### Output NSC IR

```json
{
  "functions": [
    {
      "name": "main",
      "blocks": [
        {
          "label": "entry",
          "instructions": [
            {"opcode": "LOAD_CONST", "operand": 42},
            {"opcode": "STORE", "operand": "x"},
            {"opcode": "LOAD_CONST", "operand": 10},
            {"opcode": "STORE", "operand": "y"},
            {"opcode": "LOAD", "operand": "x"},
            {"opcode": "LOAD", "operand": "y"},
            {"opcode": "GT"},
            {"opcode": "IF_FALSE", "operand": "else_1"},
            {"opcode": "LOAD_CONST", "operand": 1},
            {"opcode": "RETURN"},
            {"opcode": "JUMP", "operand": "endif_1"}
          ]
        }
      ]
    }
  ],
  "bytecode": "01002A027801020279030078030079200030000B01014031000E010040"
}
```

## Implementation

```python
from cnsc.haai.ghll.lowering import GHLLToNSCLowerer

def lower_ghll_to_nsc(ast: AST, type_env: TypeEnvironment) -> NSCProgram:
    """
    Lower GHLL AST to NSC IR.
    
    Preconditions:
    - ast.is_valid() == True
    - type_env.is_complete() == True
    
    Returns:
        NSCProgram with bytecode and metadata
    """
    lowerer = GHLLToNSCLowerer()
    program = lowerer.lower(ast)
    
    # Emit lowering receipt
    receipt = emit_receipt(
        step_type=ReceiptStepType.PARSE,
        source="ghll-nsc-lowerer",
        input_data={"ast_nodes": ast.node_count},
        output_data={"bytecode_size": len(program.bytecode), "functions": len(program.functions)},
    )
    
    return program
```

## Version Compatibility

| GHLL Version | NSC Version | Status |
|--------------|-------------|--------|
| 1.0.0 | 1.0.0 | Required |
| 1.1.0 | 1.0.0 | Compatible |

## See Also

- Implementation: [`src/cnsc/haai/ghll/lowering.py`](../../src/cnsc/haai/ghll/lowering.py)
- NSC Spec: [`spec/nsc/`](../../spec/nsc/)
- Type System: [`src/cnsc/haai/ghll/types.py`](../../src/cnsc/haai/ghll/types.py)
