# Package Namespace Architecture

## Overview

This document describes the package structure of CNsc-HAAI and clarifies the naming conventions.

## Current Package Structure

```
src/
├── cnhaai/           # Abstraction layer (legacy, standalone)
│   └── core/
│       ├── abstraction.py
│       ├── coherence.py
│       ├── gates.py
│       ├── phases.py
│       └── receipts.py
│   └── kernel/
│       └── minimal.py
│
├── cnsc/             # CLI entry point (namespace package)
│   └── haai/        # Main application modules
│       ├── ats/     # ATS kernel types & verification
│       ├── cli/     # Command-line interface
│       ├── ghll/    # Glyphic High-Level Language
│       ├── glll/    # Glyphic Low-Level Language
│       ├── gml/     # Governance Metadata Language
│       ├── graphgml/ # Graph representation
│       ├── nsc/     # Network Structured Code (VM, IR, gates)
│       └── tgs/     # Temporal Governance System
│
├── cnsc_haai/       # Consensus kernel (underscore variant)
│   ├── ats/
│   │   └── verifier_state.py
│   └── consensus/
│       ├── autonomic.py
│       ├── chain.py
│       ├── codec.py
│       ├── compat.py
│       ├── continuous.py
│       ├── finalize.py
│       ├── fraudproof.py
│       ├── hash.py
│       ├── jcs.py
│       ├── merkle.py
│       ├── retention.py
│       ├── slab.py
│       └── topology.py
│
└── npe/             # Network Proposal Engine
    ├── api/         # HTTP/WS API
    ├── cli/         # CLI commands
    ├── core/        # QFixed18, canonicalization, PRNG
    ├── proposers/   # Proposal generators
    ├── registry/    # Proposer registry
    ├── retrieval/   # Corpus/codebook retrieval
    ├── rv/         # Receipt verification
    ├── schemas/     # JSON schemas
    └── scoring/     # Candidate ranking
```

## Naming Rationale

| Package | Style | Reason |
|---------|-------|--------|
| `cnsc/haai` | Namespace (dot) | CLI application, hierarchical modules |
| `cnsc_haai` | Underscore | Consensus kernel - follows Python PEP8 for modules |
| `cnhaai` | Legacy | Original project name, kept for compatibility |
| `npe` | Short | Network Proposal Engine - main subsystem |

## Import Patterns

### For Consensus Kernel (chain, merkle, slab, etc.)
```python
from cnsc_shaai.consensus.chain import chain_hash_v1
from cnsc_shaai.consensus.merkle import MerkleTree
```

### For ATS/RV Verification
```python
from cnsc.haai.ats.types import State, Receipt
from cnsc.haai.ats.rv import ReceiptVerifier
```

### For NSC/VM Execution
```python
from cnsc.haai.nsc.vm import VM
from cnsc.haai.nsc.ir import NSCProgram
```

### For GHLL Parsing
```python
from cnsc.haai.ghll.parser import parse_ghll
from cnsc.haai.ghll.types import TypeChecker
```

### For NPE Operations
```python
from npe.core.qfixed18 import q18_mul, q18_div
from npe.rv.verify_proposal import verify_proposal
```

## Migration Notes

### Why Both `cnsc/` and `cnsc_haai/`?

- `cnsc/haai` uses Python's namespace package feature (implicit)
- `cnsc_haai` uses traditional package with `__init__.py`

This was an organic growth decision. Both patterns work but mixing them creates confusion.

### Future Consolidation

If the project decides to consolidate, the recommended approach would be:

1. Move `cnsc_haai/*` → `cnsc/haai/consensus/`
2. Move `cnsc/haai/ats/*` → `cnsc/haai/ats/`
3. Deprecate `cnhaai/` package
4. Use consistent namespace packages throughout

This is a **breaking change** requiring:
- Full import path updates
- CI/CD pipeline changes
- Documentation updates
- Migration guide for users

## Running the CLI

```bash
# Using python -m
python -m cnsc.haai --help

# Or using the cnsc-haai entry point (if installed)
cnsc-haai --help
```
