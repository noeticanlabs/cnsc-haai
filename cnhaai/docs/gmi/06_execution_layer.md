# 6. Execution Layer

## 6.1 Execution Function

$$\mathrm{Execute}(Q_{\text{accepted}}, S_t) \rightarrow (S_t', E)$$

Where:
- $S_t'$ = new state
- $E$ = execution trace metadata

**Execution must be deterministic.**

## 6.2 Determinism Rule

Given:
- same accepted proposals
- same pre-state
- same VM version

Then:
- same post-state hash
- same execution metrics
- same receipt digest

## 6.3 Execution Trace

The execution trace contains:
- Action sequence executed
- State modifications per action
- Resource consumption per action
- Error conditions encountered

## 6.4 CNHAI Mapping

| GMI Concept | CNHAI Equivalent |
|-------------|------------------|
| Execute | NSC VM.run() |
| Action | NSC Action |
| Trace | Receipt.execution_trace |
| VM version | NSC.VERSION |
