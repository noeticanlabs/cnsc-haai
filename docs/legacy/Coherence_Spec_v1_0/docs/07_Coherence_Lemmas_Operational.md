# Coherence Lemmas (Operational)

Each lemma has **preconditions** and a **measurable conclusion**, and must map to a CI test.

## Affordability Gate Lemma

**Preconditions:** Hard gates pass; soft gates satisfy policy thresholds.

**Conclusion:** Accepted states are inside the policy-safe region.

**CI mapping:** Gate-policy test verifies accept only when residuals \(\leq\) thresholds and hysteresis allows exit.

## No-Smuggling Lemma

**Preconditions:** Rails are bounded and declared.

**Conclusion:** All stability sources appear as bounded rails in receipts; no unlogged stabilization is permitted.

**CI mapping:** Receipt schema test requires rail bounds and before/after values.

## Anti-Chatter Lemma

**Preconditions:** Hysteresis and monotone mitigation strategy are enabled.

**Conclusion:** Infinite oscillation between accept/retry is prevented.

**CI mapping:** Hysteresis test exercises enter/exit thresholds across multiple retries.

## Termination Lemma

**Preconditions:** Bounded retries and a minimum \(dt\) floor are configured.

**Conclusion:** Each step terminates in accept or abort within finite retries.

**CI mapping:** Retry-limit test confirms abort at configured limit and logs decision reason.

## Replay Lemma

**Preconditions:** Receipts include state summary, residuals, debt, gates, rails, policy id, and hashes.

**Conclusion:** Decisions are replayable and recomputable from receipts within tolerance.

**CI mapping:** Replay test recomputes decisions and verifies hash chain integrity.
