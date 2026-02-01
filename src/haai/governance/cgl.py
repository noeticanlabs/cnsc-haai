"""
CGL (Coherence Governance Language) Implementation

Provides policy-based governance and compliance checking for HAAI agents.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class Policy:
    """Represents a governance policy."""
    policy_id: str
    name: str
    description: str
    rules: List[Dict[str, Any]]
    constraints: Dict[str, Any]
    priority: int
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert policy to dictionary."""
        return {
            "policy_id": self.policy_id,
            "name": self.name,
            "description": self.description,
            "rules": self.rules,
            "constraints": self.constraints,
            "priority": self.priority,
            "created_at": self.created_at.isoformat()
        }


class ComplianceChecker:
    """Checks compliance against governance policies."""
    
    def __init__(self):
        self.policies: Dict[str, Policy] = {}
        self.logger = logging.getLogger("haai.compliance_checker")
    
    def add_policy(self, policy: Policy) -> None:
        """Add a governance policy."""
        self.policies[policy.policy_id] = policy
        self.logger.info(f"Added policy: {policy.name}")
    
    def check_compliance(self, action: Dict[str, Any], 
                       context: Dict[str, Any]) -> Dict[str, Any]:
        """Check if action complies with all policies."""
        compliance_results = {
            "compliant": True,
            "violations": [],
            "warnings": [],
            "applied_policies": []
        }
        
        for policy in self.policies.values():
            policy_result = self._check_policy_compliance(policy, action, context)
            compliance_results["applied_policies"].append(policy.policy_id)
            
            if not policy_result["compliant"]:
                compliance_results["compliant"] = False
                compliance_results["violations"].extend(policy_result["violations"])
            
            compliance_results["warnings"].extend(policy_result.get("warnings", []))
        
        return compliance_results
    
    def _check_policy_compliance(self, policy: Policy, action: Dict[str, Any],
                               context: Dict[str, Any]) -> Dict[str, Any]:
        """Check compliance against a specific policy."""
        result = {
            "compliant": True,
            "violations": [],
            "warnings": []
        }
        
        for rule in policy.rules:
            rule_result = self._evaluate_rule(rule, action, context)
            if not rule_result["satisfied"]:
                result["compliant"] = False
                result["violations"].append({
                    "policy_id": policy.policy_id,
                    "rule": rule,
                    "reason": rule_result.get("reason", "Rule violated")
                })
        
        return result
    
    def _evaluate_rule(self, rule: Dict[str, Any], action: Dict[str, Any],
                     context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a single rule."""
        # Simplified rule evaluation
        rule_type = rule.get("type", "condition")
        
        if rule_type == "condition":
            condition = rule.get("condition", {})
            return self._evaluate_condition(condition, action, context)
        elif rule_type == "constraint":
            constraint = rule.get("constraint", {})
            return self._evaluate_constraint(constraint, action, context)
        
        return {"satisfied": True, "reason": "Unknown rule type"}
    
    def _evaluate_condition(self, condition: Dict[str, Any], action: Dict[str, Any],
                          context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a condition rule."""
        field = condition.get("field", "")
        operator = condition.get("operator", "equals")
        value = condition.get("value")
        
        # Get actual value from action or context
        actual_value = action.get(field, context.get(field))
        
        # Evaluate condition
        if operator == "equals":
            satisfied = actual_value == value
        elif operator == "not_equals":
            satisfied = actual_value != value
        elif operator == "greater_than":
            satisfied = actual_value > value
        elif operator == "less_than":
            satisfied = actual_value < value
        else:
            satisfied = True  # Unknown operator, assume satisfied
        
        return {
            "satisfied": satisfied,
            "reason": f"Field {field} {operator} {value}: {actual_value}"
        }
    
    def _evaluate_constraint(self, constraint: Dict[str, Any], action: Dict[str, Any],
                          context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a constraint rule."""
        constraint_type = constraint.get("type", "range")
        
        if constraint_type == "range":
            field = constraint.get("field", "")
            min_val = constraint.get("min")
            max_val = constraint.get("max")
            
            actual_value = action.get(field, context.get(field))
            
            if actual_value is None:
                return {"satisfied": False, "reason": f"Field {field} not found"}
            
            satisfied = min_val <= actual_value <= max_val
            return {
                "satisfied": satisfied,
                "reason": f"Field {field} in range [{min_val}, {max_val}]: {actual_value}"
            }
        
        return {"satisfied": True, "reason": "Unknown constraint type"}


class PolicyEngine:
    """Manages and executes governance policies."""
    
    def __init__(self):
        self.compliance_checker = ComplianceChecker()
        self.logger = logging.getLogger("haai.policy_engine")
        
        # Add default policies
        self._add_default_policies()
    
    def _add_default_policies(self) -> None:
        """Add default governance policies."""
        # Coherence threshold policy
        coherence_policy = Policy(
            policy_id="coherence_threshold",
            name="Coherence Threshold Policy",
            description="Ensures actions maintain minimum coherence",
            rules=[
                {
                    "type": "condition",
                    "condition": {
                        "field": "coherence_score",
                        "operator": "greater_than",
                        "value": 0.7
                    }
                }
            ],
            constraints={},
            priority=1,
            created_at=datetime.now()
        )
        
        # Resource usage policy
        resource_policy = Policy(
            policy_id="resource_limits",
            name="Resource Usage Policy",
            description="Limits resource consumption",
            rules=[
                {
                    "type": "constraint",
                    "constraint": {
                        "type": "range",
                        "field": "memory_usage_mb",
                        "min": 0,
                        "max": 1024
                    }
                }
            ],
            constraints={},
            priority=2,
            created_at=datetime.now()
        )
        
        self.compliance_checker.add_policy(coherence_policy)
        self.compliance_checker.add_policy(resource_policy)
    
    def evaluate_action(self, action: Dict[str, Any], 
                      context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate an action against all policies."""
        return self.compliance_checker.check_compliance(action, context)
    
    def add_policy(self, policy: Policy) -> None:
        """Add a new policy."""
        self.compliance_checker.add_policy(policy)
    
    def get_policies(self) -> List[Policy]:
        """Get all policies."""
        return list(self.compliance_checker.policies.values())


class CGLGovernance:
    """Main CGL governance system."""
    
    def __init__(self):
        self.policy_engine = PolicyEngine()
        self.compliance_checker = self.policy_engine.compliance_checker
        self.logger = logging.getLogger("haai.cgl_governance")
        self.is_initialized = False
    
    async def initialize(self) -> None:
        """Initialize the governance system."""
        if self.is_initialized:
            return
        
        self.logger.info("Initializing CGL Governance System")
        self.is_initialized = True
    
    def govern_action(self, action: Dict[str, Any], 
                   context: Dict[str, Any]) -> Dict[str, Any]:
        """Govern an action through policy evaluation."""
        if not self.is_initialized:
            return {
                "governed": False,
                "reason": "Governance system not initialized"
            }
        
        # Evaluate against policies
        compliance_result = self.policy_engine.evaluate_action(action, context)
        
        # Apply governance decision
        if compliance_result["compliant"]:
            result = {
                "governed": True,
                "approved": True,
                "compliance": compliance_result,
                "action": action
            }
        else:
            result = {
                "governed": True,
                "approved": False,
                "compliance": compliance_result,
                "violations": compliance_result["violations"],
                "action": None
            }
            
            self.logger.warning(f"Action rejected due to policy violations: {compliance_result['violations']}")
        
        return result
    
    def add_policy(self, policy: Policy) -> None:
        """Add a governance policy."""
        self.policy_engine.add_policy(policy)
    
    def get_governance_status(self) -> Dict[str, Any]:
        """Get governance system status."""
        policies = self.policy_engine.get_policies()
        
        return {
            "initialized": self.is_initialized,
            "total_policies": len(policies),
            "policy_types": list(set(p.policy_id.split("_")[0] for p in policies)),
            "policies": [p.to_dict() for p in policies]
        }
    
    async def shutdown(self) -> None:
        """Shutdown the governance system."""
        self.is_initialized = False
        self.logger.info("CGL Governance System shutdown")