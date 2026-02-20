# Project Identity

**CNsc-HAAI - Coh-Compliant Admissible Trajectory Space Kernel**

| Field | Value |
|-------|-------|
| **Module** | 00_identity |
| **Version** | 1.0.0 |
| **Status** | Architecture Definition |

---

## 1. Executive Identity

> **CNsc-HAAI implements a Coh-compliant Admissible Trajectory Space (ATS) kernel for dynamical cognitive systems.**

This is the foundational identity statement. Every architectural decision flows from this definition.

---

## 2. What ATS Is

The **Admissible Trajectory Space (ATS)** is a mathematical framework that:

1. **Defines** a canonical state space for cognitive computations
2. **Enumerates** admissible actions that preserve system invariants
3. **Quantifies** risk via a deterministic functional V: X → Q≥0
4. **Enforces** a budget law that bounds cumulative risk accumulation
5. **Verifies** every trajectory step through a deterministic receipt verifier

The ATS kernel does not govern physics. It governs **admissible computational trajectories**.

---

## 3. What Coh Is

**Coh** is the principle that all state transitions must preserve system coherence. In the ATS context, Coh manifests as:

- **Risk Monotonicity**: V(x_{k+1}) ≤ V(x_k) + κ·B_k (risk cannot explode)
- **Budget Boundedness**: Cumulative positive risk delta is bounded by initial budget
- **Deterministic Verifiability**: Every step can be independently verified without ambiguity

Coh is not a "feature" — it is the **invariant enforcement mechanism** of the ATS kernel.

---

## 4. What CNsc-HAAI Is NOT

CNsc-HAAI is NOT:

| Not | Reason |
|-----|--------|
| **An AI Framework** | It does not provide neural networks, transformers, or ML training |
| **A Blockchain** | It has no consensus protocol, mining, or token economics |
| **A PDE Solver** | It does not solve differential equations |
| **A General-Purpose VM** | It executes only ATS-governed cognitive operations |

CNsc-HAAI is a **verification kernel** that hosts dynamical cognitive systems.

---

## 5. System Position

```
┌─────────────────────────────────────────────────────────────┐
│                    CNsc-HAAI Kernel                         │
│                  (ATS Implementation)                       │
├─────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────┐  │
│  │            Coh Kernel                                 │  │
│  │  - Deterministic Numeric Domain (QFixed)            │  │
│  │  - Receipt Verifier (RV)                             │  │
│  │  - Budget Law Enforcement                             │  │
│  │  - Canonical Serialization                           │  │
│  └───────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────┐  │
│  │        Hosted Cognitive System                        │  │
│  │  - NSC (Network Structured Code)                     │  │
│  │  - GML (Governance Metadata Language)                 │  │
│  │  - GHLL (Glyphic High-Level Language)                │  │
│  │  - GLLL (Glyphic Low-Level Language)                │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. Clean Identity Statement (for README)

> **CNsc-HAAI** implements a deterministic Coh kernel that defines and enforces Admissible Trajectory Spaces (ATS) for dynamical cognitive systems.
>
> Every state transition must carry a machine-verifiable receipt proving compliance with risk monotonicity and budget constraints.
>
> The system defines the set of admissible executions as those accepted by the receipt verifier.

---

## 7. References

- [ATS Definition](./ats_definition.md)
- [Coh Kernel Scope](./coh_kernel_scope.md)
- [Budget Law](../10_mathematical_core/budget_law.md)
- [Receipt Verifier Specification](../20_coh_kernel/rv_step_spec.md)
