# GHLL ↔ NSC Interface — v1.0

Pipeline:
GHLL source → AST(spans) → NSC IR(typed) → opcode selection → NSC packet + bytecode + debug map.

Symbolic mode aims for lossless structure retention; exec mode prioritizes deterministic bytecode with spans preserved.
