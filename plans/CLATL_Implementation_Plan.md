# CLATL Implementation Plan: Hazard Gridworld Benchmark

## Executive Summary

This plan implements a **Closed-Loop Adaptive Task Layer (CLATL)** on top of the existing GMI coherence kernel. The system will demonstrate "intelligence" by reducing task loss (distance-to-goal) over time while maintaining perfect safety invariants.

### Operational Definition of Intelligence (from GMI spec)

A system is "intelligent" **iff** over time it reduces a **task loss** under constraints:

```
V_total(z,t) = V_coh(z) + λ(t) * V_task(z,t)
```

While **never** violating:
- **Admissibility**: z ∈ K (state stays in safe region)
- **Budget law**: b ≥ 0 with absorption at b = 0
- **Replay determinism** from receipts

---

## Phase 1: Hazard Gridworld Benchmark

### Task A: Hazard Gridworld with Drifting Goal

| Component | Specification |
|-----------|---------------|
| **Grid** | N×M grid with walls, hazards, start, goal |
| **Goal drift** | Deterministic drift every N steps (seeded PRNG) |
| **Observation** | Local patch (partial observability) + goal beacon |
| **Actions** | N/S/E/W/Stay (5 actions) |
| **Safety** | Hazard hit = violation (prevented by gate) |
| **Metric P(t)** | Rolling average distance-to-goal + success rate |

> **FIX 1 & 2**: Environment is deterministic. Goal drift uses internal PRNG seeded once per episode (seed stored in receipt).

---

## Architecture: CLATL Components

```mermaid
graph TD
    subgraph "CLATL Runtime"
        E[Environment<br/>EnvStep] -->|o_t| P[Proposer<br/>ProposalSet]
        P -->|A_t| G[Governor<br/>GateAccept + Score]
        G -->|a_t| E
        G -->|receipt| R[Receipt<br/>Chain]
    end
    
    subgraph "GMI Kernel (Existing)"
        K[in_K<br/>Admissibility]
        L[V_coh<br/>Lyapunov]
        B[budget<br/>Law]
    end
    
    G -->|GateAccept| K
    G -->|GateAccept| L
    G -->|GateAccept| B
    
    subgraph "Task Layer"
        T[V_task<br/>Distance to Goal]
        D[Goal Drifter<br/>λ(t) Scheduler]
    end
    
    G -->|Score| T
    D -->|λ(t)| G
```

### Component Interfaces

#### 1. Environment (`gridworld_env.py`)

```python
@dataclass(frozen=True)
class GridWorldState:
    """Grid world state - completely deterministic."""
    position: Tuple[int, int]      # Agent position (x, y)
    goal: Tuple[int, int]          # Current goal position
    grid: List[List[int]]          # 0=empty, 1=wall, 2=hazard, 3=goal
    t: int                         # Step counter
    drift_seed: int                # Seed for deterministic goal drift
    
@dataclass(frozen=True)
class GridWorldObs:
    """Observation: local patch + goal beacon."""
    local_patch: List[List[int]]   # 5x5 view centered on agent
    goal_delta: Tuple[int, int]    # (dx, dy) to goal
    distance_to_goal: int          # Manhattan distance
    # NOTE: Proposer receives (state, obs) tuple, NOT just obs

def env_step(
    state: GridWorldState,
    action: str  # 'N', 'S', 'E', 'W', 'Stay'
) -> Tuple[GridWorldState, float]:
    """Deterministic step function. Returns (next_state, reward)."""
    
def create_initial_state(
    grid: List[List[int]],
    start: Tuple[int, int],
    goal: Tuple[int, int],
    seed: int  # Seed for deterministic drift sequence
) -> GridWorldState:
    """Create initial state with seeded drift generator."""
```

> **FIX 1**: `GridWorldObs` is minimal. Proposer receives `(state, obs)` to access `state.position` directly.

#### 2. Task Loss + Competence Metric (`task_loss.py`)

> **FIX 5**: Stronger competence metric to prevent "do nothing" gaming.

```python
@dataclass
class CompetenceMetrics:
    """Conjunction of metrics to prevent gaming."""
    success_rate: float           # Fraction of episodes reaching goal
    avg_steps_to_goal: float      # Average steps (lower = better)
    avg_distance_to_goal: float   # Rolling average distance
    
def compute_competence(
    task_performance_history: List[int],
    episode_boundaries: List[int],
    success_flags: List[bool]
) -> CompetenceMetrics:
    """
    Compute conjunction competence metric.
    
    Agent is "competent" iff ALL of:
    - success_rate >= 0.5 (at least half the goals reached)
    - avg_steps_to_goal decreasing over episodes
    - avg_distance_to_goal decreasing over time
    
    This prevents "freeze in safe corner" gaming.
    """
    # ... implementation
```

> **FIX 6**: Metabolic costs tied to cognition.

```python
# Work costs (quantized, like GMI budget)
W_MOVE = 1_000_000       # QFixed: 1.0
W_PROPOSE = 500_000     # QFixed: 0.5 per proposal generated
W_MEMORY_WRITE = 100_000 # QFixed: 0.1 per memory update
W_REJECTED_ATTEMPT = 50_000  # Small cost for failed exploration

def compute_metabolic_cost(
    action: str,
    num_proposals_generated: int,
    memory_writes: int,
    action_was_rejected: bool
) -> int:
    """Compute total work cost for a step."""
    cost = W_MOVE
    cost += num_proposals_generated * W_PROPOSE
    cost += memory_writes * W_MEMORY_WRITE
    if action_was_rejected:
        cost += W_REJECTED_ATTEMPT
    return cost
```

This makes curiosity metabolically expensive - exploration has real cost.

---

## Design Decision: Lexicographic (NOT Scalarized)

> **FIX 7**: Clarified objective function semantics.

The plan says `V_total = V_coh + λ(t) * V_task` but also says "coherence is hard constraint, task is soft objective."

These conflict. We choose **LEXICOGRAPHIC**:

| Layer | Priority | What happens |
|-------|----------|---------------|
| **Governance** | 1st (hard) | Enforce: `in_K`, `V_coh descent`, `b ≥ 0` |
| **Task** | 2nd (soft) | Among safe actions, maximize task score |

The Governor **never** considers `V_total = V_coh + λ*V_task` as a scalar. It:
1. Filters to safe actions only (enforcing coherence invariants)
2. Among survivors, picks highest `task_score`

This is cleaner and aligns with "governance first."

```python
def V_task_distance(state: GridWorldState) -> int:
    """Task loss: Manhattan distance to goal (lower is better)."""
    return abs(state.position[0] - state.goal[0]) + \
           abs(state.position[1] - state.goal[1])

def compute_total_objective(
    V_coh: int,           # From GMI Lyapunov
    V_task: int,           # From task loss
    lambda_t: int         # Time-varying weight
) -> int:
    """V_total = V_coh + λ(t) * V_task (lexicographic: coh is hard, task is soft)"""
    return V_coh + lambda_t * V_task
```

#### 3. Proposer (`proposer_iface.py`)

```python
@dataclass(frozen=True)
class TaskProposal:
    """Proposal for gridworld action."""
    action: str                      # 'N', 'S', 'E', 'W', 'Stay'
    expected_next_position: Tuple[int, int]
    V_task_proposal: int             # Predicted task loss after action
    
class TaskProposer:
    """Generates proposals. Nondeterministic proposals are receipted."""
    
    def propose(
        self,
        obs: GridWorldObs,
        V_coh: int,
        memory: Dict
    ) -> List[TaskProposal]:
        """Generate proposal set with deterministic exploration bonus."""
        
        # Base proposals: all 5 actions
        proposals = []
        for action in ['N', 'S', 'E', 'W', 'Stay']:
            # Compute expected next state
            next_pos = self._apply_action(obs.position, action)
            # Compute predicted task loss
            v_task = self._distance_to_goal(next_pos, obs.goal_delta)
            proposals.append(TaskProposal(...))
        
        # Add deterministic exploration bonus (budget-governed)
        # Score = -V_task + α(budget) * 1/sqrt(N(s) + 1)
        
        return proposals
```

#### 4. Governor (`governor_iface.py`)

```python
def select_action(
    proposals: List[TaskProposal],
    state: GridWorldState,
    gmi_state: GMIState,    # For coherence check
    gmi_params: GMIParams
) -> Tuple[Optional[TaskProposal], List[str]]:
    """
    LEXICOGRAPHIC selection (coherence hard, task soft):
    1. Filter: environment safety (not hitting hazards/walls)
    2. Filter: GMI admissibility (in_K check)
    3. Filter: coherence Lyapunov rule (V_coh descent)
    4. Filter: absorption at b=0 (only dissipative moves)
    5. Select: highest task score among survivors
    
    Returns (selected_proposal, rejection_reasons)
    """
    safe = []
    for p in proposals:
        reasons = []
        
        # === FIX 4: Stronger Governor ===
        
        # Gate 1: Environment safety (no hazard/wall)
        next_pos = p.expected_next_position
        cell = state.grid[next_pos[1]][next_pos[0]]
        if cell in (CELL_WALL, CELL_HAZARD):
            reasons.append(f"environment_unsafe_cell_{cell}")
        
        # Gate 2: GMI admissibility check
        # Predict next GMI state (approximate using known dynamics)
        gmi_next = predict_gmi_state(gmi_state, p.action, gmi_params)
        if not in_K(gmi_next, gmi_params):
            reasons.append("gmi_admissibility_violation")
        
        # Gate 3: Coherence Lyapunov (must descend or stay same)
        V_coh_prev = V_extended_q(gmi_state, gmi_params)
        V_coh_next = V_extended_q(gmi_next, gmi_params)
        if V_coh_next > V_coh_prev:
            reasons.append(f"coherence_lyapunov_increase_{V_coh_next}_{V_coh_prev}")
        
        # Gate 4: Absorption at b=0
        if gmi_state.b <= 0:
            # At absorption, only allow V_coh-neutral or V_coh-decreasing moves
            if V_coh_next > V_coh_prev:
                reasons.append("absorption_violation")
        
        if not reasons:
            safe.append(p)
    
    if not safe:
        return None, reasons  # All rejection reasons
    
    # Select best task score (lexicographic: safety done, now optimize)
    best = max(safe, key=lambda p: p.task_score)
    return best, []
```

#### 5. CLATL Runtime (`clatl_runtime.py`)

```python
@dataclass
class CLATLStepReceipt:
    """Receipt for one CLATL step (includes ProposalSet commitment for replay)."""
    step: int
    gmi_receipt: GMIStepReceipt              # From GMI kernel
    
    # === FIX 3: ProposalSet receipt for deterministic replay ===
    proposalset_root: bytes                  # Merkle root of all proposals
    proposalset_slab_id: Optional[str]       # Slab ID if stored externally
    chosen_proposal_index: int              # Index of selected proposal
    chosen_proposal_hash: bytes              # Hash of chosen proposal
    
    task_performance: int                    # V_task after this step
    
@dataclass
class CLATLRunReceipt:
    """Complete receipt for a CLATL run."""
    run_id: str
    initial_gmi_state_hash: bytes
    initial_gridworld_hash: bytes
    drift_seed: int                          # Seed for deterministic goal drift
    goal_drift_schedule: List[int]           # Steps at which goal shifts
    step_receipts: List[CLATLStepReceipt]   # Each step with ProposalSet commitment
    task_performance: List[int]              # V_task at each step
    invariant_violations: List[str]          # Any safety violations
    
def run_clatl_episode(
    gmi_state: GMIState,
    gridworld: GridWorldState,
    max_steps: int,
    goal_drift_every: int,
    drift_seed: int,                         # FIX 2: seeded drift
    params: GMIParams
) -> CLATLRunReceipt:
    """Execute one CLATL episode with full receipt (deterministic)."""
    
    receipts = []
    task_perf = []
    
    # FIX 2: Initialize deterministic drift generator with seed
    drift_gen = DeterministicDrift(drift_seed)
    
    for t in range(max_steps):
        # 1. Drift goal if scheduled (deterministic)
        if t > 0 and t % goal_drift_every == 0:
            gridworld = drift_goal(gridworld, next(drift_gen))
        
        # 2. Get observation
        obs = get_observation(gridworld)
        
        # 3. Get coherence state
        V_coh = V_extended_q(gmi_state, params)
        
        # 4. Propose actions (receipted)
        proposals = proposer.propose(state=gridworld, obs=obs, V_coh=V_coh, memory=memory)
        
        # FIX 3: Build ProposalSet receipt BEFORE selection
        proposalset_root = build_merkle_root(proposals)
        
        # 5. Governor selects action (lexicographic: safety first, then task)
        selected, reasons = governor.select_action(
            proposals, gridworld, gmi_state, params
        )
        
        if selected is None:
            # No safe action - record violation
            violations.append(f"step_{t}:{reasons}")
            continue
            
        # 6. Execute in environment (deterministic)
        next_gridworld, reward = env_step(gridworld, selected.action)
        
        # 7. Execute in GMI (update coherence state)
        gmi_action = translate_to_gmi_action(selected.action)
        gmi_next, step_receipt = gmi_step(gmi_state, gmi_action, {}, params, chain)
        
        # 8. Record with ProposalSet commitment
        step_rec = CLATLStepReceipt(
            step=t,
            gmi_receipt=step_receipt,
            proposalset_root=proposalset_root,
            proposalset_slab_id=None,
            chosen_proposal_index=proposals.index(selected),
            chosen_proposal_hash=hash_proposal(selected),
            task_performance=V_task_distance(next_gridworld)
        )
        receipts.append(step_rec)
        task_perf.append(V_task_distance(next_gridworld))
        
        # 9. Update state
        gridworld = next_gridworld
        gmi_state = gmi_next
        
    return CLATLRunReceipt(...)
```

---

## Directory Structure

```
src/cnsc_haai/
├── tasks/                    # NEW: Task layer
│   ├── __init__.py
│   ├── gridworld_env.py     # Deterministic env + seed receipt
│   └── task_loss.py         # V_task definitions
├── agent/                    # NEW: Agent layer
│   ├── __init__.py
│   ├── clatl_runtime.py      # Closed-loop runner
│   ├── proposer_iface.py    # NPE adapter
│   └── governor_iface.py   # TGS adapter
└── gmi/                      # Existing (unchanged)
    └── ...

compliance_tests/clatl/        # NEW: CLATL compliance tests
├── __init__.py
├── test_invariants_never_break.py
├── test_replay_exact.py
├── test_task_improves_under_budget.py
└── test_recovery_after_goal_shift.py
```

---

## Implementation Steps

### Step 1: Create Task Layer (`tasks/`)

1. **`gridworld_env.py`**
   - Define `GridWorldState`, `GridWorldObs` dataclasses
   - Implement deterministic `env_step()` with seed
   - Implement `drift_goal()` for non-stationary objective
   - Add receipt generation (hash of initial state + seed)

2. **`task_loss.py`**
   - Implement `V_task_distance()` - Manhattan distance
   - Implement `V_task_success()` - binary success indicator
   - Define `λ(t)` scheduler (piecewise constant)

### Step 2: Create Agent Layer (`agent/`)

3. **`proposer_iface.py`**
   - Define `TaskProposal` dataclass
   - Implement `TaskProposer` with deterministic exploration bonus
   - Formula: `Score = -V_task + α(b) * 1/sqrt(N(s)+1)`
   - Where `α(b) = min(b / b_max, 1)` - shrinks with budget

4. **`governor_iface.py`**
   - Implement `select_action()` with lexicographic filtering
   - Gate 1: hazard avoidance
   - Gate 2: GMI admissibility check
   - Gate 3: budget availability
   - Return selected action or None with reasons

5. **`clatl_runtime.py`**
   - Implement `run_clatl_episode()`
   - Implement `CLATLRunReceipt` dataclass
   - Wire together: Env → Proposer → Governor → GMI
   - Add full receipt chain for replay

### Step 3: Create Compliance Tests (`compliance_tests/clatl/`)

6. **`test_invariants_never_break.py`**
   - Test: `z_t ∈ K` always (no admissibility violation)
   - Test: `b_t ≥ 0` always (no budget violation)
   - Test: No hazard collisions

7. **`test_replay_exact.py`**
   - Test: Same seed + same actions → exact same trajectory
   - Test: Receipt chain verification

8. **`test_task_improves_under_budget.py`**
   - Test: Rolling average distance-to-goal decreases over episodes
   - Test: Performance improves with more budget
   - Test: Success rate increases

9. **`test_recovery_after_goal_shift.py`**
   - Test: Inject goal drift, measure recovery time
   - Test: No invariant violations during recovery
   - Test: Performance recovers to baseline

---

## Key Invariants (to be verified by tests)

| Invariant | Description | Test |
|-----------|-------------|------|
| **Admissibility** | `in_K(gmi_state) == True` at all steps | `test_invariants_never_break` |
| **Budget** | `b >= 0` at all steps | `test_invariants_never_break` |
| **Safety** | No hazard collisions | `test_invariants_never_break` |
| **Determinism** | Replay produces identical轨迹 | `test_replay_exact` |
| **Competence** | Task loss decreases over time | `test_task_improves_under_budget` |
| **Recovery** | Goal shift → recover without violations | `test_recovery_after_goal_shift` |

---

## Metrics to Track

### Competence (should improve)
- `P(t)` = rolling average distance-to-goal
- Success rate (reached goal / total episodes)
- Regret = optimal distance - actual distance

### Safety (should be flat zero)
- `sum(1 for s in states if not in_K(s))` = 0
- Hazard hit count = 0
- Negative budget count = 0

### Metabolic (should follow patterns)
- Budget trajectory `b_t`
- Path-integral `W_slab`
- Exploration activity

---

## Dependencies on Existing Code

| Existing Module | Usage |
|-----------------|-------|
| `cnsc_haai.gmi.types.GMIState` | Coherence state |
| `cnsc_haai.gmi.types.GMIAction` | Action representation |
| `cnsc_haai.gmi.lyapunov.V_extended_q` | Coherence Lyapunov |
| `cnsc_haai.gmi.admissible.in_K` | Admissibility check |
| `cnsc_haai.gmi.step.gmi_step` | GMI state transition |
| `cnsc_haai.gmi.params.GMIParams` | Parameters |
| `cnsc_haai.consensus.chain` | Receipt chain |

---

## Success Criteria

1. **All 4 compliance tests pass**
2. **Task performance improves** across episodes (distance-to-goal decreases)
3. **Zero safety violations** in 100+ episode runs
4. **Exact replay** verified via receipt chain
5. **Recovery within 20 steps** after goal drift

---

## Future Extensions (Post-Phase 1)

- Task B: Online function approximation
- Stochastic exploration (PRNG seeded by receipts)
- Multi-agent coordination
- The "capstone theorem" proof: persistent bounded excitation → non-zero competence
