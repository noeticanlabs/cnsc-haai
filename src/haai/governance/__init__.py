"""
HAAI Governance Module

Provides comprehensive governance, safety, and compliance capabilities for HAAI agents.
Includes policy enforcement, identity management, safety monitoring, multi-level enforcement,
and complete audit trails with cryptographic verification.
"""

from .policy_engine import (
    PolicyEngine,
    Policy,
    PolicyType,
    PolicyStatus,
    PolicyRule,
    PolicyConstraint,
    EnforcementLevel,
    PolicyConflict
)

from .identity_access import (
    IdentityAccessManager,
    AgentIdentity,
    Role,
    AccessRequest,
    AuthenticationMethod,
    AccessLevel,
    SeparationDutyType,
    SeparationOfDuty,
    AuditEvent
)

from .safety_monitoring import (
    SafetyMonitoringSystem,
    SafetyMetric,
    SafetyIncident,
    SafetyRule,
    SafetyLevel,
    IncidentType,
    ResponseAction,
    EmergencyOverride
)

from .enforcement import (
    EnforcementCoordinator,
    EnforcementDecision,
    EnforcementRule,
    EnforcementLevel as EnforcementPointLevel,
    EnforcementAction,
    EnforcementPriority,
    GatewayEnforcement,
    SchedulerEnforcement,
    RuntimeEnforcement,
    OutputEnforcement
)

from .audit_evidence import (
    AuditEvidenceSystem,
    AuditReceipt,
    Evidence,
    ReceiptType,
    EvidenceType,
    ComplianceStandard,
    TamperDetection,
    ComplianceReporter
)

from .integrated_governance import (
    HAAIGovernanceIntegrator,
    GovernanceConfig,
    GovernanceMode,
    GovernanceDecision
)

# Legacy compatibility
from .cgl import CGLGovernance, ComplianceChecker

__all__ = [
    # Policy Engine
    "PolicyEngine",
    "Policy",
    "PolicyType", 
    "PolicyStatus",
    "PolicyRule",
    "PolicyConstraint",
    "EnforcementLevel",
    "PolicyConflict",
    
    # Identity and Access Management
    "IdentityAccessManager",
    "AgentIdentity",
    "Role",
    "AccessRequest",
    "AuthenticationMethod",
    "AccessLevel",
    "SeparationDutyType",
    "SeparationOfDuty",
    "AuditEvent",
    
    # Safety Monitoring
    "SafetyMonitoringSystem",
    "SafetyMetric",
    "SafetyIncident",
    "SafetyRule",
    "SafetyLevel",
    "IncidentType",
    "ResponseAction",
    "EmergencyOverride",
    
    # Enforcement
    "EnforcementCoordinator",
    "EnforcementDecision",
    "EnforcementRule",
    "EnforcementPointLevel",
    "EnforcementAction",
    "EnforcementPriority",
    "GatewayEnforcement",
    "SchedulerEnforcement",
    "RuntimeEnforcement",
    "OutputEnforcement",
    
    # Audit and Evidence
    "AuditEvidenceSystem",
    "AuditReceipt",
    "Evidence",
    "ReceiptType",
    "EvidenceType",
    "ComplianceStandard",
    "TamperDetection",
    "ComplianceReporter",
    
    # Integrated Governance
    "HAAIGovernanceIntegrator",
    "GovernanceConfig",
    "GovernanceMode",
    "GovernanceDecision",
    
    # Legacy
    "CGLGovernance",
    "ComplianceChecker"
]