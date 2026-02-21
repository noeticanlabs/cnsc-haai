# 4. Witness Availability (Hard Gate)

## 4.1 Dependency Graph

Given policy checks $c_j$, define:
$$c_j \rightarrow f \quad \text{iff evaluating } c_j \text{ requires field } f$$

Construct directed graph $G_P$.

## 4.2 WitnessAvail Predicate

$$\mathrm{WitnessAvail}(P, \mathcal{F}) := \text{Graph acyclic} \land \forall c_j: \text{dependencies}(c_j) \subseteq \mathcal{F}$$

This is machine-checkable.

**Failure is fatal to candidate.**

## 4.3 Witness Structure

Each proposal declares its required witness fields:
```json
{
  "candidate_id": "sha256:...",
  "required_witness_fields": ["belief:concept_a", "memory:cell_0"],
  "payload": {...}
}
```

## 4.4 CNHAI Mapping

| GMI Concept | CNHAI Equivalent |
|-------------|------------------|
| Policy checks | Gate predicates |
| Dependencies | Gate input fields |
| WitnessAvail | Gate.can_execute() |

## 4.5 Acyclicity Requirement

The dependency graph must be acyclic. Cycles indicate:
- Self-referential policy checks
- Circular witness requirements
- Invalid policy specification

Such policies are rejected at load time.
