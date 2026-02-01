"""
Enhanced CGL Policy Engine

Provides comprehensive policy parsing, evaluation, conflict detection,
and enforcement capabilities for HAAI governance.
"""

import logging
import re
import json
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Tuple, Union
from datetime import datetime, timedelta
from enum import Enum
import asyncio


class PolicyType(Enum):
    """Types of governance policies."""
    SAFETY = "safety"
    SECURITY = "security"
    PERFORMANCE = "performance"
    COMPLIANCE = "compliance"
    ETHICAL = "ethical"
    RESOURCE = "resource"
    PRIVACY = "privacy"


class PolicyStatus(Enum):
    """Policy lifecycle status."""
    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEPRECATED = "deprecated"
    CONFLICTED = "conflicted"


class EnforcementLevel(Enum):
    """Policy enforcement levels."""
    ADVISORY = "advisory"
    WARNING = "warning"
    BLOCKING = "blocking"
    CRITICAL = "critical"


@dataclass
class PolicyConstraint:
    """Represents a policy constraint."""
    constraint_id: str
    name: str
    type: str  # range, set, pattern, function
    parameters: Dict[str, Any]
    enforcement_level: EnforcementLevel
    description: str = ""
    
    def evaluate(self, value: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate constraint against a value."""
        if self.type == "range":
            return self._evaluate_range(value, context)
        elif self.type == "set":
            return self._evaluate_set(value, context)
        elif self.type == "pattern":
            return self._evaluate_pattern(value, context)
        elif self.type == "function":
            return self._evaluate_function(value, context)
        else:
            return {"satisfied": True, "reason": "Unknown constraint type"}
    
    def _evaluate_range(self, value: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate range constraint."""
        min_val = self.parameters.get("min")
        max_val = self.parameters.get("max")
        
        if value is None:
            return {"satisfied": False, "reason": f"Value is None"}
        
        try:
            numeric_value = float(value)
            satisfied = (min_val is None or numeric_value >= min_val) and \
                       (max_val is None or numeric_value <= max_val)
            
            return {
                "satisfied": satisfied,
                "reason": f"Value {numeric_value} in range [{min_val}, {max_val}]"
            }
        except (ValueError, TypeError):
            return {"satisfied": False, "reason": f"Value {value} is not numeric"}
    
    def _evaluate_set(self, value: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate set membership constraint."""
        allowed_values = self.parameters.get("allowed_values", set())
        excluded_values = self.parameters.get("excluded_values", set())
        
        if value in excluded_values:
            return {"satisfied": False, "reason": f"Value {value} is excluded"}
        
        if allowed_values and value not in allowed_values:
            return {"satisfied": False, "reason": f"Value {value} not in allowed set"}
        
        return {"satisfied": True, "reason": f"Value {value} allowed"}
    
    def _evaluate_pattern(self, value: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate pattern constraint."""
        pattern = self.parameters.get("pattern", "")
        
        if not isinstance(value, str):
            return {"satisfied": False, "reason": f"Value {value} is not a string"}
        
        try:
            satisfied = bool(re.match(pattern, value))
            return {
                "satisfied": satisfied,
                "reason": f"Value '{value}' matches pattern '{pattern}': {satisfied}"
            }
        except re.error:
            return {"satisfied": False, "reason": f"Invalid pattern: {pattern}"}
    
    def _evaluate_function(self, value: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate function-based constraint."""
        function_name = self.parameters.get("function", "")
        
        # Built-in safety functions
        if function_name == "coherence_threshold":
            threshold = self.parameters.get("threshold", 0.7)
            coherence = context.get("coherence_score", 0.0)
            satisfied = coherence >= threshold
            return {
                "satisfied": satisfied,
                "reason": f"Coherence {coherence} >= threshold {threshold}"
            }
        elif function_name == "resource_limit":
            resource_type = self.parameters.get("resource_type", "memory")
            limit = self.parameters.get("limit", 1024)
            usage = context.get(f"{resource_type}_usage", 0)
            satisfied = usage <= limit
            return {
                "satisfied": satisfied,
                "reason": f"{resource_type} usage {usage} <= limit {limit}"
            }
        elif function_name == "abstraction_depth":
            max_depth = self.parameters.get("max_depth", 10)
            current_depth = context.get("abstraction_depth", 0)
            satisfied = current_depth <= max_depth
            return {
                "satisfied": satisfied,
                "reason": f"Abstraction depth {current_depth} <= max {max_depth}"
            }
        
        return {"satisfied": True, "reason": f"Unknown function: {function_name}"}


@dataclass
class PolicyRule:
    """Represents a policy rule."""
    rule_id: str
    name: str
    conditions: List[Dict[str, Any]]
    constraints: List[PolicyConstraint]
    actions: List[Dict[str, Any]]
    priority: int = 1
    enabled: bool = True
    
    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate rule against context."""
        if not self.enabled:
            return {"applicable": False, "reason": "Rule disabled"}
        
        # Check conditions
        for condition in self.conditions:
            if not self._evaluate_condition(condition, context):
                return {"applicable": False, "reason": f"Condition not met: {condition}"}
        
        # Evaluate constraints
        constraint_results = []
        for constraint in self.constraints:
            field = constraint.parameters.get("field", "")
            value = context.get(field)
            result = constraint.evaluate(value, context)
            constraint_results.append({
                "constraint_id": constraint.constraint_id,
                "result": result
            })
        
        # Check if any constraint is violated
        violations = [cr for cr in constraint_results if not cr["result"]["satisfied"]]
        
        return {
            "applicable": True,
            "constraints_satisfied": len(violations) == 0,
            "constraint_results": constraint_results,
            "violations": violations,
            "actions": self.actions if len(violations) == 0 else []
        }
    
    def _evaluate_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate a single condition."""
        field = condition.get("field", "")
        operator = condition.get("operator", "equals")
        expected_value = condition.get("value")
        
        actual_value = context.get(field)
        
        if operator == "equals":
            return actual_value == expected_value
        elif operator == "not_equals":
            return actual_value != expected_value
        elif operator == "in":
            return actual_value in expected_value
        elif operator == "not_in":
            return actual_value not in expected_value
        elif operator == "exists":
            return actual_value is not None
        elif operator == "not_exists":
            return actual_value is None
        
        return True  # Unknown operator, assume satisfied


@dataclass
class Policy:
    """Enhanced policy representation."""
    policy_id: str
    name: str
    description: str
    policy_type: PolicyType
    status: PolicyStatus
    rules: List[PolicyRule]
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0"
    author: str = "system"
    tags: Set[str] = field(default_factory=set)
    
    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate policy against context."""
        if self.status != PolicyStatus.ACTIVE:
            return {"applicable": False, "reason": f"Policy status: {self.status.value}"}
        
        rule_results = []
        for rule in self.rules:
            result = rule.evaluate(context)
            rule_results.append({
                "rule_id": rule.rule_id,
                "result": result
            })
        
        # Determine overall policy outcome
        applicable_rules = [rr for rr in rule_results if rr["result"]["applicable"]]
        violations = []
        
        for rr in applicable_rules:
            if not rr["result"]["constraints_satisfied"]:
                violations.extend(rr["result"]["violations"])
        
        return {
            "policy_id": self.policy_id,
            "applicable": len(applicable_rules) > 0,
            "compliant": len(violations) == 0,
            "rule_results": rule_results,
            "violations": violations,
            "actions": [action for rr in applicable_rules for action in rr["result"]["actions"]]
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert policy to dictionary."""
        return {
            "policy_id": self.policy_id,
            "name": self.name,
            "description": self.description,
            "policy_type": self.policy_type.value,
            "status": self.status.value,
            "rules": [
                {
                    "rule_id": rule.rule_id,
                    "name": rule.name,
                    "conditions": rule.conditions,
                    "constraints": [
                        {
                            "constraint_id": c.constraint_id,
                            "name": c.name,
                            "type": c.type,
                            "parameters": c.parameters,
                            "enforcement_level": c.enforcement_level.value,
                            "description": c.description
                        } for c in rule.constraints
                    ],
                    "actions": rule.actions,
                    "priority": rule.priority,
                    "enabled": rule.enabled
                } for rule in self.rules
            ],
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
            "author": self.author,
            "tags": list(self.tags)
        }


class PolicyConflict:
    """Represents a policy conflict."""
    
    def __init__(self, policy1_id: str, policy2_id: str, conflict_type: str, 
                 description: str, severity: str = "medium"):
        self.policy1_id = policy1_id
        self.policy2_id = policy2_id
        self.conflict_type = conflict_type
        self.description = description
        self.severity = severity
        self.detected_at = datetime.now()
        self.resolution_strategy = None
        self.resolved = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert conflict to dictionary."""
        return {
            "policy1_id": self.policy1_id,
            "policy2_id": self.policy2_id,
            "conflict_type": self.conflict_type,
            "description": self.description,
            "severity": self.severity,
            "detected_at": self.detected_at.isoformat(),
            "resolution_strategy": self.resolution_strategy,
            "resolved": self.resolved
        }


class PolicyEngine:
    """Enhanced policy engine with conflict detection and resolution."""
    
    def __init__(self):
        self.policies: Dict[str, Policy] = {}
        self.conflicts: List[PolicyConflict] = []
        self.logger = logging.getLogger("haai.policy_engine")
        self._policy_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = timedelta(minutes=5)
        
        # Load default policies
        self._load_default_policies()
    
    def _load_default_policies(self) -> None:
        """Load default governance policies."""
        # Coherence Threshold Policy
        coherence_policy = Policy(
            policy_id="coherence_threshold_v1",
            name="Coherence Threshold Policy",
            description="Ensures all operations maintain minimum coherence",
            policy_type=PolicyType.SAFETY,
            status=PolicyStatus.ACTIVE,
            rules=[
                PolicyRule(
                    rule_id="coherence_min_threshold",
                    name="Minimum Coherence Check",
                    conditions=[
                        {"field": "operation_type", "operator": "exists"}
                    ],
                    constraints=[
                        PolicyConstraint(
                            constraint_id="coherence_min",
                            name="Minimum Coherence",
                            type="function",
                            parameters={
                                "function": "coherence_threshold",
                                "threshold": 0.7,
                                "field": "coherence_score"
                            },
                            enforcement_level=EnforcementLevel.BLOCKING
                        )
                    ],
                    actions=[
                        {"type": "log", "level": "warning", "message": "Coherence below threshold"},
                        {"type": "require_approval", "role": "safety_officer"}
                    ],
                    priority=1
                )
            ],
            tags={"safety", "coherence", "core"}
        )
        
        # Resource Usage Policy
        resource_policy = Policy(
            policy_id="resource_limits_v1",
            name="Resource Usage Limits",
            description="Prevents resource exhaustion and ensures fair usage",
            policy_type=PolicyType.RESOURCE,
            status=PolicyStatus.ACTIVE,
            rules=[
                PolicyRule(
                    rule_id="memory_limit",
                    name="Memory Usage Limit",
                    conditions=[
                        {"field": "operation_type", "operator": "exists"}
                    ],
                    constraints=[
                        PolicyConstraint(
                            constraint_id="memory_max",
                            name="Maximum Memory",
                            type="function",
                            parameters={
                                "function": "resource_limit",
                                "resource_type": "memory",
                                "limit": 1024,
                                "field": "memory_usage_mb"
                            },
                            enforcement_level=EnforcementLevel.WARNING
                        )
                    ],
                    actions=[
                        {"type": "log", "level": "warning", "message": "High memory usage"},
                        {"type": "optimize", "target": "memory"}
                    ],
                    priority=2
                ),
                PolicyRule(
                    rule_id="abstraction_depth_limit",
                    name="Abstraction Depth Limit",
                    conditions=[
                        {"field": "operation_type", "operator": "equals", "value": "abstraction"}
                    ],
                    constraints=[
                        PolicyConstraint(
                            constraint_id="depth_max",
                            name="Maximum Abstraction Depth",
                            type="function",
                            parameters={
                                "function": "abstraction_depth",
                                "max_depth": 10,
                                "field": "abstraction_depth"
                            },
                            enforcement_level=EnforcementLevel.BLOCKING
                        )
                    ],
                    actions=[
                        {"type": "log", "level": "error", "message": "Abstraction depth exceeded"}
                    ],
                    priority=1
                )
            ],
            tags={"resource", "performance", "limits"}
        )
        
        # Safety Monitoring Policy
        safety_policy = Policy(
            policy_id="safety_monitoring_v1",
            name="Safety Monitoring Policy",
            description="Continuous safety monitoring and incident detection",
            policy_type=PolicyType.SAFETY,
            status=PolicyStatus.ACTIVE,
            rules=[
                PolicyRule(
                    rule_id="safety_score_check",
                    name="Safety Score Validation",
                    conditions=[
                        {"field": "operation_type", "operator": "exists"}
                    ],
                    constraints=[
                        PolicyConstraint(
                            constraint_id="safety_min_score",
                            name="Minimum Safety Score",
                            type="range",
                            parameters={
                                "min": 0.8,
                                "field": "safety_score"
                            },
                            enforcement_level=EnforcementLevel.CRITICAL
                        )
                    ],
                    actions=[
                        {"type": "log", "level": "critical", "message": "Safety score critical"},
                        {"type": "emergency_stop"},
                        {"type": "notify", "role": "safety_officer"}
                    ],
                    priority=1
                )
            ],
            tags={"safety", "monitoring", "critical"}
        )
        
        # Add policies to engine
        self.add_policy(coherence_policy)
        self.add_policy(resource_policy)
        self.add_policy(safety_policy)
    
    def add_policy(self, policy: Policy) -> None:
        """Add a policy to the engine."""
        self.policies[policy.policy_id] = policy
        self.logger.info(f"Added policy: {policy.name} ({policy.policy_id})")
        
        # Check for conflicts
        self._detect_conflicts(policy)
    
    def remove_policy(self, policy_id: str) -> None:
        """Remove a policy from the engine."""
        if policy_id in self.policies:
            del self.policies[policy_id]
            self.logger.info(f"Removed policy: {policy_id}")
            
            # Remove related conflicts
            self.conflicts = [c for c in self.conflicts 
                             if c.policy1_id != policy_id and c.policy2_id != policy_id]
    
    def update_policy(self, policy_id: str, updates: Dict[str, Any]) -> None:
        """Update an existing policy."""
        if policy_id not in self.policies:
            raise ValueError(f"Policy {policy_id} not found")
        
        policy = self.policies[policy_id]
        
        # Update fields
        for field, value in updates.items():
            if hasattr(policy, field):
                setattr(policy, field, value)
        
        policy.updated_at = datetime.now()
        self.logger.info(f"Updated policy: {policy_id}")
        
        # Re-check for conflicts
        self._detect_conflicts(policy)
    
    def evaluate_policies(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate all applicable policies against context."""
        # Check cache first
        cache_key = self._generate_cache_key(context)
        if cache_key in self._policy_cache:
            cached_result = self._policy_cache[cache_key]
            if datetime.now() - cached_result["cached_at"] < self._cache_ttl:
                return cached_result["result"]
        
        evaluation_results = {
            "context": context,
            "evaluated_at": datetime.now().isoformat(),
            "policy_results": {},
            "overall_compliant": True,
            "total_violations": [],
            "required_actions": [],
            "warnings": []
        }
        
        # Evaluate each policy
        for policy in self.policies.values():
            policy_result = policy.evaluate(context)
            evaluation_results["policy_results"][policy.policy_id] = policy_result
            
            if policy_result["applicable"]:
                if not policy_result["compliant"]:
                    evaluation_results["overall_compliant"] = False
                    evaluation_results["total_violations"].extend(policy_result["violations"])
                
                evaluation_results["required_actions"].extend(policy_result["actions"])
        
        # Cache result
        self._policy_cache[cache_key] = {
            "result": evaluation_results,
            "cached_at": datetime.now()
        }
        
        return evaluation_results
    
    def _detect_conflicts(self, new_policy: Policy) -> None:
        """Detect conflicts between policies."""
        for existing_policy in self.policies.values():
            if existing_policy.policy_id == new_policy.policy_id:
                continue
            
            conflict = self._check_policy_conflict(new_policy, existing_policy)
            if conflict:
                self.conflicts.append(conflict)
                self.logger.warning(f"Policy conflict detected: {conflict.description}")
    
    def _check_policy_conflict(self, policy1: Policy, policy2: Policy) -> Optional[PolicyConflict]:
        """Check for conflicts between two policies."""
        # Check for constraint conflicts
        for rule1 in policy1.rules:
            for rule2 in policy2.rules:
                for constraint1 in rule1.constraints:
                    for constraint2 in rule2.constraints:
                        # Same field, different constraints
                        field1 = constraint1.parameters.get("field")
                        field2 = constraint2.parameters.get("field")
                        
                        if field1 and field1 == field2:
                            if self._constraints_conflict(constraint1, constraint2):
                                return PolicyConflict(
                                    policy1.policy_id,
                                    policy2.policy_id,
                                    "constraint_conflict",
                                    f"Conflicting constraints on field {field1}",
                                    "high"
                                )
        
        return None
    
    def _constraints_conflict(self, constraint1: PolicyConstraint, 
                            constraint2: PolicyConstraint) -> bool:
        """Check if two constraints conflict."""
        # Range conflicts
        if constraint1.type == "range" and constraint2.type == "range":
            min1 = constraint1.parameters.get("min", float("-inf"))
            max1 = constraint1.parameters.get("max", float("inf"))
            min2 = constraint2.parameters.get("min", float("-inf"))
            max2 = constraint2.parameters.get("max", float("inf"))
            
            # Check if ranges are incompatible
            if max1 < min2 or max2 < min1:
                return True
        
        # Set conflicts
        if constraint1.type == "set" and constraint2.type == "set":
            allowed1 = set(constraint1.parameters.get("allowed_values", []))
            allowed2 = set(constraint2.parameters.get("allowed_values", []))
            
            if allowed1 and allowed2 and allowed1.isdisjoint(allowed2):
                return True
        
        return False
    
    def _generate_cache_key(self, context: Dict[str, Any]) -> str:
        """Generate cache key for context."""
        context_str = json.dumps(context, sort_keys=True)
        return hashlib.md5(context_str.encode()).hexdigest()
    
    def get_policy(self, policy_id: str) -> Optional[Policy]:
        """Get a policy by ID."""
        return self.policies.get(policy_id)
    
    def list_policies(self, policy_type: Optional[PolicyType] = None,
                     status: Optional[PolicyStatus] = None) -> List[Policy]:
        """List policies with optional filtering."""
        policies = list(self.policies.values())
        
        if policy_type:
            policies = [p for p in policies if p.policy_type == policy_type]
        
        if status:
            policies = [p for p in policies if p.status == status]
        
        return policies
    
    def get_conflicts(self) -> List[PolicyConflict]:
        """Get all policy conflicts."""
        return self.conflicts.copy()
    
    def resolve_conflict(self, conflict_id: str, resolution_strategy: str) -> None:
        """Resolve a policy conflict."""
        for conflict in self.conflicts:
            if (f"{conflict.policy1_id}_{conflict.policy2_id}" == conflict_id or
                f"{conflict.policy2_id}_{conflict.policy1_id}" == conflict_id):
                conflict.resolution_strategy = resolution_strategy
                conflict.resolved = True
                self.logger.info(f"Resolved conflict: {conflict.description}")
                return
        
        raise ValueError(f"Conflict {conflict_id} not found")
    
    def clear_cache(self) -> None:
        """Clear policy evaluation cache."""
        self._policy_cache.clear()
        self.logger.info("Policy cache cleared")
    
    def get_engine_status(self) -> Dict[str, Any]:
        """Get policy engine status."""
        active_policies = [p for p in self.policies.values() if p.status == PolicyStatus.ACTIVE]
        unresolved_conflicts = [c for c in self.conflicts if not c.resolved]
        
        return {
            "total_policies": len(self.policies),
            "active_policies": len(active_policies),
            "policy_types": list(set(p.policy_type.value for p in self.policies.values())),
            "total_conflicts": len(self.conflicts),
            "unresolved_conflicts": len(unresolved_conflicts),
            "cache_size": len(self._policy_cache),
            "cache_ttl_minutes": self._cache_ttl.total_seconds() / 60
        }