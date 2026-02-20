# Action Algebra

**Typed NSC Operations and Cognitive Updates**

| Field | Value |
|-------|-------|
| **Module** | 10_mathematical_core |
| **Section** | Action Algebra |
| **Version** | 1.0.0 |

---

## 1. Action Space Definition

The action algebra A defines the set of permissible operations within the ATS:

```
A = { act | act : X → X }
```

Each action is a deterministic function that transforms the state space X to itself.

---

## 2. Action Categories

### 2.1 Belief Operations (A_belief)

| Action | Signature | Description |
|--------|-----------|-------------|
| **BELIEF_UPDATE** | X_belief × ConceptID × BeliefVector → X_belief | Update belief about a concept |
| **BELIEF_MERGE** | X_belief × ConceptID × ConceptID → X_belief | Merge two beliefs |
| **BELIEF_DELETE** | X_belief × ConceptID → X_belief | Remove a belief |
| **BELIEF_RECALL** | X_belief × MemoryRef → X_belief | Retrieve belief from memory |

### 2.2 Memory Operations (A_memory)

| Action | Signature | Description |
|--------|-----------|-------------|
| **MEMORY_WRITE** | X_memory × Address × MemoryCell → X_memory | Write to memory |
| **MEMORY_READ** | X_memory × Address → MemoryCell | Read from memory |
| **MEMORY_ALLOC** | X_memory × Size → X_memory | Allocate memory |
| **MEMORY_FREE** | X_memory × Address → X_memory | Free memory |

### 2.3 Planning Operations (A_plan)

| Action | Signature | Description |
|--------|-----------|-------------|
| **PLAN_APPEND** | X_plan × PlannedAction → X_plan | Add action to plan |
| **PLAN_PREPEND** | X_plan × PlannedAction → X_plan | Add action to front |
| **PLAN_REMOVE** | X_plan × StepID → X_plan | Remove action from plan |
| **PLAN_CLEAR** | X_plan → X_plan | Clear entire plan |

### 2.4 Policy Operations (A_policy)

| Action | Signature | Description |
|--------|-----------|-------------|
| **POLICY_UPDATE** | X_policy × StateRegion × ActionDistribution → X_policy | Update policy mapping |
| **POLICY_COPY** | X_policy × PolicyID → X_policy | Copy policy version |
| **POLICY_ROLLBACK** | X_policy × PolicyID → X_policy | Revert to old policy |

### 2.5 I/O Operations (A_io)

| Action | Signature | Description |
|--------|-----------|-------------|
| **IO_INPUT** | X_io × InputData → X_io | Accept external input |
| **IO_OUTPUT** | X_io × OutputData → X_io | Produce external output |
| **IO_FLUSH** | X_io → X_io | Flush output buffer |

---

## 3. Action Type System

### 3.1 Type Signatures

Every action has a static type signature:

```
action_name : (InputTypes...) → OutputType
```

### 3.2 Type Validation

The verifier checks:
1. Action type exists in A
2. Input types match signature
3. Output type is valid X component
4. No type coercion occurs

### 3.3 Type Safety Rules

| Rule | Description |
|------|-------------|
| **T1** | All actions have explicit type signatures |
| **T2** | Type checking occurs before execution |
| **T3** | Invalid types result in rejection |
| **T4** | No dynamic type generation in consensus path |

---

## 4. Action Validity

### 4.1 Preconditions

An action act ∈ A is applicable to state x ∈ X if:

```
precondition(act, x) = true
```

### 4.2 Postconditions

Applying action act to state x produces:

```
x' = act(x)
```

Where x' must satisfy:
- x' ∈ X (valid state)
- x' serializes deterministically

### 4.3 Determinism Requirement

All actions must be deterministic:

```
∀x, act(x) = act(x)
```

Non-deterministic actions are rejected by the verifier.

---

## 5. Composite Actions

### 5.1 Action Sequences

Actions can be composed:

```
act_seq = act_1 ; act_2 ; ... ; act_n
```

The composition is valid if:
- Each act_i ∈ A
- Each precondition satisfied in sequence

### 5.2 Action Products

Parallel actions on independent state components:

```
act_product = (act_belief, act_memory, act_plan, act_policy, act_io)
```

Product is valid if all components are individually valid.

---

## 6. References

- [ATS Definition](../00_identity/ats_definition.md)
- [State Space](./state_space.md)
- [NSC Integration](../40_nsc_integration/nsc_vm_to_ats_bridge.md)
- [Receipt Schema](../20_coh_kernel/receipt_schema.md)
