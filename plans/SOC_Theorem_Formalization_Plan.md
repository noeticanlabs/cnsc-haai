# SOC Theorem Formalization Plan

## Objective

Formalize the [LEMMA-NEEDED] items in the Scale-Free Renorm Theorem Program to upgrade the SOC attractor proof from heuristic to theorem-grade.

## Current Status

The following are marked as [LEMMA-NEEDED]:
1. Near-zero-drift increment model for X_t
2. Jump magnitude relation S_k = f(X_τ_k)
3. Ladder-height/first-passage theorem application

## Three Lemma Roadmap

### Lemma 1: Increment Model Formalization

**Goal**: Justify X_{t+1} = X_t + ξ_t with near-zero drift

**Approach**:
- Model σ_t = η(B_t) · ||A_t|| · ||G_t|| as a stochastic process
- Use NC2 (log-balance): E[log σ] ≈ 0 implies E[ξ] ≈ 0
- Prove mixing/ergodicity for the operator dynamics
- Show the invariant measure exists and is unique

**Key Theorems to Cite**:
- Birkhoff ergodic theorem
- Law of large numbers for martingale differences
- Foster-Lyapunov criteria for stability

### Lemma 2: Jump Relation

**Goal**: Define f(x) and prove f(x) ≍ x at large x

**Approach**:
- Define event size S_k as the "energy release" during renorm
- Relate S_k to the overshoot X_τ_k (distance above critical surface)
- Show that for large overshoot, cascade magnitude scales linearly

**Key Relationship**:
```
S_k ∝ X_τ_k = log(σ_τ_k)  (when σ > 1)
```

### Lemma 3: Ladder Height / First Passage

**Goal**: Apply appropriate random walk theorem

**Candidate Theorems**:
1. **Lamperti's Criteria** - for random walks with asymptotically zero drift
2. **Renewal Theorem** - for crossing distributions
3. **Spitzer's Theorem** - for ladder height distributions
4. **Weiss's Theory** - for hazard rates

**Approach**:
- Show increments satisfy: E[ξ] = 0, Var(ξ) > 0, i.i.d. or mixing
- Apply Lamperti's criterion for regular variation
- Conclude: P(S_k > x) ~ x^{-α} (power law)

## Mathematical Framework

### The Process

```
X_t = log(σ_t) = log(η(B_t)) + log(||A_t||) + log(||G_t||)

Between renorms: X_{t+1} = X_t + ξ_t  (additive increments)

At renorm τ_k: X_{τ_k^+} = X_{τ_k} - J_k  (downward jump)
               where J_k ≥ X_{τ_k} (enforced by verifier)
```

### Scale-Free Claim

If:
1. ξ_t has zero mean, finite variance
2. J_k scales with X_{τ_k} (proportional overshoot)
3. Timescale separation holds (drive >> cascade)

Then:
- Crossing times have power-law distribution
- Event sizes S_k follow power law: P(S_k > x) ∝ x^{-1}

## Implementation Steps

### Step 1: Create Lemma 1 Draft
- Write mathematical specification of increment process
- Define the stochastic dynamics for σ_t
- Prove existence of invariant measure

### Step 2: Create Lemma 2 Draft  
- Define event size function f(x)
- Prove asymptotic equivalence f(x) ≍ x
- Connect to physical interpretation

### Step 3: Create Lemma 3 Draft
- Select appropriate theorem (Lamperti recommended)
- Verify hypotheses hold for our process class
- Derive power-law exponent

### Step 4: Integration
- Combine lemmas into unified proof
- Update theorem program status tags
- Add to main documentation

## References

- Lamperti, J. (1960). Criteria for the recurrence of Markov chains with a drift
- Spitzer, F. (1956). Principles of Random Walk
- renewal theory references
- SOC literature: Bak, Tang, Wiesenfeld (1987)

## Files to Create/Modify

- `docs/soc/02_scale_free_renorm_theorem_program.md` - Update with lemma drafts
- `docs/soc/04_lemma_1_increment_model.md` - New
- `docs/soc/05_lemma_2_jump_relation.md` - New
- `docs/soc/06_lemma_3_ladder_height.md` - New

## Status

- [ ] Lemma 1: Increment Model
- [ ] Lemma 2: Jump Relation  
- [ ] Lemma 3: Ladder Height
- [ ] Integration into Theorem Program
