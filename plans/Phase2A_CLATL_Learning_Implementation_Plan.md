# Phase 2A Implementation Plan - Minimal Learnable World Model

## Executive Summary

Implement deterministic representation learning for CLATL using a linear latent dynamics model in QFixed arithmetic. This provides real learning without neural network complexity.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     CLATL Runtime                                │
│  ┌─────────┐    ┌──────────┐    ┌───────────┐    ┌─────────┐ │
│  │ Task    │───▶│ Proposer │───▶│ Governor  │───▶│ GMI     │ │
│  │ Layer   │    │          │    │           │    │ Kernel  │ │
│  └─────────┘    └──────────┘    └───────────┘    └─────────┘ │
│       │                                       │                │
│       ▼                                       ▼                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  Model Layer (Phase 2)                   │   │
│  │  ┌──────────┐  ┌───────────┐  ┌────────────┐          │   │
│  │  │ Encoder  │  │ Dynamics  │  │ Predictor  │          │   │
│  │  │ s = E(o) │  │ s' = A*s  │  │ o' = C*s'   │          │   │
│  │  │          │  │           │  │            │          │   │
│  │  └────┬─────┘  └─────┬─────┘  └──────┬─────┘          │   │
│  │       │               │               │                 │   │
│  │       ▼               ▼               ▼                 │   │
│  │  ┌─────────────────────────────────────────────┐       │   │
│  │  │              Loss: ||s' - ŝ'||² + ||o' - ô'||²  │       │   │
│  │  └─────────────────────────────────────────────┘       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Learning Layer (Phase 2A)                   │   │
│  │  ┌──────────────┐  ┌────────────┐  ┌───────────────┐   │   │
│  │  │ ReplayBuffer │─▶│ Batching   │─▶│ Update Rule  │   │   │
│  │  │ (deterministic│  │ (hash-based│  │ (sign-descent│   │   │
│  │  │  retention)  │  │  selection)│  │  + trust reg)│   │   │
│ ──────┘ │  └────────  └────────────┘  └───────┬───────┘   │   │
│  │                                              │           │   │
│  │                                              ▼           │   │
│  │                                    ┌─────────────────┐   │   │
│  │                                    │ Acceptance Test │   │   │
│  │                                    │ (governed gate) │   │   │
│  │                                    └────────┬────────┘   │   │
│  │                                             │            │   │
│  │                                             ▼            │   │
│  │                                   ┌─────────────────┐   │   │
│  │                                   │ UpdateReceipt   │   │   │
│  │                                   │ (chain hash)    │   │   │
│  │                                   └─────────────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Implementation Details

### 1. Memory Module: `src/cnsc_haai/memory/replay_buffer.py`

**Purpose**: Bounded buffer with deterministic retention and hash-based pruning.

**Key Functions**:
- `ReplayBuffer.add(transition)` - Add with FIFO eviction
- `ReplayBuffer.sample_deterministic(batch_size, seed)` - Hash-based selection
- `ReplayBuffer.get_root()` - Merkle root for receipts
- `Transition` dataclass with hash for audit

**Determinism**: Uses LCG (Linear Congruential Generator) for reproducible sampling.

### 2. Learn Module: New Files

#### `src/cnsc_haai/learn/batching.py`
- `select_batch_deterministic(buffer, batch_size, seed)` - Hash-based index selection
- Returns indices that can be receipted

#### `src/cnsc_haai/learn/update_rule.py`
- `compute_prediction_loss(model_params, batch)` - Real MSE loss computation
- `propose_update(current_params, batch, learning_rate)` - Sign-descent on each parameter
- `apply_update(params, delta)` - Returns new params
- Cost: `W_update = k * batch_size * param_count_changed`

#### `src/cnsc_haai/learn/acceptance.py`
- `trust_region_check(old_params, new_params, old_loss, new_loss, gamma)` 
- `budget_check(budget, update_cost)` - Verify enough budget
- `create_update_receipt(...)` - Produce UpdateReceipt with all hashes

### 3. Update `src/cnsc_haai/learn/__init__.py`

Replace placeholder functions with real implementations:
- `trust_region_update()` - Actually computes loss and updates params
- `bounded_update()` - Checks budget constraints properly
- Add `governed_update()` - Combines trust region + budget + acceptance

### 4. Wire into CLATL Runtime

In `clatl_runtime.py`:
- Add `model_params` field to track current world model
- Add `replay_buffer` to store transitions
- Every N steps: trigger governed update
- Proposer uses model predictions to score actions

### 5. Missing Tests

#### `test_prediction_error_decreases.py`
- Run 20 episodes with learning enabled
- Collect prediction losses
- Assert median loss in last 10 episodes < median in first 10 episodes

#### `test_policy_beats_phase1.py`
- Create task where model helps (partial observability / beacon lag)
- Run Phase 2 agent with world model
- Run Phase 1 baseline (no model)
- Assert Phase 2 achieves higher competence

#### `test_replay_reconstructs_params.py`
- Run learning episode with receipts
- Replay from receipts
- Assert final params hash matches

## File Structure After Implementation

```
src/cnsc_haai/
├── model/
│   ├── __init__.py          # Already exists
│   ├── encoder.py           # Already exists (LatentState, EncoderParams)
│   ├── dynamics.py          # Already exists (DynamicsParams, A, B, C)
│   ├── predictor.py         # Already exists
│   └── loss.py              # Already exists
├── memory/
│   ├── __init__.py          # Contains ReplayBuffer (keep)
│   └── replay_buffer.py     # NEW: Full implementation
├── learn/
│   ├── __init__.py          # UPDATE: Real learning functions
│   ├── batching.py          # NEW: Deterministic batch selection
│   ├── update_rule.py       # NEW: Loss computation + sign-descent
│   └── acceptance.py        # NEW: Trust region + budget checks
└── agent/
    └── clatl_runtime.py     # UPDATE: Wire learning

compliance_tests/phase2/
├── __init__.py              # Already exists
├── test_invariants_never_break.py  # Already exists
├── test_prediction_error_decreases.py  # NEW
├── test_policy_beats_phase1.py      # NEW
└── test_replay_reconstructs_params.py # NEW
```

## Key Invariants (Tests Must Verify)

1. **Determinism**: Same seed → same trajectory → same params
2. **Receipt Integrity**: Every update produces a receipt with chain hash
3. **Budget Compliance**: Updates only proceed if `cost ≤ budget`
4. **Trust Region**: `‖Δπ‖ ≤ δ(b)` must hold
5. **Loss Improvement**: `new_loss ≤ old_loss` (or within ε)
6. **Safety Preserved**: GMI invariants still hold after learning

## Success Criteria

- [ ] All 26 existing tests still pass
- [ ] 3 new Phase 2 tests pass
- [ ] Prediction loss demonstrably decreases over episodes
- [ ] Phase 2 policy outperforms Phase 1 baseline
- [ ] Replay reconstructs exact parameter trajectory
