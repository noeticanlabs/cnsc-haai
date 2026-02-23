# ATS Documentation

**Autonomic Transaction System Specifications**

The ATS (Autonomic Transaction System) is the core coherence kernel that enforces budget laws and ensures deterministic replay.

## Sections

| Section | Description | Files |
|---------|-------------|-------|
| [00_identity/](00_identity/) | Project identity, ATS definition, kernel scope | 4 |
| [10_mathematical_core/](10_mathematical_core/) | State space, action algebra, budget law | 8 |
| [20_coh_kernel/](20_coh_kernel/) | Canonical serialization, receipt schema | 8 |
| [30_ats_runtime/](30_ats_runtime/) | Runtime specs, state digest, budget transitions | 6 |
| [40_nsc_integration/](40_nsc_integration/) | NSC integration, gate-to-receipt translation | 4 |
| [50_security_model/](50_security_model/) | Security model, adversary model, float prohibition | 5 |
| [60_test_vectors/](60_test_vectors/) | Test vectors for verification | 5 |
| [90_roadmap/](90_roadmap/) | Future plans and upgrades | 4 |

## Getting Started

1. **Understanding ATS**: Start with [ats_definition.md](00_identity/ats_definition.md)
2. **Core Concepts**: See [coh_kernel_scope.md](00_identity/coh_kernel_scope.md)
3. **Mathematical Foundation**: See [state_space.md](10_mathematical_core/state_space.md)

## Key Specifications

- **Receipt Schema**: [receipt_schema.md](20_coh_kernel/receipt_schema.md)
- **Budget Law**: [budget_law.md](10_mathematical_core/budget_law.md)
- **Chain Hash Universal**: [chain_hash_universal.md](20_coh_kernel/chain_hash_universal.md)
- **Security Model**: [adversary_model.md](50_security_model/adversary_model.md)

## Related Documentation

- [GMI](../gmi/) - Global Memory Infrastructure
- [COH-AGI](../coh-agi/) - Coherent AGI architecture
- [Spine](../spine/) - Core abstraction theory
