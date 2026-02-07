# GLLL to GHLL Binding Contract

**Spec Version:** 1.0.0  
**Seam:** GLLL → GHLL  
**Status:** Canonical

## Overview

This contract defines the binding rules for mapping GLLL glyph sequences to GHLL semantic atoms. The binding process is deterministic and error-tolerant.

## Preconditions

Before binding can occur:

| # | Condition | Description |
|---|-----------|-------------|
| 1 | Valid codebook | Codebook must be loaded and validated |
| 2 | Glyph sequence | Input must be a valid glyph sequence |
| 3 | No encoding errors | Glyphs must decode to valid Hadamard codes |
| 4 | Boundary aligned | Glyph boundaries must be preserved |

## Binding Rules

### Rule 1: Direct Mapping

```
For each glyph g:
  token = codebook.lookup(g.symbol)
  tokens.append(token)
```

### Rule 2: Sequence Mapping

For multi-glyph sequences:

```
For glyph sequence [g1, g2, ...]:
  If sequence in codebook.sequences:
    token = codebook.sequences[sequence]
  Else:
    Apply Rule 1 to each glyph
```

### Rule 3: Context-Dependent Mapping

When ambiguity exists:

```
For glyph g in context C:
  candidates = codebook.lookup_all(g.symbol)
  selected = resolve_ambiguity(candidates, C)
```

## Wire Format

### Input (GLLL Packet)

```json
{
  "packet_type": "DATA",
  "glyphs": ["GLYPH_1", "GLYPH_2", "..."],
  "checksum": "sha256:...",
  "sequence_number": 0,
  "total_packets": 1
}
```

### Output (GHLL Tokens)

```json
{
  "tokens": [
    {"type": "KEYWORD", "value": "if", "span": {"start": 0, "end": 2}},
    {"type": "IDENTIFIER", "value": "x", "span": {"start": 3, "end": 4}},
    ...
  ],
  "provenance": {
    "source": "glll-ghll-binder",
    "glyph_count": 15,
    "token_count": 10
  }
}
```

## Error Codes

| Code | Meaning | Handling |
|------|---------|----------|
| `INVALID_GLYPH` | Unknown glyph symbol | Skip with warning |
| `AMBIGUOUS_BINDING` | Multiple bindings possible | Apply context rules |
| `CODEBOOK_MISSING` | No codebook loaded | Abort with error |
| `CHECKSUM_FAILED` | Packet integrity check failed | Reject packet |

## Example

### Input Glyphs

```
["START", "S", "Y", "M", "B", "O", "L", "_", "A", "END"]
```

### Bound Tokens

```json
{
  "tokens": [
    {"type": "DELIMITER", "value": "START", "span": {"start": 0, "end": 1}},
    {"type": "SYMBOL", "value": "SYMBOL_A", "span": {"start": 1, "end": 9}}
  ],
  "provenance": {
    "source": "glll-ghll-binder",
    "glyph_count": 10,
    "token_count": 2
  }
}
```

## Implementation

```python
from cnsc.haai.glll.mapping import GlyphMapper, BindingType

def bind_glyphs(glyphs: list, codebook: Codebook) -> BindingResult:
    """
    Bind glyph sequence to GHLL tokens.
    
    Preconditions:
    - codebook.is_valid() == True
    - len(glyphs) > 0
    
    Returns:
        BindingResult with tokens and provenance
    """
    mapper = GlyphMapper(codebook)
    bindings = []
    
    for glyph in glyphs:
        binding = mapper.map_glyph(glyph)
        bindings.append(binding)
    
    # Emit binding receipt
    receipt = emit_receipt(
        step_type=ReceiptStepType.PARSE,
        source="glll-ghll-binder",
        input_data={"glyph_count": len(glyphs)},
        output_data={"token_count": len(bindings)},
    )
    
    return BindingResult(tokens=bindings, receipt=receipt)
```

## Version Compatibility

| Codebook Version | Binder Version | Status |
|-----------------|----------------|--------|
| 1.0.0 | 1.0.0 | Required |
| 1.0.0 | 1.1.0 | Compatible |

## See Also

- Implementation: [`src/cnsc/haai/glll/mapping.py`](../../src/cnsc/haai/glll/mapping.py)
- Codebook: [`src/cnsc/haai/glll/codebook.py`](../../src/cnsc/haai/glll/codebook.py)
- Seam principles: [`spec/seam/00_Seam_Principles.md`](../../spec/seam/00_Seam_Principles.md)
