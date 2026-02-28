"""
Scoring Utilities for NPE Candidates.

Computes utility, risk, cost, and confidence scores for candidates.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..core.types import Candidate, Scores


@dataclass
class ScoreWeights:
    """Weights for computing composite scores.

    Attributes:
        risk_weight: Weight for risk score
        utility_weight: Weight for utility score
        cost_weight: Weight for cost score
        confidence_weight: Weight for confidence score
    """

    risk_weight: float = 0.25
    utility_weight: float = 0.35
    cost_weight: float = 0.20
    confidence_weight: float = 0.20


def compute_scores(
    candidates: List[Candidate],
    weights: Optional[ScoreWeights] = None,
    context: Optional[Dict[str, Any]] = None,
) -> List[Candidate]:
    """Compute and update scores for candidates.

    Args:
        candidates: List of candidates to score
        weights: Optional score weights
        context: Optional context for scoring

    Returns:
        Candidates with updated scores
    """
    if weights is None:
        weights = ScoreWeights()

    for candidate in candidates:
        # Compute candidate-specific scores
        scores = _score_candidate(candidate, weights, context)
        candidate.scores = scores

    return candidates


def _score_candidate(
    candidate: Candidate,
    weights: ScoreWeights,
    context: Optional[Dict[str, Any]],
) -> Scores:
    """Score an individual candidate.

    Args:
        candidate: The candidate to score
        weights: Score weights
        context: Optional context

    Returns:
        Computed scores
    """
    payload = candidate.payload
    candidate_type = candidate.candidate_type

    # Base scores from candidate
    base_scores = candidate.scores

    # Adjust based on candidate type
    if candidate_type == "repair":
        return _score_repair(payload, base_scores, weights)
    elif candidate_type == "plan":
        return _score_plan(payload, base_scores, weights)
    elif candidate_type == "solver_config":
        return _score_solver_config(payload, base_scores, weights)
    elif candidate_type == "explain":
        return _score_explain(payload, base_scores, weights)
    else:
        return base_scores


def _score_repair(
    payload: Dict[str, Any],
    base_scores: Scores,
    weights: ScoreWeights,
) -> Scores:
    """Score a repair candidate.

    Args:
        payload: Repair payload
        base_scores: Base scores
        weights: Score weights

    Returns:
        Adjusted scores
    """
    # Adjust based on repair properties
    repair_type = payload.get("repair_type", "parameter_adjustment")

    # Risk adjustment
    risk = base_scores.risk
    if repair_type == "parameter_adjustment":
        risk = min(risk + 0.1, 0.9)
    elif repair_type == "code_change":
        risk = min(risk + 0.2, 0.95)

    # Utility based on preconditions
    preconditions = payload.get("preconditions", [])
    utility = base_scores.utility
    if len(preconditions) > 3:
        utility = min(utility + 0.1, 1.0)

    return Scores(
        risk=risk,
        utility=utility,
        cost=base_scores.cost,
        confidence=base_scores.confidence,
    )


def _score_plan(
    payload: Dict[str, Any],
    base_scores: Scores,
    weights: ScoreWeights,
) -> Scores:
    """Score a plan candidate.

    Args:
        payload: Plan payload
        base_scores: Base scores
        weights: Score weights

    Returns:
        Adjusted scores
    """
    steps = payload.get("steps", [])

    # Adjust based on plan length
    cost = base_scores.cost
    if len(steps) > 5:
        cost = min(cost + 0.2, 1.0)
    elif len(steps) < 3:
        cost = max(cost - 0.1, 0.1)

    # Adjust utility based on completeness
    utility = base_scores.utility
    if all("parameters" in s for s in steps):
        utility = min(utility + 0.1, 1.0)

    return Scores(
        risk=base_scores.risk,
        utility=utility,
        cost=cost,
        confidence=base_scores.confidence,
    )


def _score_solver_config(
    payload: Dict[str, Any],
    base_scores: Scores,
    weights: ScoreWeights,
) -> Scores:
    """Score a solver config candidate.

    Args:
        payload: Config payload
        base_scores: Base scores
        weights: Score weights

    Returns:
        Adjusted scores
    """
    safety_level = payload.get("safety_level", "conservative")

    # Conservative configs have lower risk
    risk = base_scores.risk
    if safety_level == "conservative":
        risk = max(risk - 0.1, 0.1)

    return Scores(
        risk=risk,
        utility=base_scores.utility,
        cost=base_scores.cost,
        confidence=base_scores.confidence,
    )


def _score_explain(
    payload: Dict[str, Any],
    base_scores: Scores,
    weights: ScoreWeights,
) -> Scores:
    """Score an explain candidate.

    Args:
        payload: Explanation payload
        base_scores: Base scores
        weights: Score weights

    Returns:
        Adjusted scores
    """
    summary = payload.get("summary", {})
    recommendations = payload.get("recommendations", [])

    # Explanations with recommendations have higher utility
    utility = base_scores.utility
    if len(recommendations) > 2:
        utility = min(utility + 0.1, 1.0)

    return Scores(
        risk=base_scores.risk,
        utility=utility,
        cost=base_scores.cost,
        confidence=base_scores.confidence,
    )


def compute_composite_score(scores: Scores, weights: ScoreWeights) -> float:
    """Compute a composite score from individual scores.

    Args:
        scores: Individual scores
        weights: Score weights

    Returns:
        Composite score (0.0-1.0)
    """
    # Lower risk is better, so invert it
    adjusted_risk = 1.0 - scores.risk

    composite = (
        weights.risk_weight * adjusted_risk
        + weights.utility_weight * scores.utility
        + weights.cost_weight * (1.0 - scores.cost)  # Lower cost is better
        + weights.confidence_weight * scores.confidence
    )

    return max(0.0, min(1.0, composite))
