# 11. Renormalization (RCFA Layer)

## 11.1 Definition

Renormalization is optional for v1 but fully defined.

$$\mathrm{Renorm} : \mathcal{S} \rightarrow (\mathcal{S}', \rho)$$

Where $\rho$ = renorm_receipt.

## 11.2 Constraints

- Preserved invariants declared
- Mapping between old summaries and new summaries explicit
- Budget impact recorded

## 11.3 Restrictions

Renorm cannot violate WitnessAvail for active policies.

## 11.4 CNHAI Mapping

| GMI Concept | CNHAI Equivalent |
|-------------|------------------|
| Renorm | RCFA.abstraction() |
| renorm_receipt | AbstractionReceipt |

## 11.5 Status

**v1**: Optional, not required for minimal proof.

**v2**: Required for hierarchical operation.
