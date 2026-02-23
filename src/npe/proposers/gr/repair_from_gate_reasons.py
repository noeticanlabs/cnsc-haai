"""
Repair Proposer from Gate Reasons.

Maps gate failures to repair actions using the repair map codebook.
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
    """Propose repairs based on gate failures.
    
    Args:
        context: Execution context with failure info
        budget: Budget constraints
        registry: Proposer registry
        
    Returns:
        List of repair candidates
    """
    candidates = []
    
    # Get failure info from context
    failure = context.get("failure", {})
    failing_gates = failure.get("failing_gates", [])
    
    if not failing_gates:
        return candidates
    
    # Load repair map
    codebook_store = context.get("codebook_store")
    if not codebook_store:
        return candidates
    
    # Generate repair candidates for each failing gate
    for gate_type in failing_gates:
        repair_actions = codebook_store.get_repair_actions("gr", gate_type)
        
        for action in repair_actions:
            if len(candidates) >= budget.max_candidates:
                break
            candidate = _create_repair_candidate(gate_type, action, context)
            if candidate:
                candidates.append(candidate)
    
    # Enforce global budget limit
    return candidates[:budget.max_candidates]


def _create_repair_candidate(
    gate_type: str,
    action: Dict[str, Any],
    context: Dict[str, Any],
) -> Candidate:
    """Create a repair candidate from an action.
    
    Args:
        gate_type: The failing gate type
        action: Repair action from codebook
        context: Execution context
        
    Returns:
        Candidate or None if invalid
    """
    # Build payload
    payload = {
        "repair_type": action.get("type", "parameter_adjustment"),
        "target_gate": gate_type,
        "description": action.get("description", ""),
        "parameters": action.get("parameters", {}),
        "rationale": action.get("rationale", ""),
        "preconditions": action.get("preconditions", []),
    }
    
    # Compute payload hash
    payload_hash = hash_candidate_payload(payload)
    
    # Get state and constraints hashes
    state_ref = context.get("state_ref")
    constraints_ref = context.get("constraints_ref")
    
    # Handle both dict (test) and StateRef object (production)
    if state_ref is None:
        input_state_hash = ""
    elif isinstance(state_ref, dict):
        input_state_hash = state_ref.get("state_hash", "")
    else:
        input_state_hash = state_ref.state_hash if hasattr(state_ref, 'state_hash') else ""
    # Handle both dict (test) and ConstraintsRef object (production)
    if constraints_ref is None:
        constraints_hash = ""
    elif isinstance(constraints_ref, dict):
        constraints_hash = constraints_ref.get("constraints_hash", "")
    else:
        constraints_hash = constraints_ref.constraints_hash if hasattr(constraints_ref, 'constraints_hash') else ""
    
    # Create candidate
    candidate = Candidate(
        candidate_hash="",  # Will be computed
        candidate_type="repair",
        domain="gr",
        input_state_hash=input_state_hash,
        constraints_hash=constraints_hash,
        payload_format="json",
        payload_hash=payload_hash,
        payload=payload,
        evidence=[],
        scores=_score_repair(action),
        suggested_gate_stack=action.get("suggested_gate_stack"),
        proposer_meta=ProposerMeta(
            proposer_id="gr.repair.from_gate_reasons",
            invocation_order=0,
        ),
    )
    
    # Compute candidate hash
    candidate.candidate_hash = hash_candidate({
        "candidate_type": candidate.candidate_type,
        "domain": candidate.domain,
        "input_state_hash": candidate.input_state_hash,
        "constraints_hash": candidate.constraints_hash,
        "payload_hash": candidate.payload_hash,
        "payload": candidate.payload,
    })
    
    return candidate


def _score_repair(action: Dict[str, Any]) -> Scores:
    """Score a repair action.
    
    Args:
        action: Repair action from codebook
        
    Returns:
        Scores for the repair
    """
    # Base scores
    risk = 0.3  # Conservative by default
    utility = 0.7
    cost = 0.3
    confidence = 0.8
    
    # Adjust based on action properties
    if action.get("safety_level") == "high":
        risk = 0.1
        confidence = 0.9
    elif action.get("safety_level") == "low":
        risk = 0.6
        confidence = 0.5
    
    # Adjust based on impact
    impact = action.get("impact", "medium")
    if impact == "low":
        utility = 0.5
        cost = 0.2
    elif impact == "high":
        utility = 0.9
        cost = 0.5
    
    return Scores(
        risk=risk,
        utility=utility,
        cost=cost,
        confidence=confidence,
    )
