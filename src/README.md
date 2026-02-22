# CNsc-HAAI Source Code

This directory contains the complete implementation of the CNsc-HAAI (Coh-Compliant Admissible Trajectory Space Kernel) system.

## Project Structure

```
src/
├── cnhaai/           # Legacy abstraction layer
├── cnsc/             # Main CLI application
│   └── haai/        # Core modules (ATS, NSC, GHLL, GML, TGS)
├── cnsc_haai/       # Consensus kernel
│   └── consensus/   # Chain, Merkle, Slab, Finalization
└── npe/             # Network Proposal Engine
```

## Quick Start

### Running Tests

```bash
# Run all tests
PYTHONPATH=./src pytest -q

# Run specific test module
PYTHONPATH=./src pytest tests/ -v

# Run with coverage
PYTHONPATH=./src pytest --cov=src --cov-report=html
```

### Running the CLI

```bash
# Start NPE server
PYTHONPATH=./src python -m npe.api.server

# Use CLI
PYTHONPATH=./src python -m cnsc.haai --help

# Run specific commands
python -m cnsc.haai parse --file example.ghll
python -m cnsc.haai compile --input program.nsc
python -m cnsc.haai run --bytecode program.bin
```

### Using NPE API

```bash
# Start server
PYTHONPATH=./src python -m npe.api.server

# Submit proposal request
curl -X POST http://localhost:8080/propose \
  -H "Content-Type: application/json" \
  -d @examples/proposal_request.json
```

## Module Overview

### Consensus Kernel (`cnsc_haai/consensus/`)

The consensus kernel provides deterministic cryptographic primitives:

| Module | Description |
|--------|-------------|
| `chain.py` | Receipt chain hashing (SHA256 typed prefixes) |
| `merkle.py` | Merkle tree construction and proof verification |
| `slab.py` | Slab buffer and registry management |
| `finalize.py` | Slab finalization and receipt creation |
| `fraudproof.py` | Dispute handling and fraud proof verification |
| `jcs.py` | RFC 8785 JSON Canonicalization |
| `hash.py` | SHA256 utilities with domain separation |
| `topology.py` | Topology change detection and hysteresis |
| `retention.py` | Slab retention policies |
| `autonomic.py` | Autonomic state management |

### NPE - Network Proposal Engine (`npe/`)

The NPE generates proposals and repairs for cognitive operations:

| Module | Description |
|--------|-------------|
| `core/qfixed18.py` | QFixed18 fixed-point arithmetic (2^18 scale) |
| `core/canon.py` | CJ0 canonical serialization |
| `core/prng_chacha20.py` | Deterministic ChaCha20 PRNG |
| `core/binary_parser.py` | Delta program binary parsing |
| `core/delta_program.py` | Delta program opcodes and certificates |
| `rv/verify_proposal.py` | Receipt verification pipeline |
| `api/server.py` | HTTP/Unix socket API server |
| `proposers/gr/` | Governance/repair proposers |
| `retrieval/` | Corpus, codebook, and evidence retrieval |
| `scoring/` | Candidate ranking and pruning |

### NSC - Network Structured Code (`cnsc/haai/nsc/`)

NSC provides a bytecode VM for executing cognitive programs:

| Module | Description |
|--------|-------------|
| `vm.py` | Stack-based bytecode VM (757 lines) |
| `ir.py` | Intermediate representation (500+ lines) |
| `cfa.py` | Control flow automaton |
| `gates.py` | Gate evaluation (EvidenceSufficiency, CoherenceCheck) |
| `proposer_client.py` | NPE service client |

### GHLL - Glyphic High-Level Language (`cnsc/haai/ghll/`)

GHLL is a typed language for cognitive operations:

| Module | Description |
|--------|-------------|
| `parser.py` | Lexer and parser (1100+ lines) |
| `lexicon.py` | Parse forms and lexicon manager |
| `types.py` | Type system with checker (677+ lines) |

### GML - Governance Metadata Language (`cnsc/haai/gml/`)

GML manages execution traces and receipts:

| Module | Description |
|--------|-------------|
| `phaseloom.py` | Phase threading and coupling |
| `receipts.py` | Receipt system (1200+ lines) |
| `replay.py` | Replay engine and verification |
| `trace.py` | Trace event management |

### TGS - Temporal Governance System (`cnsc/haai/tgs/`)

TGS enforces temporal constraints and coherence:

| Module | Description |
|--------|-------------|
| `clock.py` | Multiple clock types: Consistency, Commitment, Causality, Resource, Taint, Drift (500+ lines) |
| `governor.py` | Temporal governance engine |
| `rails.py` | Coherence rail evaluation |
| `receipt.py` | Receipt emission |
| `snapshot.py` | State snapshot management |

### ATS - Admissible Trajectory Space (`cnsc/haai/ats/`)

ATS defines the mathematical kernel:

| Module | Description |
|--------|-------------|
| `types.py` | State, Action, Receipt, Budget types |
| `numeric.py` | QFixed implementation with overflow checking |
| `risk.py` | Risk functional V computation |
| `rv verifier |
| `budget.py` |.py` | Receipt Budget manager |
| `bridge.py` | GML ↔ ATS bridge |

## Key Design Principles

1. **Determinism**: All operations must be reproducible. No floating-point, no random values without seed.
2. **Type Safety**: Full type hints throughout, validated with mypy.
3. **Canonical Serialization**: All data structures use RFC 8785 JCS for deterministic hashing.
4. **Fixed-Point Arithmetic**: QFixed18 (2^18 = 262,144 scale) for all numeric operations.
5. **Receipt Verification**: Every state transition carries a machine-verifiable receipt.

## Development

### Setup Virtual Environment

```bash
make venv
# or manually:
python -m venv venv
source venv/bin/activate
pip install -e .
pip install pytest pytest-cov black flake8 mypy
```

### Code Quality

```bash
# Lint
make lint

# Format
black src/

# Type check
mypy src/
```

## See Also

- [Package Structure](PACKAGE_STRUCTURE.md) - Detailed namespace documentation
- [../docs/ats/](../docs/ats/) - ATS mathematical specifications
- [../docs/architecture/](../docs/architecture/) - Architecture documentation
