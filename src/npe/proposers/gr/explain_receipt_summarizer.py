"""
Receipt Summarizer Proposer.

Creates structured explanations from receipt data.
"""

from typing import Any, Dict, List

from ...core.budgets import Budgets
from ...core.hashing import hash_candidate, hash_candidate_payload
from ...core.types import Candidate, EvidenceItem, ProposerMeta, Scores


def propose(
    context: Dict[str, Any],
    budget: Budgets,
    registry: Any,
) -> List[Candidate]:
    """Propose explanations from receipts.
    
    Args:
        context: Execution context with receipts
        budget: Budget constraints
        registry: Proposer registry
        
    Returns:
        List of explanation candidates
    """
    candidates = []
    
    # Get receipts from context
    receipts_store = context.get("receipts_store")
    if not receipts_store:
        return candidates
    
    # Get state and failure info
    state_ref = context.get("state_ref")
    failure = context.get("failure", {})
    
    # Search for relevant receipts
    relevant_receipts = []
    
    if failure.get("failing_gates"):
        for gate_id in failure["failing_gates"]:
            relevant_receipts.extend(receipts_store.get_by_gate_id(gate_id))
    
    # Get passing receipts for comparison
    passing_receipts = receipts_store.get_passing_receipts()[:10]
    
    # Create explanation candidate
    if relevant_receipts or passing_receipts:
        candidate = _create_explanation(
            relevant_receipts,
            passing_receipts,
            state_ref,
            failure,
            context,
        )
        if candidate:
            candidates.append(candidate)
    
    return candidates


def _create_explanation(
    failing_receipts: List[Any],
    passing_receipts: List[Any],
    state_ref: Any,
    failure: Dict[str, Any],
    context: Dict[str, Any],
) -> Candidate:
    """Create an explanation candidate from receipts.
    
    Args:
        failing_receipts: Receipts from failing gates
        passing_receipts: Sample of passing receipts
        state_ref: Current state reference
        failure: Failure information
        context: Execution context
        
    Returns:
        Explanation candidate
    """
    # Build explanation payload
    payload = {
        "explain_type": "receipt_summarization",
        "summary": _summarize_receipts(failing_receipts, passing_receipts),
        "failure_analysis": _analyze_failure(failure),
        "comparison": _compare_outcomes(failing_receipts, passing_receipts),
        "recommendations": _generate_recommendations(failing_receipts),
    }
    
    payload_hash = hash_candidate_payload(payload)
    
    input_state_hash = state_ref.state_hash if state_ref else ""
    
    # Create evidence items from receipts
    evidence = []
    for receipt in failing_receipts[:5]:
        evidence_item = EvidenceItem(
            evidence_id=receipt.receipt_id,
            source_type="receipt",
            source_ref=receipt.metadata.get("source", ""),
            content_hash=receipt.receipt_id,
            relevance=0.9,
        )
        evidence.append(evidence_item)
    
    candidate = Candidate(
        candidate_hash="",
        candidate_type="explain",
        domain="gr",
        input_state_hash=input_state_hash,
        constraints_hash="",
        payload_format="json",
        payload_hash=payload_hash,
        payload=payload,
        evidence=evidence,
        scores=_score_explanation(failing_receipts),
        proposer_meta=ProposerMeta(
            proposer_id="gr.explain.receipt_summarizer",
            invocation_order=0,
        ),
    )
    
    candidate.candidate_hash = hash_candidate({
        "candidate_type": candidate.candidate_type,
        "domain": candidate.domain,
        "input_state_hash": candidate.input_state_hash,
        "constraints_hash": candidate.constraints_hash,
        "payload_hash": candidate.payload_hash,
        "payload": candidate.payload,
    })
    
    return candidate


def _summarize_receipts(
    failing: List[Any],
    passing: List[Any],
) -> Dict[str, Any]:
    """Summarize receipt data.
    
    Args:
        failing: Failing receipts
        passing: Passing receipts
        
    Returns:
        Summary dict
    """
    return {
        "failing_count": len(failing),
        "passing_sample_count": len(passing),
        "common_reasons": _get_common_values(failing, "reason_code"),
        "common_gates": _get_common_values(failing, "gate_id"),
    }


def _analyze_failure(failure: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze the failure.
    
    Args:
        failure: Failure information
        
    Returns:
        Analysis dict
    """
    return {
        "failing_gates": failure.get("failing_gates", []),
        "proof_hash": failure.get("proof_hash", ""),
        "gate_stack_id": failure.get("gate_stack_id", ""),
    }


def _compare_outcomes(
    failing: List[Any],
    passing: List[Any],
) -> Dict[str, Any]:
    """Compare failing and passing outcomes.
    
    Args:
        failing: Failing receipts
        passing: Passing receipts
        
    Returns:
        Comparison dict
    """
    return {
        "pass_rate": len(passing) / (len(failing) + len(passing) + 0.001),
        "fail_rate": len(failing) / (len(failing) + len(passing) + 0.001),
    }


def _generate_recommendations(failing: List[Any]) -> List[str]:
    """Generate recommendations based on failures.
    
    Args:
        failing: Failing receipts
        
    Returns:
        List of recommendations
    """
    recommendations = []
    
    common_reasons = _get_common_values(failing, "reason_code")
    for reason in common_reasons[:3]:
        recommendations.append(f"Address {reason} issues")
    
    return recommendations


def _get_common_values(receipts: List[Any], field: str) -> List[str]:
    """Get most common values for a field.
    
    Args:
        receipts: List of receipts
        field: Field to extract
        
    Returns:
        List of common values sorted by frequency
    """
    from collections import Counter
    
    values = [getattr(r, field, None) for r in receipts if getattr(r, field, None)]
    counter = Counter(values)
    return [v for v, _ in counter.most_common(5)]


def _score_explanation(failing: List[Any]) -> Scores:
    """Score an explanation.
    
    Args:
        failing: Failing receipts
        
    Returns:
        Scores for the explanation
    """
    return Scores(
        risk=0.1,  # Explanations don't introduce risk
        utility=0.8,
        cost=0.1,
        confidence=0.7 + min(len(failing) * 0.05, 0.2),  # More evidence = higher confidence
    )
