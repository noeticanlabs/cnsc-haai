# Phase 3 Implementation Plan: Governed Planning + Skills

## Executive Summary

This plan implements Phase 3 of the CNSC-HAAI system: **Governed Planning + Skills (GMI v3 / CLATL Phase 3)**. Phase 3 adds multi-step lookahead planning to the existing reactive policy system while maintaining all Phase 1-2 invariants: budget governance, deterministic receipts, and replay verification.

### Dependencies
- **Phase 1**: GMI kernel (`src/cnsc_haai/gmi/`) - ✅ Complete
- **Phase 2**: Learning system (`src/cnsc_haai/learn/`, `src/cnsc_haai/model/`) - ✅ Complete
- **Phase 3**: Planning + Skills - 📋 This plan

---

## Architecture

```
src/cnsc_haai/
├── agent/                      # Orchestration (existing)
│   └── clatl_runtime.py       # Will call planner or reactive proposer
│
├── model/                      # Predictive substrate (existing)
│   ├── encoder.py
│   ├── dynamics.py            # Used by planning for rollouts
│   └── predictor.py
│
├── planning/                   # NEW: Planning engine
│   ├── __init__.py
│   ├── planner_mpc.py         # Main entry: plan_and_select(...)
│   ├── planset_generator.py   # Deterministic PlanSet generation
│   ├── plan_gating.py         # Stepwise safety + budget feasibility
│   ├── plan_scoring.py        # J(Pi) computation
│   ├── plan_receipts.py       # PlanSetReceipt, PlanDecisionReceipt
│   ├── plan_merkle.py         # Merkle tree for plan commitment
│   └── tie_break.py           # Deterministic tie-breaking
│
├── options/                    # NEW: Skills/Options
│   ├── __init__.py
│   ├── option_types.py        # Option dataclass
│   ├── option_registry.py    # Registry + built-in skills
│   ├── option_runtime.py     # Execute options
│   └── option_receipts.py    # Option receipts
│
└── tasks/
    └── benchmarks/            # NEW: Planning benchmarks
        ├── __init__.py
        ├── key_door_maze.py
        ├── delayed_corridor.py
        └── beacon_lag.py
```

### Dependency Rules
- `planning/` may import `model/` and `tasks/` but **must not** import `agent/`
- `options/` can be used by `planning/` but should not depend on `planning/`
- `agent/` imports `planning/` and decides when to use it

---

## Step-by-Step Implementation

### Step 1: Create planning/ Package

#### 1.1 planset_generator.py
**Purpose**: Generate deterministic candidate plans using mixed-radix indexing

**Key Functions**:
- `generate_planset(base_actions: List, H: int, m: int, seed: int) -> List[Plan]`
- Uses hash-based action selection: `action = base_actions[hash(i||h||seed) % A]`
- Includes special plans: greedy, wall-follow, backtrack, stay

**Receipt Integration**: Each plan gets a deterministic hash for Merkle inclusion

#### 1.2 plan_gating.py
**Purpose**: Verify plan safety and budget feasibility step-by-step

**Key Functions**:
- `gate_plan(plan: Plan, state: GMIState, model, budget: int) -> GateResult`
- Checks per step:
  - Hazard avoidance (mapped from latent to grid)
  - Admissibility bounds (position inside map)
  - Budget feasibility (projected b >= 0 after planning+execution)
- Returns: `GateResult(accepted: bool, reason_codes: List[str])`

**Absorption Rule**: If `b == 0`, only "Stay" plan is admissible

#### 1.3 plan_scoring.py
**Purpose**: Compute J(Pi) for admissible plans

**Key Functions**:
- `score_plan(plan: Plan, state: GMIState, model, goal_pos, hazard_mask) -> QFixed`
- Formula:
  ```
  J(Pi) = sum_h [lambda_T * V_task(s_hat_h) + lambda_C * CurvPenalty(C_t, s_hat_h) - alpha(b) * InfoGain(s_hat_h, a_h)] + lambda_F * V_task(s_hat_H)
  ```
- V_task: predicted distance-to-goal
- CurvPenalty: penalize hazard-proximal trajectories
- InfoGain: optional (ensemble disagreement or residual)

#### 1.4 plan_receipts.py
**Purpose**: Define receipt structures for planning

**Key Types**:
```python
@dataclass(frozen=True)
class PlanSetReceipt:
    t: int                          # Step index
    env_state_hash: str
    gmi_state_hash: str
    planner_config_hash: str       # H, m, weights
    seed: int
    planset_root: str               # Merkle root
    plans_count: int
    horizon: int

@dataclass(frozen=True)
class PlanDecisionReceipt:
    t: int
    planset_root: str
    chosen_plan_index: int
    chosen_plan_hash: str
    gate_reason_codes_summary: Dict[str, int]
    chosen_action: GMIAction
    predicted_cost_J: QFixed
    budget_before: int
    budget_after_planning: int
```

#### 1.5 tie_break.py
**Purpose**: Deterministic tie-breaking when scores are equal

**Key Functions**:
- `tie_break_plans(plans: List[Plan], scores: List[QFixed]) -> Plan`
- Lexicographic by: plan_hash (ascending)
- Ensures reproducibility

#### 1.6 planner_mpc.py
**Purpose**: Main MPC planning entry point

**Key Functions**:
- `plan_and_select(state: GMIState, model, budget: int, config: PlannerConfig) -> Tuple[GMIAction, PlanningReceipts]`
- MPC Loop:
  1. Generate PlanSet (deterministic)
  2. Commit PlanSet (Merkle root)
  3. Gate each plan (safety-first)
  4. Score admissible plans
  5. Tie-break if needed
  6. Return first action + receipts

**Budget-Adaptive**:
```python
m = min(m_max, 1 + b // b_unit)
H = min(H_max, 1 + b // h_unit)
```

---

### Step 2: Create options/ Package

#### 2.1 option_types.py
**Purpose**: Define Option structure

```python
@dataclass(frozen=True)
class Option:
    id: str
    initiation: Callable[[LatentState], bool]  # I(s)
    termination: Callable[[LatentState], bool] # beta(s)
    policy: Callable[[LatentState], GMIAction] # pi_omega(s)
    max_steps: int
```

#### 2.2 option_registry.py
**Purpose**: Registry of built-in skills

**Built-in Options**:
- `GoToGoalGreedy`: Move toward goal by delta
- `AvoidHazardGradient`: Move away from hazard mask
- `WallFollowLeft`: Follow wall on left
- `WallFollowRight`: Follow wall on right
- `BacktrackLastSafe`: Return to last safe position

**Key Functions**:
- `get_option(option_id: str) -> Option`
- `list_options() -> List[str]`
- All options deterministic

#### 2.3 option_runtime.py
**Purpose**: Execute options, unfold to primitive actions

**Key Functions**:
- `execute_option(option: Option, state: LatentState) -> OptionExecution`
- Tracks internal steps
- Respects max_steps and termination
- Each internal action passes through governor

#### 2.4 option_receipts.py
**Purpose**: Receipts for option execution

```python
@dataclass(frozen=True)
class OptionStartReceipt:
    t: int
    option_id: str
    start_state_hash: str

@dataclass(frozen=True)
class OptionStepReceipt:
    t: int
    option_id: str
    internal_step: int
    action: GMIAction
    resulting_state_hash: str

@dataclass(frozen=True)
class OptionEndReceipt:
    t: int
    option_id: str
    total_steps: int
    final_state_hash: str
    termination_reason: str
```

---

### Step 3: Create Benchmarks

#### 3.1 key_door_maze.py
**Environment**:
- Start → Key → Door → Goal
- Door blocks goal unless key acquired
- Hazards create dead-ends that greedy agents choose
- Goal shifts after door opens

**Why it forces planning**: Requires "subgoal then goal" - must get key before door

#### 3.2 delayed_corridor.py
**Environment**:
- Two corridors: short (ends in hazard trap) vs long (safe)
- Only lookahead avoids repeated trap

**Why it forces planning**: Requires anticipating future hazard

#### 3.3 beacon_lag.py
**Environment**:
- Goal beacon delayed/noisy
- POMDP with partial observability

**Why it forces planning**: Reactive policy dithers; planner integrates belief

---

### Step 4: Compliance Tests

#### 4.1 test_planset_receipt_required.py
**Verifies**:
- Chosen plan has PlanSet commitment
- Chosen plan is member of committed PlanSet (Merkle proof)

#### 4.2 test_budget_charged_for_planning.py
**Verifies**:
- Budget debit = κ_plan * m * H + κ_gate * m + κ_exec
- Proportional to planning work

#### 4.3 test_invariants_never_break_under_planning.py
**Verifies** (on all benchmarks):
- Hazards never entered
- State always in bounds
- Budget never negative
- Absorption respected at b=0

#### 4.4 test_planner_beats_phase2_baseline.py
**Verifies**:
- On Key-Door Maze: planner success rate > baseline + 30%
- OR median steps-to-goal < baseline - threshold
- Baseline = Phase 2 policy without planning

#### 4.5 test_replay_reconstructs_plan_choice.py
**Verifies**:
- Replay reproduces: PlanSet root, chosen plan hash, first action, state hash
- Any mismatch = test fail

---

### Step 5: Integration into CLATL Runtime

#### 5.1 Modify agent/clatl_runtime.py
- Add planner proposer option
- Switch between reactive and planning based on config/flags

#### 5.2 Extend GMIState
- Add `phase: int` field (1, 2, or 3)
- Add `planner_config: PlannerConfig` field

#### 5.3 Wire Budget-Adaptive Planning
- Implement m(H) and H(b) functions
- Disable planning at b=0 (absorption)

---

### Step 6: Budget Law Extensions

#### 6.1 Extend gmi/types.py
- Add `planning_work: WorkUnits` to step request
- Define constants: κ_plan, κ_gate, κ_exec

#### 6.2 Update gmi/step.py
- Deduct planning costs before action execution
- Apply absorption rule

#### 6.3 Absorption Rule
```python
if budget == 0:
    # Only safe idle allowed
    action = Stay
    planning_disabled = True
```

---

## Mermaid: Phase 3 Runtime Flow

```mermaid
flowchart TD
    A[Observe o_t] --> B[Encode s_t = encode<br>o_t, M_t, pi_t]
    B --> C{b == 0?}
    C -->|Yes| D[Absorption Mode<br>action = Stay]
    C -->|No| E[Generate PlanSet 𝓟_t]
    E --> F[Receipt-Commit<br>Merkle root]
    F --> G[Gate Each Plan<br>safety + budget]
    G --> H[Score Admissible Plans<br>J(Pi)]
    H --> I[Tie-Break<br>lexicographic]
    I --> J[Execute a_t = Π*[0]]
    D --> K[Update GMI State]
    J --> K
    K --> L[Record Receipts<br>PlanSet + Decision]
    L --> M[Update Memory<br>+ Learning]
    M --> N[Next Step]
```

---

## Acceptance Criteria

Phase 3 is **complete** when:

1. ✅ All 5 Phase 3 compliance tests pass
2. ✅ Planner beats Phase 2 baseline on 2/3 planning benchmarks
3. ✅ No invariant violations across 1000+ steps
4. ✅ Replay reproduces plan decisions exactly

---

## Implementation Priority

1. **First**: PlanSet generation + receipts (enables verification)
2. **Second**: Gating (safety-first prevents disasters)
3. **Third**: Scoring (task + curvature)
4. **Fourth**: Replay test (forces determinism)
5. **Fifth**: Key-Door benchmark + baseline comparison
6. **Sixth**: Options (if time permits)
7. **Seventh**: Remaining benchmarks

This order prevents "planner works but can't be reproduced" failures.

---

## Risk Mitigation

| Risk | Mitigation |
|------|-------------|
| Determinism bugs | Use test_replay_reconstructs_plan_choice early |
| Safety violations | Gate all plans before scoring |
| Budget exhaustion | Implement absorption rule rigorously |
| Performance regression | Test planner vs baseline on each benchmark |

---

*Plan created for Phase 3: Governed Planning + Skills*
*Dependencies: Phase 1 (GMI kernel), Phase 2 (Learning)*
