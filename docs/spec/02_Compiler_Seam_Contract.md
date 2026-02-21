# Compiler Seam Contract

## GHLL ↔ NSC
- GHLL AST/IR lowers to NSC IR/bytecode.
- Provenance spans are preserved across lowering.

## GLLL ↔ GHLL
- GLLL encoding maps to GHLL tokens.
- Lexicon-driven mapping enforces deterministic decode.

## Rewrite Packet Mapping
- Rewrite packet fields align with compiler phases and receipts.
- Mapping rules are versioned and schema-validated.
