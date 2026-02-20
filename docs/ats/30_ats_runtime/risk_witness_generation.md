# Risk Witness Generation

**Producing Verifiable Risk Evidence**

| Field | Value |
|-------|-------|
| **Module** | 30_ats_runtime |
| **Section** | Risk Witness Generation |
| **Version** | 1.0.0 |

---

## 1. Overview

A risk witness is the evidence that proves the risk functional V was computed correctly. The runtime generates witnesses; the kernel verifies them.

---

## 2. Witness Components

### 2.1 Required Witness Data

```json
{
  "risk_witness": {
    "state_hash": "sha256:...",
    "risk_value_q": "1000000000000000000",
    "components": {
      "belief": "500000000000000000",
      "memory": "200000000000000000",
      "plan": "100000000000000000",
      "policy": "100000000000000000",
      "io": "100000000000000000"
    },
    "weights": {
      "belief": "200000000000000000",
      "memory": "200000000000000000",
      "plan": "200000000000000000",
      "policy": "200000000000000000",
      "io": "200000000000000000"
    },
    "computation_proof": "sha256:..."
  }
}
```

### 2.2 Witness Fields

| Field | Type | Description |
|-------|------|-------------|
| **state_hash** | sha256 | Hash of state being measured |
| **risk_value_q** | QFixed(18) | Total risk V(x) |
| **components** | object | Risk per component |
| **weights** | object | Weights used in aggregation |
| **computation_proof** | sha256 | Hash of computation trace |

---

## 3. Generation Process

### 3.1 Component Risk Computation

```python
def compute_component_risks(state: State) -> ComponentRisks:
    return ComponentRisks(
        belief=V_belief(state.belief),
        memory=V_memory(state.memory),
        plan=V_plan(state.plan),
        policy=V_policy(state.policy),
        io=V_io(state.io)
    )
```

### 3.2 Aggregation

```python
def aggregate_risk(components: ComponentRisks, weights: Weights) -> QFixed:
    risk = (
        weights.belief * components.belief +
        weights.memory * components.memory +
        weights.plan * components.plan +
        weights.policy * components.policy +
        weights.io * components.io
    )
    return risk
```

### 3.3 Witness Construction

```python
def generate_risk_witness(state: State) -> RiskWitness:
    components = compute_component_risks(state)
    risk = aggregate_risk(components, STANDARD_WEIGHTS)
    
    return RiskWitness(
        state_hash=sha256(canonical_bytes(state)),
        risk_value_q=str(risk),
        components={k: str(v) for k, v in components.items()},
        weights=STANDARD_WEIGHTS,
        computation_proof=sha256(str(components) + str(STANDARD_WEIGHTS))
    )
```

---

## 4. Verification

### 4.1 Kernel Verification

The kernel verifies the witness by recomputing:

```python
def verify_risk_witness(witness: RiskWitness, state: State) -> bool:
    # Verify state hash
    if witness.state_hash != sha256(canonical_bytes(state)):
        return False
    
    # Recompute component risks
    components = compute_component_risks(state)
    
    # Verify each component
    for name, value in components.items():
        if witness.components[name] != str(value):
            return False
    
    # Recompute total
    total = aggregate_risk(components, witness.weights)
    if witness.risk_value_q != str(total):
        return False
    
    return True
```

---

## 5. Witness Properties

### 5.1 Determinism

| Property | Guarantee |
|----------|-----------|
| **Same State** | Same witness (always) |
| **Same Weights** | Witness reproducible |
| **Witness Checkable** | Independent verification |

### 5.2 Efficiency

| Operation | Complexity |
|-----------|------------|
| **Generation** | O(N) where N = state size |
| **Verification** | O(N) where N = state size |

---

## 6. Weight Standardization

### 6.1 Default Weights

```python
STANDARD_WEIGHTS = Weights(
    belief=0.2,   # 20%
    memory=0.2,   # 20%
    plan=0.2,    # 20%
    policy=0.2,   # 20%
    io=0.2       # 20%
)
```

### 6.2 Fixed Weights

Weights are **fixed at ATS initialization**:
- Cannot change during execution
- Stored in ATS configuration
- Same for all steps

---

## 7. References

- [Risk Functional V](../10_mathematical_core/risk_functional_V.md)
- [State Space](../10_mathematical_core/state_space.md)
- [RV Step Specification](../20_coh_kernel/rv_step_spec.md)
- [State Digest Model](./state_digest_model.md)
