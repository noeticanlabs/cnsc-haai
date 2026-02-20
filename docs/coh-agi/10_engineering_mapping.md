# Engineering Mapping to Code Modules

**Code → Documentation Mapping**

## Consensus Layer

| Component | Code Module | Documentation |
|-----------|-------------|---------------|
| JCS Serialization | `src/cnsc_haai/consensus/jcs.py` | [RFC8785](https://datatracker.ietf.org/doc/html/rfc8785) |
| Chain Hash | `src/cnsc_haai/consensus/chain.py` | [Chain Hash Universal](../ats/20_coh_kernel/chain_hash_universal.md) |
| Merkle Tree | `src/cnsc_haai/consensus/merkle.py` | [Coh Merkle v1](../ats/20_coh_kernel/coh.merkle.v1.md) |
| Retention Policy | `src/cnsc_haai/consensus/retention.py` | [Retention Policy](../ats/20_coh_kernel/retention_policy.md) |
| Slab Builder | `src/cnsc_haai/consensus/slab.py` | [Slab Compression](../ats/30_ats_runtime/slab_compression_rules.md) |
| Fraud Proof | `src/cnsc_haai/consensus/fraudproof.py` | [Fraud Proof Rules](../ats/20_coh_kernel/fraud_proof_rules.md) |
| Finalization | `src/cnsc_haai/consensus/finalize.py` | [Finalize Rules](../ats/20_coh_kernel/finalize_rules.md) |

## Advanced Features

| Component | Code Module | Documentation |
|-----------|-------------|---------------|
| Continuous Trajectory | `src/cnsc_haai/consensus/continuous.py` | [Continuous Manifold Flow](../ats/10_mathematical_core/continuous_manifold_flow.md) |
| Topology Engine | `src/cnsc_haai/consensus/topology.py` | [Topology Change Budget](../ats/10_mathematical_core/topology_change_budget.md) |
| Autonomic Controller | `src/cnsc_haai/consensus/autonomic.py` | [Autonomic Regulation](../ats/10_mathematical_core/autonomic_regulation.md) |

## Schemas

| Schema | File |
|--------|------|
| Slab Receipt | `schemas/coh.receipt.slab.v1.schema.json` |
| Fraud Proof | `schemas/coh.receipt.fraudproof.v1.schema.json` |
| Finalize | `schemas/coh.receipt.finalize.v1.schema.json` |
| Topology Jump | `schemas/coh.receipt.topology_jump.v1.schema.json` |
| Retention Policy | `schemas/coh.policy.retention.v1.schema.json` |
