# Example 00: GLLL Encode/Decode

**Purpose**: Demonstrate GLLL (Glyphic Low-Level Language) encoding and decoding

---

## Overview

GLLL provides error-tolerant binary encoding using Hadamard basis for reliable transmission.

---

## Encoding Data

```python
from cnsc.haai.glll.hadamard import encode_hadamard, decode_hadamard
from cnsc.haai.glll.codebook import Codebook

# Load codebook
codebook = Codebook.load("npe_assets/codebooks/gr/plan_templates.yaml")

# Encode data
data = {"action": "diagnose", "confidence": 0.9}
encoded = encode_hadamard(data, codebook)

print(f"Encoded length: {len(encoded)} bits")
print(f"Encoded: {encoded}")
```

---

## Decoding Data

```python
# Decode with error tolerance
decoded = decode_hadamard(encoded, codebook, max_errors=3)

print(f"Decoded: {decoded}")
```

---

## Running the Example

```bash
python -c "
from cnsc.haai.glll.hadamard import encode_hadamard, decode_hadamard
from cnsc.haai.glll.codebook import Codebook

codebook = Codebook.load('npe_assets/codebooks/gr/plan_templates.yaml')
data = {'action': 'diagnose', 'confidence': 0.9}
encoded = encode_hadamard(data, codebook)
decoded = decode_hadamard(encoded, codebook)
print(f'Decoded matches: {data == decoded}')
"
```

---

## Expected Output

```
Encoded length: 128 bits
Decoded matches: True
```

---

## Related Documents

- [GLLL Specification](../../spec/glll/01_Hadamard_Basis_and_Glyph_Construction.md)
- [Codebook Format](../../spec/glll/02_Codebook_Format.md)
