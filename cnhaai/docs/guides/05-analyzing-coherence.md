# Guide 05: Analyzing Coherence

**Version**: 1.0.0
**Status**: DRAFT

---

## ⚠️ CRITICAL: Use Correct Coherence Module

> **WARNING**: This codebase has TWO coherence implementations with DIFFERENT purposes:

| Module | Purpose | Use For |
|--------|---------|---------|
| `cnhaai.core.coherence` | UI display only | NOTHING ATS-related |
| `cnsc.haai.ats.risk` | Deterministic verification | ATS verification |

**For analyzing coherence in the ATS stack, use `cnsc.haai.ats.risk`, NOT `cnhaai.core.coherence`.**

---

## Overview

This guide explains how to analyze coherence in CNHAAI using the correct deterministic module.

---

## Coherence Analysis with ATS Kernel

### Step 1: Import Correct Module

```python
# WRONG - UI only
from cnhaai.core.coherence import CoherenceBudget  # DON'T USE

# CORRECT - Deterministic ATS
from cnsc.haai.ats.risk import CoherenceRisk
from cnsc.haai.ats.numeric import QFixed
```

### Step 2: Analyze Risk Functional

```python
from cnsc.haai.ats.risk import CoherenceRisk, RiskState

# Create risk analyzer
risk = CoherenceRisk()

# Analyze current state
state = RiskState(
    budget=QFixed(1000, 18),
    residual_dynamical=0.1,
    residual_clock=0.05
)

# Compute risk functional V(s)
v = risk.compute_V(state)
print(f"Risk functional V: {v}")

# Check admissibility
is_admissible = risk.check_admissibility(state)
print(f"State admissible: {is_admissible}")
```

### Step 3: Budget Transitions

```python
from cnsc.haai.ats.budget import BudgetTransition

transition = BudgetTransition(
    current_budget=QFixed(1000, 18),
    risk_delta=QFixed(-50, 18),
    min_budget=QFixed(100, 18)
)

new_budget = transition.apply()
print(f"New budget: {new_budget}")
```

---

## Coherence Metrics

| Metric | Description | Range |
|--------|-------------|-------|
| V(s) | Risk functional | 0.0 - 1.0 |
| B | Budget | QFixed |
| ∇_u u | Dynamical residual | float |
| g(u,u)+1 | Clock residual | float |

---

## Best Practices

1. **Use ATS kernel**: Always use `cnsc.haai.ats.*` for verification
2. **Determinism**: Use QFixed for all numeric operations
3. **Immutability**: Never modify budget in place
4. **Logging**: Log all risk computations

---

## Common Issues

| Issue | Solution |
|-------|----------|
| Using wrong module | Use `cnsc.haai.ats.risk` |
| Float overflow | Use QFixed arithmetic |
| Non-deterministic | Ensure no float operations |

---

## Related Documents

- [Coh Kernel Scope](../../docs/ats/00_identity/coh_kernel_scope.md)
- [Risk Functional V](../../docs/ats/10_mathematical_core/risk_functional_V.md)
- [Budget Law](../../docs/ats/10_mathematical_core/budget_law.md)
