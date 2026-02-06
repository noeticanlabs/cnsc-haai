# Canonical Algorithms

Each algorithm must declare inputs, outputs, gate checks, rail bounds, and receipt emission points.

## 1) Banker Algorithm (accept/retry/abort)

**Inputs:** state \(x\), proposal \(\Delta x\), gate policy \(G\), rails \(R\), budget \(B\), policy id.

**Outputs:** decision \(\in\{\text{accept},\text{retry},\text{abort}\}\), receipt.

**Pseudocode:**

```
compute r(x + Δx)
compute C(x + Δx)
check hard gates
if hard gates fail:
  apply bounded rail
  emit receipt(decision=retry|abort, reason=hard_gate_fail)
  return retry or abort
check soft gates with hysteresis
if soft gates fail:
  apply bounded rail
  emit receipt(decision=retry|abort, reason=soft_gate_fail)
  return retry or abort
accept step
emit receipt(decision=accept, reason=policy_satisfied)
return accept
```

**Receipt emission points:** after each gate evaluation and after any rail application.

## 2) Repair / Projection Algorithm

**Inputs:** state \(x\), constraints \(\mathcal K\), projection bound \(\beta\).

**Outputs:** repaired state \(x'\), repair receipt.

**Pseudocode:**

```
find projection x' = Π_K(x) subject to ||x' - x|| ≤ β
recompute residuals and debt
emit receipt with before/after and bound β
return x'
```

## 3) Backtracking / Checkpoint Algorithm

**Inputs:** checkpoint list \(\{x_k\}\), retry limit \(N\).

**Outputs:** selected checkpoint, receipt.

**Pseudocode:**

```
if retry_count > N:
  emit receipt(decision=abort, reason=retry_limit)
  abort
select most recent checkpoint
restore state
emit receipt with checkpoint hash
return state
```

## 4) Evidence Escalation Algorithm

**Inputs:** claim set \(S\), tool budget \(T\), depth limit \(D\).

**Outputs:** expanded evidence, receipt.

**Pseudocode:**

```
while budget remains and gates require evidence:
  query tool
  verify constraints
  update residuals
emit receipt with tool actions and bounds
```

## Rail priority policy (single canonical ordering)

1. **Hard gate rails** (e.g., NaN/Inf repair, projection).
2. **Step-size / damping rails** (stability control).
3. **Evidence / backtrack rails** (knowledge repair).
4. **Abort** if bounds are exhausted.
