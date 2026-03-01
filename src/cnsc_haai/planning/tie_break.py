"""
Tie-Breaking - Deterministic Selection When Scores Are Equal

When multiple plans have equal scores, we need deterministic tie-breaking
to ensure reproducible behavior. This module implements lexicographic
tie-breaking by plan hash.
"""

from __future__ import annotations
from typing import List, Tuple

from .planset_generator import Plan


def tie_break_plans(
    plans: List[Plan],
    scores: List[int],
) -> Tuple[int, Plan]:
    """
    Resolve ties using lexicographic ordering by plan hash.
    
    When multiple plans have the same score, this ensures deterministic
    selection by comparing plan hashes lexicographically (ascending).
    
    Args:
        plans: List of plans (same length as scores)
        scores: List of scores (same length as plans)
    
    Returns:
        (best_index, best_plan)
    
    Raises:
        ValueError: If plans and scores have different lengths
    """
    if len(plans) != len(scores):
        raise ValueError(f"Plans ({len(plans)}) and scores ({len(scores)}) must have same length")
    
    if not plans:
        raise ValueError("Cannot tie-break empty list")
    
    # Find minimum score
    min_score = min(scores)
    
    # Get all plans with minimum score
    min_score_indices = [i for i, s in enumerate(scores) if s == min_score]
    
    if len(min_score_indices) == 1:
        # No tie - single best plan
        idx = min_score_indices[0]
        return idx, plans[idx]
    
    # Tie-breaking: sort by plan_hash (lexicographic, ascending)
    tied_plans = [(i, plans[i]) for i in min_score_indices]
    tied_plans.sort(key=lambda x: x[1].plan_hash)
    
    # Return first after sorting
    return tied_plans[0]


def tie_break_by_index(
    plans: List[Plan],
    scores: List[int],
) -> int:
    """
    Simple tie-breaking by lowest index.
    
    This is a simpler alternative that just picks the plan
    with the lowest index among tied scores.
    
    Args:
        plans: List of plans
        scores: List of scores
    
    Returns:
        Index of best plan
    """
    if len(plans) != len(scores):
        raise ValueError(f"Plans ({len(plans)}) and scores ({len(scores)}) must have same length")
    
    if not plans:
        raise ValueError("Cannot tie-break empty list")
    
    # Find minimum score
    min_score = min(scores)
    
    # Get first plan with minimum score
    for i, s in enumerate(scores):
        if s == min_score:
            return i
    
    # Should never reach here
    return 0


def verify_tie_break_determinism(
    plans: List[Plan],
    scores: List[int],
    num_trials: int = 10,
) -> bool:
    """
    Verify that tie-breaking is deterministic across multiple calls.
    
    Args:
        plans: List of plans
        scores: List of scores
        num_trials: Number of trials to run
    
    Returns:
        True if all trials return same result
    """
    if len(plans) != len(scores):
        raise ValueError(f"Plans ({len(plans)}) and scores ({len(scores)}) must have same length")
    
    results = []
    for _ in range(num_trials):
        idx, _ = tie_break_plans(plans, scores)
        results.append(idx)
    
    # All results should be the same
    return len(set(results)) == 1
