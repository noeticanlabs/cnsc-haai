# 7. Budget Algebra

## 7.1 Budget Space

Let $B_t \in \mathbb{R}_{\geq 0}^k$.

Budget is a k-dimensional non-negative vector.

## 7.2 Budget Update

$$B_{t+1} = B_t - \sum_i W_i$$

Where $W_i$ = measured work of candidate i.

## 7.3 MonotonicityB_{ Constraint

$$t+1} \leq B_t$$

unless explicit credit receipt exists.

## 7.4 Budget Violations

| Condition | Action |
|-----------|--------|
| $B_{t+1} < 0$ | REJECT_BUDGET |
| $B_{t+1} > B_t$ | Requires credit receipt |

## 7.5 CNHAI Mapping

| GMI Concept | CNHAI Equivalent |
|-------------|------------------|
| Budget | Budget (QFixed vector) |
| Work | risk_delta (QFixed) |
| Credit | Explicit CreditReceipt |
| B_t >= 0 | Budget.check_invariant() |

## 7.6 Budget Law Theorem

**Budget Monotonicity**: Without explicit credit, $B_{t+1} \leq B_t$ always holds.

This is enforced by the budget transition function.
