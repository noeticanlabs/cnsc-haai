# Glossary

This glossary defines terms used across the Coherence Governance Layer (CGL). The goal is boring precision.

## Core coherence terms

**Coherence field (θ)**  
A phase-like field (scalar or vector) used by the runtime to represent resonance / alignment. In many models, coherent structure is a function of spatial gradients and potential wells.

**Coherence measure (𝒞)**  
A normalized measure of phase alignment. A common choice:
\[
\mathcal C = \left|\langle e^{i\theta}\rangle\right|^2
\]
where the angle brackets denote an averaging window (space, ensemble, or time).

**Limit of Coherence (LoC)**  
A boundary in parameter space where stable behavior transitions to instability. In operational terms: the runtime becomes non-predictive, non-repeatable, or unsafe beyond the LoC.

**Coherence budget**  
A quantified allowance for “how much instability risk” a workload may consume. Budgets are defined in policy and enforced in runtime gates (rate limits, amplitude limits, spectral constraints, energy caps).

**Coherence envelope**  
A vector of safe ranges for monitored signals (e.g., 𝒞, gradient norms, energy density, spectral peaks). Policies define envelopes; enforcement compares live telemetry to them.

**Resonance hazard**  
A workload characteristic (input, parameter, or excitation pattern) likely to drive runaway amplification, phase-locking collapse, or boundary-condition violations.

## Governance terms

**Policy bundle**  
A versioned set of policies + metadata + signatures that CGL uses as the single source of truth for decisions.

**Policy decision**  
A deterministic result of evaluating a request against policy: `allow`, `deny`, or `allow_with_constraints` (plus constraints).

**Attestation**  
A cryptographic statement that a policy bundle (or config) is authentic and approved. Attestation binds *content* to *identity* and *time*.

**Change request (CR)**  
A governance artifact describing a change to policy, enforcement parameters, or runtime configuration, including reviewers and approvals.

**Evidence**  
Immutable audit artifacts supporting that the system behaved as claimed: signed event logs, hashes of policy bundles, traces, and approvals.

## Runtime integration terms

**Workload**  
A unit of work submitted to the runtime: a simulation run, field solve, glyph compilation, or controlled experiment.

**Enforcement point (EP)**  
A gate where CGL can constrain or block action: API gateway, job scheduler, runtime plugin, kernel shim, or sidecar.

**Quarantine**  
A restricted execution mode used when signals breach safety envelopes: reduced amplitude, reduced degrees of freedom, isolated environment, enhanced logging, and explicit operator acknowledgement.

**Fail-safe**  
A behavior that defaults to safety: deny execution, degrade to stable defaults, or isolate the workload when uncertain.

