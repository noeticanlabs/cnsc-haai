# 19. Runtime API

## 19.1 Overview

The GMI Runtime (`GMIRuntime`) provides the high-level interface for executing GMI ticks with proposal handling, gate evaluation, and complete receipt generation.

## 19.2 Core Functions

### gmi_tick

The main entry point for executing a single GMI step:

```
gmi_tick(
    state: GMIState,
    observation: bytes,
    proposals: List[Proposal],
    ctx: Dict[str, Any],
    chain_prev: bytes,
    params: Optional[GMIParams] = None,
) -> Tuple[GMIState, GMIRuntimeReceipt]
```

**Parameters:**
- `state` - Current GMI state
- `observation` - External observation bytes
- `proposals` - List of proposals from predictor (may be empty)
- `ctx` - Execution context dictionary
- `chain_prev` - Previous chain hash for receipt chaining
- `params` - Optional GMI parameters (uses defaults if None)

**Returns:**
- Tuple of (new_state, runtime_receipt)

### GMIRuntime Class

Stateful wrapper for continuous GMI execution:

```python
class GMIRuntime:
    def __init__(self, params: Optional[GMIParams] = None): ...
    def tick(self, observation: bytes, proposals: List[Proposal]) -> GMIRuntimeReceipt: ...
    @property
    def state(self) -> GMIState: ...
    @property
    def chain_tip(self) -> bytes: ...
```

## 19.3 Receipt Types

### GMIRuntimeReceipt

Extended receipt including proposal metadata:

```python
@dataclass(frozen=True)
class GMIRuntimeReceipt:
    step_receipt: GMIStepReceipt      # Core step receipt
    proposal_set_root: Optional[bytes] # Merkle root of proposals
    proposal_count: int               # Number of proposals evaluated
    selected_proposal_id: Optional[str] # ID of selected proposal (if any)
    gate_decisions: List[GateDecision] # Per-proposal gate results
    work_units: WorkUnits             # Metabolic work tracking
    total_work_q: int                 # Total work in Q units
```

### WorkUnits

Metabolic budget consumption tracking:

```python
@dataclass(frozen=True)
class WorkUnits:
    proposal_generation_cost: int = 0
    witness_acquisition_cost: int = 0
    gate_evaluation_cost: int = 0
    execution_cost: int = 0
    memory_write_cost: int = 0
    repair_cost: int = 0
```

## 19.4 Proposal Handling

### Proposal Selection

The runtime deterministically selects proposals based on score (highest first):

```python
@dataclass(frozen=True)
class Proposal:
    proposal_id: str
    action: GMIAction
    score: int           # Higher score = higher priority
    metadata: Dict[str, Any]
```

### Gate Decision

Each proposal is evaluated through the gate stack:

```python
@dataclass(frozen=True)
class GateDecision:
    proposal_id: str
    accepted: bool
    rejection_code: Optional[str]
    kkt_residual: Optional[int]
```

## 19.5 Determinism Guarantees

The runtime ensures determinism through:

1. **Proposal Ordering**: Proposals are sorted by score (descending), then by proposal_id (ascending) for tie-breaking
2. **Merkle Root**: ProposalSet is committed to a Merkle root for cryptographic receipt
3. **Integer Arithmetic**: All computations use QFixed6 (no floats)
4. **Chain Hashing**: Each receipt includes chain_prev for tamper-evident chaining

## 19.6 CNHAI Mapping

| GMI Runtime Concept | CNHAI Equivalent |
|---------------------|------------------|
| GMIRuntime | GMI Kernel Wrapper |
| gmi_tick | Single Step Execution |
| WorkUnits | BudgetAccounting |
| proposal_set_root | NPE Receipt Merkle |
| chain_tip | Receipt Chain |

## 19.7 Usage Example

```python
from cnsc_haai.gmi import (
    GMIState, GMIRuntime, GMIParams,
    GMIAction, Proposal
)

# Initialize runtime
params = GMIParams.default()
runtime = GMIRuntime(params=params)

# Create proposal
action = GMIAction(action_type=1, params={})
proposal = Proposal(
    proposal_id="prop_001",
    action=action,
    score=1000,
    metadata={}
)

# Execute tick
receipt = runtime.tick(
    observation=b"observation_data",
    proposals=[proposal]
)

# Verify receipt
print(f"Chain tip: {receipt.step_receipt.chain_hash.hex()}")
print(f"Selected: {receipt.selected_proposal_id}")
print(f"Work: {receipt.total_work_q}")
```
