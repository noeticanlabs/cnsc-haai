"""
Template Plan Library Proposer.

Selects and instantiates plan templates based on goal type.
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
    """Propose plans from template library.

    Args:
        context: Execution context with goals
        budget: Budget constraints
        registry: Proposer registry

    Returns:
        List of plan candidates
    """
    candidates = []

    # Get goals from context
    goals = context.get("goals", [])

    if not goals:
        return candidates

    # Load plan templates
    codebook_store = context.get("codebook_store")
    if not codebook_store:
        return candidates

    # Process each goal
    for goal in goals:
        goal_type = goal.get("goal_type", "")
        goal_payload = goal.get("goal_payload", {})

        # Get templates for this goal type
        templates = codebook_store.get_plan_templates(goal_type)

        for template in templates[: budget.max_candidates]:
            candidate = _instantiate_template(template, goal_payload, context)
            if candidate:
                candidates.append(candidate)

    return candidates


def _instantiate_template(
    template: Dict[str, Any],
    goal_payload: Dict[str, Any],
    context: Dict[str, Any],
) -> Candidate:
    """Instantiate a plan template with goal parameters.

    Args:
        template: Plan template from codebook
        goal_payload: Parameters from the goal
        context: Execution context

    Returns:
        Instantiated plan candidate
    """
    # Merge template with goal parameters
    payload = {
        "plan_type": template.get("type", "generic"),
        "template_id": template.get("template_id", ""),
        "name": template.get("name", ""),
        "description": template.get("description", ""),
        "steps": [],
        "parameters": dict(template.get("parameters", {})),
    }

    # Instantiate steps with goal parameters
    for step in template.get("steps", []):
        instantiated_step = {
            "step_id": step.get("step_id", ""),
            "action": step.get("action", ""),
            "description": step.get("description", ""),
        }

        # Fill in parameters from goal payload
        params = step.get("parameters", {})
        filled_params = {}
        for key, value in params.items():
            if isinstance(value, str) and value.startswith("${"):
                param_name = value[2:-1]
                filled_params[key] = goal_payload.get(param_name, value)
            else:
                filled_params[key] = value
        instantiated_step["parameters"] = filled_params

        payload["steps"].append(instantiated_step)

    # Add metadata
    payload["goal_type"] = template.get("goal_type", "")
    payload["tags"] = template.get("tags", [])
    payload["preconditions"] = template.get("preconditions", [])
    payload["postconditions"] = template.get("postconditions", [])

    payload_hash = hash_candidate_payload(payload)

    state_ref = context.get("state_ref")
    constraints_ref = context.get("constraints_ref")

    input_state_hash = state_ref.state_hash if state_ref else ""
    constraints_hash = constraints_ref.constraints_hash if constraints_ref else ""

    candidate = Candidate(
        candidate_hash="",
        candidate_type="plan",
        domain="gr",
        input_state_hash=input_state_hash,
        constraints_hash=constraints_hash,
        payload_format="json",
        payload_hash=payload_hash,
        payload=payload,
        evidence=[],
        scores=_score_template(template, goal_payload),
        proposer_meta=ProposerMeta(
            proposer_id="gr.template.plan_library",
            invocation_order=0,
        ),
    )

    candidate.candidate_hash = hash_candidate(
        {
            "candidate_type": candidate.candidate_type,
            "domain": candidate.domain,
            "input_state_hash": candidate.input_state_hash,
            "constraints_hash": candidate.constraints_hash,
            "payload_hash": candidate.payload_hash,
            "payload": candidate.payload,
        }
    )

    return candidate


def _score_template(
    template: Dict[str, Any],
    goal_payload: Dict[str, Any],
) -> Scores:
    """Score a template instantiation.

    Args:
        template: Plan template
        goal_payload: Goal parameters

    Returns:
        Scores for the plan
    """
    # Base scores
    base_confidence = template.get("confidence", 0.7)

    # Check parameter coverage
    params = template.get("parameters", {})
    filled = sum(1 for v in params.values() if not isinstance(v, str) or not v.startswith("${"))
    coverage = filled / len(params) if params else 1.0

    confidence = base_confidence * coverage

    # Estimate utility and cost from template properties
    complexity = template.get("complexity", "medium")
    if complexity == "low":
        utility = 0.6
        cost = 0.2
    elif complexity == "high":
        utility = 0.9
        cost = 0.6
    else:
        utility = 0.7
        cost = 0.4

    return Scores(
        risk=0.3,
        utility=utility,
        cost=cost,
        confidence=confidence,
    )
