# CNSC-HAAI

Monorepo scaffold for the **NSC + GHLL + GLLL + GML** stack with a single compiler seam and ledger-truth runtime contract.

## Doc Spine (v1.0)

```
/README.md
/VERSION.md
/CHANGELOG.md
/LICENSE

/docs/
  00_System_Overview.md
  01_Coherence_PoC_Canon.md
  02_Compiler_Seam_Contract.md
  03_Ledger_Truth_Contract.md

/spec/
  nsc/
  ghll/
  glll/
  gml/
  seam/

/schemas/
  packet.schema.json
  rewrite_packet.schema.json
  receipt.schema.json
  lexicon.schema.json
  hadamard_glyph.schema.json
  traceloom.schema.json

/src/
  nsc/
  ghll/
  glll/
  gml/
  seam/

/examples/
  ghll/
  glll/
  gml/
  end_to_end/

/compliance_tests/
  nsc/
  ghll/
  glll/
  gml/
  seam/

/tools/
  nsc_cli/
  verifier/
  lexicon_builder/
  glyph_codegen/

/artifacts/
  receipts/
  golden_parses/
  golden_bytecode/
  golden_traces/
```

## Build Order
1. Schemas + receipts
2. NSC CFA + Banker (gates/rails/termination)
3. GHLL grammar + typing + rewrite operators
4. GLLL codebook + deterministic encode/decode + mapping to GHLL
5. GML trace + PhaseLoom + replay verifier
