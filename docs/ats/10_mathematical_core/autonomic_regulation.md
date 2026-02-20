# Autonomic Regulation

**μ Modulation and Fatigue Controller**

| Field | Value |
|-------|-------|
| **Module** | 10_mathematical_core |
| **Section** | Autonomic Regulation |
| **Version** | 1.0.0 |
| **Status** | ACTIVE |

---

## 1. Overview

This specification defines the autonomic regulation mechanism for the ATS, including:
- **μ (mu)**: Stiffness/modulation parameter in (0, 1]
- **f (fatigue)**: Fatigue parameter ≥ 0

These parameters modulate the repair operator, hysteresis thresholds, and tax rates.

---

## 2. Parameter Definitions

### 2.1 μ (Stiffness Modulator)

μ controls how "stiff" or "flexible" the coherence repair mechanism is:

| μ Value | Behavior |
|---------|----------|
| μ → 1 | High stiffness, aggressive repair |
| μ → 0 | Low stiffness, allows more drift |

Constraints:
```
0 < μ ≤ 1
```

### 2.2 f (Fatigue)

Fatigue accumulates over time as the system works:

```
f ≥ 0
```

Fatigue increases when:
- Risk increases despite repair attempts
- Budget is consumed rapidly

Fatigue decreases when:
- Risk decreases (coherence improves)
- Budget is preserved

---

## 3. ODE Dynamics

### 3.1 μ Dynamics (Slow Time)

```
dμ/dt = α_μ * (μ_target - μ) - β_μ * f
```

Where:
- μ_target = 1.0 (default, maximum stiffness)
- α_μ = adaptation rate
- β_μ = fatigue coupling

### 3.2 f Dynamics (Slow Time)

```
df/dt = γ * max(0, ΔV) - δ * (1 - μ) * f
```

Where:
- γ = risk accumulation rate
- δ = recovery rate
- ΔV = risk delta

---

## 4. Modulated Thresholds

### 4.1 θ_up (Upward Threshold)

Threshold for accepting risk increases:

```
θ_up(μ) = θ_base * μ
```

When μ is high, threshold is lower (stricter).

### 4.2 θ_down (Downward Threshold)

Threshold for accepting risk decreases:

```
θ_down(μ) = θ_base / μ
```

When μ is high, threshold is higher (easier to accept improvements).

---

## 5. Modulated Tax Rates

The tax rate for budget consumption is modulated by μ:

```
tax_rate(μ) = tax_base / μ
```

Higher μ means higher taxes (more conservative budget use).

---

## 6. Saturation/Projection

Parameters are projected to valid ranges:

```
μ = min(1.0, max(0.01, μ))
f = max(0, f)
```

**μ never leaves (0, 1]**

---

## 7. Integration with Continuous Solver

The continuous solver uses μ to scale the repair operator:

```python
def repair_operator(state, mu):
    """
    Apply coherence repair scaled by μ.
    
    Higher μ = stronger repair.
    """
    base_repair = compute_base_repair(state)
    scaled_repair = base_repair * mu
    return project_to_admissible(scaled_repair)
```

---

## 8. Integration with Morphogenesis

Morphogenesis uses θ_up and θ_down:

```python
def check_admissibility(risk_delta, mu):
    """
    Check if step is admissible using modulated thresholds.
    """
    if risk_delta > 0:
        # Risk increasing - check θ_up
        threshold = theta_base * mu
        return risk_delta <= threshold
    else:
        # Risk decreasing - check θ_down
        threshold = theta_base / mu
        return abs(risk_delta) >= threshold
```

---

## 9. Parameter Broadcasting

Parameters are included in receipts for verification:

```json
{
  "mu": "0.800000000000000000",
  "fatigue": "100000000000000000",
  "theta_up": "0.8",
  "theta_down": "1.25",
  "tax_rate": "1.25"
}
```

---

## 10. References

- [Continuous Manifold Flow](./continuous_manifold_flow.md)
- [Budget Law](./budget_law.md)
- [Global Hybrid Stability](./global_hybrid_stability.md)
