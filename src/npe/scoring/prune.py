"""
Pruning Utilities for NPE Candidates.

Implements deduplication and dominance pruning.
"""

from typing import Any, Dict, List, Set


def deduplicate(candidates: List[Any]) -> List[Any]:
    """Remove duplicate candidates by payload hash.
    
    Duplicates are defined as candidates with the same
    (candidate_type, payload_hash) pair.
    
    Args:
        candidates: List of candidates
        
    Returns:
        Deduplicated list preserving order
    """
    seen: Set[str] = []
    unique = []
    
    for candidate in candidates:
        key = (candidate.candidate_type, candidate.payload_hash)
        key_str = f"{key[0]}:{key[1]}"
        
        if key_str not in seen:
            seen.add(key_str)
            unique.append(candidate)
    
    return unique


def dominance_prune(candidates: List[Any]) -> List[Any]:
    """Prune dominated candidates.
    
    A candidate is dominated if there exists another candidate
    that is at least as good in all dimensions and strictly
    better in at least one.
    
    Args:
        candidates: List of candidates
        
    Returns:
        Pareto-optimal candidates
    """
    if len(candidates) <= 1:
        return candidates
    
    # Group by candidate type
    by_type: Dict[str, List[Any]] = {}
    for candidate in candidates:
        if candidate.candidate_type not in by_type:
            by_type[candidate.candidate_type] = []
        by_type[candidate.candidate_type].append(candidate)
    
    # Prune within each type
    pruned: List[Any] = []
    for candidate_type, type_candidates in by_type.items():
        non_dominated = _get_non_dominated(type_candidates)
        pruned.extend(non_dominated)
    
    return pruned


def _get_non_dominated(candidates: List[Any]) -> List[Any]:
    """Get non-dominated candidates using Pareto optimality.
    
    A candidate dominates another if:
    - risk <= other.risk (lower is better)
    - utility >= other.utility (higher is better)
    - cost <= other.cost (lower is better)
    - confidence >= other.confidence (higher is better)
    
    Args:
        candidates: List of candidates
        
    Returns:
        Non-dominated candidates
    """
    if len(candidates) <= 1:
        return candidates[:]
    
    non_dominated = []
    
    for i, c1 in enumerate(candidates):
        is_dominated = False
        for c2 in candidates:
            if c1 is c2:
                continue
            
            # Check if c2 dominates c1
            if (
                c2.scores.risk <= c1.scores.risk and
                c2.scores.utility >= c1.scores.utility and
                c2.scores.cost <= c1.scores.cost and
                c2.scores.confidence >= c1.scores.confidence and
                (
                    c2.scores.risk < c1.scores.risk or
                    c2.scores.utility > c1.scores.utility or
                    c2.scores.cost < c1.scores.cost or
                    c2.scores.confidence > c1.scores.confidence
                )
            ):
                is_dominated = True
                break
        
        if not is_dominated:
            non_dominated.append(c1)
    
    return non_dominated


def prune_by_count(candidates: List[Any], max_count: int) -> List[Any]:
    """Prune candidates to maximum count.
    
    Args:
        candidates: List of candidates
        max_count: Maximum number to keep
        
    Returns:
        Truncated list
    """
    if len(candidates) <= max_count:
        return candidates[:]
    
    # Keep first max_count (already sorted)
    return candidates[:max_count]


def combine_pruning(candidates: List[Any], max_count: int = 16) -> List[Any]:
    """Combine all pruning operations.
    
    Args:
        candidates: List of candidates
        max_count: Maximum final count
        
    Returns:
        Pruned candidates
    """
    # First deduplicate
    unique = deduplicate(candidates)
    
    # Then dominance prune
    non_dominated = dominance_prune(unique)
    
    # Finally limit count
    return prune_by_count(non_dominated, max_count)
