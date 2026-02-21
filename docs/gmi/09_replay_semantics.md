# 9. Replay Semantics

## 9.1 Replay Function

$$\mathrm{Replay}(ReceiptBundle, S_t) \rightarrow (S_t', C_{t+1})$$

Replay must satisfy:
- recomputed post_state_hash matches receipt
- recomputed chain_tip matches stored tip

**Replay failure = corruption.**

## 9.2 Replay Verification

Replay verification checks:
1. **State Hash**: $H(S_t') = $ Receipt.post_state_hash
2. **Chain Hash**: $C_{t+1} = $ Receipt.new_chain_tip
3. **Budget**: $B_{t+1} \leq B_t$ (or has credit)
4. **Decision**: DecisionRecord matches gate output

## 9.3 CNHAI Mapping

| GMI Concept | CNHAI Equivalent |
|-------------|------------------|
| Replay | ReceiptVerifier.verify_step() |
| State verification | _verify_state_hash_after() |
| Chain verification | _verify_chain_link() |
| Budget verification | _verify_budget_law() |

## 9.4 Replay Consistency Theorem

Given receipt bundle R and initial state S_0:
$$\mathrm{Replay}(R, S_0) = (S_n, C_n)$$

where recomputed $(S_n, C_n)$ matches receipt claims.
