"""
Evidence Filters.

Implements taint, scenario, time, and privacy filters for evidence retrieval.
"""

from typing import Any, Dict, List, Optional


def apply_filters(
    evidence: List[Dict[str, Any]],
    context: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Apply all relevant filters to evidence.

    Args:
        evidence: List of evidence items
        context: Execution context with filter parameters

    Returns:
        Filtered evidence list
    """
    filtered = evidence

    # Get context parameters
    ctx = context.get("context", {})
    scenario_id = ctx.get("scenario_id")
    time_scope = ctx.get("time_scope", {})
    policy_tags = ctx.get("policy_tags", [])

    # Apply scenario scope filter
    if scenario_id:
        filtered = scenario_scope_filter(filtered, scenario_id)

    # Apply time scope filter
    if time_scope:
        filtered = time_scope_filter(filtered, time_scope)

    # Apply privacy filter
    filtered = privacy_scope_filter(filtered, policy_tags)

    # Apply trust scope filter
    allowed_sources = ctx.get("allowed_sources", [])
    if allowed_sources:
        filtered = trust_scope_filter(filtered, allowed_sources)

    return filtered


def scenario_scope_filter(
    evidence: List[Dict[str, Any]],
    scenario_id: str,
) -> List[Dict[str, Any]]:
    """Filter evidence by scenario scope.

    Cross-scenario evidence is filtered out by default.

    Args:
        evidence: List of evidence items
        scenario_id: Current scenario identifier

    Returns:
        Filtered evidence with matching scenario
    """
    filtered = []

    for item in evidence:
        item_scenario = item.get("scope", {}).get("scenario_id")

        # Include if no scenario set (universal) or matches current
        if item_scenario is None or item_scenario == scenario_id:
            item["filters_applied"] = item.get("filters_applied", []) + ["scenario_scope"]
            filtered.append(item)

    return filtered


def time_scope_filter(
    evidence: List[Dict[str, Any]],
    time_scope: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Filter evidence by time scope.

    Args:
        evidence: List of evidence items
        time_scope: Time scope parameters (e.g., {"after": 1234567890, "before": 1234567900})

    Returns:
        Filtered evidence within time bounds
    """
    if not time_scope:
        return evidence

    after = time_scope.get("after")
    before = time_scope.get("before")

    filtered = []

    for item in evidence:
        item_time = item.get("scope", {}).get("timestamp")

        if item_time is None:
            # Include undated evidence
            item["filters_applied"] = item.get("filters_applied", []) + ["time_scope"]
            filtered.append(item)
        else:
            # Check bounds
            include = True
            if after is not None and item_time < after:
                include = False
            if before is not None and item_time > before:
                include = False

            if include:
                item["filters_applied"] = item.get("filters_applied", []) + ["time_scope"]
                filtered.append(item)

    return filtered


def privacy_scope_filter(
    evidence: List[Dict[str, Any]],
    policy_tags: List[str],
) -> List[Dict[str, Any]]:
    """Filter evidence by privacy scope.

    Filters out evidence with privacy tags that don't match policy.

    Args:
        evidence: List of evidence items
        policy_tags: List of allowed privacy policy tags

    Returns:
        Filtered evidence respecting privacy
    """
    if not policy_tags:
        # Default: allow all
        return evidence

    filtered = []

    for item in evidence:
        taint_tags = item.get("taint_tags", [])
        privacy_tags = [t for t in taint_tags if t.startswith("privacy:")]

        # Check if any privacy tag is allowed
        allowed = True
        for priv_tag in privacy_tags:
            # Extract the privacy level from tag (e.g., "privacy:internal")
            if priv_tag not in policy_tags:
                allowed = False
                break

        if allowed:
            item["filters_applied"] = item.get("filters_applied", []) + ["privacy_scope"]
            filtered.append(item)

    return filtered


def trust_scope_filter(
    evidence: List[Dict[str, Any]],
    allowed_sources: List[str],
) -> List[Dict[str, Any]]:
    """Filter evidence by trusted sources.

    Args:
        evidence: List of evidence items
        allowed_sources: List of allowed source types

    Returns:
        Filtered evidence from trusted sources
    """
    if not allowed_sources:
        return evidence

    filtered = []

    for item in evidence:
        source_type = item.get("source_type", "")

        if source_type in allowed_sources:
            item["filters_applied"] = item.get("filters_applied", []) + ["trust_scope"]
            filtered.append(item)

    return filtered


def taint_filter(
    evidence: List[Dict[str, Any]],
    exclude_tags: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Filter evidence by taint tags.

    Args:
        evidence: List of evidence items
        exclude_tags: Tags that exclude evidence

    Returns:
        Filtered evidence without excluded taint tags
    """
    if not exclude_tags:
        return evidence

    filtered = []

    for item in evidence:
        taint_tags = item.get("taint_tags", [])

        has_excluded = any(tag in exclude_tags for tag in taint_tags)

        if not has_excluded:
            item["filters_applied"] = item.get("filters_applied", []) + ["taint_filter"]
            filtered.append(item)

    return filtered
