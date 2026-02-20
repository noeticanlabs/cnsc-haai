# Example 01: GHLL Parse and Rewrite

**Purpose**: Demonstrate GHLL parsing and rewrite operations

---

## Overview

GHLL (Graphical Hypertext Linking Language) provides typed grammar and semantic constraints for meaning representation.

---

## Parsing GHLL

```python
from cnsc.haai.ghll.parser import GHLLParser

# Create parser
parser = GHLLParser()

# Parse GHLL source
source = """
let x = 5 in
where x > 0
return x * 2
"""

ast = parser.parse(source)
print(f"AST: {ast}")
```

---

## Rewrite Operations

```python
from cnsc.haai.ghll.rewrite import RewriteEngine

# Create rewrite engine
engine = RewriteEngine()

# Apply rewrite rule
result = engine.apply("constant_folding", ast)
print(f"Rewritten: {result}")
```

---

## Running the Example

```bash
python -c "
from cnsc.haai.ghll.parser import GHLLParser
from cnsc.haai.ghll.rewrite import RewriteEngine

parser = GHLLParser()
source = 'let x = 5 in return x * 2'
ast = parser.parse(source)
print(f'Parsed: {ast}')
"
```

---

## Expected Output

```
Parsed: Let(x=5, Return(BinOp(*, x, 2)))
```

---

## Related Documents

- [GHLL Design Principles](../../spec/ghll/00_GHLL_Design_Principles.md)
- [GHLL Grammar EBNF](../../spec/ghll/02_Grammar_EBNF.md)
