# GMI v1 Document Spine

## Overview

This directory contains the complete specification of Governed Metabolic Intelligence (GMI) v1.

GMI is a deterministic, governed state transition system with cryptographic accountability and replayable state transitions.

## Directory Structure

### Core Specification
- `00_gmi_scope.md` - Scope and target object definition
- `01_formal_model.md` - Formal core model (State, Step, Decomposition)
- `02_predictor_layer.md` - Proposal generation layer
- `03_witness_availability.md` - Hard gate with dependency graphs
- `04_gate_stack.md` - Deterministic gating with rejection codes
- `05_execution_layer.md` - Deterministic execution semantics
- `06_budget_algebra.md` - Budget monotonicity constraints
- `07_receipt_bundle.md` - Cryptographic receipt structure
- `08_replay_semantics.md` - Replay verification
- `09_adaptation.md` - Governed metabolic adaptation
- `10_renormalization.md` - RCFA layer (optional v1)
- `11_cryptographic_layer.md` - Hashing and Merkle commitments
- `12_security_model.md` - Adversaries and defenses
- `13_proof_obligations.md` - Minimal proof requirements
- `14_computational_nature.md` - Continuous vs discrete governance
- `15_test_procedure.md` - First GMI v1 test
- `16_upgrade_path.md` - GMI v2 roadmap
- `17_receipt_bundle.md` - Extended receipt structure (v1.5+)
- `18_metabolic_tracking.md` - Work-unit budget enforcement
- `19_runtime_api.md` - Runtime engine and API (v1.6)

### Appendices
- `appendices/json_schemas.md` - JSON Schema definitions
- `appendices/determinism_harness.md` - Test harness code
- `appendices/lean_proof_sketch.md` - Lean formalization

## Version
- **GMI v1.6** - Runtime Integration
- **Date**: 2026-02-28
- **Status**: Complete (no placeholders)

## Relationship to CNHAI

GMI v1 is the canonical specification layer that formalizes the CNHAI implementation:

| GMI Concept | CNHAI Equivalent |
|-------------|------------------|
| State S_t | ATS StateCore |
| Predictor | NPE (Neural Planning Engine) |
| Gate | Gate Manager |
| Execution | NSC VM |
| Receipt | ATS Receipt |
| Chain Tip | Chain Hash |
| Budget | Coherence Budget |
| Renormalization | RCFA Abstraction |

## Key Invariants

1. **Determinism**: Given identical inputs → identical outputs
2. **Budget Monotonicity**: B_{t+1} ≤ B_t (unless credit receipt)
3. **Replay Consistency**: Replay reproduces identical state hash
4. **Witness Soundness**: No policy check without required fields
