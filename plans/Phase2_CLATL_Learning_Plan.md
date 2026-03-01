# Phase 2 Implementation Plan: Representation Learning + World-Model Learning

## Overview

Phase 1 proved: "the organism can hunt under constraints."

Phase 2 proves: "the organism can learn a model of its world and use it to hunt better—without breaking invariants."

### Phase 2 Scope Lock

**Goal:** Learn an internal predictive model online, improve task performance, keep:
- (z ∈ K) always
- Budget absorption at (b = 0)
- Deterministic receipts/replay
- No unreceipted nondeterminism

**What changes from Phase 1:** cognition is no longer just "search + novelty"; it maintains a learnable internal state (m_t) and parameters (π_t) updated under a governed update operator.

---

## 1) Architecture Components

### Model Layer (`src/cnsc_haai/model/`)

```
┌─────────────────────────────────────────────────────────────┐
│                    World Model (π)                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Encoder  │→│ Dynamics │→│ Predictor│→│ Task Head│  │
│  │ s_t = eπ │  │ ŝ(t+1)  │  │ ô(t+1)   │  │ r̂(t+1)   │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
```

#### encoder.py
```python
@dataclass(frozen=True)
class EncoderParams:
    """Encoder parameters (QFixed for determinism)."""
    weights: Tuple[Tuple[int, ...], ...]  # QFixed scaled
    bias: Tuple[int, ...]
    
def encode(
    obs: GridWorldObs,
    params: EncoderParams
) -> LatentState:
    """Map observation to latent state: s_t = e_π(o_t, M_t)"""
```

#### dynamics.py
```python
@dataclass(frozen=True)
class DynamicsParams:
    """Dynamics model parameters."""
    transition_matrix: Tuple[Tuple[int, ...], ...]
    
def predict_next_state(
    latent: LatentState,
    action: str,
    params: DynamicsParams
) -> LatentState:
    """Predict next latent: ŝ_{t+1} = f_π(s_t, a_t)"""
```

#### predictor.py
```python
def predict_observation(
    latent: LatentState,
    params: PredictorParams
) -> GridWorldObs:
    """Predict observation: ô_{t+1} = g_π(ŝ_{t+1})"""
    
def predict_reward(
    latent: LatentState,
    action: str,
    params: TaskParams
) -> int:
    """Predict reward: r̂_{t+1} = h_π(s_t, a_t)"""
```

#### loss.py
```python
def compute_prediction_loss(
    actual_obs: GridWorldObs,
    predicted_obs: GridWorldObs,
    actual_reward: int,
    predicted_reward: int
) -> int:
    """V_pred(t) = ℓ(o_{t+1}, ô_{t+1}) + ℓ_r(r_{t+1}, r̂_{t+1})"""
    # All QFixed integers for determinism
```

---

## 2) Learning Update Rule (The Core)

### update_rule.py

**Phase 2 Hard Rule:** A parameter update is only accepted if it is:
1. **Admissible** (π_{t+1} ∈ K_π)
2. **Paid for** (budget debit tied to update magnitude)
3. **Certified** (passes deterministic acceptance test)

#### Option A: Trust-Region Descent Gate
```python
def trust_region_update(
    params: ModelParams,
    batch: List[Transition],
    budget: int,
    gamma: int  # Trust region coefficient
) -> Tuple[ModelParams, bool, UpdateReceipt]:
    """
    Accept if:
    V_pred(π_{t+1}) ≤ V_pred(π_t) - γ * |π_{t+1} - π_t|²
    
    Returns (new_params, accepted, receipt)
    """
```

#### Option B: Safe Update Bound  
```python
def bounded_update(
    params: ModelParams,
    batch: List[Transition],
    budget: int,
    delta_max: int
) -> Tuple[ModelParams, bool, UpdateReceipt]:
    """
    Accept if:
    - |Δπ| ≤ δ(b_t)  (norm bounded by budget)
    - validation loss doesn't increase
    
    Returns (new_params, accepted, receipt)
    """
```

---

## 3) Memory System

### memory/replay_buffer.py

```python
@dataclass(frozen=True)
class Transition:
    """A receipted transition for training."""
    obs: GridWorldObs
    action: str
    next_obs: GridWorldObs
    reward: int
    hash: bytes  # For audit

class ReplayBuffer:
    """Bounded replay buffer with deterministic retention."""
    
    def __init__(self, capacity: int, retention_policy: str = "fifo"):
        self.capacity = capacity
        self.buffer: List[Transition] = []
        self.retention_policy = retention_policy
        
    def add(self, transition: Transition):
        """Add transition, evict deterministically if full."""
        
    def sample_deterministic(self, batch_size: int, seed: int) -> List[Transition]:
        """Deterministic batch selection via hash-based indexing."""
        
    def get_root(self) -> bytes:
        """Merkle root of all transitions for receipt."""
```

---

## 4) Phase 2 Governance

### acceptance.py

```python
def governed_update(
    current_params: ModelParams,
    proposed_params: ModelParams,
    old_loss: int,
    new_loss: int,
    budget: int,
    delta_norm: int
) -> Tuple[bool, str]:
    """
    Lexicographic acceptance:
    1. Check admissibility: params in K_π
    2. Check budget: b' ≥ 0 after update cost
    3. Check loss: new_loss ≤ old_loss (or trust region)
    """
```

---

## 5) Phase 2 Benchmark

Upgrade Hazard Gridworld to be partially observable:
- Observation = local patch only (no full state)
- Goal beacon may be noisy or delayed
- Hazards may shift (bounded drift)

This makes the learned model matter for performance.

---

## 6) Directory Structure

```
src/cnsc_haai/
├── model/                    # NEW: World model components
│   ├── __init__.py
│   ├── encoder.py           # Latent encoder
│   ├── dynamics.py          # Transition model
│   ├── predictor.py         # Observation/reward predictor
│   └── loss.py             # Prediction loss
├── learn/                   # NEW: Learning components
│   ├── __init__.py
│   ├── update_rule.py       # Trust-region / bounded update
│   ├── batching.py          # Deterministic batch selection
│   └── acceptance.py        # Update gate
├── memory/                  # NEW: Memory components
│   ├── __init__.py
│   ├── replay_buffer.py     # Bounded buffer + retention
│   └── priorities.py       # Residual-based priority
├── tasks/                   # Phase 1 (existing)
└── agent/                   # Phase 1 (existing)

compliance_tests/phase2/     # NEW: Phase 2 tests
├── __init__.py
├── test_prediction_error_decreases.py
├── test_policy_beats_phase1.py
├── test_replay_reconstructs_params.py
├── test_invariants_never_break.py
└── test_budget_stays_bounded.py
```

---

## 7) Test Plan

### test_prediction_error_decreases.py
- Train model online
- Measure prediction error on held-out transitions
- Assert: error decreases over time

### test_policy_beats_phase1.py
- Run Phase 2 agent vs Phase 1 baseline
- Assert: Phase 2 reaches goal faster / more reliably

### test_replay_reconstructs_params.py
- Record full run with receipts
- Replay from receipts
- Assert: π_t sequence is identical

### test_invariants_never_break.py
- Same as Phase 1, plus:
- Assert: π_t stays in K_π
- Assert: budget never goes negative during learning

### test_budget_stays_bounded.py
- Run many episodes
- Track cumulative budget spent on learning
- Assert: budget trajectory is bounded and decreasing

---

## 8) Key Invariants

| Invariant | Description |
|-----------|-------------|
| Admissibility (π) | π ∈ K_π always |
| Budget | b ≥ 0 after learning cost |
| Determinism | Same seed → same π_t sequence |
| Loss monotonic | V_pred decreases on accepted updates |
| Safety preserved | No more violations than Phase 1 |

---

## 9) The Core Theorem

**Theorem (Governed Learning Stability, Phase 2).**

Under bounded excitation, deterministic batch selection, admissible trust-region updates, and coercive prediction loss:

1. Parameter trajectory (π_t) remains in K_π
2. Budget remains nonnegative with absorption at b = 0
3. Prediction loss is non-increasing along accepted updates
4. Closed-loop agent achieves decreasing prediction error while maintaining invariance

---

## 10) Enhancement: Semantic Governor Gates (Phase 1.5)

**Note:** Before implementing Phase 2, apply this improvement to make Gates 2/3 truly semantic:

In `clatl_runtime.py`, before calling `select_action()`, compute predicted GMI states for each proposal:

```python
# Compute predicted GMI states for each proposal
predicted_gmi_states = []
for proposal in proposals:
    gmi_action = _translate_to_gmi_action(proposal.action)
    pred_gmi_state, _ = gmi_step(current_gmi, gmi_action, {}, gmi_params, chain)
    predicted_gmi_states.append(pred_gmi_state)

# Pass to governor for semantic gate checking
decision = select_action(
    proposals=proposals,
    gridworld_state=current_gridworld,
    gmi_state=current_gmi,
    gmi_params=gmi_params,
    predicted_gmi_states=predicted_gmi_states,  # Now semantic!
)
```

This makes Gate 2 (admissibility) and Gate 3 (Lyapunov) truly check the *predicted* next state, not just the current state.

---

## 11) Next Steps

1. Create Phase 2 plan document in `/plans/` ✅
2. Apply Phase 1.5 governor upgrade (semantic gates)
3. Implement model layer components
4. Implement learning update rule
5. Implement replay buffer
6. Implement Phase 2 compliance tests
7. Run tests and verify learning improves performance
