# Spine Documentation

**Core Abstraction Theory**

The Spine provides the foundational theory for abstraction in the CNSC-HAAI system.

## Sections (00-24)

| Section | Description |
|---------|-------------|
| 00-04 | Project overview, problem statement, vision, core definition, design principles |
| 05-09 | Abstraction theory, types, contracts, hierarchy construction and navigation |
| 10-14 | Abstraction ladders, cross-layer alignment, coherence principles, POC lemmas |
| 15-19 | Gate theory and implementation, rail theory, time and phase |
| 20-24 | Memory models, receipt system, learning under coherence, failure modes |

## Getting Started

1. **Start here**: [00-project-overview.md](00-project-overview.md)
2. **Core concepts**: [05-abstraction-theory.md](05-abstraction-theory.md)
3. **Design principles**: [04-design-principles.md](04-design-principles.md)

## Related Documentation

- [ATS](../ats/) - Autonomic Transaction System
- [GMI](../gmi/) - Global Memory Infrastructure
- [COH-AGI](../coh-agi/) - Coherent AGI architecture
- [SOC Spine](../soc/) - Self-Organized Criticality framework

---

## SOC Spine (Self-Organized Criticality)

The SOC spine provides the mathematical framework for understanding renormalization criticality and scale-free cascade statistics.

| Section | Description |
|---------|-------------|
| [01_soc_attractor_necessary_conditions.md](../soc/01_soc_attractor_necessary_conditions.md) | Necessary conditions NC1-NC5 for SOC attractor existence |
| [02_scale_free_renorm_theorem_program.md](../soc/02_scale_free_renorm_theorem_program.md) | Physics-to-math bridge for scale-free statistics |
| [03_runtime_trigger_spec.md](../soc/03_runtime_trigger_spec.md) | Runtime trigger and acceptance predicate |

### Key Components

- **Schema**: [`schemas/coh.renorm_criticality_receipt.v1.json`](../../schemas/coh.renorm_criticality_receipt.v1.json)
- **Implementation**: [`src/soc/`](../../src/soc/)
