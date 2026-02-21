# 3. Predictor Layer

## 3.1 Definition

Predictor is a proposal generator:
$$\mathrm{Predict} : (\mathcal{S}, \mathcal{O}, \mathcal{P}) \rightarrow \mathcal{Q}$$

Where $\mathcal{Q}$ = ProposalSet.

## 3.2 ProposalSet Structure

Each proposal $q_i \in \mathcal{Q}$ is:
$$q_i = (\text{candidate_id}, \text{payload}, \text{required_witness_fields}, \text{predicted_cost}, \text{source_tag})$$

### Constraints

- **candidate_id** = SHA256(JCS(payload))
- **required_witness_fields** ⊆ declared policy check dependencies
- **predicted_cost** is labeled HEURISTIC

### Determinism

Predictor **MAY BE NON-DETERMINISTIC**.

GMI does not require predictor determinism.

The gate and execution layers are deterministic regardless of predictor behavior.

## 3.3 CNHAI Mapping

| GMI Concept | CNHAI Equivalent |
|-------------|------------------|
| Predictor | NPE (Neural Planning Engine) |
| Proposal | NPEProposalRequest |
| candidate_id | sha256(JCS(payload)) |
| predicted_cost | budget_delta (QFixed) |

## 3.4 Proposal Acceptance

The gate layer evaluates proposals and produces a deterministic DecisionRecord regardless of how many or which proposals the predictor generates.
