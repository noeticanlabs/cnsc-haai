"""
Integrated Governance System

Brings together all governance components (policy engine, identity & access,
safety monitoring, enforcement, and audit/evidence) into a cohesive
system that integrates seamlessly with HAAI agents.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from enum import Enum

from .policy_engine import PolicyEngine, Policy, PolicyType
from .identity_access import IdentityAccessManager, AccessLevel, AuthenticationMethod
from .safety_monitoring import SafetyMonitoringSystem, SafetyLevel, IncidentType
from .enforcement import EnforcementCoordinator, EnforcementLevel
from .audit_evidence import AuditEvidenceSystem, ReceiptType, EvidenceType


class GovernanceMode(Enum):
    """Governance operation modes."""
    STRICT = "strict"          # All policies enforced, no exceptions
    PERMISSIVE = "permissive"  # Policies enforced with logging only
    LEARNING = "learning"      # Monitor and learn, minimal enforcement
    EMERGENCY = "emergency"    # Emergency override mode
    MAINTENANCE = "maintenance" # Maintenance mode with reduced enforcement


@dataclass
class GovernanceConfig:
    """Configuration for governance system."""
    mode: GovernanceMode = GovernanceMode.STRICT
    policy_evaluation_interval: float = 1.0
    safety_monitoring_interval: float = 0.5
    audit_retention_days: int = 90
    enable_real_time_enforcement: bool = True
    enable_compliance_reporting: bool = True
    emergency_override_duration: int = 30
    max_concurrent_operations: int = 100
    resource_limits: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GovernanceDecision:
    """Represents a governance decision."""
    decision_id: str
    operation_id: str
    agent_id: str
    allowed: bool
    reason: str
    policy_results: Dict[str, Any]
    safety_level: SafetyLevel
    enforcement_actions: List[str]
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class HAAIGovernanceIntegrator:
    """Integrates governance with HAAI agent operations."""
    
    def __init__(self, config: Optional[GovernanceConfig] = None):
        self.config = config or GovernanceConfig()
        
        # Initialize governance components
        self.policy_engine = PolicyEngine()
        self.identity_manager = IdentityAccessManager()
        self.safety_monitoring = SafetyMonitoringSystem()
        self.enforcement_coordinator = EnforcementCoordinator()
        self.audit_system = AuditEvidenceSystem()
        
        # Integration state
        self.mode = self.config.mode
        self.active_operations: Dict[str, Dict[str, Any]] = {}
        self.governance_decisions: List[GovernanceDecision] = []
        
        # Callbacks for HAAI integration
        self.operation_callbacks: Dict[str, Callable] = {}
        
        self.logger = logging.getLogger("haai.governance.integrator")
        
        # Setup integration hooks
        self._setup_integration_hooks()
    
    def _setup_integration_hooks(self) -> None:
        """Setup integration hooks with HAAI components."""
        # Policy engine hooks
        self.policy_engine.add_event_callback = self._on_policy_event
        
        # Safety monitoring hooks
        self.safety_monitoring.add_incident_callback = self._on_safety_incident
        
        # Enforcement hooks
        self.enforcement_coordinator.add_escalation_callback = self._on_enforcement_escalation
    
    async def initialize(self) -> None:
        """Initialize the integrated governance system."""
        self.logger.info("Initializing Integrated Governance System")
        
        try:
            # Start safety monitoring
            if self.config.enable_real_time_enforcement:
                asyncio.create_task(self.safety_monitoring.start_monitoring())
            
            # Create initial identities for system components
            await self._create_system_identities()
            
            # Create initial policies for HAAI operations
            await self._create_haai_policies()
            
            # Setup enforcement rules
            await self._setup_enforcement_rules()
            
            # Create initial audit checkpoint
            self.audit_system.create_compliance_checkpoint("initialization")
            
            self.logger.info("Integrated Governance System initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize governance system: {e}")
            raise
    
    async def _create_system_identities(self) -> None:
        """Create system identities for HAAI components."""
        # HAAI Core System
        self.identity_manager.create_identity(
            agent_id="haai_core",
            name="HAAI Core System",
            authentication_method=AuthenticationMethod.TOKEN,
            credentials={"token": "core_system_token"},
            roles=["system_admin"]
        )
        
        # Reasoning Engine
        self.identity_manager.create_identity(
            agent_id="reasoning_engine",
            name="Reasoning Engine",
            authentication_method=AuthenticationMethod.TOKEN,
            credentials={"token": "reasoning_token"},
            roles=["operator"]
        )
        
        # Safety Monitor
        self.identity_manager.create_identity(
            agent_id="safety_monitor",
            name="Safety Monitor",
            authentication_method=AuthenticationMethod.TOKEN,
            credentials={"token": "safety_token"},
            roles=["safety_officer"]
        )
        
        # Learning System
        self.identity_manager.create_identity(
            agent_id="learning_system",
            name="Learning System",
            authentication_method=AuthenticationMethod.TOKEN,
            credentials={"token": "learning_token"},
            roles=["operator"]
        )
    
    async def _create_haai_policies(self) -> None:
        """Create HAAI-specific governance policies."""
        # Coherence Governance Policy
        coherence_policy = Policy(
            policy_id="haai_coherence_governance",
            name="HAAI Coherence Governance",
            description="Ensures coherence in HAAI operations",
            policy_type=PolicyType.SAFETY,
            status=self.policy_engine.compliance_checker.PolicyStatus.ACTIVE,
            rules=[
                # Minimum coherence for reasoning operations
                {
                    "rule_id": "reasoning_coherence_min",
                    "name": "Reasoning Coherence Minimum",
                    "conditions": [
                        {"field": "operation_type", "operator": "equals", "value": "reasoning"}
                    ],
                    "constraints": [
                        {
                            "constraint_id": "min_coherence",
                            "name": "Minimum Coherence Score",
                            "type": "function",
                            "parameters": {
                                "function": "coherence_threshold",
                                "threshold": 0.75,
                                "field": "coherence_score"
                            },
                            "enforcement_level": "blocking"
                        }
                    ],
                    "actions": [
                        {"type": "log", "level": "warning"},
                        {"type": "require_approval", "role": "safety_officer"}
                    ],
                    "priority": 1
                }
            ]
        )
        
        # Abstraction Depth Policy
        abstraction_policy = Policy(
            policy_id="haai_abstraction_governance",
            name="HAAI Abstraction Governance",
            description="Controls abstraction depth and complexity",
            policy_type=PolicyType.SAFETY,
            status=self.policy_engine.compliance_checker.PolicyStatus.ACTIVE,
            rules=[
                {
                    "rule_id": "abstraction_depth_limit",
                    "name": "Abstraction Depth Limit",
                    "conditions": [
                        {"field": "operation_type", "operator": "equals", "value": "abstraction"}
                    ],
                    "constraints": [
                        {
                            "constraint_id": "max_depth",
                            "name": "Maximum Abstraction Depth",
                            "type": "function",
                            "parameters": {
                                "function": "abstraction_depth",
                                "max_depth": 12,
                                "field": "abstraction_depth"
                            },
                            "enforcement_level": "critical"
                        }
                    ],
                    "actions": [
                        {"type": "log", "level": "error"},
                        {"type": "emergency_stop"}
                    ],
                    "priority": 1
                }
            ]
        )
        
        # Learning Safety Policy
        learning_policy = Policy(
            policy_id="haai_learning_governance",
            name="HAAI Learning Governance",
            description="Ensures safe learning operations",
            policy_type=PolicyType.SAFETY,
            status=self.policy_engine.compliance_checker.PolicyStatus.ACTIVE,
            rules=[
                {
                    "rule_id": "learning_rate_limit",
                    "name": "Learning Rate Limit",
                    "conditions": [
                        {"field": "operation_type", "operator": "equals", "value": "learning"}
                    ],
                    "constraints": [
                        {
                            "constraint_id": "max_learning_rate",
                            "name": "Maximum Learning Rate",
                            "type": "range",
                            "parameters": {
                                "min": 0.0,
                                "max": 0.1,
                                "field": "learning_rate"
                            },
                            "enforcement_level": "warning"
                        }
                    ],
                    "actions": [
                        {"type": "log", "level": "warning"},
                        {"type": "modify", "parameter": "learning_rate", "value": 0.05}
                    ],
                    "priority": 2
                }
            ]
        )
        
        # Add policies to engine
        self.policy_engine.add_policy(coherence_policy)
        self.policy_engine.add_policy(abstraction_policy)
        self.policy_engine.add_policy(learning_policy)
    
    async def _setup_enforcement_rules(self) -> None:
        """Setup enforcement rules for HAAI operations."""
        # Add custom enforcement rules would go here
        pass
    
    async def govern_operation(self, operation: Dict[str, Any]) -> GovernanceDecision:
        """Govern an HAAI operation through all governance layers."""
        operation_id = operation.get("operation_id", f"op_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        agent_id = operation.get("agent_id", "unknown")
        
        # Create audit receipt for operation
        receipt_id = self.audit_system.create_receipt(
            receipt_type=ReceiptType.OPERATION,
            operation_id=operation_id,
            agent_id=agent_id,
            details={"operation": operation}
        )
        
        try:
            # 1. Authentication and Authorization
            auth_result = await self._authenticate_and_authorize(operation)
            if not auth_result["authorized"]:
                decision = GovernanceDecision(
                    decision_id=f"dec_{operation_id}",
                    operation_id=operation_id,
                    agent_id=agent_id,
                    allowed=False,
                    reason=f"Authorization failed: {auth_result['reason']}",
                    policy_results={},
                    safety_level=SafetyLevel.WARNING,
                    enforcement_actions=["block"]
                )
                self._record_governance_decision(decision, receipt_id)
                return decision
            
            # 2. Policy Evaluation
            policy_results = self.policy_engine.evaluate_policies(operation)
            
            # 3. Safety Check
            safety_status = self.safety_monitoring.get_safety_status()
            current_safety_level = SafetyLevel(safety_status["overall_safety_level"])
            
            # 4. Enforcement Decision
            enforcement_result = await self.enforcement_coordinator.enforce_request(operation)
            
            # 5. Make final governance decision
            allowed = self._make_governance_decision(
                policy_results, safety_status, enforcement_result
            )
            
            decision = GovernanceDecision(
                decision_id=f"dec_{operation_id}",
                operation_id=operation_id,
                agent_id=agent_id,
                allowed=allowed,
                reason=self._generate_decision_reason(policy_results, safety_status, enforcement_result),
                policy_results=policy_results,
                safety_level=current_safety_level,
                enforcement_actions=enforcement_result.get("decisions", {}),
                metadata={
                    "receipt_id": receipt_id,
                    "auth_result": auth_result,
                    "enforcement_result": enforcement_result
                }
            )
            
            # Add evidence to receipt
            self.audit_system.add_evidence(
                receipt_id=receipt_id,
                evidence_type=EvidenceType.SYSTEM_OUTPUT,
                content=decision.to_dict(),
                metadata={"governance_decision": True}
            )
            
            # Track active operation
            if allowed:
                self.active_operations[operation_id] = {
                    "operation": operation,
                    "decision": decision,
                    "started_at": datetime.now(),
                    "receipt_id": receipt_id
                }
            
            self._record_governance_decision(decision, receipt_id)
            return decision
            
        except Exception as e:
            self.logger.error(f"Error governing operation {operation_id}: {e}")
            
            decision = GovernanceDecision(
                decision_id=f"dec_{operation_id}",
                operation_id=operation_id,
                agent_id=agent_id,
                allowed=False,
                reason=f"Governance error: {str(e)}",
                policy_results={},
                safety_level=SafetyLevel.CRITICAL,
                enforcement_actions=["emergency_stop"]
            )
            
            self._record_governance_decision(decision, receipt_id)
            return decision
    
    async def _authenticate_and_authorize(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate and authorize operation."""
        agent_id = operation.get("agent_id")
        credentials = operation.get("credentials", {})
        
        if not agent_id:
            return {"authorized": False, "reason": "No agent ID provided"}
        
        # Authenticate
        auth_result = self.identity_manager.authenticate(agent_id, credentials)
        if not auth_result["success"]:
            return {"authorized": False, "reason": auth_result["reason"]}
        
        # Authorize
        resource = operation.get("resource", "haai_operation")
        action = operation.get("action", "execute")
        access_level = AccessLevel(operation.get("access_level", "execute"))
        
        authz_result = self.identity_manager.authorize(
            agent_id, resource, action, access_level, operation
        )
        
        return authz_result
    
    def _make_governance_decision(self, policy_results: Dict[str, Any],
                                safety_status: Dict[str, Any],
                                enforcement_result: Dict[str, Any]) -> bool:
        """Make final governance decision based on all inputs."""
        # In strict mode, any violation blocks
        if self.mode == GovernanceMode.STRICT:
            if not policy_results.get("overall_compliant", True):
                return False
            
            if safety_status["overall_safety_level"] in ["critical", "emergency"]:
                return False
            
            if enforcement_result.get("allowed") is False:
                return False
        
        # In permissive mode, log violations but allow
        elif self.mode == GovernanceMode.PERMISSIVE:
            return True
        
        # In learning mode, allow most operations
        elif self.mode == GovernanceMode.LEARNING:
            if safety_status["overall_safety_level"] == "emergency":
                return False
            return True
        
        # In emergency mode, allow critical operations only
        elif self.mode == GovernanceMode.EMERGENCY:
            return safety_status["overall_safety_level"] != "emergency"
        
        return True
    
    def _generate_decision_reason(self, policy_results: Dict[str, Any],
                                safety_status: Dict[str, Any],
                                enforcement_result: Dict[str, Any]) -> str:
        """Generate reason for governance decision."""
        reasons = []
        
        if not policy_results.get("overall_compliant", True):
            reasons.append(f"Policy violations: {len(policy_results.get('total_violations', []))}")
        
        safety_level = safety_status["overall_safety_level"]
        if safety_level in ["critical", "emergency"]:
            reasons.append(f"Safety level: {safety_level}")
        
        if enforcement_result.get("allowed") is False:
            reasons.append("Enforcement blocked")
        
        if not reasons:
            reasons.append("All checks passed")
        
        return "; ".join(reasons)
    
    def _record_governance_decision(self, decision: GovernanceDecision, receipt_id: str) -> None:
        """Record governance decision."""
        self.governance_decisions.append(decision)
        
        # Keep only recent decisions
        if len(self.governance_decisions) > 1000:
            self.governance_decisions = self.governance_decisions[-1000:]
        
        # Update receipt with decision
        receipt = self.audit_system.get_receipt(receipt_id)
        if receipt:
            receipt.details["governance_decision"] = decision.to_dict()
    
    async def complete_operation(self, operation_id: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Complete an operation and validate result."""
        if operation_id not in self.active_operations:
            return {"success": False, "reason": "Operation not found"}
        
        operation_data = self.active_operations[operation_id]
        receipt_id = operation_data["receipt_id"]
        
        try:
            # Validate result through output enforcement
            validation_result = await self.enforcement_coordinator.validate_result(
                result, operation_data["operation"]
            )
            
            # Update safety metrics based on result
            if "coherence_score" in result:
                self.safety_monitoring.update_metric("coherence_score", result["coherence_score"])
            
            if "abstraction_quality" in result:
                self.safety_monitoring.update_metric("abstraction_quality", result["abstraction_quality"])
            
            # Add result evidence to receipt
            self.audit_system.add_evidence(
                receipt_id=receipt_id,
                evidence_type=EvidenceType.SYSTEM_OUTPUT,
                content=result,
                metadata={"operation_completion": True, "validation": validation_result}
            )
            
            # Clean up active operation
            del self.active_operations[operation_id]
            
            return {
                "success": True,
                "validation": validation_result,
                "receipt_id": receipt_id
            }
            
        except Exception as e:
            self.logger.error(f"Error completing operation {operation_id}: {e}")
            return {"success": False, "reason": str(e)}
    
    def set_governance_mode(self, mode: GovernanceMode, reason: str = "") -> None:
        """Set governance mode."""
        old_mode = self.mode
        self.mode = mode
        
        self.logger.info(f"Governance mode changed: {old_mode.value} -> {mode.value}")
        
        if reason:
            self.logger.info(f"Reason: {reason}")
    
    def request_emergency_override(self, reason: str, requested_by: str,
                                  duration_minutes: int = None) -> str:
        """Request emergency override."""
        duration = duration_minutes or self.config.emergency_override_duration
        
        request_id = self.safety_monitoring.emergency_override.request_override(
            request_id=f"override_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            reason=reason,
            requested_by=requested_by,
            duration_minutes=duration
        )
        
        return request_id
    
    def get_governance_status(self) -> Dict[str, Any]:
        """Get comprehensive governance status."""
        return {
            "mode": self.mode.value,
            "active_operations": len(self.active_operations),
            "total_decisions": len(self.governance_decisions),
            "policy_engine": self.policy_engine.get_engine_status(),
            "identity_manager": self.identity_manager.get_system_status(),
            "safety_monitoring": self.safety_monitoring.get_safety_status(),
            "enforcement_coordinator": self.enforcement_coordinator.get_enforcement_status(),
            "audit_system": self.audit_system.get_system_status()
        }
    
    def generate_compliance_report(self, standard: str = "ISO_27001",
                                 days: int = 30) -> Dict[str, Any]:
        """Generate compliance report."""
        from .audit_evidence import ComplianceStandard
        
        try:
            compliance_standard = ComplianceStandard(standard.lower())
            return self.audit_system.generate_compliance_report(compliance_standard, days)
        except ValueError:
            return {"error": f"Unknown compliance standard: {standard}"}
    
    # Event handlers
    def _on_policy_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Handle policy events."""
        self.logger.info(f"Policy event: {event_type} - {data}")
    
    def _on_safety_incident(self, incident: Dict[str, Any]) -> None:
        """Handle safety incidents."""
        self.logger.warning(f"Safety incident: {incident}")
        
        # In strict mode, consider switching to emergency mode
        if self.mode == GovernanceMode.STRICT and incident.get("severity") == "emergency":
            self.set_governance_mode(
                GovernanceMode.EMERGENCY,
                f"Emergency safety incident: {incident.get('title', 'Unknown')}"
            )
    
    def _on_enforcement_escalation(self, decision: Dict[str, Any]) -> None:
        """Handle enforcement escalations."""
        self.logger.warning(f"Enforcement escalation: {decision}")
    
    # HAAI Integration Methods
    def register_operation_callback(self, operation_type: str, callback: Callable) -> None:
        """Register callback for HAAI operations."""
        self.operation_callbacks[operation_type] = callback
    
    async def integrate_with_haai_agent(self, haai_agent) -> None:
        """Integrate governance with HAAI agent."""
        # Register governance hooks with agent
        if hasattr(haai_agent, 'reasoning_engine'):
            haai_agent.reasoning_engine.add_pre_execution_hook(
                self._governance_pre_execution_hook
            )
            haai_agent.reasoning_engine.add_post_execution_hook(
                self._governance_post_execution_hook
            )
        
        if hasattr(haai_agent, 'learning_system'):
            haai_agent.learning_system.add_learning_hook(
                self._governance_learning_hook
            )
        
        if hasattr(haai_agent, 'attention_system'):
            haai_agent.attention_system.add_allocation_hook(
                self._governance_attention_hook
            )
        
        self.logger.info("Governance system integrated with HAAI agent")
    
    async def _governance_pre_execution_hook(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """Pre-execution governance hook."""
        decision = await self.govern_operation(operation)
        
        if not decision.allowed:
            return {"allowed": False, "reason": decision.reason}
        
        return {"allowed": True}
    
    async def _governance_post_execution_hook(self, operation: Dict[str, Any],
                                            result: Dict[str, Any]) -> None:
        """Post-execution governance hook."""
        operation_id = operation.get("operation_id")
        if operation_id:
            await self.complete_operation(operation_id, result)
    
    async def _governance_learning_hook(self, learning_data: Dict[str, Any]) -> None:
        """Learning governance hook."""
        # Govern learning operations
        await self.govern_operation({
            "operation_type": "learning",
            "agent_id": "learning_system",
            "learning_data": learning_data
        })
    
    async def _governance_attention_hook(self, attention_data: Dict[str, Any]) -> None:
        """Attention allocation governance hook."""
        # Govern attention allocation
        await self.govern_operation({
            "operation_type": "attention_allocation",
            "agent_id": "attention_system",
            "attention_data": attention_data
        })