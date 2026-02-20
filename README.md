# CNSC-HAAI

## Coherence-Native, Safety-Constrained Hybrid Artificial Intelligence

> *"Intelligence is not prediction. Intelligence is staying coherent while changing."*

---

## Executive Summary

CNSC-HAAI is a **coherence-native cognitive runtime** engineered for **auditable, deterministic, and constraint-governed intelligence**. It represents a fundamental architectural shift from probability-optimized systems to coherence-optimized computation.

CNSC-HAAI is **not** a language model. It is **not** a prompt-driven agent. It is **not** a black box.

Instead, CNSC-HAAI is a **composable intelligence substrate** where reasoning is constrained by explicit invariants, decisions are logged as cryptographic receipts, execution is fully replayable, violations are detected (not narrated), and coherence is enforced through mathematical guarantees rather than heuristic approximations.

---

## Core Design Philosophy

### The Coherence Imperative

Where conventional AI systems optimize for:
- Next-token probability
- Reward signals  
- Surface plausibility

CNSC-HAAI optimizes for:
- **Structural coherence** — Internal consistency of the knowledge graph
- **Temporal consistency** — Preservation of state across phases
- **Constraint preservation** — Enforcement of explicit invariants
- **Causal accountability** — Full traceability of decision chains

This single philosophical shift fundamentally transforms every aspect of the system's architecture, from the lowest-level bytecode to the highest-level user interface.

---

## Architectural Overview

CNSC-HAAI implements a **Triaxis architecture** combining three abstraction layers with a deterministic execution substrate and a mathematically-verified coherence kernel.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         INTERFACE LAYER                                  │
│            CLI / HTTP API / LLM Proposal Adapters                       │
├─────────────────────────────────────────────────────────────────────────┤
│                          TRIAXIS LAYERS                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        │
│  │  GHLL           │  │  GLLL           │  │  GML            │        │
│  │  (Meaning)      │  │  (Integrity)    │  │  (Forensics)    │        │
│  │  Typed grammar  │  │  Reversible     │  │  Trace, receipts│        │
│  │  & semantic     │  │  packetization  │  │  & replay       │        │
│  │  constraints    │  │  & encoding     │  │  verification   │        │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘        │
├─────────────────────────────────────────────────────────────────────────┤
│                    NSC EXECUTION SUBSTRATE                              │
│         IR / VM / Control Flow Automaton / Gates / Rails               │
│              Executes GHLL → produces GML receipts                     │
├─────────────────────────────────────────────────────────────────────────┤
│                     COHERENCE KERNEL (ATS)                              │
│    Budget Law / Risk Functional / Receipt Verifier / Phased Exec      │
└─────────────────────────────────────────────────────────────────────────┘
```

### The Triaxis

| Layer | Purpose | Key Properties |
|-------|---------|-----------------|
| **GHLL** (Graphical Hypertext Linking Language) | Semantic representation | Typed grammar, semantic constraints, rewrite operators |
| **GLLL** (Graphical Low-Level Language) | Data integrity | Hadamard encoding, noise tolerance, reversible packetization |
| **GML** (Graph Machine Language) | Operational forensics | Trace model, receipt chains, checkpoint backtracking |

### Core Runtime Components

| Component | Description | Consensus-Critical |
|-----------|-------------|-------------------|
| **NSC** (Noetica Symbolic Code) | Execution substrate with IR, VM, CFA, gates, and rails | ✅ Yes |
| **ATS/Coh Kernel** | Deterministic receipt verification, budget enforcement | ✅ Yes |
| **TGS** (Time Governor System) | Debug/telemetry, phase management | ❌ No |
| **CNHAAI Core** | Heuristic coherence scoring (UI only) | ❌ No |
| **NPE** (Neural Planning Engine) | Coherence-constrained proposal generation | ✅ Yes |

---

## Foundational Concepts

### The Principle of Coherence

The **Principle of Coherence (PoC)** states that all state transitions in a cognitive system must preserve system invariants. In the ATS context, PoC manifests as:

- **Risk Monotonicity**: V(x_{k+1}) ≤ V(x_k) + κ·B_k — risk cannot explode uncontrollably
- **Budget Boundedness**: Cumulative positive risk delta is bounded by initial budget
- **Deterministic Verifiability**: Every step can be independently verified without ambiguity

### Gates and Rails

**Gates** are runtime checks with formal guarantees — they enforce invariants at decision points. Each gate evaluation produces a receipt documenting:

- What assumptions were checked
- Which witnesses were used
- What contract allowed the action

**Rails** are execution pathways with bounded behavior — they constrain the space of possible transitions to a safe subspace.

### Receipts as First-Class Artifacts

Every meaningful operation in CNSC-HAAI produces a **receipt** — a cryptographic record containing:

- **Chain hash** — Cryptographic linkage to previous receipts
- **Merkle root** — Integrity verification of micro-receipts
- **Budget deltas** — Risk accumulation tracking
- **Witness data** — Formal proofs of constraint satisfaction

Receipts enable:
- Forensic analysis after the fact
- Exact replay of any execution
- Comparison against prior runs
- Trustless verification by third parties

---

## Key System Properties

### 1. Determinism by Default

Given identical inputs, configuration, and system state:
- The same execution path occurs
- The same receipts are produced
- The same replay verification succeeds

This is **not optional** and **not heuristic**. Determinism is enforced through the deterministic numeric domain (QFixed arithmetic) and canonical serialization (JCS).

### 2. Constraints as Runtime Law

Rules are not prompts. Policies are not suggestions. Constraints exist as:

- **Gates**: Formal runtime checks with mathematical guarantees
- **Rails**: Execution pathways enforcing bounded behavior  
- **Invariants**: Properties that must hold throughout execution
- **Budget Law**: Cumulative risk bounded by initial allocation

### 3. No Float in Consensus

CNSC-HAAI prohibits floating-point arithmetic in consensus-critical paths. All numeric computation uses **QFixed** — deterministic fixed-point arithmetic with known precision bounds.

### 4. Proof-Anchored Verification

Named **Gate Contracts** bind formal theorems to runtime-checkable assumptions, producing certified guarantees logged as receipts. The receipt verifier (RV) performs deterministic verification of every step.

---

## System Capabilities

### End-to-End Workflow

```
GLLL Encoding → GHLL Parsing → NSC Execution → GML Receipts → Replay Verification
     ↑                                                                      │
     └──────────────────────────────────────────────────────────────────────┘
```

1. **Input Encoding** (GLLL): High-fidelity, noise-tolerant encoding using Hadamard basis
2. **Semantic Parsing** (GHLL): Typed grammar parsing with rewrite operators and guards
3. **Execution** (NSC): Control Flow Automaton (CFA) processes rewrite graphs
4. **Receipt Emission** (GML): Chain-linked receipts with Merkle verification
5. **Verification** (ATS): Deterministic replay and audit

### The NPE (Neural Planning Engine)

The NPE is an external proposer service that handles proposal generation and repair operations under coherence constraints. It provides:

- Template-based plan generation
- Receipt summarization and repair
- Rule atomic safety verification
- Coherence-constrained reasoning

---

## Project Structure

```
cnsc-haai/
├── src/
│   ├── cnsc/haai/              # Primary implementation
│   │   ├── ats/                # ATS Kernel (receipts, budget, risk, verifier)
│   │   ├── ghll/               # GHLL compiler (lexicon, parser, types)
│   │   ├── glll/               # GLLL codec (hadamard, codebook, packetizer)
│   │   ├── gml/                # GML (trace, receipts, replay, phaseloom)
│   │   ├── graphgml/           # Graph-based GML for structural relations
│   │   ├── nsc/                # NSC runtime (VM, CFA, gates, IR)
│   │   ├── tgs/                # TGS (debug/telemetry - NOT consensus)
│   │   └── cli/                # Command-line interface
│   ├── cnhaai/                 # Coherence kernel (UI-only heuristics)
│   │   └── core/               # abstraction, coherence, gates, phases, receipts
│   ├── cnsc_haai/              # Legacy consensus layer
│   │   └── consensus/          # Chain, merkle, slab, finalize, fraudproof
│   └── npe/                    # Neural Planning Engine
│       ├── api/                # HTTP/Unix socket server
│       ├── core/               # Budgets, canon, hashing, time, types
│       ├── proposers/           # Proposal generation with coherence
│       ├── retrieval/           # Corpus, codebook, query, receipts store
│       └── scoring/            # Ranking and pruning algorithms
├── spec/                       # Detailed specifications
│   ├── ghll/                   # GHLL design principles, grammar, type system
│   ├── glll/                   # GLLL threat model, hadamard, codebook
│   ├── gml/                    # GML trace model, phases, receipts
│   ├── nsc/                    # NSC goals, packet format, CFA, VM
│   ├── graphgml/               # GraphGML specification
│   └── seam/                   # Cross-layer contracts
├── docs/ats/                   # ATS specification (canonical)
│   ├── 00_identity/            # Project identity and scope
│   ├── 10_mathematical_core/  # Action algebra, admissibility, budgets
│   ├── 20_coh_kernel/          # Chain hash, merkle, serialization
│   ├── 30_ats_runtime/        # Budget transitions, replay, state digest
│   ├── 40_nsc_integration/    # NSC-to-ATS bridge, policy constraints
│   ├── 50_security_model/     # Adversary model, float prohibition
│   └── 60_test_vectors/        # Deterministic replay traces
├── compliance_tests/           # Test suites for all components
├── examples/end_to_end/        # Comprehensive usage examples
├── schemas/                    # JSON schemas for data formats
└── plans/                      # Implementation roadmaps
```

---

## Installation

```bash
# Clone the repository
git clone https://github.com/your-org/cnsc-haai.git
cd cnsc-haai

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Run tests (requires PYTHONPATH)
PYTHONPATH=./src pytest -v

# Verify installation
PYTHONPATH=./src python -m cnsc.haai --help
```

---

## Quick Start

### CLI Usage

```bash
PYTHONPATH=./src python -m cnsc.haai --help
```

### NPE Server

```bash
# Start the NPE HTTP server (default: 127.0.0.1:8080)
PYTHONPATH=./src python -m npe.api.server

# Or use the CLI
cd src/npe && pip install -e . && npe serve
```

### End-to-End Examples

See the [`examples/end_to_end/`](examples/end_to_end/) directory:

| Example | Description |
|---------|-------------|
| [`00_glll_encode_decode.md`](examples/end_to_end/00_glll_encode_decode.md) | GLLL encoding/decoding with noise tolerance |
| [`01_ghll_parse_rewrite.md`](examples/end_to_end/01_ghll_parse_rewrite.md) | GHLL parsing and rewrite operator application |
| [`02_nsc_cfa_run.md`](examples/end_to_end/02_nsc_cfa_run.md) | NSC execution with Control Flow Automaton |
| [`03_gml_trace_audit.md`](examples/end_to_end/03_gml_trace_audit.md) | GML trace generation and audit verification |

---

## Test Coverage

| Suite | Coverage | Status |
|-------|----------|--------|
| GraphGML | 148 tests | ✅ Pass |
| TGS | 39 tests | ✅ Pass |
| Other Components | ~735 tests | ✅ Pass |
| **Total** | **922+ tests** | ✅ All Passing |

---

## Documentation

### Specification Hierarchy

1. **ATS Specifications** ([`docs/ats/`](docs/ats/)) — Canonical mathematical specifications
   - Identity and scope definitions
   - Mathematical core (action algebra, admissibility, budgets)
   - Coherence kernel (chain hash, merkle, serialization)
   - Runtime specifications
   - Security model

2. **Component Specifications** ([`spec/`](spec/)) — Detailed design documents
   - GHLL: Grammar, type system, rewrite operators
   - GLLL: Hadamard encoding, codebook format
   - GML: Trace model, receipt specification
   - NSC: VM, CFA, gates and rails
   - Seam: Cross-layer contracts

3. **SPINE Documentation** ([`cnhaai/docs/`](cnhaai/docs/)) — Legacy (deprecated)
   - *Note: Migrated to `docs/ats/` as of 2026-02-20*

### Key Terminology

| Term | Definition |
|------|------------|
| **ATS** | Admissible Trajectory Space — Mathematical framework for bounded cognitive computation |
| **Coh** | Principle of Coherence — Invariant preservation across state transitions |
| **QFixed** | Deterministic fixed-point arithmetic (no floats in consensus) |
| **JCS** | JSON Canonicalization Scheme — Deterministic serialization |
| **CFA** | Control Flow Automaton — NSC execution model |
| **Gate Contract** | Formal binding of theorems to runtime-checkable assumptions |
| **Chain Hash** | Cryptographic linkage of receipts in temporal sequence |
| **Merkle Root** | Digest of micro-receipts enabling partial verification |

---

## Contributing

Contributions are welcome. Please ensure:

- All tests pass (`PYTHONPATH=./src pytest -v`)
- Type hints on all function signatures
- Docstrings for public modules, functions, and classes
- No floating-point arithmetic in consensus-critical paths

### Development Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e .

# Run tests with coverage
PYTHONPATH=./src pytest --cov=src/cnsc/haai

# Run specific test suites
PYTHONPATH=./src pytest compliance_tests/ -v
```

---

## License

Apache License 2.0 — see the [LICENSE](LICENSE) file for details.

---

## Citation

If you use CNSC-HAAI in research, please cite:

```bibtex
@misc{cnsc-haai,
  title = {CNSC-HAAI: Coherence-Native, Safety-Constrained Hybrid Artificial Intelligence},
  author = {NoeticanLabs},
  year = {2026},
  url = {https://github.com/your-org/cnsc-haai}
}
```

---

## Acknowledgments

- NoeticanLabs for the original Coherence Framework
- Research partners and contributors
- The formal methods community for verification techniques

---

## Version Information

| Component | Version | Status |
|-----------|---------|--------|
| CNSC-HAAI | 1.0.0 | Canonical |
| Principle of Coherence | v1.0 | Required |
| NSC Specification | v1.0 | Required |
| GHLL Specification | v1.0 | Required |
| GLLL Specification | v1.0 | Required |
| GML Specification | v1.0 | Required |
| Seam Contract | v1.0 | Required |
