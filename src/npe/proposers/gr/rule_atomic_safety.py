"""
Atomic Safety Rule Proposer.

Proposes conservative safety configurations from rulepacks.
"""

from typing import Any, Dict, List

from ...core.budgets import Budgets
from ...core.hashing import hash_candidate, hash_candidate_payload
from ...core.types import Candidate, ProposerMeta, Scores


def propose(
    context: Dict[str, Any],
    budget: Budgets,
    registry: Any,
) -> List[Candidate]:
    """Propose safety rules from rulepacks.
    
    Args:
        context: Execution context
        budget: Budget constraints
        registry: Proposer registry
        
    Returns:
        List of solver config and repair candidates
    """
    candidates = []
    
    # Get risk posture from context
    ctx = context.get("context", {})
    risk_posture = ctx.get("risk_posture", "conservative")
    
    # Load rulepacks
    codebook_store = context.get("codebook_store")
    if not codebook_store:
        return candidates
    
    # Get conservative knobs
    knobs = codebook_store.get_conservative_knobs("gr")
    
    if not knobs:
        return candidates
    
    # Create solver config candidate
    solver_config = _create_solver_config(knobs, risk_posture, context)
    if solver_config:
        candidates.append(solver_config)
    
    # Create safety repair candidates for applicable rules
    rules = codebook_store.get_rules("gr")
    for rule in rules[:budget.max_candidates]:
        if rule.get("safety_critical", False):
            repair = _create_safety_repair(rule, context)
            if repair:
                candidates.append(repair)
    
    return candidates


def _create_solver_config(
    knobs: Dict[str, Any],
    risk_posture: str,
    context: Dict[str, Any],
) -> Candidate:
    """Create a solver configuration candidate.
    
    Args:
        knobs: Conservative knob settings
        risk_posture: Current risk posture
        context: Execution context
        
    Returns:
        Solver config candidate
    """
    # Adjust knobs based on risk posture
    if risk_posture == "aggressive":
        # Relax some constraints
        knobs = dict(knobs)
        for key in knobs:
            if isinstance(knobs[key], (int, float)):
                knobs[key] = knobs[key] * 1.5 if key.startswith("max_") else knobs[key]
    
    payload = {
        "config_type": "solver",
        "knobs": knobs,
        "risk_posture": risk_posture,
        "safety_level": "conservative",
    }
    
    payload_hash = hash_candidate_payload(payload)
    
    state_ref = context.get("state_ref")
    constraints_ref = context.get("constraints_ref")
    
    input_state_hash = state_ref.state_hash if state_ref else ""
    constraints_hash = constraints_ref.constraints_hash if constraints_ref else ""
    
    candidate = Candidate(
        candidate_hash="",
        candidate_type="solver_config",
        domain="gr",
        input_state_hash=input_state_hash,
        constraints_hash=constraints_hash,
        payload_format="json",
        payload_hash=payload_hash,
        payload=payload,
        evidence=[],
        scores=_score_config(knobs, risk_posture),
        proposer_meta=ProposerMeta(
            proposer_id="gr.rule.atomic_safety",
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


def _create_safety_repair(
    rule: Dict[str, Any],
    context: Dict[str, Any],
) -> Candidate:
    """Create a safety repair candidate from a rule.
    
    Args:
        rule: Safety rule from rulepacks
        context: Execution context
        
    Returns:
        Safety repair candidate
    """
    payload = {
        "repair_type": "safety_enforcement",
        "rule_id": rule.get("rule_id", ""),
        "rule_name": rule.get("name", ""),
        "description": rule.get("description", ""),
        "enforcement": rule.get("enforcement", "hard"),
        "parameters": rule.get("parameters", {}),
    }
    
    payload_hash = hash_candidate_payload(payload)
    
    state_ref = context.get("state_ref")
    constraints_ref = context.get("constraints_ref")
    
    input_state_hash = state_ref.state_hash if state_ref else ""
    constraints_hash = constraints_ref.constraints_hash if constraints_ref else ""
    
    candidate = Candidate(
        candidate_hash="",
        candidate_type="repair",
        domain="gr",
        input_state_hash=input_state_hash,
        constraints_hash=constraints_hash,
        payload_format="json",
        payload_hash=payload_hash,
        payload=payload,
        evidence=[],
        scores=_score_rule(rule),
        proposer_meta=ProposerMeta(
            proposer_id="gr.rule.atomic_safety",
            invocation_order=1,
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


def _score_config(knobs: Dict[str, Any], risk_posture: str) -> Scores:
    """Score a solver configuration.
    
    Args:
        knobs: Configuration knobs
        risk_posture: Current risk posture
        
    Returns:
        Scores for the config
    """
    return Scores(
        risk=0.2 if risk_posture == "conservative" else 0.5,
        utility=0.7,
        cost=0.3,
        confidence=0.9,
    )


def _score_rule(rule: Dict[str, Any]) -> Scores:
    """Score a safety rule.
    
    Args:
        rule: Safety rule
        
    Returns:
        Scores for the rule
    """
    return Scores(
        risk=0.1,  # Safety rules reduce risk
        utility=0.8,
        cost=0.2,
        confidence=0.9,
    )
