# 14. Minimal Proof Obligations

To claim GMI v1 exists:

## 14.1 Determinism Theorem

Given fixed proposal set and state, Step is deterministic.

$$\forall (S, Q, P): \mathrm{Step}(S, Q, P) = \mathrm{Step}(S, Q, P)$$

## 14.2 Budget Monotonicity Theorem

Budgets never increase without explicit credit receipt.

$$\forall (S, Q, P): B_{t+1} \leq B_t \lor \exists \text{CreditReceipt}$$

## 14.3 Replay Consistency Theorem

Replay reproduces identical state hash and chain tip.

$$\forall (R, S_0): \mathrm{Replay}(R, S_0).state\_hash = R.post\_state\_hash$$

## 14.4 Witness Soundness

No policy check evaluated without required fields.

$$\forall c_j: \mathrm{evaluating}(c_j) \implies \text{dependencies}(c_j) \subseteq \mathcal{F}$$
