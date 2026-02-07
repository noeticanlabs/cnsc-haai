# System Overview

> **DEPRECATED**: This file is archived. Use current documentation instead.
> 
> For current documentation:
> - **Overview**: [`cnhaai/docs/spine/00-project-overview.md`](cnhaai/docs/spine/00-project-overview.md)
> - **Specs**: [`spec/`](spec/)

## Layer Model
- **GLLL → GHLL → NSC → GML**
- Two alphabets with one compiler seam and one ledger-truth runtime contract.

## Phase-Governed Execution
- Control Flow Automaton (CFA) governs phase transitions.
- PoC gates/rails/receipts provide runtime constraints.

## Determinism + Replayability
- Deterministic compilation, execution, and receipt emission.
- Replayability verified through ledger truth and receipt chains.
