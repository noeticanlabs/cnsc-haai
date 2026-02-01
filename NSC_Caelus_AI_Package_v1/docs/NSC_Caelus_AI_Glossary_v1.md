# NSC Caelus AI - Glossary & Lexicon (v1)
Generated 2026-02-01

This glossary defines the technical vocabulary used across the NSC Caelus AI specification, evaluation protocol, and safety/governance runbooks. Definitions are normative: if a term is used in the system, it should match what is written here.

## A. Acronyms
**A/B test**  (Acronym)
Online experiment that randomly assigns traffic to two variants (A=baseline, B=change) to estimate causal impact on KPI and guardrails.
*Operational notes*: Caelus A/B tests must run with rollback criteria and complete receipts for both variants.
*Example*: B improves tool_use_success_rate without increasing hallucination_rate.

**AGI**  (Acronym)
Artificial General Intelligence: a system intended to perform well across a wide range of tasks, not just a narrow benchmark.
*Operational notes*: In this packet, AGI is treated as an evaluation and governance problem: define tasks, measure performance, and enforce safety rails.

**CI**  (Acronym)
Confidence interval: a statistical range likely to contain the true value of a metric, used to avoid over-trusting single-run results.
*Operational notes*: Report mean and 95% CI over seeds for offline suites.
*Example*: tool_use_success_rate = 0.872 ± 0.010 (95% CI).

**GMRES**  (Acronym)
Generalized Minimal Residual: an iterative method for solving sparse linear systems, often used inside elliptic solvers.
*Operational notes*: In the GR solver reference integration, GMRES may be paired with preconditioning and multigrid.

**GR**  (Acronym)
General Relativity: the physics framework describing gravity as spacetime curvature.
*Operational notes*: Used as a high-rigor reference domain to force explicit invariants and verification.

**JSONL**  (Acronym)
JSON Lines: a file format where each line is a standalone JSON object, convenient for append-only logs.
*Operational notes*: Receipt ledgers are stored as JSONL for streaming and auditability.

**KPI**  (Acronym)
Key Performance Indicator: the primary metric the system is optimized to improve.
*Operational notes*: Rule: one primary KPI at a time; everything else is a guardrail or diagnostic.
*Example*: Primary KPI: tool_use_success_rate.

**LLM**  (Acronym)
Large Language Model: a neural model trained on text to predict tokens; used for reasoning and generation in Caelus.
*Operational notes*: LLMs are treated as fallible components that must be constrained by gates/rails and verified by receipts.

**MG**  (Acronym)
Multigrid: a class of solvers that accelerate convergence of elliptic PDE solves by operating on multiple resolutions.
*Operational notes*: Used for constraint solves or Poisson-like subproblems.

**NSC**  (Acronym)
In Caelus: the tag-and-gate semantic control layer (NSC tags) used for routing, enforcement, and evaluation slicing.
*Operational notes*: NSC is the shared vocabulary: a semantic bus connecting orchestration, safety, memory, and evaluation.

**P0/P1**  (Acronym)
Incident severity labels: P0 is immediate pager-level; P1 is urgent but not existential.
*Operational notes*: Safety rail violations (no_future_leak, privacy scope breach, schema corruption) are P0.

**PDF**  (Acronym)
Portable Document Format, used for reviewer-ready exports and archiving.
*Operational notes*: In this packet, DOCX is the editable source; PDFs are the review artifacts.

**PII**  (Acronym)
Personally Identifiable Information: data that can identify a person directly or indirectly.
*Operational notes*: PII classification is required for memory writes and for user-facing disclosure decisions.

**RK4**  (Acronym)
Runge-Kutta 4th order: a common explicit time-integration method.
*Operational notes*: GR solver uses RK4 as a reference time integrator; stability is monitored via constraints.

**SLA**  (Acronym)
Service Level Agreement: a contractual operational guarantee (often external).
*Operational notes*: Caelus focuses on SLOs; SLAs are derived once performance is stable.

**SLO**  (Acronym)
Service Level Objective: a target reliability/latency/quality goal for a service.
*Operational notes*: Example SLO: p95 latency <= 1.8s while meeting quality guardrails.

**TTL**  (Acronym)
Time-to-live: an expiration policy for tags or memory records.
*Operational notes*: TTL prevents stale context from persisting unless promoted by receipts.

## B. Core Concepts
**Aeonic clocks**  (Concept)
A scheduling abstraction that treats time as multi-scale: fast loops (per step), medium loops (per request), and slow loops (per project).
*Operational notes*: Used to coordinate PhaseLoom threads and enforce time budgets across tool calls and verification.

**Aeonic Memory Bank**  (System)
A tiered memory store (L0-L3) with explicit provenance, privacy scope, and retention policies per record.
*Operational notes*: Memory is not implicit; every stored item must be a schema-valid MemoryRecord with a policy.

**Audit completeness**  (Metric/Property)
The fraction of requests for which all required receipts, tool traces, and gate decisions are present and schema-valid.
*Operational notes*: A minimum standard (example): >= 99.5%. Missing receipts is treated as a correctness failure, not a logging nuisance.

**Baseline**  (Concept)
The reference system or policy used for comparison in evaluation (routing policy, model_id, or gating thresholds).
*Operational notes*: All reported gains must specify the baseline and hold cost/latency budgets constant unless explicitly traded.

**Claim**  (Concept)
A statement the system asserts as true (or better) that requires evidence. Claims are tracked as ClaimNodes in the experiment DAG.
*Operational notes*: A claim is not considered real until supported by at least one receipt and an eval run under stated conditions.

**Compaction**  (Process)
A controlled transformation of memory records that reduces size while preserving specified meaning under an explicit loss budget.
*Operational notes*: Compaction must emit its own receipt: input hashes -> output hash + diff + loss budget.

**Deterministic replay**  (Property)
The ability to reproduce decisions and outputs from recorded inputs (hashes, configs, seeds) with acceptable tolerance.
*Operational notes*: Deterministic replay is required for audit and debugging; it constrains decoding and tool contracts.

**Domain slice**  (Concept)
A labeled subset of evaluation data (or traffic) grouped by domain, tags, or risk profile.
*Operational notes*: Slices prevent average metrics from hiding failure clusters.
*Example*: tooluse_holdout_v1 slice: domain=maintenance.

**Error cluster**  (Concept)
A grouping of failures that share a root cause or signature; used for targeted fixes and regression tests.
*Operational notes*: Each cluster should be tagged and associated with representative examples and receipts.

**Experiment DAG**  (Concept)
A dependency graph of artifacts and claims: dataset nodes, model nodes, eval nodes, and claim nodes with receipts as edges.
*Operational notes*: The DAG is the anti-handwaving machine: no provenance, no claim.

**Gate**  (Mechanism)
A decision function that inspects inputs/outputs/state and returns a structured GateDecision that can alter control flow.
*Operational notes*: Gates are logged and replayable; they should be deterministic given the same inputs.

**Guardrail metric**  (Metric)
A metric that must not degrade beyond a limit while optimizing the primary KPI.
*Operational notes*: If the KPI improves but a guardrail is breached, the change does not ship.

**Human review**  (Process)
A controlled handoff where a human makes or approves a decision the system is not permitted to make autonomously.
*Operational notes*: Triggered by '''defer''' gate outcomes or risk thresholds.

**Invariant**  (Concept)
A property that should remain true across execution (e.g., schema validity, no future leak, physics constraints).
*Operational notes*: Rails are implemented invariants that cannot be overridden.

**Orchestration**  (Concept)
The control logic that sequences planning, tool use, verification, and memory updates.
*Operational notes*: In Caelus, orchestration is executed by PhaseLoom.

**Receipt**  (Artifact)
An immutable, schema-valid record binding inputs (dataset hash, code commit, config hash, seed) to outputs (artifacts + hashes) and metrics.
*Operational notes*: Receipts are the unit of trust for external reviewers.

**Receipt Ledger**  (Artifact store)
An append-only log of receipts and related events (e.g., tag events, gate decisions).
*Operational notes*: Used for audits, reproducibility, and failure analysis.

**Routing policy**  (Policy)
Rules that select tools, prompts, verification steps, and memory slices based on NSC tags, domain, and risk.
*Operational notes*: Routing is governed and versioned; changes require receipts and regression testing.

**Sandbox**  (Safety control)
An isolated execution environment for tools to reduce risk of side effects and contain failures.
*Operational notes*: Tooling should run in sandbox mode by default for evaluation and sensitive operations.

**Semantic bus**  (Metaphor)
A shared vocabulary (NSC tags + schemas) that lets independent layers coordinate without ad hoc coupling.
*Operational notes*: Tags + structured decisions are the bus, not natural language prose.

**Tool contract**  (Interface)
A precise definition of tool inputs/outputs, schemas, timeouts, and failure behavior.
*Operational notes*: Stable tool contracts are required for deterministic replay.

**Tool budget**  (Constraint)
Limits on number of tool calls, time per call, and total latency per request.
*Operational notes*: Budget prevents runaway tool loops and keeps latency predictable.

## C. Artifacts and Data Structures
**ClaimNode**  (Data structure)
A structured representation of a claim: statement, KPI target, guardrails, conditions, evidence references, and status.
*Operational notes*: ClaimNodes are the units that move from proposed -> tested -> replicated -> shipped.

**EvalRun**  (Data structure)
A structured record of an evaluation run: suite name, model_id, dataset split hashes, protocol parameters, results, and artifacts.
*Operational notes*: EvalRun is paired with a Receipt; the EvalRun describes what happened, the Receipt binds it to hashes.

**GateDecision**  (Data structure)
A structured output from a gate: decision (allow/warn/block/reroute/defer), reasons, thresholds, actions, and tags.
*Operational notes*: GateDecision must be emitted for every gate check in production-relevant modes.

**MemoryRecord**  (Data structure)
A structured record stored in Aeonic Memory Bank: tier, key, value, provenance, privacy scope, and retention.
*Operational notes*: A MemoryRecord without provenance and policy is invalid and must be blocked.

**Provenance**  (Metadata)
Information about where an artifact or memory record came from (source + references + hashes).
*Operational notes*: Provenance is non-optional for audit-grade claims.

**Split hash**  (Data integrity)
A hash that identifies the exact dataset split used (train/val/test) to prevent leakage and ensure reproducibility.
*Operational notes*: If split hashes differ, results are not comparable without a clear justification.

**TagEvent**  (Data structure)
A structured event describing tag creation or update: actor, scope, tags applied, evidence, confidence, and TTL policy.
*Operational notes*: TagEvents allow audit of routing decisions and evaluation slicing.

**Version bundle**  (Artifact)
A packaged set of model_id + routing policy + gate thresholds + schemas used for a deployment.
*Operational notes*: Rollbacks operate on version bundles to restore known-good behavior.

## D. Metrics and Evaluation
**False block rate**  (Metric)
The fraction of benign requests incorrectly blocked or deferred by safety gates.
*Operational notes*: A key usability guardrail: safety must not collapse the system into '''no'''.

**Hallucination rate**  (Metric)
The fraction of outputs containing claims unsupported by provided evidence or receipts, as measured by a rubric and replay checks.
*Operational notes*: Measured per suite and per slice; must remain <= 0.03 (example guardrail).

**Latency (p95)**  (Metric)
The 95th percentile end-to-end response time.
*Operational notes*: Used as a guardrail; should remain within the operational budget (example: <= 1.8s).

**Replay match rate**  (Metric)
The fraction of replays that match the original run on decisions and key metrics within tolerance.
*Operational notes*: Core reproducibility metric for REPRO_V1.

**Shadow mode**  (Evaluation stage)
A deployment stage where the new variant runs in production silently for measurement, without affecting user-visible outputs.
*Operational notes*: Shadow mode should log the same receipts and slices as online runs.

**Tool-use success rate**  (Metric)
The fraction of tasks where the system selects appropriate tools, uses them correctly, and produces a correct final answer.
*Operational notes*: Primary KPI in this packet; computed with suite-specific success criteria.

**Violation rate**  (Metric)
The fraction of requests that trigger a safety rail violation (temporal leak, privacy scope breach, schema corruption).
*Operational notes*: For SAFETY_V1, target is 0.0.

## E. Safety and Governance
**Circuit breaker**  (Control)
A mechanism that stops or degrades behavior when failures or timeouts exceed thresholds (e.g., tool loop runaway).
*Operational notes*: Prevents latency spirals and cascading failures.

**No future leak**  (Safety rail)
A hard invariant: the system must not use information dated after the task context time.
*Operational notes*: Enforced by timestamped retrieval/tool outputs plus gate_no_future_leak. Violations are P0.

**Privacy scope**  (Safety rail)
An invariant restricting what data can be stored or disclosed based on PII classification and allowed scopes.
*Operational notes*: Default is restrictive: if scope is unclear, block or defer.

**Safe mode**  (Operational state)
A degraded operating mode that restricts tools, raises gating thresholds, and increases human review to contain incidents.
*Operational notes*: Triggered by P0 conditions or sustained guardrail breaches.

**Schema validation**  (Safety rail)
The requirement that all tool outputs and stored records conform to defined schemas.
*Operational notes*: Prevents silent corruption and enables reliable replay and parsing.

**Rollback**  (Operational action)
Reverting to the last known-good version bundle (model + routing + gate thresholds) when KPI or safety standards regress.
*Operational notes*: Rollbacks must be tested as part of deployment readiness.

## F. Domain Lexicon: Smart GR Solver Reference Integration
**Constraint (GR)**  (Domain term)
Equations that must remain satisfied during evolution (e.g., Hamiltonian and momentum constraints).
*Operational notes*: Caelus logs constraint norms and triggers gates when divergence exceeds thresholds.

**Gauge condition**  (Domain term)
A choice of coordinates or additional conditions used to make the GR system well-posed for numerical evolution.
*Operational notes*: Gauge choices affect stability and must be recorded in configs and receipts.

**GRRHS**  (Component)
The right-hand-side computation for the GR evolution equations used by the time integrator.
*Operational notes*: Treated as a deterministic function of state and parameters for replay and testing.

**Spectral cache**  (Component)
A cache of spectral representations (or basis projections) to accelerate repeated operations.
*Operational notes*: Cache hits/misses are monitored because they affect both latency and reproducibility.

**Stability limit**  (Domain term)
A numerical bound (often CFL-like) beyond which explicit integration becomes unstable.
*Operational notes*: Enforced by gates that monitor step size and constraint growth.

## G. Change control
Any change to these definitions must be versioned and accompanied by a receipt that records what changed, why it changed, and which tests were re-run. If a term is used inconsistently, the definition here wins, and the inconsistent usage is a bug.