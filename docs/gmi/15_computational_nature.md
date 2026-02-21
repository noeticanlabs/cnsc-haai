# 15. Computational Nature

## 15.1 System Type

GMI is a **projected continuous-dynamical system** with **discrete governance interrupts**.

## 15.2 Continuous Dynamics

- World model evolution
- Prediction heuristics

## 15.3 Discrete Governance

- Proposal gating
- Execution commit
- Ledger write

## 15.4 Mathematical Characterization

$$\dot{x} = f(x, t) \quad \text{(continuous)}$$

$$x(t_{k+1}) = G(x(t_k), u_k) \quad \text{(discrete governance)}$$

Where $G$ = Gate $\circ$ Execute.

This matches the "Coh-governed projected dynamical system" framework.
