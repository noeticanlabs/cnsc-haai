# Hybrid Morphogenesis

**Topology Changes with Safety Constraints**

## Overview

Morphogenesis (atlas topology changes) is constrained to ensure hybrid safety:
- Expansion: budget gate b >= Δ_struct
- Pruning: distortion bound <= MAX_DISTORTION
- Hysteresis: |Δ_struct| >= threshold

## Critical Constraint

**Topology changes only occur at slab boundaries.**

This ensures:
- Consistent Merkle proofs within slabs
- Valid fraud proof references
- Deterministic behavior

See:
- [Topology Change Budget](../ats/10_mathematical_core/topology_change_budget.md)
- [Continuous Manifold Flow](../ats/10_mathematical_core/continuous_manifold_flow.md)
