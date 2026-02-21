# 2. Formal Core Model

## 2.1 State Space

### Definition

Let:
- $\mathcal{S}$ = State space
- $\mathcal{O}$ = Observation space
- $\mathcal{P}$ = Policy space
- $\mathcal{B}$ = Budget space
- $\mathcal{R}$ = Receipt space

### State at Time t

State at time $t$:
$$S_t = (W_t, M_t, B_t, C_t)$$

Where:
- $W_t$ = world model (belief state)
- $M_t$ = memory (PhaseLoom log index)
- $B_t \in \mathbb{R}_{\geq 0}^k$ = budget vector
- $C_t$ = chain tip (cryptographic commitment)

## 2.2 The GMI Step Operator

### Definition

We define:
$$\mathrm{Step} : (\mathcal{S}, \mathcal{O}, \mathcal{P}) \rightarrow (\mathcal{S}, \mathcal{D}, \mathcal{R})$$

Where:
- $\mathcal{D}$ = DecisionRecord
- $\mathcal{R}$ = ReceiptBundle

### Step Decomposition

$$\mathrm{Step} = \mathrm{Ledger} \circ \mathrm{Verify} \circ \mathrm{Execute} \circ \mathrm{Gate} \circ \mathrm{Predict}$$

This is not rhetorical. It is a strict composition.

## 2.3 State Transition Law

### Transition Function

Given:
- Current state $S_t$
- Observation $O_t$
- Policy $P$

The GMI step produces:
$$(S_{t+1}, D, R) = \mathrm{Step}(S_t, O_t, P)$$

### Composition Law

The step operator satisfies:
$$\mathrm{Step} = \mathrm{Ledger} \circ \mathrm{Verify} \circ \mathrm{Execute} \circ \mathrm{Gate} \circ \mathrm{Predict}$$

Each component is deterministic.

## 2.4 CNHAI Mapping

| GMI Symbol | CNHAI Equivalent | Type |
|------------|------------------|------|
| $W_t$ | BeliefState | Dict[str, List[QFixed]] |
| $M_t$ | MemoryState | List[bytes] |
| $B_t$ | Budget | QFixed vector |
| $C_t$ | Chain hash | sha256:hex |
| $\mathcal{O}$ | Episode observation | Any |
| $\mathcal{P}$ | Policy state | PolicyState |
| $D$ | DecisionRecord | Receipt.decision |
| $R$ | ReceiptBundle | Receipt |
