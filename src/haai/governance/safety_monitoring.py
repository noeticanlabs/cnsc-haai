"""
Safety Monitoring and Response System

Provides real-time safety monitoring across all HAAI abstraction levels,
automated safety response mechanisms, incident detection and classification,
and emergency override capabilities.
"""

import logging
import asyncio
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Set
from datetime import datetime, timedelta
from enum import Enum
import statistics


class SafetyLevel(Enum):
    """Safety levels for monitoring."""
    SAFE = "safe"
    CAUTION = "caution"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class IncidentType(Enum):
    """Types of safety incidents."""
    COHERENCE_DEGRADATION = "coherence_degradation"
    ABSTRACTION_FAILURE = "abstraction_failure"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    POLICY_VIOLATION = "policy_violation"
    SYSTEM_ANOMALY = "system_anomaly"
    SECURITY_BREACH = "security_breach"
    SAFETY_BREACH = "safety_breach"


class ResponseAction(Enum):
    """Types of safety response actions."""
    LOG = "log"
    ALERT = "alert"
    THROTTLE = "throttle"
    ISOLATE = "isolate"
    ROLLBACK = "rollback"
    EMERGENCY_STOP = "emergency_stop"
    SAFE_MODE = "safe_mode"
    OVERRIDE = "override"


@dataclass
class SafetyMetric:
    """Represents a safety metric."""
    metric_id: str
    name: str
    description: str
    current_value: float
    threshold_caution: float
    threshold_warning: float
    threshold_critical: float
    threshold_emergency: float
    unit: str = ""
    trend_window: int = 10
    history: List[float] = field(default_factory=list)
    
    def update_value(self, value: float) -> SafetyLevel:
        """Update metric value and return safety level."""
        self.history.append(value)
        
        # Keep only recent history
        if len(self.history) > self.trend_window:
            self.history = self.history[-self.trend_window:]
        
        self.current_value = value
        
        # Determine safety level
        if value >= self.threshold_emergency:
            return SafetyLevel.EMERGENCY
        elif value >= self.threshold_critical:
            return SafetyLevel.CRITICAL
        elif value >= self.threshold_warning:
            return SafetyLevel.WARNING
        elif value >= self.threshold_caution:
            return SafetyLevel.CAUTION
        else:
            return SafetyLevel.SAFE
    
    def get_trend(self) -> str:
        """Get trend direction."""
        if len(self.history) < 3:
            return "stable"
        
        recent = self.history[-3:]
        if recent[-1] > recent[-2] > recent[-3]:
            return "increasing"
        elif recent[-1] < recent[-2] < recent[-3]:
            return "decreasing"
        else:
            return "stable"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metric to dictionary."""
        return {
            "metric_id": self.metric_id,
            "name": self.name,
            "description": self.description,
            "current_value": self.current_value,
            "threshold_caution": self.threshold_caution,
            "threshold_warning": self.threshold_warning,
            "threshold_critical": self.threshold_critical,
            "threshold_emergency": self.threshold_emergency,
            "unit": self.unit,
            "trend": self.get_trend(),
            "history_count": len(self.history)
        }


@dataclass
class SafetyIncident:
    """Represents a safety incident."""
    incident_id: str
    incident_type: IncidentType
    severity: SafetyLevel
    title: str
    description: str
    detected_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    context: Dict[str, Any] = field(default_factory=dict)
    metrics_snapshot: Dict[str, float] = field(default_factory=dict)
    response_actions: List[Dict[str, Any]] = field(default_factory=list)
    resolved: bool = False
    resolution_notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert incident to dictionary."""
        return {
            "incident_id": self.incident_id,
            "incident_type": self.incident_type.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "detected_at": self.detected_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "context": self.context,
            "metrics_snapshot": self.metrics_snapshot,
            "response_actions": self.response_actions,
            "resolved": self.resolved,
            "resolution_notes": self.resolution_notes
        }


@dataclass
class SafetyRule:
    """Represents a safety monitoring rule."""
    rule_id: str
    name: str
    description: str
    incident_type: IncidentType
    conditions: List[Dict[str, Any]]
    response_actions: List[Dict[str, Any]]
    enabled: bool = True
    priority: int = 1
    
    def evaluate(self, metrics: Dict[str, SafetyMetric], 
                context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Evaluate safety rule."""
        if not self.enabled:
            return None
        
        # Check all conditions
        for condition in self.conditions:
            if not self._evaluate_condition(condition, metrics, context):
                return None
        
        return {
            "rule_id": self.rule_id,
            "incident_type": self.incident_type,
            "response_actions": self.response_actions,
            "severity": self._calculate_severity(metrics, context)
        }
    
    def _evaluate_condition(self, condition: Dict[str, Any],
                           metrics: Dict[str, SafetyMetric],
                           context: Dict[str, Any]) -> bool:
        """Evaluate a single condition."""
        condition_type = condition.get("type", "metric")
        
        if condition_type == "metric":
            metric_id = condition.get("metric_id")
            operator = condition.get("operator", ">")
            threshold = condition.get("threshold")
            
            if metric_id not in metrics:
                return False
            
            metric = metrics[metric_id]
            value = metric.current_value
            
            if operator == ">":
                return value > threshold
            elif operator == ">=":
                return value >= threshold
            elif operator == "<":
                return value < threshold
            elif operator == "<=":
                return value <= threshold
            elif operator == "==":
                return value == threshold
            elif operator == "!=":
                return value != threshold
        
        elif condition_type == "context":
            field = condition.get("field")
            operator = condition.get("operator", "==")
            expected_value = condition.get("value")
            
            actual_value = context.get(field)
            
            if operator == "==":
                return actual_value == expected_value
            elif operator == "!=":
                return actual_value != expected_value
            elif operator == "in":
                return actual_value in expected_value
            elif operator == "not_in":
                return actual_value not in expected_value
        
        return False
    
    def _calculate_severity(self, metrics: Dict[str, SafetyMetric],
                           context: Dict[str, Any]) -> SafetyLevel:
        """Calculate incident severity."""
        # Default to warning
        max_severity = SafetyLevel.WARNING
        
        for condition in self.conditions:
            if condition.get("type") == "metric":
                metric_id = condition.get("metric_id")
                if metric_id in metrics:
                    metric = metrics[metric_id]
                    current_level = metric.update_value(metric.current_value)
                    
                    # Use the highest severity level
                    severity_order = [
                        SafetyLevel.SAFE,
                        SafetyLevel.CAUTION,
                        SafetyLevel.WARNING,
                        SafetyLevel.CRITICAL,
                        SafetyLevel.EMERGENCY
                    ]
                    
                    if severity_order.index(current_level) > severity_order.index(max_severity):
                        max_severity = current_level
        
        return max_severity


class EmergencyOverride:
    """Manages emergency override capabilities."""
    
    def __init__(self):
        self.active_overrides: Dict[str, Dict[str, Any]] = {}
        self.override_history: List[Dict[str, Any]] = []
        self.logger = logging.getLogger("haai.emergency_override")
    
    def request_override(self, request_id: str, reason: str, 
                        requested_by: str, duration_minutes: int = 30,
                        scope: List[str] = None) -> Dict[str, Any]:
        """Request an emergency override."""
        override = {
            "request_id": request_id,
            "reason": reason,
            "requested_by": requested_by,
            "requested_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(minutes=duration_minutes),
            "scope": scope or ["all"],
            "approved": False,
            "approved_by": None,
            "approved_at": None,
            "active": False
        }
        
        self.active_overrides[request_id] = override
        
        self.logger.info(f"Emergency override requested: {request_id}")
        
        return {
            "request_id": request_id,
            "status": "pending_approval",
            "expires_at": override["expires_at"].isoformat()
        }
    
    def approve_override(self, request_id: str, approved_by: str) -> Dict[str, Any]:
        """Approve an emergency override."""
        if request_id not in self.active_overrides:
            raise ValueError(f"Override request {request_id} not found")
        
        override = self.active_overrides[request_id]
        override["approved"] = True
        override["approved_by"] = approved_by
        override["approved_at"] = datetime.now()
        override["active"] = True
        
        self.logger.warning(f"Emergency override activated: {request_id} by {approved_by}")
        
        # Add to history
        self.override_history.append(override.copy())
        
        return {
            "request_id": request_id,
            "status": "active",
            "approved_by": approved_by,
            "expires_at": override["expires_at"].isoformat()
        }
    
    def is_override_active(self, scope: str = "all") -> bool:
        """Check if there's an active override for the given scope."""
        for override in self.active_overrides.values():
            if not override["active"]:
                continue
            
            if override["expires_at"] < datetime.now():
                override["active"] = False
                continue
            
            if scope in override["scope"] or "all" in override["scope"]:
                return True
        
        return False
    
    def deactivate_override(self, request_id: str, deactivated_by: str) -> Dict[str, Any]:
        """Deactivate an emergency override."""
        if request_id not in self.active_overrides:
            raise ValueError(f"Override request {request_id} not found")
        
        override = self.active_overrides[request_id]
        override["active"] = False
        override["deactivated_by"] = deactivated_by
        override["deactivated_at"] = datetime.now()
        
        self.logger.info(f"Emergency override deactivated: {request_id} by {deactivated_by}")
        
        return {
            "request_id": request_id,
            "status": "deactivated",
            "deactivated_by": deactivated_by
        }
    
    def get_active_overrides(self) -> List[Dict[str, Any]]:
        """Get all active overrides."""
        active = []
        for override in self.active_overrides.values():
            if override["active"] and override["expires_at"] > datetime.now():
                active.append(override)
        return active


class SafetyMonitoringSystem:
    """Main safety monitoring and response system."""
    
    def __init__(self):
        self.metrics: Dict[str, SafetyMetric] = {}
        self.rules: Dict[str, SafetyRule] = {}
        self.incidents: List[SafetyIncident] = []
        self.emergency_override = EmergencyOverride()
        
        self.response_handlers: Dict[ResponseAction, Callable] = {}
        self.monitoring_active = False
        self.monitoring_interval = 1.0  # seconds
        
        self.logger = logging.getLogger("haai.safety_monitoring")
        
        # Initialize default metrics and rules
        self._initialize_default_metrics()
        self._initialize_default_rules()
        self._initialize_response_handlers()
    
    def _initialize_default_metrics(self) -> None:
        """Initialize default safety metrics."""
        # Coherence Score
        coherence_metric = SafetyMetric(
            metric_id="coherence_score",
            name="Coherence Score",
            description="Overall system coherence",
            current_value=1.0,
            threshold_caution=0.8,
            threshold_warning=0.7,
            threshold_critical=0.6,
            threshold_emergency=0.5,
            unit="score"
        )
        
        # Resource Usage
        resource_metric = SafetyMetric(
            metric_id="resource_usage",
            name="Resource Usage",
            description="System resource utilization",
            current_value=0.3,
            threshold_caution=0.6,
            threshold_warning=0.75,
            threshold_critical=0.85,
            threshold_emergency=0.95,
            unit="percentage"
        )
        
        # Abstraction Quality
        abstraction_metric = SafetyMetric(
            metric_id="abstraction_quality",
            name="Abstraction Quality",
            description="Quality of abstraction operations",
            current_value=0.9,
            threshold_caution=0.8,
            threshold_warning=0.7,
            threshold_critical=0.6,
            threshold_emergency=0.5,
            unit="score"
        )
        
        # Response Time
        response_time_metric = SafetyMetric(
            metric_id="response_time",
            name="Response Time",
            description="System response time",
            current_value=100.0,
            threshold_caution=500.0,
            threshold_warning=1000.0,
            threshold_critical=2000.0,
            threshold_emergency=5000.0,
            unit="ms"
        )
        
        # Error Rate
        error_rate_metric = SafetyMetric(
            metric_id="error_rate",
            name="Error Rate",
            description="System error rate",
            current_value=0.01,
            threshold_caution=0.05,
            threshold_warning=0.1,
            threshold_critical=0.2,
            threshold_emergency=0.3,
            unit="percentage"
        )
        
        for metric in [coherence_metric, resource_metric, abstraction_metric,
                      response_time_metric, error_rate_metric]:
            self.metrics[metric.metric_id] = metric
    
    def _initialize_default_rules(self) -> None:
        """Initialize default safety rules."""
        # Coherence Degradation Rule
        coherence_rule = SafetyRule(
            rule_id="coherence_degradation",
            name="Coherence Degradation Detection",
            description="Detects when coherence drops below safe levels",
            incident_type=IncidentType.COHERENCE_DEGRADATION,
            conditions=[
                {
                    "type": "metric",
                    "metric_id": "coherence_score",
                    "operator": "<",
                    "threshold": 0.7
                }
            ],
            response_actions=[
                {"type": "alert", "message": "Coherence degradation detected"},
                {"type": "throttle", "severity": "medium"}
            ],
            priority=1
        )
        
        # Resource Exhaustion Rule
        resource_rule = SafetyRule(
            rule_id="resource_exhaustion",
            name="Resource Exhaustion Detection",
            description="Detects when resource usage is critical",
            incident_type=IncidentType.RESOURCE_EXHAUSTION,
            conditions=[
                {
                    "type": "metric",
                    "metric_id": "resource_usage",
                    "operator": ">",
                    "threshold": 0.85
                }
            ],
            response_actions=[
                {"type": "alert", "message": "Resource usage critical"},
                {"type": "throttle", "severity": "high"},
                {"type": "log", "level": "critical"}
            ],
            priority=2
        )
        
        # Abstraction Failure Rule
        abstraction_rule = SafetyRule(
            rule_id="abstraction_failure",
            name="Abstraction Failure Detection",
            description="Detects abstraction quality degradation",
            incident_type=IncidentType.ABSTRACTION_FAILURE,
            conditions=[
                {
                    "type": "metric",
                    "metric_id": "abstraction_quality",
                    "operator": "<",
                    "threshold": 0.6
                }
            ],
            response_actions=[
                {"type": "alert", "message": "Abstraction quality degraded"},
                {"type": "isolate", "component": "abstraction_engine"}
            ],
            priority=1
        )
        
        # System Anomaly Rule
        anomaly_rule = SafetyRule(
            rule_id="system_anomaly",
            name="System Anomaly Detection",
            description="Detects general system anomalies",
            incident_type=IncidentType.SYSTEM_ANOMALY,
            conditions=[
                {
                    "type": "metric",
                    "metric_id": "error_rate",
                    "operator": ">",
                    "threshold": 0.1
                }
            ],
            response_actions=[
                {"type": "alert", "message": "System anomaly detected"},
                {"type": "log", "level": "warning"}
            ],
            priority=3
        )
        
        for rule in [coherence_rule, resource_rule, abstraction_rule, anomaly_rule]:
            self.rules[rule.rule_id] = rule
    
    def _initialize_response_handlers(self) -> None:
        """Initialize response action handlers."""
        self.response_handlers[ResponseAction.LOG] = self._handle_log_action
        self.response_handlers[ResponseAction.ALERT] = self._handle_alert_action
        self.response_handlers[ResponseAction.THROTTLE] = self._handle_throttle_action
        self.response_handlers[ResponseAction.ISOLATE] = self._handle_isolate_action
        self.response_handlers[ResponseAction.ROLLBACK] = self._handle_rollback_action
        self.response_handlers[ResponseAction.EMERGENCY_STOP] = self._handle_emergency_stop
        self.response_handlers[ResponseAction.SAFE_MODE] = self._handle_safe_mode
        self.response_handlers[ResponseAction.OVERRIDE] = self._handle_override_action
    
    async def start_monitoring(self) -> None:
        """Start safety monitoring."""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.logger.info("Safety monitoring started")
        
        while self.monitoring_active:
            try:
                await self._monitoring_cycle()
                await asyncio.sleep(self.monitoring_interval)
            except Exception as e:
                self.logger.error(f"Error in monitoring cycle: {e}")
                await asyncio.sleep(1.0)
    
    async def stop_monitoring(self) -> None:
        """Stop safety monitoring."""
        self.monitoring_active = False
        self.logger.info("Safety monitoring stopped")
    
    async def _monitoring_cycle(self) -> None:
        """Execute one monitoring cycle."""
        # Evaluate all safety rules
        for rule in self.rules.values():
            rule_result = rule.evaluate(self.metrics, {})
            
            if rule_result:
                await self._handle_rule_violation(rule, rule_result)
        
        # Check for expired overrides
        self._cleanup_expired_overrides()
    
    async def _handle_rule_violation(self, rule: SafetyRule, 
                                   rule_result: Dict[str, Any]) -> None:
        """Handle a safety rule violation."""
        # Create incident
        incident = SafetyIncident(
            incident_id=f"inc_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{rule.rule_id}",
            incident_type=rule_result["incident_type"],
            severity=rule_result["severity"],
            title=f"Safety Rule Violation: {rule.name}",
            description=f"Rule '{rule.name}' was triggered",
            context={"rule_id": rule.rule_id, "rule_result": rule_result},
            metrics_snapshot={mid: m.current_value for mid, m in self.metrics.items()}
        )
        
        self.incidents.append(incident)
        
        self.logger.warning(f"Safety incident detected: {incident.incident_id}")
        
        # Execute response actions
        for action in rule_result["response_actions"]:
            await self._execute_response_action(action, incident)
    
    async def _execute_response_action(self, action: Dict[str, Any], 
                                      incident: SafetyIncident) -> None:
        """Execute a safety response action."""
        action_type = ResponseAction(action.get("type", "log"))
        
        if action_type in self.response_handlers:
            try:
                await self.response_handlers[action_type](action, incident)
                
                # Record action in incident
                incident.response_actions.append({
                    "action": action,
                    "executed_at": datetime.now().isoformat(),
                    "success": True
                })
                
            except Exception as e:
                self.logger.error(f"Failed to execute action {action_type}: {e}")
                
                incident.response_actions.append({
                    "action": action,
                    "executed_at": datetime.now().isoformat(),
                    "success": False,
                    "error": str(e)
                })
    
    async def _handle_log_action(self, action: Dict[str, Any], 
                                incident: SafetyIncident) -> None:
        """Handle log response action."""
        level = action.get("level", "info")
        message = action.get("message", f"Safety incident: {incident.incident_id}")
        
        if level == "debug":
            self.logger.debug(message)
        elif level == "info":
            self.logger.info(message)
        elif level == "warning":
            self.logger.warning(message)
        elif level == "error":
            self.logger.error(message)
        elif level == "critical":
            self.logger.critical(message)
    
    async def _handle_alert_action(self, action: Dict[str, Any], 
                                 incident: SafetyIncident) -> None:
        """Handle alert response action."""
        message = action.get("message", f"Safety alert: {incident.title}")
        
        # Log alert
        self.logger.warning(f"ALERT: {message}")
        
        # In a real implementation, this would send notifications
        # For now, just log the alert
        print(f"🚨 SAFETY ALERT: {message}")
    
    async def _handle_throttle_action(self, action: Dict[str, Any], 
                                    incident: SafetyIncident) -> None:
        """Handle throttle response action."""
        severity = action.get("severity", "medium")
        
        # Log throttling
        self.logger.warning(f"Throttling system operations (severity: {severity})")
        
        # In a real implementation, this would interface with the system
        # to reduce operation rates or resource usage
    
    async def _handle_isolate_action(self, action: Dict[str, Any], 
                                    incident: SafetyIncident) -> None:
        """Handle isolate response action."""
        component = action.get("component", "unknown")
        
        self.logger.critical(f"Isolating component: {component}")
        
        # In a real implementation, this would isolate the component
        # to prevent further issues
    
    async def _handle_rollback_action(self, action: Dict[str, Any], 
                                     incident: SafetyIncident) -> None:
        """Handle rollback response action."""
        target = action.get("target", "last_state")
        
        self.logger.warning(f"Rolling back to: {target}")
        
        # In a real implementation, this would rollback system state
    
    async def _handle_emergency_stop(self, action: Dict[str, Any], 
                                    incident: SafetyIncident) -> None:
        """Handle emergency stop response action."""
        self.logger.critical("EMERGENCY STOP ACTIVATED")
        
        # In a real implementation, this would safely stop all operations
        # This is the most severe response action
    
    async def _handle_safe_mode(self, action: Dict[str, Any], 
                               incident: SafetyIncident) -> None:
        """Handle safe mode response action."""
        self.logger.warning("Entering safe mode")
        
        # In a real implementation, this would put the system in safe mode
        # with limited functionality
    
    async def _handle_override_action(self, action: Dict[str, Any], 
                                     incident: SafetyIncident) -> None:
        """Handle override response action."""
        scope = action.get("scope", "all")
        
        self.logger.warning(f"Safety override requested for scope: {scope}")
        
        # This would interface with the emergency override system
    
    def update_metric(self, metric_id: str, value: float) -> SafetyLevel:
        """Update a safety metric."""
        if metric_id not in self.metrics:
            raise ValueError(f"Metric {metric_id} not found")
        
        metric = self.metrics[metric_id]
        return metric.update_value(value)
    
    def add_metric(self, metric: SafetyMetric) -> None:
        """Add a new safety metric."""
        self.metrics[metric.metric_id] = metric
        self.logger.info(f"Added safety metric: {metric.metric_id}")
    
    def add_rule(self, rule: SafetyRule) -> None:
        """Add a new safety rule."""
        self.rules[rule.rule_id] = rule
        self.logger.info(f"Added safety rule: {rule.rule_id}")
    
    def get_incidents(self, unresolved_only: bool = True,
                     incident_type: Optional[IncidentType] = None) -> List[SafetyIncident]:
        """Get safety incidents."""
        incidents = self.incidents.copy()
        
        if unresolved_only:
            incidents = [i for i in incidents if not i.resolved]
        
        if incident_type:
            incidents = [i for i in incidents if i.incident_type == incident_type]
        
        return sorted(incidents, key=lambda i: i.detected_at, reverse=True)
    
    def resolve_incident(self, incident_id: str, resolution_notes: str = "") -> bool:
        """Resolve a safety incident."""
        for incident in self.incidents:
            if incident.incident_id == incident_id and not incident.resolved:
                incident.resolved = True
                incident.resolved_at = datetime.now()
                incident.resolution_notes = resolution_notes
                
                self.logger.info(f"Resolved incident: {incident_id}")
                return True
        
        return False
    
    def get_safety_status(self) -> Dict[str, Any]:
        """Get overall safety status."""
        # Calculate overall safety level
        safety_levels = []
        for metric in self.metrics.values():
            level = metric.update_value(metric.current_value)
            safety_levels.append(level)
        
        # Determine overall level (most severe)
        level_order = [
            SafetyLevel.SAFE,
            SafetyLevel.CAUTION,
            SafetyLevel.WARNING,
            SafetyLevel.CRITICAL,
            SafetyLevel.EMERGENCY
        ]
        
        overall_level = SafetyLevel.SAFE
        for level in safety_levels:
            if level_order.index(level) > level_order.index(overall_level):
                overall_level = level
        
        # Count unresolved incidents by severity
        unresolved_incidents = [i for i in self.incidents if not i.resolved]
        incident_counts = {}
        for incident in unresolved_incidents:
            severity = incident.severity.value
            incident_counts[severity] = incident_counts.get(severity, 0) + 1
        
        return {
            "overall_safety_level": overall_level.value,
            "monitoring_active": self.monitoring_active,
            "total_metrics": len(self.metrics),
            "total_rules": len(self.rules),
            "unresolved_incidents": len(unresolved_incidents),
            "incident_counts": incident_counts,
            "active_overrides": len(self.emergency_override.get_active_overrides()),
            "metrics": {mid: m.to_dict() for mid, m in self.metrics.items()}
        }
    
    def _cleanup_expired_overrides(self) -> None:
        """Clean up expired emergency overrides."""
        for request_id, override in self.emergency_override.active_overrides.items():
            if override["active"] and override["expires_at"] < datetime.now():
                override["active"] = False
                self.logger.info(f"Emergency override expired: {request_id}")