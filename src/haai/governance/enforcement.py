"""
Enforcement Point Implementation

Provides multi-level enforcement across the HAAI architecture:
- Gateway-level enforcement for pre-execution checks
- Scheduler-level enforcement for resource management
- Runtime-level enforcement for live monitoring
- Output-level enforcement for result validation
"""

import logging
import asyncio
import hashlib
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Set
from datetime import datetime, timedelta
from enum import Enum
import uuid


class EnforcementLevel(Enum):
    """Enforcement levels in the system."""
    GATEWAY = "gateway"
    SCHEDULER = "scheduler"
    RUNTIME = "runtime"
    OUTPUT = "output"


class EnforcementAction(Enum):
    """Types of enforcement actions."""
    ALLOW = "allow"
    BLOCK = "block"
    MODIFY = "modify"
    DELAY = "delay"
    ESCALATE = "escalate"
    LOG = "log"
    QUARANTINE = "quarantine"


class EnforcementPriority(Enum):
    """Enforcement priority levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class EnforcementDecision:
    """Represents an enforcement decision."""
    decision_id: str
    enforcement_level: EnforcementLevel
    action: EnforcementAction
    priority: EnforcementPriority
    reason: str
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if decision is expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert decision to dictionary."""
        return {
            "decision_id": self.decision_id,
            "enforcement_level": self.enforcement_level.value,
            "action": self.action.value,
            "priority": self.priority.value,
            "reason": self.reason,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "metadata": self.metadata
        }


@dataclass
class EnforcementRule:
    """Represents an enforcement rule."""
    rule_id: str
    name: str
    description: str
    enforcement_level: EnforcementLevel
    conditions: List[Dict[str, Any]]
    actions: List[Dict[str, Any]]
    priority: EnforcementPriority = EnforcementPriority.MEDIUM
    enabled: bool = True
    cooldown_period: timedelta = field(default_factory=lambda: timedelta(seconds=0))
    last_triggered: Optional[datetime] = None
    
    def can_trigger(self) -> bool:
        """Check if rule can trigger (respecting cooldown)."""
        if self.cooldown_period.total_seconds() == 0:
            return True
        
        if self.last_triggered is None:
            return True
        
        return datetime.now() - self.last_triggered > self.cooldown_period
    
    def evaluate(self, context: Dict[str, Any]) -> Optional[EnforcementDecision]:
        """Evaluate rule against context."""
        if not self.enabled or not self.can_trigger():
            return None
        
        # Check all conditions
        for condition in self.conditions:
            if not self._evaluate_condition(condition, context):
                return None
        
        # Create enforcement decision
        action = EnforcementAction(self.actions[0].get("type", "allow"))
        priority = self.priority
        
        decision = EnforcementDecision(
            decision_id=f"dec_{uuid.uuid4().hex[:8]}",
            enforcement_level=self.enforcement_level,
            action=action,
            priority=priority,
            reason=self.name,
            context=context,
            metadata={"rule_id": self.rule_id, "actions": self.actions}
        )
        
        # Update last triggered
        self.last_triggered = datetime.now()
        
        return decision
    
    def _evaluate_condition(self, condition: Dict[str, Any], 
                           context: Dict[str, Any]) -> bool:
        """Evaluate a single condition."""
        condition_type = condition.get("type", "field")
        
        if condition_type == "field":
            field = condition.get("field", "")
            operator = condition.get("operator", "equals")
            expected_value = condition.get("value")
            
            actual_value = self._get_nested_value(context, field)
            
            return self._compare_values(actual_value, operator, expected_value)
        
        elif condition_type == "policy":
            policy_result = condition.get("policy_result", {})
            return policy_result.get("compliant", True) is False
        
        elif condition_type == "safety":
            safety_level = condition.get("safety_level", "warning")
            current_safety = context.get("safety_level", "safe")
            
            level_order = ["safe", "caution", "warning", "critical", "emergency"]
            return level_order.index(current_safety) >= level_order.index(safety_level)
        
        elif condition_type == "identity":
            required_role = condition.get("required_role")
            agent_roles = context.get("agent_roles", [])
            
            return required_role in agent_roles
        
        return True
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get nested value from dictionary using dot notation."""
        keys = path.split(".")
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current
    
    def _compare_values(self, actual: Any, operator: str, expected: Any) -> bool:
        """Compare values using operator."""
        if operator == "equals":
            return actual == expected
        elif operator == "not_equals":
            return actual != expected
        elif operator == "greater_than":
            return actual > expected
        elif operator == "less_than":
            return actual < expected
        elif operator == "greater_equal":
            return actual >= expected
        elif operator == "less_equal":
            return actual <= expected
        elif operator == "in":
            return actual in expected
        elif operator == "not_in":
            return actual not in expected
        elif operator == "exists":
            return actual is not None
        elif operator == "not_exists":
            return actual is None
        elif operator == "contains":
            return expected in str(actual)
        elif operator == "matches":
            import re
            return bool(re.match(str(expected), str(actual)))
        
        return False


class GatewayEnforcement:
    """Gateway-level enforcement for pre-execution checks."""
    
    def __init__(self):
        self.rules: Dict[str, EnforcementRule] = {}
        self.decision_cache: Dict[str, EnforcementDecision] = {}
        self.logger = logging.getLogger("haai.enforcement.gateway")
        self.cache_ttl = timedelta(minutes=5)
    
    def add_rule(self, rule: EnforcementRule) -> None:
        """Add a gateway enforcement rule."""
        if rule.enforcement_level != EnforcementLevel.GATEWAY:
            raise ValueError("Rule must be for gateway enforcement level")
        
        self.rules[rule.rule_id] = rule
        self.logger.info(f"Added gateway enforcement rule: {rule.rule_id}")
    
    async def enforce(self, request: Dict[str, Any]) -> EnforcementDecision:
        """Enforce gateway rules on a request."""
        context = {
            "request": request,
            "timestamp": datetime.now().isoformat(),
            "enforcement_level": "gateway"
        }
        
        # Evaluate all rules
        decisions = []
        for rule in self.rules.values():
            decision = rule.evaluate(context)
            if decision:
                decisions.append(decision)
        
        if not decisions:
            # Default allow if no rules match
            return EnforcementDecision(
                decision_id=f"dec_{uuid.uuid4().hex[:8]}",
                enforcement_level=EnforcementLevel.GATEWAY,
                action=EnforcementAction.ALLOW,
                priority=EnforcementPriority.LOW,
                reason="No matching rules - default allow",
                context=context
            )
        
        # Select highest priority decision
        highest_priority = max(decisions, key=lambda d: d.priority.value)
        
        # Cache decision
        cache_key = self._generate_cache_key(request)
        self.decision_cache[cache_key] = highest_priority
        
        self.logger.info(f"Gateway enforcement decision: {highest_priority.action.value}")
        
        return highest_priority
    
    def _generate_cache_key(self, request: Dict[str, Any]) -> str:
        """Generate cache key for request."""
        request_str = json.dumps(request, sort_keys=True)
        return hashlib.md5(request_str.encode()).hexdigest()


class SchedulerEnforcement:
    """Scheduler-level enforcement for resource management."""
    
    def __init__(self):
        self.rules: Dict[str, EnforcementRule] = {}
        self.resource_limits: Dict[str, Dict[str, Any]] = {}
        self.active_allocations: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger("haai.enforcement.scheduler")
    
    def add_rule(self, rule: EnforcementRule) -> None:
        """Add a scheduler enforcement rule."""
        if rule.enforcement_level != EnforcementLevel.SCHEDULER:
            raise ValueError("Rule must be for scheduler enforcement level")
        
        self.rules[rule.rule_id] = rule
        self.logger.info(f"Added scheduler enforcement rule: {rule.rule_id}")
    
    def set_resource_limit(self, resource_type: str, limit: Dict[str, Any]) -> None:
        """Set resource limits."""
        self.resource_limits[resource_type] = limit
        self.logger.info(f"Set resource limit for {resource_type}: {limit}")
    
    async def enforce_allocation(self, allocation_request: Dict[str, Any]) -> EnforcementDecision:
        """Enforce scheduler rules on resource allocation."""
        context = {
            "allocation_request": allocation_request,
            "timestamp": datetime.now().isoformat(),
            "enforcement_level": "scheduler",
            "active_allocations": self.active_allocations
        }
        
        # Check resource limits
        resource_type = allocation_request.get("resource_type")
        requested_amount = allocation_request.get("amount", 0)
        
        if resource_type in self.resource_limits:
            limit = self.resource_limits[resource_type]
            current_usage = self._get_current_usage(resource_type)
            
            if current_usage + requested_amount > limit.get("max", float("inf")):
                return EnforcementDecision(
                    decision_id=f"dec_{uuid.uuid4().hex[:8]}",
                    enforcement_level=EnforcementLevel.SCHEDULER,
                    action=EnforcementAction.BLOCK,
                    priority=EnforcementPriority.HIGH,
                    reason=f"Resource limit exceeded for {resource_type}",
                    context=context,
                    metadata={
                        "resource_type": resource_type,
                        "requested": requested_amount,
                        "current_usage": current_usage,
                        "limit": limit.get("max")
                    }
                )
        
        # Evaluate all rules
        decisions = []
        for rule in self.rules.values():
            decision = rule.evaluate(context)
            if decision:
                decisions.append(decision)
        
        if not decisions:
            # Allow allocation
            allocation_id = allocation_request.get("allocation_id", f"alloc_{uuid.uuid4().hex[:8]}")
            self.active_allocations[allocation_id] = {
                "resource_type": resource_type,
                "amount": requested_amount,
                "allocated_at": datetime.now(),
                "request": allocation_request
            }
            
            return EnforcementDecision(
                decision_id=f"dec_{uuid.uuid4().hex[:8]}",
                enforcement_level=EnforcementLevel.SCHEDULER,
                action=EnforcementAction.ALLOW,
                priority=EnforcementPriority.MEDIUM,
                reason="Resource allocation approved",
                context=context
            )
        
        # Return highest priority decision
        highest_priority = max(decisions, key=lambda d: d.priority.value)
        
        self.logger.info(f"Scheduler enforcement decision: {highest_priority.action.value}")
        
        return highest_priority
    
    def release_allocation(self, allocation_id: str) -> None:
        """Release a resource allocation."""
        if allocation_id in self.active_allocations:
            del self.active_allocations[allocation_id]
            self.logger.info(f"Released allocation: {allocation_id}")
    
    def _get_current_usage(self, resource_type: str) -> float:
        """Get current resource usage."""
        usage = 0.0
        for allocation in self.active_allocations.values():
            if allocation["resource_type"] == resource_type:
                usage += allocation["amount"]
        return usage


class RuntimeEnforcement:
    """Runtime-level enforcement for live monitoring."""
    
    def __init__(self):
        self.rules: Dict[str, EnforcementRule] = {}
        self.active_operations: Dict[str, Dict[str, Any]] = {}
        self.monitoring_active = False
        self.logger = logging.getLogger("haai.enforcement.runtime")
    
    def add_rule(self, rule: EnforcementRule) -> None:
        """Add a runtime enforcement rule."""
        if rule.enforcement_level != EnforcementLevel.RUNTIME:
            raise ValueError("Rule must be for runtime enforcement level")
        
        self.rules[rule.rule_id] = rule
        self.logger.info(f"Added runtime enforcement rule: {rule.rule_id}")
    
    async def start_operation(self, operation: Dict[str, Any]) -> EnforcementDecision:
        """Start monitoring an operation."""
        operation_id = operation.get("operation_id", f"op_{uuid.uuid4().hex[:8]}")
        
        self.active_operations[operation_id] = {
            "operation": operation,
            "started_at": datetime.now(),
            "status": "running",
            "metrics": {},
            "violations": []
        }
        
        context = {
            "operation": operation,
            "operation_id": operation_id,
            "timestamp": datetime.now().isoformat(),
            "enforcement_level": "runtime",
            "event_type": "operation_start"
        }
        
        # Evaluate rules for operation start
        decisions = []
        for rule in self.rules.values():
            decision = rule.evaluate(context)
            if decision:
                decisions.append(decision)
        
        if not decisions:
            return EnforcementDecision(
                decision_id=f"dec_{uuid.uuid4().hex[:8]}",
                enforcement_level=EnforcementLevel.RUNTIME,
                action=EnforcementAction.ALLOW,
                priority=EnforcementPriority.MEDIUM,
                reason="Operation started",
                context=context
            )
        
        highest_priority = max(decisions, key=lambda d: d.priority.value)
        
        if highest_priority.action == EnforcementAction.BLOCK:
            self.active_operations[operation_id]["status"] = "blocked"
        
        return highest_priority
    
    async def update_operation_metrics(self, operation_id: str, 
                                       metrics: Dict[str, Any]) -> List[EnforcementDecision]:
        """Update operation metrics and enforce rules."""
        if operation_id not in self.active_operations:
            return []
        
        operation = self.active_operations[operation_id]
        operation["metrics"].update(metrics)
        
        context = {
            "operation_id": operation_id,
            "operation": operation["operation"],
            "metrics": operation["metrics"],
            "timestamp": datetime.now().isoformat(),
            "enforcement_level": "runtime",
            "event_type": "metrics_update"
        }
        
        # Evaluate all rules
        decisions = []
        for rule in self.rules.values():
            decision = rule.evaluate(context)
            if decision:
                decisions.append(decision)
                operation["violations"].append({
                    "rule_id": rule.rule_id,
                    "decision": decision.to_dict(),
                    "timestamp": datetime.now().isoformat()
                })
        
        return decisions
    
    async def stop_operation(self, operation_id: str) -> EnforcementDecision:
        """Stop monitoring an operation."""
        if operation_id not in self.active_operations:
            return EnforcementDecision(
                decision_id=f"dec_{uuid.uuid4().hex[:8]}",
                enforcement_level=EnforcementLevel.RUNTIME,
                action=EnforcementAction.ALLOW,
                priority=EnforcementPriority.LOW,
                reason="Operation not found",
                context={"operation_id": operation_id}
            )
        
        operation = self.active_operations[operation_id]
        operation["status"] = "completed"
        operation["completed_at"] = datetime.now()
        
        context = {
            "operation_id": operation_id,
            "operation": operation["operation"],
            "duration": (operation["completed_at"] - operation["started_at"]).total_seconds(),
            "violations": len(operation["violations"]),
            "timestamp": datetime.now().isoformat(),
            "enforcement_level": "runtime",
            "event_type": "operation_stop"
        }
        
        # Clean up old operations (keep last 100)
        if len(self.active_operations) > 100:
            oldest_ops = sorted(
                self.active_operations.items(),
                key=lambda x: x[1]["started_at"]
            )[:50]
            
            for op_id, _ in oldest_ops:
                del self.active_operations[op_id]
        
        return EnforcementDecision(
            decision_id=f"dec_{uuid.uuid4().hex[:8]}",
            enforcement_level=EnforcementLevel.RUNTIME,
            action=EnforcementAction.ALLOW,
            priority=EnforcementPriority.MEDIUM,
            reason="Operation completed",
            context=context
        )


class OutputEnforcement:
    """Output-level enforcement for result validation."""
    
    def __init__(self):
        self.rules: Dict[str, EnforcementRule] = {}
        self.validation_cache: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger("haai.enforcement.output")
    
    def add_rule(self, rule: EnforcementRule) -> None:
        """Add an output enforcement rule."""
        if rule.enforcement_level != EnforcementLevel.OUTPUT:
            raise ValueError("Rule must be for output enforcement level")
        
        self.rules[rule.rule_id] = rule
        self.logger.info(f"Added output enforcement rule: {rule.rule_id}")
    
    async def validate_output(self, output: Dict[str, Any], 
                            context: Dict[str, Any]) -> EnforcementDecision:
        """Validate output against enforcement rules."""
        validation_context = {
            "output": output,
            "context": context,
            "timestamp": datetime.now().isoformat(),
            "enforcement_level": "output"
        }
        
        # Evaluate all rules
        decisions = []
        for rule in self.rules.values():
            decision = rule.evaluate(validation_context)
            if decision:
                decisions.append(decision)
        
        if not decisions:
            return EnforcementDecision(
                decision_id=f"dec_{uuid.uuid4().hex[:8]}",
                enforcement_level=EnforcementLevel.OUTPUT,
                action=EnforcementAction.ALLOW,
                priority=EnforcementPriority.MEDIUM,
                reason="Output validation passed",
                context=validation_context
            )
        
        # Return highest priority decision
        highest_priority = max(decisions, key=lambda d: d.priority.value)
        
        self.logger.info(f"Output enforcement decision: {highest_priority.action.value}")
        
        return highest_priority


class EnforcementCoordinator:
    """Coordinates enforcement across all levels."""
    
    def __init__(self):
        self.gateway = GatewayEnforcement()
        self.scheduler = SchedulerEnforcement()
        self.runtime = RuntimeEnforcement()
        self.output = OutputEnforcement()
        
        self.escalation_handlers: Dict[str, Callable] = {}
        self.enforcement_history: List[Dict[str, Any]] = []
        self.logger = logging.getLogger("haai.enforcement.coordinator")
        
        # Initialize default rules
        self._initialize_default_rules()
    
    def _initialize_default_rules(self) -> None:
        """Initialize default enforcement rules."""
        # Gateway rules
        gateway_rule = EnforcementRule(
            rule_id="gateway_policy_check",
            name="Policy Compliance Check",
            description="Check policy compliance at gateway",
            enforcement_level=EnforcementLevel.GATEWAY,
            conditions=[
                {
                    "type": "policy",
                    "policy_result": {"compliant": False}
                }
            ],
            actions=[
                {"type": "block"},
                {"type": "escalate", "severity": "high"}
            ],
            priority=EnforcementPriority.HIGH
        )
        
        # Scheduler rules
        scheduler_rule = EnforcementRule(
            rule_id="scheduler_resource_check",
            name="Resource Limit Check",
            description="Check resource availability",
            enforcement_level=EnforcementLevel.SCHEDULER,
            conditions=[
                {
                    "type": "field",
                    "field": "allocation_request.amount",
                    "operator": "greater_than",
                    "value": 1000
                }
            ],
            actions=[
                {"type": "delay", "duration": 5},
                {"type": "escalate", "severity": "medium"}
            ],
            priority=EnforcementPriority.MEDIUM
        )
        
        # Runtime rules
        runtime_rule = EnforcementRule(
            rule_id="runtime_safety_check",
            name="Runtime Safety Check",
            description="Monitor safety during execution",
            enforcement_level=EnforcementLevel.RUNTIME,
            conditions=[
                {
                    "type": "safety",
                    "safety_level": "critical"
                }
            ],
            actions=[
                {"type": "modify", "action": "reduce_complexity"},
                {"type": "escalate", "severity": "critical"}
            ],
            priority=EnforcementPriority.CRITICAL,
            cooldown_period=timedelta(seconds=30)
        )
        
        # Output rules
        output_rule = EnforcementRule(
            rule_id="output_validation",
            name="Output Validation",
            description="Validate output quality",
            enforcement_level=EnforcementLevel.OUTPUT,
            conditions=[
                {
                    "type": "field",
                    "field": "output.coherence_score",
                    "operator": "less_than",
                    "value": 0.7
                }
            ],
            actions=[
                {"type": "quarantine"},
                {"type": "escalate", "severity": "medium"}
            ],
            priority=EnforcementPriority.HIGH
        )
        
        self.gateway.add_rule(gateway_rule)
        self.scheduler.add_rule(scheduler_rule)
        self.runtime.add_rule(runtime_rule)
        self.output.add_rule(output_rule)
    
    async def enforce_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Enforce a request through all levels."""
        enforcement_log = {
            "request_id": request.get("request_id", f"req_{uuid.uuid4().hex[:8]}"),
            "timestamp": datetime.now().isoformat(),
            "levels": {}
        }
        
        try:
            # Gateway enforcement
            gateway_decision = await self.gateway.enforce(request)
            enforcement_log["levels"]["gateway"] = gateway_decision.to_dict()
            
            if gateway_decision.action == EnforcementAction.BLOCK:
                await self._handle_escalation(gateway_decision)
                return {
                    "enforced": True,
                    "allowed": False,
                    "blocked_at": "gateway",
                    "decision": gateway_decision.to_dict(),
                    "log": enforcement_log
                }
            
            # Scheduler enforcement (if resource allocation needed)
            if "resource_request" in request:
                scheduler_decision = await self.scheduler.enforce_allocation(
                    request["resource_request"]
                )
                enforcement_log["levels"]["scheduler"] = scheduler_decision.to_dict()
                
                if scheduler_decision.action == EnforcementAction.BLOCK:
                    await self._handle_escalation(scheduler_decision)
                    return {
                        "enforced": True,
                        "allowed": False,
                        "blocked_at": "scheduler",
                        "decision": scheduler_decision.to_dict(),
                        "log": enforcement_log
                    }
            
            # Runtime enforcement
            if "operation" in request:
                runtime_decision = await self.runtime.start_operation(request["operation"])
                enforcement_log["levels"]["runtime"] = runtime_decision.to_dict()
                
                if runtime_decision.action == EnforcementAction.BLOCK:
                    await self._handle_escalation(runtime_decision)
                    return {
                        "enforced": True,
                        "allowed": False,
                        "blocked_at": "runtime",
                        "decision": runtime_decision.to_dict(),
                        "log": enforcement_log
                    }
            
            # Success
            enforcement_log["enforcement_successful"] = True
            self.enforcement_history.append(enforcement_log)
            
            return {
                "enforced": True,
                "allowed": True,
                "decisions": enforcement_log["levels"],
                "log": enforcement_log
            }
            
        except Exception as e:
            self.logger.error(f"Enforcement error: {e}")
            enforcement_log["error"] = str(e)
            
            return {
                "enforced": False,
                "error": str(e),
                "log": enforcement_log
            }
    
    async def validate_result(self, result: Dict[str, Any], 
                            context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a result through output enforcement."""
        try:
            output_decision = await self.output.validate_output(result, context)
            
            validation_log = {
                "result_id": result.get("result_id", f"res_{uuid.uuid4().hex[:8]}"),
                "timestamp": datetime.now().isoformat(),
                "output_decision": output_decision.to_dict()
            }
            
            if output_decision.action == EnforcementAction.BLOCK or \
               output_decision.action == EnforcementAction.QUARANTINE:
                await self._handle_escalation(output_decision)
            
            return {
                "validated": True,
                "approved": output_decision.action == EnforcementAction.ALLOW,
                "decision": output_decision.to_dict(),
                "log": validation_log
            }
            
        except Exception as e:
            self.logger.error(f"Output validation error: {e}")
            return {
                "validated": False,
                "error": str(e)
            }
    
    async def _handle_escalation(self, decision: EnforcementDecision) -> None:
        """Handle enforcement escalation."""
        escalation_data = {
            "decision": decision.to_dict(),
            "timestamp": datetime.now().isoformat()
        }
        
        # Log escalation
        self.logger.warning(f"Enforcement escalation: {decision.action.value} - {decision.reason}")
        
        # In a real implementation, this would notify appropriate parties
        # For now, just log the escalation
        print(f"🚨 ENFORCEMENT ESCALATION: {decision.action.value.upper()}")
        print(f"   Reason: {decision.reason}")
        print(f"   Level: {decision.enforcement_level.value}")
        print(f"   Priority: {decision.priority.name}")
    
    def get_enforcement_status(self) -> Dict[str, Any]:
        """Get overall enforcement status."""
        return {
            "gateway_rules": len(self.gateway.rules),
            "scheduler_rules": len(self.scheduler.rules),
            "runtime_rules": len(self.runtime.rules),
            "output_rules": len(self.output.rules),
            "active_operations": len(self.runtime.active_operations),
            "resource_allocations": len(self.scheduler.active_allocations),
            "enforcement_history_size": len(self.enforcement_history)
        }