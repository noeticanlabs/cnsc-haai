# Documentation Architecture

**Status:** Canonical

## Overview

This document explains the CNHAAI documentation structure and how different documentation directories relate to each other.

## Directory Structure

```
cnsc-haai/
├── docs/ats/               # ATS Kernel Documentation (canonical)
│   ├── 00_identity/       # Project identity and ATS definition
│   ├── 10_mathematical_core/  # Core mathematical objects
│   ├── 20_coh_kernel/     # Coh kernel implementation
│   ├── 30_ats_runtime/    # ATS runtime specifications
│   ├── 40_nsc_integration/ # NSC to ATS bridging
│   ├── 50_security_model/ # Security and adversary model
│   ├── 60_test_vectors/   # Test vectors for CI
│   └── 90_roadmap/        # Future research directions
│
├── spec/                    # Technical specifications (canonical)
│   ├── ghll/               # GHLL language spec
│   ├── glll/               # GLLL encoding spec
│   ├── nsc/                # NSC runtime spec
│   ├── gml/                # GML trace/receipt spec
│   └── seam/               # Layer seam contracts
│
├── cnhaai/docs/            # Theory and learning path
│   ├── spine/              # Ordered learning modules (00-24)
│   └── appendices/         # Reference appendices
│
├── examples/               # End-to-end examples
│   ├── end_to_end/         # Complete walkthroughs
│   ├── ghll/               # GHLL examples
│   ├── glll/               # GLLL examples
│   └── gml/                # GML examples
│
└── docs/                   # Legacy docs (deprecated)
    └── ...                 # Use spec/ and cnhaai/docs/ instead
```

## Documentation Categories

| Category | Location | Purpose | Audience |
|----------|----------|---------|----------|
| **ATS Kernel** | `docs/ats/` | Admissible Trajectory Space kernel specification | System architects |
| **Specs** | `spec/` | Implementation reference | Developers |
| **Theory** | `cnhaai/docs/spine/` | Learning path | New contributors |
| **Reference** | `cnhaai/docs/appendices/` | Quick reference | All users |
| **Examples** | `examples/` | Tutorials | Learners |
| **Legacy** | `docs/` | Archived | Migration only |

## Relationship Between Docs

```
cnhaai/docs/spine/      spec/               examples/
     │                     │                     │
     ▼                     ▼                     ▼
  Theory ─────────────► Spec ─────────────► Examples
     │                     │                     │
     │    ┌────────────────┘                     │
     │    │                                      │
     └────┴──────────────────────────────────────┘
          │
          ▼
   cnhaai/docs/appendices/
          │
          ▼
      Reference
```

## Mapping Between Spec and Spine

| Spec File | Spine Module | Description |
|-----------|--------------|-------------|
| `spec/ghll/` | Modules 01-09 | GHLL language |
| `spec/glll/` | Modules 00-08 | GLLL encoding |
| `spec/nsc/` | Modules 01-10 | NSC runtime |
| `spec/gml/` | Modules 01-08 | GML trace |
| `spec/seam/` | Module 07 | Seam contracts |

## Mapping Between ATS and System Components

| ATS Document | System Component | Description |
|--------------|------------------|-------------|
| `docs/ats/00_identity/` | Project Identity | ATS as the kernel |
| `docs/ats/10_mathematical_core/` | Core Math | X, A, V, B definitions |
| `docs/ats/20_coh_kernel/` | Kernel | RV, serialization, receipts |
| `docs/ats/30_ats_runtime/` | Runtime | Execution and verification |
| `docs/ats/40_nsc_integration/` | NSC Bridge | Hosting cognitive systems |
| `docs/ats/50_security_model/` | Security | Adversary model, determinism |
| `docs/ats/60_test_vectors/` | Testing | CI test vectors |
| `docs/ats/90_roadmap/` | Future | Research directions |

## Choosing Which Doc to Use

| Question | Answer | Use This |
|----------|--------|----------|
| What is ATS and how does it work? | Start here | `docs/ats/00_identity/ats_definition.md` |
| I want to learn CNHAAI | Start here | `cnhaai/docs/spine/00-project-overview.md` |
| I need to implement ATS kernel | Go deep | `docs/ats/20_coh_kernel/rv_step_spec.md` |
| I need to implement a feature | Go deep | `spec/` |
| I need a quick reference | Look up | `cnhaai/docs/appendices/` |
| I want a complete example | Follow | `examples/end_to_end/` |
| I'm maintaining old code | Migrate | `docs/` (deprecated) |

## Contributing to Docs

1. **ATS kernel specs** → Add to `docs/ats/`
2. **New specs** → Add to `spec/`
3. **Theory/explanation** → Add to `cnhaai/docs/spine/`
4. **Reference material** → Add to `cnhaai/docs/appendices/`
5. **Tutorials** → Add to `examples/`

## Deprecation Policy

Old documentation is marked with:
```
> **DEPRECATED**: Use [current location] instead.
```

Migration guides are provided in:
- [`Coherence_Spec_v1_0/README.md`](Coherence_Spec_v1_0/README.md)
- This file

## See Also

- ATS Kernel definition: [`docs/ats/00_identity/ats_definition.md`](docs/ats/00_identity/ats_definition.md)
- ATS RV Specification: [`docs/ats/20_coh_kernel/rv_step_spec.md`](docs/ats/20_coh_kernel/rv_step_spec.md)
- Project overview: [`cnhaai/docs/spine/00-project-overview.md`](cnhaai/docs/spine/00-project-overview.md)
- Quick start: [`cnhaai/docs/guides/00-quick-start.md`](cnhaai/docs/guides/00-quick-start.md)
