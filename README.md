# CNSC-HAAI

**Coherence-Native, Safety-Constrained Hybrid Artificial Intelligence**

> *Intelligence is not prediction. Intelligence is staying coherent while changing.*

---

## What is CNSC-HAAI?

CNSC-HAAI is a **coherence-native cognitive runtime** designed for **auditable, deterministic, and constraint-governed intelligence**.

It is **not** a language model. It is **not** a prompt-driven agent. It is **not** a black box.

Instead, CNSC-HAAI is a **composable intelligence substrate** where:
- Reasoning is **constrained by explicit invariants**
- Decisions are **logged as receipts**
- Execution is **replayable**
- Violations are **detected, not narrated**
- Coherence is **enforced, not hoped for**

CNSC-HAAI is built for **trustable intelligence at personal and small-scale deployment**, where correctness, explainability, and persistence matter more than fluency.

---

## Core Design Principle

> **Coherence is the primary objective, not likelihood.**

Where most AI systems optimize for:
- Next-token probability
- Reward signals
- Surface plausibility

CNSC-HAAI optimizes for:
- **Structural coherence**
- **Temporal consistency**
- **Constraint preservation**
- **Causal accountability**

This single shift changes everything.

---

## Architecture Overview

CNSC-HAAI combines **Triaxis** (the three-layer abstraction hierarchy) with **NSC** (the execution substrate) and **CNHAAI** (the coherence kernel).

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

### Core Components

| Component | Description |
|-----------|-------------|
| **GHLL** (Graphical Hypertext Linking Language) | Typed grammar & semantic constraints for meaning representation |
| **GLLL** (Graphical Low-Level Language) | Reversible packetization & encoding for integrity |
| **GML** (Graph Machine Language) | Trace, receipts, and replay verification for forensics |
| **NSC** (Neural State Controller) | Execution substrate with IR, VM, gates, and rails |
| **TGS** (Time Governor System) | Temporal governance and bounded execution |
| **NPE** (Neural Planning Engine) | Planning and reasoning with coherence constraints |

---

## Key Features

### 1. Determinism by Default
Given the same inputs, configuration, and state:
- The same execution path occurs
- The same receipts are produced
- The same replay verifies

This is **not optional** and **not heuristic**.

### 2. Constraints Are Runtime Law
Rules are not prompts. Policies are not suggestions. Constraints live as:
- **Gates**: Runtime checks with formal guarantees
- **Rails**: Execution pathways with bounded behavior
- **Invariants**: Properties that must hold throughout execution

### 3. Receipts, Not Explanations
CNSC-HAAI records:
- What assumptions were checked
- Which gate was evaluated
- What witnesses were used
- Which contract allowed the action

This enables forensic analysis, audit, replay, rollback, and trust.

### 4. Replayable Intelligence
Any execution can be:
- Replayed
- Verified
- Compared against prior runs
- Audited after the fact

### 5. Proof-Anchored Gates
Named Gate Contracts bind formal theorems to runtime-checkable assumptions, producing certified guarantees logged as receipts.

---

## Installation

```bash
# Clone the repository
git clone https://github.com/your-org/cnsc-haai.git
cd cnsc-haai

# Install dependencies
pip install -e .

# Run tests
pytest -q

# Verify installation
python -m cnsc.haai --help
```

---

## Quick Start

### Basic Usage

```bash
# View help
python -m cnsc.haai --help

# Run the NPE server
python -m npe.api.server

# Or using the CLI
npe serve
```

### End-to-End Examples

See the [`examples/end_to_end/`](examples/end_to_end/) directory for comprehensive examples:
- [`00_glll_encode_decode.md`](examples/end_to_end/00_glll_encode_decode.md) - GLLL encoding/decoding
- [`01_ghll_parse_rewrite.md`](examples/end_to_end/01_ghll_parse_rewrite.md) - GHLL parsing and rewriting
- [`02_nsc_cfa_run.md`](examples/end_to_end/02_nsc_cfa_run.md) - NSC execution with CFA
- [`03_gml_trace_audit.md`](examples/end_to_end/03_gml_trace_audit.md) - GML trace and audit

---

## Project Structure

```
cnsc-haai/
├── spec/              # Detailed specifications for all components
├── src/
│   ├── cnsc/haai/     # Primary implementation (CLI, Triaxis, NSC)
│   ├── cnhaai/        # Coherence kernel documentation
│   └── npe/           # Neural Planning Engine
├── compliance_tests/  # Test suites for all components
├── examples/          # End-to-end usage examples
├── docs/              # Architecture and documentation
├── Coherence_Spec_v1_0/  # Coherence framework documentation
└── schemas/           # JSON Schemas for data formats
```

---

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting pull requests.

### Development Setup

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=src/cnsc/haai
```

### Code Style

- Follow PEP 8 guidelines
- Use type hints for all function signatures
- Write docstrings for all public modules, functions, and classes
- Ensure all tests pass before submitting

---

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

---

## Contact

- **Repository**: https://github.com/your-org/cnsc-haai
- **Issues**: Please use the GitHub issue tracker
- **Discussions**: Use GitHub Discussions for questions and ideas

---

## Acknowledgments

- NoeticanLabs for the original Coherence Framework
- Research partners and contributors
- The formal methods community for verification techniques

---

## Citation

If you use CNSC-HAAI in your research, please cite:

```bibtex
@misc{cnsc-haai,
  title = {CNSC-HAAI: Coherence-Native, Safety-Constrained Hybrid Artificial Intelligence},
  author = {NoeticanLabs},
  year = {2026},
  url = {https://github.com/your-org/cnsc-haai}
}
```
