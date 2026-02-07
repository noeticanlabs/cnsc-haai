# Cross-Reference Index

**Status:** Canonical

## Overview

This index provides bidirectional links between specifications, code, and documentation.

## Spec to Code Mapping

| Spec Section | Code Module | File |
|--------------|-------------|------|
| `spec/ghll/02_Grammar_EBNF.md` | GHLL Parser | [`src/cnsc/haai/ghll/parser.py`](src/cnsc/haai/ghll/parser.py) |
| `spec/ghll/03_Type_System.md` | Type System | [`src/cnsc/haai/ghll/types.py`](src/cnsc/haai/ghll/types.py) |
| `spec/ghll/04_Rewrite_Operators.md` | Rewriting | [`src/cnsc/haai/ghll/rewrite.py`](src/cnsc/haai/ghll/rewrite.py) |
| `spec/glll/01_Hadamard_Basis.md` | Hadamard | [`src/cnsc/haai/glll/hadamard.py`](src/cnsc/haai/glll/hadamard.py) |
| `spec/glll/02_Codebook_Format.md` | Codebook | [`src/cnsc/haai/glll/codebook.py`](src/cnsc/haai/glll/codebook.py) |
| `spec/glll/04_Encoding_Decoding.md` | Packetizer | [`src/cnsc/haai/glll/packetizer.py`](src/cnsc/haai/glll/packetizer.py) |
| `spec/glll/06_GLLL_to_GHLL_Mapping.md` | Mapping | [`src/cnsc/haai/glll/mapping.py`](src/cnsc/haai/glll/mapping.py) |
| `spec/nsc/05_CFA_Flow_Automaton.md` | CFA | [`src/cnsc/haai/nsc/cfa.py`](src/cnsc/haai/nsc/cfa.py) |
| `spec/nsc/07_Bytecode_and_VM.md` | VM | [`src/cnsc/haai/nsc/vm.py`](src/cnsc/haai/nsc/vm.py) |
| `spec/nsc/06_Gates_Rails_Receipts.md` | Gates | [`src/cnsc/haai/nsc/gates.py`](src/cnsc/haai/nsc/gates.py) |
| `spec/gml/02_Trace_Model.md` | Trace | [`src/cnsc/haai/gml/trace.py`](src/cnsc/haai/gml/trace.py) |
| `spec/gml/03_Receipt_Spec.md` | Receipts | [`src/cnsc/haai/gml/receipts.py`](src/cnsc/haai/gml/receipts.py) |
| `spec/gml/05_Query_Audit.md` | Replay | [`src/cnsc/haai/gml/replay.py`](src/cnsc/haai/gml/replay.py) |
| `spec/seam/01_GLLL_to_GHLL_Binding.md` | Mapping | [`src/cnsc/haai/glll/mapping.py`](src/cnsc/haai/glll/mapping.py) |
| `spec/seam/02_GHLL_to_NSC_Lowering.md` | Lowering | [`src/cnsc/haai/ghll/lowering.py`](src/cnsc/haai/ghll/lowering.py) |
| `spec/seam/03_NSC_to_GML_Receipt_Emission.md` | Receipts | [`src/cnsc/haai/gml/receipts.py`](src/cnsc/haai/gml/receipts.py) |

## Code to Spec Mapping

| Code Module | Spec Reference |
|-------------|----------------|
| [`src/cnsc/haai/ghll/parser.py`](src/cnsc/haai/ghll/parser.py/ghll/02_Grammar_EBN) | `specF.md` |
| [`src/cnsc/haai/ghll/types.py`](src/cnsc/haai/ghll/types.py) | `spec/ghll/03_Type_System.md` |
| [`src/cnsc/haai/ghll/rewrite.py`](src/cnsc/haai/ghll/rewrite.py) | `spec/ghll/04_Rewrite_Operators.md` |
| [`src/cnsc/haai/glll/hadamard.py`](src/cnsc/haai/glll/hadamard.py) | `spec/glll/01_Hadamard_Basis.md` |
| [`src/cnsc/haai/glll/codebook.py`](src/cnsc/haai/glll/codebook.py) | `spec/glll/02_Codebook_Format.md` |
| [`src/cnsc/haai/glll/packetizer.py`](src/cnsc/haai/glll/packetizer.py) | `spec/glll/04_Encoding_Decoding.md` |
| [`src/cnsc/haai/glll/mapping.py`](src/cnsc/haai/glll/mapping.py) | `spec/glll/06_GLLL_to_GHLL_Mapping.md` |
| [`src/cnsc/haai/nsc/cfa.py`](src/cnsc/haai/nsc/cfa.py) | `spec/nsc/05_CFA_Flow_Automaton.md` |
| [`src/cnsc/haai/nsc/vm.py`](src/cnsc/haai/nsc/vm.py) | `spec/nsc/07_Bytecode_and_VM.md` |
| [`src/cnsc/haai/nsc/gates.py`](src/cnsc/haai/nsc/gates.py) | `spec/nsc/06_Gates_Rails_Receipts.md` |
| [`src/cnsc/haai/gml/trace.py`](src/cnsc/haai/gml/trace.py) | `spec/gml/02_Trace_Model.md` |
| [`src/cnsc/haai/gml/receipts.py`](src/cnsc/haai/gml/receipts.py) | `spec/gml/03_Receipt_Spec.md` |
| [`src/cnsc/haai/gml/replay.py`](src/cnsc/haai/gml/replay.py) | `spec/gml/05_Query_Audit.md` |
| [`src/cnsc/haai/cli/commands.py`](src/cnsc/haai/cli/commands.py) | `spec/nsc/09_CLI_and_Tooling.md` |

## Doc to Spec Mapping

| Documentation | Spec Reference |
|---------------|----------------|
| `cnhaai/docs/spine/00-project-overview.md` | `README.md` |
| `cnhaai/docs/spine/21-receipt-system.md` | `spec/gml/03_Receipt_Spec.md` |
| `cnhaai/docs/spine/22-receipt-implementation.md` | `spec/gml/03_Receipt_Spec.md` |
| `cnhaai/docs/appendices/appendix-c-receipt-schema.md` | `schemas/receipt.schema.json` |

## Schema References

| Schema | Used By |
|--------|---------|
| `schemas/receipt.schema.json` | `src/cnsc/haai/gml/receipts.py`, `cnhaai/docs/appendices/appendix-c-receipt-schema.md` |
| `schemas/hadamard_glyph.schema.json` | `src/cnsc/haai/glll/codebook.py` |
| `schemas/packet.schema.json` | `src/cnsc/haai/glll/packetizer.py` |
| `schemas/traceloom.schema.json` | `src/cnsc/haai/gml/trace.py` |

## Example References

| Example | Related Specs |
|---------|---------------|
| `examples/end_to_end/00_glll_encode_decode.md` | `spec/glll/`, `src/cnsc/haai/glll/codebook.py` |
| `examples/end_to_end/01_ghll_parse_rewrite.md` | `spec/ghll/`, `src/cnsc/haai/ghll/parser.py` |
| `examples/end_to_end/02_nsc_cfa_run.md` | `spec/nsc/`, `src/cnsc/haai/nsc/vm.py` |
| `examples/end_to_end/03_gml_trace_audit.md` | `spec/gml/`, `src/cnsc/haai/gml/receipts.py` |

## Quick Lookup

### Finding Implementation

| I want to... | Look here |
|--------------|-----------|
| Parse GHLL source | [`src/cnsc/haai/ghll/parser.py`](src/cnsc/haai/ghll/parser.py) |
| Type check | [`src/cnsc/haai/ghll/types.py`](src/cnsc/haai/ghll/types.py) |
| Encode/decode Hadamard | [`src/cnsc/haai/glll/hadamard.py`](src/cnsc/haai/glll/hadamard.py) |
| Manage codebooks | [`src/cnsc/haai/glll/codebook.py`](src/cnsc/haai/glll/codebook.py) |
| Execute bytecode | [`src/cnsc/haai/nsc/vm.py`](src/cnsc/haai/nsc/vm.py) |
| Evaluate gates | [`src/cnsc/haai/nsc/gates.py`](src/cnsc/haai/nsc/gates.py) |
| Create receipts | [`src/cnsc/haai/gml/receipts.py`](src/cnsc/haai/gml/receipts.py) |
| Replay execution | [`src/cnsc/haai/gml/replay.py`](src/cnsc/haai/gml/replay.py) |

### Finding Specs

| I want to learn about... | Look here |
|--------------------------|-----------|
| GHLL grammar | `spec/ghll/02_Grammar_EBNF.md` |
| GLLL encoding | `spec/glll/01_Hadamard_Basis.md` |
| NSC bytecode | `spec/nsc/07_Bytecode_and_VM.md` |
| Receipt schema | `spec/gml/03_Receipt_Spec.md` |
| Seam contracts | `spec/seam/01_GLLL_to_GHLL_Binding.md` |
| CLI commands | `docs/cli-reference.md` |

## Navigation Tips

1. **Code → Spec**: Check the module docstring for spec references
2. **Spec → Code**: Check the "See Also" section at the bottom
3. **Docs → Spec**: Use `docs/ARCHITECTURE.md` for navigation
4. **Examples → Implementation**: Each example links to relevant code files
