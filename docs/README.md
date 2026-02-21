# CNSC-HAAI Documentation

> **Note:** This is the main documentation index. See also: [Legacy Spine (deprecated)](SPINE.md)

**Version:** 1.0  
**Last Updated:** 2026-02-21

Welcome to the CNSC-HAAI documentation. This is the authoritative source for all project specifications, guides, and references.

## Quick Links

| Section | Description | Files |
|---------|-------------|-------|
| [Spine](spine/) | Core abstraction theory | 24 |
| [ATS](ats/) | Autonomic Transaction System specifications | 40+ |
| [GMI](gmi/) | Global Memory Infrastructure | 20+ |
| [COH-AGI](coh-agi/) | Coherent AGI architecture | 11 |
| [Guides](guides/) | User and developer guides | 6 |
| [Appendices](appendices/) | Reference material, schemas, glossary | 8 |

## Getting Started

1. **New to CNSC-HAAI?** Start with [Spine](spine/00-project-overview.md)
2. **Understanding ATS?** See [ATS Definition](ats/00_identity/ats_definition.md)
3. **Want to build?** Check out the [Guides](guides/00-quick-start.md)

## Project Structure

```
cnsc-haai/
├── src/              # Implementation source code
├── schemas/          # JSON schemas
├── plans/            # Project plans and trackers
├── tests/            # Test suite
└── docs/             # This documentation
    ├── spine/        # Core theory
    ├── ats/          # ATS specifications
    ├── gmi/          # GMI specifications
    ├── coh-agi/      # COH-AGI architecture
    ├── guides/       # User guides
    └── appendices/   # Reference material
```

## Documentation Sections

### [Spine](spine/)
Core abstraction theory and conceptual foundation
- 00-project-overview through 24-failure-modes-and-recovery

### [ATS](ats/)
Autonomic Transaction System specifications
- Identity, Mathematical Core, Coherence Kernel, Runtime, Integration, Security, Test Vectors

### [GMI](gmi/)
Global Memory Infrastructure
- Formal model, Predictor Layer, Execution Layer, Cryptographic Layer

### [COH-AGI](coh-agi/)
Coherent AGI architecture overview
- Overview, ATS Summary, Receipts and Slabs, Autonomic Regulation

### [Guides](guides/)
User and developer guides
- Quick start, Creating abstraction ladders, Developing gates, Implementing receipts

### [Appendices](appendices/)
Reference material
- Terminology, Axioms, Receipt Schema, Minimal Kernel, Glossary

## Related Documentation

- [Plans](../plans/README.md) - Project plans and TODO tracker
- [Schemas](../schemas/) - JSON schema definitions
- [CHANGELOG](../CHANGELOG.md) - Version history

## Legacy Documentation

- [docs/legacy/](../docs/legacy/) - Old v1.0 specifications
- [docs/spec/](../docs/spec/) - Old system specifications (deprecated)
- [docs/architecture/](../docs/architecture/) - Architecture documentation
