# State Space

**Canonical Cognitive State Space Definition**

| Field | Value |
|-------|-------|
| **Module** | 10_mathematical_core |
| **Section** | State Space |
| **Version** | 1.0.0 |

---

## 1. State Space Definition

The canonical state space X is defined as the Cartesian product of five cognitive components:

```
X = X_belief × X_memory × X_plan × X_policy × X_io
```

Each component must satisfy:
- **Canonical Serializability**: Produces deterministic byte representation
- **Deterministic Hashing**: Unique sha256 digest for each state
- **Type Safety**: Static typing known at verification time

---

## 2. Component Definitions

### 2.1 Belief Space (X_belief)

```
X_belief = { b | b: ConceptID → BeliefVector }
```

Represents the system's current beliefs about the world.

| Property | Specification |
|----------|---------------|
| **Keys** | ConceptID (deterministic string identifier) |
| **Values** | BeliefVector (QFixed(18) vector, L2-norm ≤ 1.0) |
| **Update** | Must preserve canonical ordering |

### 2.2 Memory Space (X_memory)

```
X_memory = { m | m: Address → MemoryCell }
```

Represents episodic and working memory.

| Property | Specification |
|----------|---------------|
| **Addressing** | Sequential integer indices |
| **Cells** | Type-tagged serialized objects |
| **Capacity** | Bounded by initial allocation |

### 2.3 Plan Space (X_plan)

```
X_plan = { p | p: StepID → PlannedAction }
```

Represents the current execution plan.

| Property | Specification |
|----------|---------------|
| **Ordering** | Ordered list (not dictionary) |
| **Steps** | StepID = sequential integer |
| **Actions** | Typed NSC operations |

### 2.4 Policy Space (X_policy)

```
X_policy = { π | π: StateRegion → ActionDistribution }
```

Represents the current control policy.

| Property | Specification |
|----------|---------------|
| **Mapping** | State → Action probability distribution |
| **Representation** | Sparse (only non-zero entries stored) |
| **Updates** | Versioned (old versions retained for replay) |

### 2.5 I/O Space (X_io)

```
X_io = (X_input, X_output, X_buffer)
```

Represents external interaction state.

| Component | Specification |
|-----------|---------------|
| **X_input** | Queue of pending inputs |
| **X_output** | Queue of produced outputs |
| **X_buffer** | Temporary I/O staging area |

---

## 3. Canonical Serialization Requirements

### 3.1 Byte Order

All multi-byte integers use **big-endian** encoding.

### 3.2 String Encoding

All strings use **UTF-8** encoding.

### 3.3 Collection Ordering

| Type | Ordering Rule |
|------|---------------|
| **Dictionary** | Keys sorted lexicographically |
| **List** | Order preserved as-is |
| **Set** | Converted to sorted list |

### 3.4 Type Tags

Every serialized object includes a type tag:

```json
{
  "__type": "X_belief",
  "__version": "1.0.0",
  "__data": { ... }
}
```

---

## 4. Deterministic Hashing

### 4.1 State Hash Computation

```
state_hash = sha256(canonical_bytes(state))
```

Where `canonical_bytes` produces:
1. Type tag (8 bytes)
2. Version (4 bytes)
3. Content (variable)

### 4.2 Collision Avoidance

The kernel enforces:
- No two distinct states produce the same hash
- Hash functions are treated as random oracles
- No預 collision attacks in consensus domain

---

## 5. State Validation Rules

A state x ∈ X is valid if and only if:

| Rule | Description |
|------|-------------|
| **T1** | All components serialize without error |
| **T2** | State hash is reproducible |
| **T3** | All type tags match expected schema |
| **T4** | No forbidden values (NaN, Infinity) |
| **T5** | Bounds constraints satisfied |

---

## 6. References

- [ATS Definition](../00_identity/ats_definition.md)
- [Canonical Serialization](../20_coh_kernel/canonical_serialization.md)
- [Action Algebra](./action_algebra.md)
- [Receipt Schema](../20_coh_kernel/receipt_schema.md)
