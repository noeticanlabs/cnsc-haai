# CNHAAI - Coherence Noetican Hierarchical Abstraction AI

**A governed reasoning system for deep, reliable AI**

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-1.0.0-green.svg)](VERSION.md)

## What is CNHAAI?

CNHAAI is an AI architecture that addresses the fundamental problem of **unbounded abstraction drift** - the tendency of AI systems to lose coherence across long reasoning chains.

### Key Features

- **Governed Abstraction**: Every abstraction is bound by explicit constraints
- **Structural Anti-Hallucination**: Hallucination is prevented by design
- **Complete Auditability**: Every decision has a cryptographic receipt
- **Graceful Degradation**: Systems fail safely, not catastrophically

## Quick Start

```python
from cnhaai import MinimalKernel

kernel = MinimalKernel()
episode = kernel.execute_episode(goal="diagnosis", evidence=[...])
receipts = kernel.get_receipts(episode.id)
```

## Documentation

### Core Documentation

| Module | Topic | Lines |
|--------|-------|-------|
| [00](docs/spine/00-project-overview.md) | Project Overview | ~650 |
| [01](docs/spine/01-problem-statement.md) | Problem Statement | ~700 |
| [02](docs/spine/02-vision-and-mission.md) | Vision and Mission | ~650 |
| [03](docs/spine/03-core-definition.md) | Core Definition | ~700 |
| [04](docs/spine/04-design-principles.md) | Design Principles | ~700 |
| [05-11](docs/spine/) | Abstraction Theory | ~7500 |
| [12-14](docs/spine/) | Coherence | ~2100 |
| [15-18](docs/spine/) | Gates and Rails | ~2700 |
| [19-22](docs/spine/) | Runtime | ~2700 |
| [23-24](docs/spine/) | Advanced Topics | ~1400 |

### References

- [Spine Index](docs/SPINE.md) - Complete navigation guide
- [Appendices](docs/appendices/) - Terminology, axioms, schemas, examples
- [Guides](docs/guides/) - How-to guides and tutorials
- [Implementation](implementation/) - Kernel specifications

## Architecture

```
GLLL → GHLL → NSC → GML
```

- **GLLL**: Glyphic Low-Level Language (binary encoding)
- **GHLL**: Glyphic High-Level Language (rewrite language)
- **NSC**: Network Structured Code (intermediate representation)
- **GML**: Governance Metadata Language (trace and audit)

## The Principle of Coherence

All CNHAAI systems are governed by the Principle of Coherence (PoC):

> All abstractions must maintain internal consistency, consistency with evidence, consistency across layers, and temporal consistency.

### PoC Lemmas

1. **Affordability**: Abstractions must have sufficient evidence
2. **No-Smuggling**: Information cannot bypass coherence checks
3. **Hysteresis**: Degradation must be gradual
4. **Termination**: Reasoning must terminate
5. **Cross-Level**: Vertical consistency must be maintained
6. **Descent**: Recovery to lower levels must be possible
7. **Replay**: All reasoning must be reproducible

## Contributing

1. Read the [Spine Index](docs/SPINE.md)
2. Review the [Design Axioms](docs/appendices/appendix-b-axioms.md)
3. Check [open issues](https://github.com/noeticanlabs/cnsc-haai/issues)
4. Submit pull requests

## License

CNHAAI is licensed under the Apache 2.0 License. See [LICENSE](LICENSE) for details.

## Resources

- [GitHub](https://github.com/noeticanlabs/cnsc-haai)
- [Noetican Labs](https://noeticanlabs.com)
- [Documentation](docs/)
- [Examples](docs/appendices/appendix-g-examples.md)

---

**Version**: 1.0.0 | **Status**: Canonical | **Release Date**: 2024-01-01
