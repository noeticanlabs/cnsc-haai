# 1. Scope Lock

## 1.1 Target Object

We define GMI as a deterministic, governed state transition system with:

- Structured proposal generation
- Policy-constrained gating
- Budget-constrained execution
- Cryptographic receipt logging
- Replayable state evolution
- Optional renormalization (state abstraction)

GMI is **NOT**:

- A large language model
- A black-box predictor
- A stochastic agent
- A metaphor

It is a **governed prediction-and-execution organism**.

## 1.2 Mathematical Characterization

GMI is formally characterized as:

```
GMI ≝ (S, O, P, Q, D, R, Step, Gate, Execute, Ledger)
```

Where:
- S = State space
- O = Observation space  
- P = Policy space
- Q = Proposal space
- D = Decision record space
- R = Receipt space
- Step = Main step operator
- Gate = Deterministic gate function
- Execute = Deterministic execution function
- Ledger = Cryptographic ledger commitment

## 1.3 What Makes It "Intelligence"?

Not prediction.
Not execution.
Not memory.

Intelligence emerges from:

```
Constrained adaptation under conserved budgets with verified state transitions.
```

That is **metabolic intelligence**.
