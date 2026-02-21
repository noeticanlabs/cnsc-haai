# 10. Adaptation (Metabolic Update)

## 10.1 Definition

Adaptation is not free mutation.

Define:
$$\mathrm{Adapt}(S_t', D, R) \rightarrow S_{t+1}$$

## 10.2 Allowed Changes

- memory consolidation
- trust weight update
- policy context adjustment
- world model refinement

## 10.3 AdaptReceipt

Each adaptation emits AdaptReceipt:
- field changed
- magnitude
- linkage to decision record

## 10.4 CNHAI Mapping

| GMI Concept | CNHAI Equivalent |
|-------------|------------------|
| Adapt | Abstraction creation |
| AdaptReceipt | Abstraction ladder entry |
| Memory consolidation | Memory abstraction |

Replay includes adaptation receipts.
