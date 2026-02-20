# Autonomic Regulation

**μ Stiffness and Fatigue Control**

## μ Parameter

The μ parameter controls stiffness of the repair operator:
- μ ∈ (0, 1]
- Higher μ = stronger repair
- Modulates thresholds and tax rates

## Fatigue

Fatigue accumulates when risk increases despite repair:
- f ≥ 0
- Increases with risk accumulation
- Decreases with recovery

## Modulated Thresholds

- θ_up(μ) = θ_base × μ
- θ_down(μ) = θ_base / μ

See:
- [Autonomic Regulation (Math)](../ats/10_mathematical_core/autonomic_regulation.md)
