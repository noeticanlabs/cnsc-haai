# GMI Adaptation Layer: CLATL

> **Status**: Implemented  
> **Tests**: 21/21 passing

This document describes the Closed-Loop Adaptive Task Layer (CLATL), which extends GMI with adaptive task behavior while preserving all safety invariants.

## Overview

CLATL adds a task layer on top of the GMI coherence kernel:

```
┌─────────────────────────────────────────────────────────────┐
│                    CLATL Runtime                             │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌───────────┐ │
│  │ Gridworld │→│ Proposer │→│ Governor  │→│ GMI Kernel│ │
│  │  (Env)   │  │(Proposal)│  │ (Gate)    │  │(Coherence)│ │
│  └──────────┘  └──────────┘  └───────────┘  └───────────┘ │
│                         ↓                                   │
│              ┌─────────────────────┐                        │
│              │ Full Receipt Chain  │                        │
│              │ (Replay Verifiable) │                        │
│              └─────────────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

## Intelligence Definition

A system is "intelligent" **iff** over time it reduces a **task loss** under constraints:

```
V_total(z,t) = V_coh(z) + λ(t) * V_task(z,t)
```

While **never** violating:
- **Admissibility**: z ∈ K (state stays in safe region)
- **Budget law**: b ≥ 0 with absorption at b = 0
- **Replay determinism** from receipts

## Components

### Task Layer (`cnsc_haai.tasks`)

| Module | Purpose |
|--------|---------|
| `gridworld_env.py` | Deterministic gridworld with hazards, walls, drifting goal |
| `task_loss.py` | V_task (distance-to-goal), competence metrics, metabolic costs |

### Agent Layer (`cnsc_haai.agent`)

| Module | Purpose |
|--------|---------|
| `proposer_iface.py` | Generates proposals with deterministic exploration bonus |
| `governor_iface.py` | Lexicographic selection: safety first, then task |
| `clatl_runtime.py` | Orchestrates closed-loop execution with receipts |

## Core Design Decisions

### 1. Lexicographic (NOT Scalarized)

The Governor enforces **hard constraints first**, then optimizes:

| Priority | Layer | What happens |
|----------|-------|--------------|
| 1st | Governance | Enforce: `in_K`, `V_coh descent`, `b ≥ 0` |
| 2nd | Task | Among safe actions, maximize task score |

This prevents "trading safety for performance."

### 2. Deterministic Exploration

Exploration is budget-governed and deterministic:

```
Score = -V_task + α(b) * 1/sqrt(N(s) + 1)
```

Where:
- α(b) = min(b / base_budget, 1) - shrinks as budget depletes
- N(s) = visitation count - exploration decreases with more visits
- At b=0, exploration vanishes completely

### 3. ProposalSet Receipt

Every decision commits to the entire proposal set:

```python
@dataclass(frozen=True)
class CLATLStepReceipt:
    proposalset_root: bytes        # Merkle root of all proposals
    chosen_proposal_index: int    # Which proposal was selected
    chosen_proposal_hash: bytes   # Hash of selected proposal
```

This ensures deterministic replay - same seed → same trajectory.

## Test Results

| Test Suite | Tests | Status |
|------------|-------|--------|
| Invariants Never Break | 6 | ✅ PASS |
| Replay Exact | 5 | ✅ PASS |
| Task Improves | 5 | ✅ PASS |
| Recovery After Drift | 5 | ✅ PASS |
| **TOTAL** | **21** | ✅ **ALL PASS** |

### Key Invariants Verified

1. **Admissibility**: `in_K(gmi_state) == True` at all steps
2. **Budget**: `b >= 0` at all steps
3. **Safety**: No hazard collisions
4. **Lyapunov**: dV <= 0 on accepted steps
5. **Determinism**: Replay produces identical trajectory

## Usage

```python
from cnsc_haai.agent.clatl_runtime import run_clatl_episode
from cnsc_haai.tasks.gridworld_env import create_initial_state, create_standard_grid
from cnsc_haai.agent.clatl_runtime import _create_initial_gmi_state

# Setup
grid, start, goal = create_standard_grid("simple")
gridworld = create_initial_state(grid, start, goal, drift_seed=42)
gmi_state = _create_initial_gmi_state(budget=10_000_000)

# Run episode
receipt = run_clatl_episode(
    gmi_state=gmi_state,
    gridworld=gridworld,
    max_steps=50,
    goal_drift_every=20,
    drift_seed=42,
    gmi_params=GMIParams(),
)

print(f"Success: {any(receipt.success_flags)}")
print(f"Violations: {receipt.invariant_violations}")
```

## Future Work

- **Task B**: Online function approximation under budget
- **Stochastic exploration**: Add PRNG seeded by receipts
- **Capstone theorem**: Prove that persistent bounded excitation → non-zero competence

---

*See also: [GMI Scope](01_gmi_scope.md), [Budget Algebra](07_budget_algebra.md), [Receipt Bundle](08_receipt_bundle.md)*
