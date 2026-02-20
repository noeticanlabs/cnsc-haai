# Topology Change Budget

**Budget Constraints for Atlas Topology Changes**

| Field | Value |
|-------|-------|
| **Module** | 10_mathematical_core |
| **Section** | Topology Change Budget |
| **Version** | 1.0.0 |
| **Status** | ACTIVE |

---

## 1. Overview

This specification defines the budget constraints for topology changes in the Atlas (cognitive state graph). Topology changes include:
- **Expansion**: Adding new nodes/edges to the atlas
- **Pruning**: Removing nodes/edges from the atlas
- **Restructuring**: Changing the connectivity pattern

---

## 2. Topology Metrics

### 2.1 Atlas Rank (r)

The rank of an atlas A is the number of active nodes:

```
r(A) = |nodes(A)|
```

### 2.2 Structural Change (Δ_struct)

The structural change is the difference in rank:

```
Δ_struct = r(A_next) - r(A_prev)
```

| Δ_struct | Meaning |
|----------|---------|
| Δ_struct > 0 | Expansion |
| Δ_struct < 0 | Pruning |
| Δ_struct = 0 | Restructuring only |

---

## 3. Budget Gate

A topology change is allowed only if:

```
b >= Δ_struct
```

Where:
- `b` = current budget (in QFixed units)
- `Δ_struct` = structural change magnitude

### 3.1 Expansion Gate

When expanding (adding nodes):

```
Require: b >= Δ_struct
New_budget = b - Δ_struct
```

### 3.2 Pruning Gate

When pruning (removing nodes):

```
Allow if: b >= 0  (budget can go negative for pruning?)
```

Actually, for pruning we compute a **distortion bound** rather than deducting budget.

---

## 4. Distortion Bound (Pruning)

When pruning, we compute a distortion bound that must be within limits:

### 4.1 Distortion Metrics

| Metric | Description |
|--------|-------------|
| `|Δ_connectivity|` | Change in connectivity |
| `|Δ_weight_sum|` | Change in total edge weight |
| `spectral_gap` | Change in spectral radius |

### 4.2 Bound Computation

```
distortion_bound = α * |Δ_connectivity| + β * |Δ_weight_sum| + γ * |spectral_gap|
```

Where α, β, γ are constants.

### 4.3 Pruning Constraint

```
distortion_bound <= MAX_DISTORTION
```

---

## 5. Hysteresis Band

Topology changes are guarded by a hysteresis band to prevent chatter:

```
|Δ_struct| >= HysteresisThreshold
```

Common values:
- `HysteresisThreshold = 1` (minimum 1 node change)
- `HysteresisThreshold = r(A) * 0.1` (10% of current size)

---

## 6. Slab Boundary Constraint

**Critical**: Topology changes can only occur at slab boundaries.

```
TopologyChangeAllowed(slab_index) = True
TopologyChangeAllowed(slab_index + 0.5) = False  # mid-slab
```

This ensures:
1. All micro receipts in a slab share the same topology
2. Merkle proofs are valid for the entire slab
3. Fraud proofs can reference a consistent state

---

## 7. Implementation Requirements

### 7.1 Budget Tracking

```python
def check_topology_change_budget(budget_q: int, delta_struct: int) -> bool:
    """
    Check if budget allows topology change.
    
    Args:
        budget_q: Current budget (QFixed)
        delta_struct: Structural change (positive = expansion)
    
    Returns:
        True if change is allowed
    """
    if delta_struct > 0:
        # Expansion: deduct from budget
        return budget_q >= delta_struct
    else:
        # Pruning: check distortion bound
        return True  # Check distortion separately
```

### 7.2 Slab Synchronization

```python
def is_slab_boundary(height: int) -> bool:
    """Check if at slab boundary."""
    return height % SLAB_SIZE == 0

def allow_topology_change(current_height: int) -> bool:
    """Only allow at slab boundaries."""
    return is_slab_boundary(current_height)
```

---

## 8. References

- [Continuous Manifold Flow](./continuous_manifold_flow.md)
- [Slab Compression Rules](../30_ats_runtime/slab_compression_rules.md)
- [Budget Law](./budget_law.md)
