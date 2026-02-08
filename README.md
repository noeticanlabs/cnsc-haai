Research & Licensing Notice
The Coherence Framework is available for non-commercial academic and government research, including NSF- and DARPA-funded projects.
Commercial use requires a separate license from NoeticanLabs.



Below is a **compelling, technically honest, and funder-/engineer-ready README** for **CNSC-HAAI**.
It's written to do three things at once:

1. Make it immediately clear **what this system is (and is not)**
2. Explain **why it fundamentally differs from LLMs and agent frameworks**
3. Provide a clear mental model for contributors, reviewers, and future you

You can drop this in as `README.md` with minimal edits.

---

# CNSC-HAAI

**Coherence-Native, Safety-Constrained Hybrid Artificial Intelligence**

> *Intelligence is not prediction.
> Intelligence is staying coherent while changing.*

---

## What is CNSC-HAAI?

**CNSC-HAAI** is a **coherence-native cognitive runtime** designed for **auditable, deterministic, and constraint-governed intelligence**.

It is **not** a language model.
It is **not** a prompt-driven agent.
It is **not** a black box.

Instead, CNSC-HAAI is a **composable intelligence substrate** where:

* reasoning is **constrained by explicit invariants**
* decisions are **logged as receipts**
* execution is **replayable**
* violations are **detected, not narrated**
* coherence is **enforced, not hoped for**

CNSC-HAAI is built for **trustable intelligence at personal and small-scale deployment**, where correctness, explainability, and persistence matter more than fluency.

---

## Core Design Principle

> **Coherence is the primary objective, not likelihood.**

Where most AI systems optimize for:

* next-token probability
* reward signals
* surface plausibility

CNSC-HAAI optimizes for:

* **structural coherence**
* **temporal consistency**
* **constraint preservation**
* **causal accountability**

This single shift changes everything.

---

## High-Level Architecture

CNSC-HAAI combines **Triaxis** (the three-layer abstraction hierarchy) with **NSC** (the execution substrate) and **CNHAAI** (the coherence kernel). Each component has a distinct role:

```
┌─────────────────────────────────────────────┐
│              Interfaces                      │  ← CLI / APIs / LLM proposal adapters
└─────────────────────┬───────────────────────┘
                      │
┌─────────────────────▼───────────────────────┐
│           Triaxis: GHLL (Meaning)            │  ← Typed grammar & semantic constraints
│           Triaxis: GLLL (Integrity)          │  ← Reversible packetization & encoding
│           Triaxis: GML (Forensics)           │  ← Trace, receipts, replay verification
└─────────────────────┬───────────────────────┘
                      │
┌─────────────────────▼───────────────────────┐
│     NSC (Noetica Symbolic Code)              │  ← Execution substrate / IR / VM / gates / rails
│     Executes GHLL → produces GML receipts    │
└─────────────────────┬───────────────────────┘
                      │
┌─────────────────────▼───────────────────────┐
│          CNHAAI (Coherence Kernel)           │  ← Governance / coherence budgets / phased execution
└─────────────────────────────────────────────┘
```

### Triaxis: The Three-Layer Abstraction Hierarchy

**Triaxis** defines the canonical abstraction structure with exactly **3 layers**:

| Layer | Purpose | Key Properties |
|-------|---------|----------------|
| **GML** (Global Meaning Layer) | Forensics, trace, receipts | Full execution history, replay verification |
| **GHLL** (Global High-Level Language) | Meaning, typed grammar | Semantic constraints, rewrite rules |
| **GLLL** (Global Low-Level Language) | Integrity, encoding | Reversible packetization, Hadamard basis |

### NSC: The Execution Substrate

**NSC (Noetica Symbolic Code)** is a **language family and execution substrate** that:

- **Executes GHLL** programs by lowering them to constrained IR
- **Manages the VM** with gates, rails, and bounded termination
- **Emits GML receipts** for every state transition
- **Is NOT a Triaxis layer** — it's the runtime that operates on Triaxis output

NSC is the "engine" that makes Triaxis specifications executable while preserving coherence properties.

### CNHAAI: The Coherence Kernel

At the foundation is a **coherence kernel** (CNHAAI):

* explicit state
* phased execution
* commitments
* coherence budgets
* receipt primitives
* **language-agnostic** and **LLM-tokenless by design** (the kernel operates on semantic units, not LLM tokens)

---

## What Makes CNSC-HAAI Different

### 1. Determinism by Default

Given the same inputs, configuration, and state:

* the same execution path occurs
* the same receipts are produced
* the same replay verifies

This is **not optional** and **not heuristic**.

---

### 2. Constraints Are Runtime Law

Rules are not prompts.
Policies are not suggestions.

Constraints live as:

* **gates**
* **rails**
* **invariants**

Violations:

* halt execution
* downgrade decisions
* generate receipts explaining *why*

---

### 3. Receipts, Not Explanations

CNSC-HAAI does not invent justifications.

It records:

* what assumptions were checked
* which gate was evaluated
* what witnesses were used
* which contract allowed the action

This enables:

* forensic analysis
* audit
* replay
* rollback
* trust

---

### 4. Replayable Intelligence

Any execution can be:

* replayed
* verified
* compared against prior runs
* audited after the fact

This is a **non-negotiable property**.

---

### 5. Proof-Anchored Gates

CNSC-HAAI integrates **formal mathematics** (Lean-verified theorems) into runtime via **Named Gate Contracts**.

A gate is not "because the model said so."
A gate is "because theorem X applies under assumptions A."

This bridges:

* formal methods
* runtime systems
* practical AI

---

## Named Gate Contracts (Key Innovation)

A **Gate Contract** binds:

* a **formal theorem**
* to **runtime-checkable assumptions**
* producing a **certified guarantee**
* logged as a **receipt**

Example:

* *If resource bounds and nonnegativity hold, then accumulated coherence time is lower-bounded.*

At runtime:

* assumptions are checked
* witnesses are logged
* guarantees are licensed
* failures are explicit

This turns "math we believe" into **math we enforce**.

---

## Relationship to LLMs

CNSC-HAAI does **not** compete with LLMs on scale or fluency.

Instead, it **complements** them.

**Recommended pattern:**

* LLMs → proposal generators
* CNSC-HAAI → judge, executor, auditor

LLMs imagine.
CNSC-HAAI decides.

---

## LLM-Tokenless by Design (Kernel Level)

At the **CNHAAI kernel level**, cognition is **LLM-tokenless by design**:

* The kernel operates on **semantic units** and **coherence states**, not LLM-generated tokens
* Language is treated as an interface, projection, or view of internal state
* This enables:
  * Continuous reasoning across timescales
  * Stability across long horizons
  * Non-linguistic cognition

> **Note:** The GHLL parser uses internal Token/SemanticUnit classes for lexical analysis of source code. This is a necessary interface for parsing text, but the CNHAAI kernel itself does not depend on or generate LLM tokens. The "tokenless" claim specifically refers to independence from LLM tokenization, not the absence of internal parsing structures.

---

## Intended Use Cases

CNSC-HAAI excels where **trust beats flash**:

* personal reasoning systems
* research assistants
* planning & scheduling
* safety-critical automation
* engineering decision support
* forensic analysis of decisions
* long-term personal memory systems

It is explicitly **not** designed for:

* open-ended chat
* creative writing at scale
* general web search replacement

---

## Project Status

> **⚠️ Prototype / Experimental - Not Production Ready**

CNSC-HAAI is an **early-stage research prototype**. The core architecture is implemented and functional for evaluation purposes, but:

* Many CLI commands are **stubs or partially implemented**
* Security keys are **hardcoded for prototype use only**
* The system is **not yet hardened for production deployment**
* Some components (NSC VM bytecode compiler) are incomplete

### Implementation Status by Component

| Component | Status | Notes |
|-----------|--------|-------|
| **Triaxis: GHLL** (lexicon, parser, types) | ✅ Implemented | Core grammar and type system complete |
| **Triaxis: GLLL** (codebook, hadamard, mapping, packetizer) | ✅ Implemented | Encoding/decoding pipeline functional |
| **Triaxis: GML** (phaseloom, receipts, replay, trace) | ✅ Implemented | Functionally implemented; receipt signing uses prototype hardcoded keys (see Security) |
| **NSC** (cfa, gates, ir, vm) | ✅ Implemented (caveat) | Implemented; VM currently missing `compile_to_bytecode` utility |
| **CLI** | ❌ Partial | `trace`, `replay`, `verify`, `encode`, `decode` commands are stubs |

This project is in the **research/experimental phase** and not yet suitable for production use.

---

## ⚠️ Security Considerations

**This is a research prototype - not secure for production use.**

Known security issues:

* **Hardcoded Security Keys**: The receipt signing and verification system uses hardcoded keys for prototype demonstration only. These are not suitable for production where cryptographic secrets must be properly managed.

* **Incomplete Validation**: Input validation and boundary checking are not yet comprehensive.

* **Stub Commands**: Several CLI commands (`trace`, `replay`, `verify`, `encode`, `decode`) are incomplete stubs and may not function as expected.

Do not use this code in any security-critical or production environment until these issues are addressed.

---

## Known Issues

The following issues are known and tracked in the prototype:

- Broken imports in `src/cnsc/haai/cli/commands.py` referencing `NSCVirtualMachine`, `compile_to_bytecode`, and `Glyph` which do not currently exist.
- Type/enum inconsistencies across modules and use of bare exception handling in some paths.

---

## Module Structure

This repository contains **two parallel module structures**:

| Path | Purpose | Status |
|------|---------|--------|
| `src/cnsc/haai/` | **Primary implementation** - CLI, Triaxis layers (GHLL, GLLL, GML), NSC execution | Active development |
| `src/cnhaai/` | **Kernel documentation** - Coherence theory specs and documentation | Reference only |
| `cnhaai/` | Standalone documentation project | Legacy |

The main implementation lives under `src/cnsc/haai/`. The `src/cnhaai/` directory contains theoretical documentation related to the coherence kernel.

---

## Philosophy (Why This Exists)

Most AI systems ask:

> *How do we make machines produce intelligent outputs?*

CNSC-HAAI asks:

> *How do we make machines remain coherent, accountable, and correct as they think, act, and change?*

The answer requires:

* constraints
* memory
* identity
* refusal
* receipts
* replay

This repository is an attempt to build that answer—cleanly, rigorously, and without illusion.

---

## Getting Started (Minimal)

```bash
pip install -e .
pytest -q
python -m cnsc.haai.cli.main --help
```

A full "Hello Cognition" end-to-end demo is provided in the integration tests.

> Note: The CLI is partially implemented. Some commands (`trace`, `replay`, `verify`, `encode`, `decode`) are stubs.

---

## Final Note

CNSC-HAAI is not trying to look intelligent.

It is trying to **be trustworthy**.

If you are interested in:

* auditable reasoning
* coherence-first AI
* formal guarantees at runtime
* intelligence that can say "no" and prove why

You're in the right place.

---
