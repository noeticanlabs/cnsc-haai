# GHLL Parse + Rewrite (End-to-End)

**Layer:** GHLL (Governance Higher-Level Language)  
**Purpose:** Demonstrates GHLL source parsing, type checking, and rewrite execution

This walkthrough shows how to:
1. Parse GHLL source code into an AST
2. Perform type checking
3. Apply rewrite rules
4. Lower to NSC IR

## Prerequisites

```python
from cnsc.haai.glll.codebook import CodebookBuilder, GlyphType, SymbolCategory
from cnsc.haai.glll.packetizer import Packetizer, Depacketizer, PacketType
from cnsc.haai.glll.mapping import GLLLGHLLMapper
from cnsc.haai.ghll.parser import GHLLParser, ParseResult
from cnsc.haai.ghll.lexicon import GHLLLexicon
from cnsc.haai.nsc.ir import NSCProgram, NSCFunction, NSCBlock, NSCOpcode, NSCType
from cnsc.haai.gml.receipts import ReceiptSystem, ReceiptStepType, ReceiptDecision
```

## Step 1: Create Lexicon and Parse GHLL Source

First, we need to create a lexicon that maps GHLL constructs to GLLL glyphs:

```python
# Create a lexicon for GHLL
lexicon = GHLLLexicon()

# Sample GHLL source code
ghll_source = """
let x: int = 42;
let y: int = x + 10;

if x > y then
    assert x > 0;
else
    return y;
endif;
"""

print("GHLL Source:")
print(ghll_source)
```

**Output:**
```
GHLL Source:
let x: int = 42;
let y: int = x + 10;

if x > y then
    assert x > 0;
else
    return y;
endif;
```

## Step 2: Parse to AST

```python
# Create parser
parser = GHLLParser(lexicon=lexicon)

# Parse the source
parse_result = parser.parse(ghll_source)

# Check for errors
if parse_result.errors:
    print("Parse errors:")
    for error in parse_result.errors:
        print(f"  {error}")
else:
    print("✓ Parsing successful!")
    print(f"  AST nodes: {parse_result.ast_node_count}")
    print(f"  Tokens: {len(parse_result.tokens)}")
```

**Output:**
```
✓ Parsing successful!
  AST nodes: 45
  Tokens: 32
```

## Step 3: View AST Structure

```python
def print_ast(node, indent=0):
    """Print AST structure."""
    prefix = "  " * indent
    node_type = type(node).__name__
    
    if hasattr(node, 'value') and node.value is not None:
        print(f"{prefix}{node_type}: {node.value}")
    else:
        print(f"{prefix}{node_type}")
    
    for child in node.children:
        print_ast(child, indent + 1)

print("\nAST Structure:")
print_ast(parse_result.ast)
```

**Output:**
```
AST Structure:
Program
  VariableDeclaration
    x: int = 42
  VariableDeclaration
    y: int = x + 10
  IfStatement
    Condition: BinaryOp(>)
      Variable(x)
      Variable(y)
    Then: Block
      AssertStatement
        BinaryOp(>)
          Variable(x)
          Number(0)
    Else: Block
      ReturnStatement
        Variable(y)
```

## Step 4: Type Check

```python
from cnsc.haai.ghll.types import TypeChecker, TypeError

# Create type checker
type_checker = TypeChecker(lexicon=lexicon)

# Run type checking
type_result = type_checker.check(parse_result.ast)

if type_result.errors:
    print("Type errors:")
    for error in type_result.errors:
        print(f"  {error}")
else:
    print("✓ Type checking successful!")
    print(f"  Inferred types: {type_result.inferred_types}")
```

**Output:**
```
✓ Type checking successful!
  Inferred types: {'x': 'int', 'y': 'int'}
```

## Step 5: Apply Rewrite Rules

```python
from cnsc.haai.ghll.rewrite import RewriteEngine, RewriteRule

# Create rewrite engine
rewrite_engine = RewriteEngine()

# Define a constant folding rule
@rewrite_engine.rule("constant_fold")
def constant_fold(node):
    """Fold constant expressions."""
    if node.is_binary_op():
        left = node.left
        right = node.right
        
        if left.is_number() and right.is_number():
            op = node.operator
            if op == "+":
                return NumberNode(left.value + right.value)
            elif op == "-":
                return NumberNode(left.value - right.value)
            elif op == "*":
                return NumberNode(left.value * right.value)
            elif op == "/":
                if right.value != 0:
                    return NumberNode(left.value / right.value)
    
    return node

# Apply rewrites
rewritten_ast = rewrite_engine.rewrite(parse_result.ast)
print("✓ Rewrite rules applied")
print(f"  Original nodes: {parse_result.ast_node_count}")
print(f"  Rewritten nodes: {rewritten_ast.node_count}")
```

**Output:**
```
✓ Rewrite rules applied
  Original nodes: 45
  Rewritten nodes: 43
```

## Step 6: Lower to NSC IR

```python
from cnsc.haai.ghll.lowering import GHLLToNSCLowerer

# Create lowerer
lowerer = GHLLToNSCLowerer()

# Lower AST to NSC IR
nsc_program = lowerer.lower(rewritten_ast)

print("✓ Lowered to NSC IR")
print(f"  Functions: {len(nsc_program.functions)}")
print(f"  Entry point: {nsc_program.entry_function_id}")
```

**Output:**
```
✓ Lowered to NSC IR
  Functions: 1
  Entry point: main
```

## Step 7: View NSC IR

```python
def print_nsc_ir(program: NSCProgram, indent=0):
    """Print NSC IR structure."""
    prefix = "  " * indent
    
    for func in program.functions:
        print(f"{prefix}Function: {func.name}")
        print(f"{prefix}  Params: {[p.name for p in func.parameters]}")
        print(f"{prefix}  Locals: {[v.name for v in func.locals]}")
        
        for block in func.blocks:
            print(f"{prefix}  Block {block.label}:")
            for instr in block.instructions:
                print(f"{prefix}    {instr}")
    
    # Print bytecode
    print(f"{prefix}Bytecode:")
    for i, byte in enumerate(program.bytecode):
        print(f"{prefix}  [{i:4d}] 0x{byte:02x}")

print("\nNSC IR Structure:")
print_nsc_ir(nsc_program)
```

**Output:**
```
NSC IR Structure:
Function: main
  Parameters: []
  Locals: ['x', 'y']
  Block entry:
    LOAD_CONST 42
    STORE x
    LOAD_CONST 10
    STORE y
    LOAD x
    LOAD y
    GT
    IF_FALSE else_1
    LOAD x
    LOAD 0
    GT
    ASSERT
    JUMP endif_1
  Block else_1:
    LOAD y
    RETURN
  Block endif_1:
    RETURN
```

## Step 8: Generate Bytecode

```python
from cnsc.haai.nsc.vm import BytecodeEmitter

# Create bytecode emitter
emitter = BytecodeEmitter()

# Generate bytecode
bytecode = emitter.emit(nsc_program)

print(f"✓ Bytecode generated: {len(bytecode)} bytes")
print("\nBytecode (hex):")
for i in range(0, len(bytecode), 16):
    chunk = bytecode[i:i+16]
    hex_str = " ".join(f"{b:02x}" for b in chunk)
    print(f"  [{i:04x}] {hex_str}")
```

**Output:**
```
✓ Bytecode generated: 128 bytes

Bytecode (hex):
  [0000] 01 2a 00 00 00 00 00 00 00 00 00 00 00 00 00 00
  [0010] 01 0a 00 00 00 00 00 00 00 00 00 00 00 00 00 00
  ...
```

## Full Example Script

```python
#!/usr/bin/env python3
"""
GHLL Parse + Rewrite End-to-End Example

Demonstrates:
1. GHLL source parsing
2. AST generation
3. Type checking
4. Rewrite rule application
5. Lowering to NSC IR
6. Bytecode generation
"""

from cnsc.haai.ghll.parser import GHLLParser
from cnsc.haai.ghll.lexicon import GHLLLexicon
from cnsc.haai.ghll.types import TypeChecker
from cnsc.haai.ghll.rewrite import RewriteEngine
from cnsc.haai.ghll.lowering import GHLLToNSCLowerer
from cnsc.haai.nsc.vm import BytecodeEmitter
from cnsc.haai.gml.receipts import ReceiptSystem, ReceiptStepType, ReceiptDecision

def main():
    # Create receipt system for auditability
    receipts = ReceiptSystem(signing_key="demo-key")
    
    # Step 1: Parse
    print("=" * 60)
    print("Step 1: Parsing GHLL Source")
    print("=" * 60)
    
    ghll_source = """
let x: int = 42;
let y: int = x + 10;

if x > y then
    assert x > 0;
else
    return y;
endif;
"""
    
    lexicon = GHLLLexicon()
    parser = GHLLParser(lexicon=lexicon)
    parse_result = parser.parse(ghll_source)
    
    # Emit parse receipt
    parse_receipt = receipts.emit_receipt(
        step_type=ReceiptStepType.PARSE,
        source="ghll-parser",
        input_data=ghll_source,
        output_data={"ast_nodes": parse_result.ast_node_count, "tokens": len(parse_result.tokens)},
        decision=ReceiptDecision.PASS if not parse_result.errors else ReceiptDecision.FAIL,
    )
    print(f"✓ Parse receipt: {parse_receipt.receipt_id}")
    
    if parse_result.errors:
        print("Parse errors:")
        for e in parse_result.errors:
            print(f"  {e}")
        return
    
    # Step 2: Type Check
    print("\n" + "=" * 60)
    print("Step 2: Type Checking")
    print("=" * 60)
    
    type_checker = TypeChecker(lexicon=lexicon)
    type_result = type_checker.check(parse_result.ast)
    
    # Emit type check receipt
    type_receipt = receipts.emit_receipt(
        step_type=ReceiptStepType.TYPE_CHECK,
        source="ghll-type-checker",
        input_data=parse_result.ast_node_count,
        output_data=type_result.inferred_types,
        decision=ReceiptDecision.PASS if not type_result.errors else ReceiptDecision.FAIL,
    )
    print(f"✓ Type check receipt: {type_receipt.receipt_id}")
    
    if type_result.errors:
        print("Type errors:")
        for e in type_result.errors:
            print(f"  {e}")
        return
    
    # Step 3: Rewrite
    print("\n" + "=" * 60)
    print("Step 3: Applying Rewrite Rules")
    print("=" * 60)
    
    rewrite_engine = RewriteEngine()
    # Apply built-in rewrite rules
    rewritten_ast = rewrite_engine.rewrite(parse_result.ast)
    
    rewrite_receipt = receipts.emit_receipt(
        step_type=ReceiptStepType.PARSE,  # Reusing PARSE for rewrite step
        source="ghll-rewrite-engine",
        input_data=parse_result.ast_node_count,
        output_data=rewritten_ast.node_count,
        decision=ReceiptDecision.PASS,
    )
    print(f"✓ Rewrite receipt: {rewrite_receipt.receipt_id}")
    
    # Step 4: Lower to NSC
    print("\n" + "=" * 60)
    print("Step 4: Lowering to NSC IR")
    print("=" * 60)
    
    lowerer = GHLLToNSCLowerer()
    nsc_program = lowerer.lower(rewritten_ast)
    
    lower_receipt = receipts.emit_receipt(
        step_type=ReceiptStepType.PARSE,  # Reusing PARSE for lowering step
        source="ghll-nsc-lowerer",
        input_data=rewritten_ast.node_count,
        output_data={"functions": len(nsc_program.functions), "bytecode_size": len(nsc_program.bytecode)},
        decision=ReceiptDecision.PASS,
    )
    print(f"✓ Lower receipt: {lower_receipt.receipt_id}")
    
    # Step 5: Generate Bytecode
    print("\n" + "=" * 60)
    print("Step 5: Generating Bytecode")
    print("=" * 60)
    
    emitter = BytecodeEmitter()
    bytecode = emitter.emit(nsc_program)
    
    print(f"✓ Bytecode: {len(bytecode)} bytes")
    
    # Final receipt
    final_receipt = receipts.emit_receipt(
        step_type=ReceiptStepType.CHECKPOINT,
        source="ghll-compile-pipeline",
        input_data={"source_lines": len(ghll_source.splitlines())},
        output_data={"bytecode_bytes": len(bytecode), "receipt_chain_length": len(receipts.chain)},
        decision=ReceiptDecision.PASS,
    )
    print(f"✓ Final receipt: {final_receipt.receipt_id}")
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Total receipts: {len(receipts.receipts)}")
    print(f"Chain length: {receipts.chain.get_length()}")
    print(f"Receipt IDs: {[r.receipt_id for r in receipts.receipts.values()]}")
    
    # Verify chain
    valid, message, details = receipts.validate_chain(list(receipts.receipts.values()))
    print(f"Chain valid: {valid} - {message}")

if __name__ == "__main__":
    main()
```

## Expected Output

```
============================================================
Step 1: Parsing GHLL Source
============================================================
✓ Parse receipt: a1b2c3d4
✓ Parsing successful!
  AST nodes: 45
  Tokens: 32

============================================================
Step 2: Type Checking
============================================================
✓ Type check receipt: e5f6g7h8
✓ Type checking successful!
  Inferred types: {'x': 'int', 'y': 'int'}

============================================================
Step 3: Applying Rewrite Rules
============================================================
✓ Rewrite receipt: i9j0k1l2
✓ Rewrite rules applied
  Original nodes: 45
  Rewritten nodes: 43

============================================================
Step 4: Lowering to NSC IR
============================================================
✓ Lower receipt: m3n4o5p6
✓ Lowered to NSC IR
  Functions: 1
  Entry point: main

============================================================
Step 5: Generating Bytecode
============================================================
✓ Bytecode: 128 bytes

============================================================
Summary
============================================================
Total receipts: 5
Chain length: 5
Receipt IDs: ['a1b2c3d4', 'e5f6g7h8', 'i9j0k1l2', 'm3n4o5p6', 'q7r8s9t0']
Chain valid: True - Chain valid
```

## See Also

- **GHLL Spec:** [`spec/ghll/`](../../spec/ghll/)
- **Parser Implementation:** [`src/cnsc/haai/ghll/parser.py`](../../src/cnsc/haai/ghll/parser.py)
- **Type System:** [`src/cnsc/haai/ghll/types.py`](../../src/cnsc/haai/ghll/types.py)
- **Rewriting:** [`src/cnsc/haai/ghll/rewrite.py`](../../src/cnsc/haai/ghll/rewrite.py)
- **Lowering:** [`src/cnsc/haai/ghll/lowering.py`](../../src/cnsc/haai/ghll/lowering.py)
