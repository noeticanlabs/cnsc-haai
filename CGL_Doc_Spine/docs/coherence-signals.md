# Coherence signals

CGL governs **operations**, but it needs measurable signals to decide “safe vs unsafe.”

This doc defines a practical signal set that works across many coherence implementations (field solvers, glyph systems, resonance computing). You can extend it, but don’t start with a zoo.

## Signal categories

### A) Alignment / order signals
These estimate “how phase-aligned is the system?”

**Coherence measure (𝒞)**  
A canonical choice:
\[
\mathcal C = \left|\langle e^{i\theta}\rangle\right|^2
\]
Operationalization:
- define an averaging window (spatial region, ensemble, or a rolling time window)
- define sampling rate and tolerances
- store both 𝒞 and confidence bounds (sample size, missingness)

**Phase variance (Var(θ))**  
A complementary view: higher variance typically correlates with lower 𝒞.

### B) Gradient and curvature proxies
Instability often shows up as explosive gradients.

**Gradient norm (‖∇θ‖)**  
Track percentile values (p50/p95/p99), not just mean.

**Laplacian energy (‖Δθ‖ or ∫|Δθ|²)**  
Useful when boundary conditions create localized curvature spikes.

### C) Spectral signals
Runaway resonance has a spectral fingerprint.

**Spectral peak ratio (SPR)**  
Ratio between dominant peak amplitude and median band power. High SPR can mean phase locking; rapidly changing SPR can mean instability onset.

**Bandwidth expansion (BWE)**  
Sudden broadening indicates chaos or uncontrolled coupling.

### D) Energy and flux constraints
Even in “pure information” systems, energy analogs exist.

**Energy density proxy (Ê)**  
Define per runtime: e.g., field energy ∫(‖∇θ‖² + V(θ))dV, or an equivalent computational energy metric.

**Injection rate (dÊ/dt)**  
A leading indicator: fast injection can push past LoC before 𝒞 drops.

### E) Runtime health signals
Sometimes the runtime is the hazard.

- iteration divergence (non-convergence rate)
- numerical stiffness alarms
- NaN/Inf occurrence
- constraint violation counts
- watchdog resets / kernel exceptions

## Risk levels

CGL maps live signals to a discrete risk state so policies stay readable.

- **GREEN:** within envelope with margin
- **YELLOW:** approaching envelope boundary (trend risk)
- **ORANGE:** envelope breach likely or minor breach observed
- **RED:** envelope breach confirmed, unstable dynamics, or integrity failure
- **BLACK:** unknown state (telemetry missing, integrity unverifiable)

A default mapping (tunable per runtime):

| Level | Trigger (any) | Default action |
|---|---|---|
| GREEN | all signals inside envelope | normal ops |
| YELLOW | trend-to-breach in T minutes | throttle risky ops |
| ORANGE | minor breach, or high SPR | require constraints + enhanced logging |
| RED | sustained breach or NaN/Inf | quarantine or stop |
| BLACK | telemetry stale, auth weak, or signature failure | deny high-risk ops |

## Signal envelopes
A policy defines envelopes as constraints like:

- 𝒞 ≥ 0.92
- p99(‖∇θ‖) ≤ 3.0 (normalized units)
- SPR ≤ 20
- dÊ/dt ≤ 0.1 per second

Envelopes must be versioned and tied to calibration data (see Testing & validation).

## Choosing initial thresholds
A sane approach:
1. run baseline workloads with safe settings
2. record signal distributions
3. set envelope bounds to conservative quantiles (e.g., p99 baseline × 1.2)
4. test with “known risky” workloads to confirm early warning signals

Governance: envelopes are **policy**, not ad-hoc runtime knobs.

