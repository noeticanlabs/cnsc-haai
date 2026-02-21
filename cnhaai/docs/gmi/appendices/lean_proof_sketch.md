# Appendix: Lean Proof Sketch

## Overview

This is a Lean 4 formalization sketch for GMI v1 proofs.

## Basic Types

```lean
/--
GMI Basic Types
--/

-- State
structure GMI.State where
  world_model : BeliefState
  memory : MemoryState
  budget : Budget
  chain_tip : ChainHash

-- Proposal
structure Proposal where
  candidate_id : Hash
  payload : Json
  witness_fields : List Field
  cost : QFixed

-- Receipt
structure Receipt where
  version : Version
  pre_state_hash : Hash
  post_state_hash : Hash
  decision_hash : Hash
  chain_tip : Hash
```

## Determinism Theorem

```lean
/--
Theorem: Gate is deterministic

Given identical inputs → identical DecisionRecord.
--/

theorem gate_deterministic (S : State) (P : Policy) (Q : List Proposal)
  (h : ∀ i j, i = j → Q[i] = Q[j]) :
  Gate.deterministic S P Q = Gate.deterministic S P Q :=
by
  -- Gate applies deterministic functions:
  -- 1. Schema validation (pure function)
  -- 2. WitnessAvail (deterministic predicate)
  -- 3. Policy evaluation (deterministic)
  -- 4. Budget check (deterministic)
  -- Therefore Gate is deterministic
  sorry
```

## Budget Monotonicity Theorem

```lean
/--
Theorem: Budget Monotonicity

Without explicit credit, B_{t+1} ≤ B_t.
--/

theorem budget_monotonicity (S : State) (Q : List Proposal)
  (h_credit : ¬HasCredit Q) :
  let S' := Execute S Q;
  S'.budget ≤ S.budget :=
by
  -- By definition of Execute:
  -- B' = B - Σ work_i
  -- work_i ≥ 0 for all i
  -- Therefore B' ≤ B
  sorry
```

## Replay Consistency Theorem

```lean
/--
Theorem: Replay Consistency

Replay reproduces identical state hash.
--/

theorem replay_consistency (R : Receipt) (S₀ : State)
  (h_valid : Receipt.valid R) :
  let (S_n, C_n) := Replay R S₀;
  S_n.hash = R.post_state_hash ∧ C_n = R.chain_tip :=
by
  -- Replay applies:
  -- 1. Verify decision_hash matches
  -- 2. Execute actions to compute state'
  -- 3. Hash state' and compare
  -- By determinism, matches receipt
  sorry
```

## Witness Soundness Theorem

```lean
/--
Theorem: Witness Soundness

No policy check evaluated without required fields.
--/

theorem witness_soundness (S : State) (c : PolicyCheck)
  (h_eval : Policy.eval c S = some result) :
  ∀ f ∈ c.dependencies, f ∈ S.witnesses :=
by
  -- By WitnessAvail precondition
  -- Before evaluation, all dependencies must be present
  sorry
```

## Running Lean Proofs

```bash
# Install Lean 4
curl https://leanprover-community.github.io/install.sh | bash

# Build and check proofs
lean --make GMI/
```

## References

- [Lean 4 Documentation](https://leanprover.github.io/)
- [Functional Programming in Lean](https://leanprover.github.io/functional_programming_in_lean/)
