"""
Ranking Utilities for NPE Candidates.

Implements stable ranking with deterministic tie-breaks.
"""

from typing import Any, List, Optional

from ..core.types import Candidate
from .prune import combine_pruning
from .score import ScoreWeights, compute_composite_score


def rank_candidates(
    candidates: List[Candidate],
    weights: Optional[ScoreWeights] = None,
    max_count: int = 16,
) -> List[Candidate]:
    """Rank and prune candidates.

    Args:
        candidates: List of candidates to rank
        weights: Optional score weights
        max_count: Maximum candidates to return

    Returns:
        Ranked and pruned candidates
    """
    if not candidates:
        return []

    # Compute composite scores
    if weights is None:
        weights = ScoreWeights()

    for candidate in candidates:
        candidate._composite_score = compute_composite_score(candidate.scores, weights)

    # Sort by composite score (descending), then by candidate type, then by payload hash
    sorted_candidates = sorted(
        candidates,
        key=lambda c: (
            -getattr(c, "_composite_score", 0.0),  # Descending
            c.candidate_type,
            c.payload_hash,
        ),
    )

    # Apply pruning
    return combine_pruning(sorted_candidates, max_count)


def stable_sort(
    candidates: List[Candidate],
    primary_key: str,
    secondary_key: Optional[str] = None,
    ascending: bool = False,
) -> List[Candidate]:
    """Stable sort candidates by key.

    Args:
        candidates: List of candidates
        primary_key: Primary sort key field
        secondary_key: Secondary sort key for ties
        ascending: Sort order

    Returns:
        Sorted candidates
    """

    def get_key(c: Candidate) -> tuple:
        primary = getattr(c, primary_key, "") or ""
        secondary = getattr(c, secondary_key, "") or "" if secondary_key else ""

        if ascending:
            return (primary, secondary)
        else:
            # For descending, we need to reverse the comparison
            # Python's sort is stable, so we can use negative for numbers
            if isinstance(primary, (int, float)):
                return (
                    -primary,
                    (
                        -float(secondary)
                        if secondary and secondary.replace(".", "").isdigit()
                        else secondary
                    ),
                )
            return (primary, secondary)

    return sorted(candidates, key=get_key)


def rank_by_utility(candidates: List[Candidate], ascending: bool = False) -> List[Candidate]:
    """Rank candidates by utility score.

    Args:
        candidates: List of candidates
        ascending: Sort order

    Returns:
        Sorted candidates
    """
    return stable_sort(candidates, "scores.utility", "payload_hash", ascending)


def rank_by_risk(candidates: List[Candidate], ascending: bool = True) -> List[Candidate]:
    """Rank candidates by risk score.

    Args:
        candidates: List of candidates
        ascending: Sort order (lower risk first by default)

    Returns:
        Sorted candidates
    """
    return stable_sort(candidates, "scores.risk", "payload_hash", ascending)


def rank_by_cost(candidates: List[Candidate], ascending: bool = True) -> List[Candidate]:
    """Rank candidates by cost score.

    Args:
        candidates: List of candidates
        ascending: Sort order (lower cost first by default)

    Returns:
        Sorted candidates
    """
    return stable_sort(candidates, "scores.cost", "payload_hash", ascending)


def rank_by_confidence(candidates: List[Candidate], ascending: bool = False) -> List[Candidate]:
    """Rank candidates by confidence score.

    Args:
        candidates: List of candidates
        ascending: Sort order

    Returns:
        Sorted candidates
    """
    return stable_sort(candidates, "scores.confidence", "payload_hash", ascending)


def multi_criteria_rank(
    candidates: List[Candidate],
    criteria: List[tuple],
    max_count: int = 16,
) -> List[Candidate]:
    """Rank by multiple criteria with tie-breakers.

    Args:
        candidates: List of candidates
        criteria: List of (field, weight) tuples
        max_count: Maximum candidates to return

    Returns:
        Ranked candidates
    """

    def compute_score(c: Candidate) -> float:
        total = 0.0
        for field, weight in criteria:
            value = getattr(c.scores, field, 0.5)
            total += value * weight
        return total

    for candidate in candidates:
        candidate._multi_score = compute_score(candidate)

    sorted_candidates = sorted(
        candidates,
        key=lambda c: (
            -getattr(c, "_multi_score", 0.0),
            c.candidate_type,
            c.payload_hash,
        ),
    )

    return sorted_candidates[:max_count]
