# 5. Gate Stack

## 5.1 Definition

$$\mathrm{Gate}(Q) \rightarrow (Q_{\text{accepted}}, D)$$

Gate applies:
1. Schema validation
2. WitnessAvail
3. Policy evaluation
4. Budget pre-check

## 5.2 DecisionRecord

DecisionRecord contains:
- accepted candidates
- rejected candidates
- rejection reasons (enumerated)

### Rejection Codes

| Code | Description |
|------|-------------|
| REJECT_SCHEMA | Proposal failed schema validation |
| REJECT_WITNESS | Required witness fields unavailable |
| REJECT_CYCLE | Dependency graph contains cycle |
| REJECT_POLICY | Policy check failed |
| REJECT_BUDGET | Insufficient budget for proposal |

## 5.3 Determinism Requirement

**Given identical inputs → identical DecisionRecord.**

The gate function is strictly deterministic regardless of:
- Predictor behavior
- External timing
- Non-deterministic factors

## 5.4 CNHAI Mapping

| GMI Concept | CNHAI Equivalent |
|-------------|------------------|
| Gate | GateManager.evaluate() |
| DecisionRecord | Receipt.decision |
| REJECT_SCHEMA | RejectionCode.INVALID_ACTION |
| REJECT_WITNESS | RejectionCode.INSUFFICIENT_WITNESS |
| REJECT_CYCLE | RejectionCode.CYCLE_DETECTED |
| REJECT_POLICY | RejectionCode.POLICY_VIOLATION |
| REJECT_BUDGET | RejectionCode.INSUFFICIENT_BUDGET |
