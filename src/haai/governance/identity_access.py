"""
Identity and Access Management for HAAI Governance

Provides comprehensive authentication, authorization, role-based access control,
and audit capabilities for HAAI agents and operations.
"""

import logging
import hashlib
import jwt
import secrets
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json


class AuthenticationMethod(Enum):
    """Authentication methods."""
    PASSWORD = "password"
    TOKEN = "token"
    CERTIFICATE = "certificate"
    BIOMETRIC = "biometric"
    MULTI_FACTOR = "multi_factor"


class AccessLevel(Enum):
    """Access levels for operations."""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"
    SYSTEM = "system"


class SeparationDutyType(Enum):
    """Types of separation of duties."""
    MAKER_CHECKER = "maker_checker"
    DUAL_CONTROL = "dual_control"
    ROTATION = "rotation"
    CONFLICT_PREVENTION = "conflict_prevention"


@dataclass
class Role:
    """Represents a role with permissions."""
    role_id: str
    name: str
    description: str
    permissions: Set[str]
    access_levels: Set[AccessLevel]
    constraints: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    is_system_role: bool = False
    
    def has_permission(self, permission: str) -> bool:
        """Check if role has a specific permission."""
        return permission in self.permissions
    
    def has_access_level(self, level: AccessLevel) -> bool:
        """Check if role has access level."""
        return level in self.access_levels
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert role to dictionary."""
        return {
            "role_id": self.role_id,
            "name": self.name,
            "description": self.description,
            "permissions": list(self.permissions),
            "access_levels": [level.value for level in self.access_levels],
            "constraints": self.constraints,
            "created_at": self.created_at.isoformat(),
            "is_system_role": self.is_system_role
        }


@dataclass
class AgentIdentity:
    """Represents an agent's identity."""
    agent_id: str
    name: str
    authentication_method: AuthenticationMethod
    credentials: Dict[str, Any]
    roles: Set[str]
    attributes: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    is_active: bool = True
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    
    def is_locked(self) -> bool:
        """Check if identity is locked."""
        if self.locked_until is None:
            return False
        return datetime.now() < self.locked_until
    
    def has_role(self, role_id: str) -> bool:
        """Check if identity has a role."""
        return role_id in self.roles
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert identity to dictionary."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "authentication_method": self.authentication_method.value,
            "roles": list(self.roles),
            "attributes": self.attributes,
            "created_at": self.created_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "is_active": self.is_active,
            "failed_login_attempts": self.failed_login_attempts,
            "locked_until": self.locked_until.isoformat() if self.locked_until else None
        }


@dataclass
class AccessRequest:
    """Represents an access request."""
    request_id: str
    agent_id: str
    resource: str
    action: str
    access_level: AccessLevel
    context: Dict[str, Any] = field(default_factory=dict)
    requested_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    justification: str = ""
    approved: Optional[bool] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    denial_reason: str = ""
    
    def is_expired(self) -> bool:
        """Check if request is expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert request to dictionary."""
        return {
            "request_id": self.request_id,
            "agent_id": self.agent_id,
            "resource": self.resource,
            "action": self.action,
            "access_level": self.access_level.value,
            "context": self.context,
            "requested_at": self.requested_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "justification": self.justification,
            "approved": self.approved,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "denial_reason": self.denial_reason
        }


@dataclass
class AuditEvent:
    """Represents an audit event."""
    event_id: str
    agent_id: str
    event_type: str
    resource: str
    action: str
    outcome: str
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "event_id": self.event_id,
            "agent_id": self.agent_id,
            "event_type": self.event_type,
            "resource": self.resource,
            "action": self.action,
            "outcome": self.outcome,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "session_id": self.session_id
        }


class SeparationOfDuty:
    """Manages separation of duties constraints."""
    
    def __init__(self):
        self.constraints: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger("haai.separation_of_duty")
    
    def add_constraint(self, constraint_id: str, constraint_type: SeparationDutyType,
                      parameters: Dict[str, Any]) -> None:
        """Add a separation of duty constraint."""
        self.constraints[constraint_id] = {
            "type": constraint_type,
            "parameters": parameters,
            "created_at": datetime.now()
        }
        self.logger.info(f"Added SoD constraint: {constraint_id}")
    
    def check_constraint(self, constraint_id: str, agent_id: str, 
                        operation: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Check if operation violates SoD constraint."""
        if constraint_id not in self.constraints:
            return {"violated": False, "reason": "Constraint not found"}
        
        constraint = self.constraints[constraint_id]
        constraint_type = constraint["type"]
        parameters = constraint["parameters"]
        
        if constraint_type == SeparationDutyType.MAKER_CHECKER:
            return self._check_maker_checker(agent_id, operation, parameters, context)
        elif constraint_type == SeparationDutyType.DUAL_CONTROL:
            return self._check_dual_control(agent_id, operation, parameters, context)
        elif constraint_type == SeparationDutyType.ROTATION:
            return self._check_rotation(agent_id, operation, parameters, context)
        elif constraint_type == SeparationDutyType.CONFLICT_PREVENTION:
            return self._check_conflict_prevention(agent_id, operation, parameters, context)
        
        return {"violated": False, "reason": "Unknown constraint type"}
    
    def _check_maker_checker(self, agent_id: str, operation: str,
                           parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Check maker-checker constraint."""
        critical_operations = parameters.get("critical_operations", [])
        
        if operation not in critical_operations:
            return {"violated": False, "reason": "Operation not critical"}
        
        # Check if same agent performed both maker and checker roles
        maker_id = context.get("maker_id")
        checker_id = context.get("checker_id")
        
        if maker_id == checker_id:
            return {
                "violated": True,
                "reason": "Same agent cannot perform maker and checker roles"
            }
        
        return {"violated": False, "reason": "Maker-checker constraint satisfied"}
    
    def _check_dual_control(self, agent_id: str, operation: str,
                          parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Check dual control constraint."""
        required_approvals = parameters.get("required_approvals", 2)
        approvals = context.get("approvals", [])
        
        if len(approvals) < required_approvals:
            return {
                "violated": True,
                "reason": f"Insufficient approvals: {len(approvals)}/{required_approvals}"
            }
        
        # Check for duplicate approvals
        unique_approvers = set(approvals)
        if len(unique_approvers) < required_approvals:
            return {
                "violated": True,
                "reason": "Duplicate approvals detected"
            }
        
        return {"violated": False, "reason": "Dual control constraint satisfied"}
    
    def _check_rotation(self, agent_id: str, operation: str,
                       parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Check rotation constraint."""
        max_duration_days = parameters.get("max_duration_days", 30)
        role_assignment_date = context.get("role_assignment_date")
        
        if role_assignment_date:
            assignment_date = datetime.fromisoformat(role_assignment_date)
            days_in_role = (datetime.now() - assignment_date).days
            
            if days_in_role > max_duration_days:
                return {
                    "violated": True,
                    "reason": f"Role rotation required: {days_in_role} days in role"
                }
        
        return {"violated": False, "reason": "Rotation constraint satisfied"}
    
    def _check_conflict_prevention(self, agent_id: str, operation: str,
                                  parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Check conflict prevention constraint."""
        conflicting_roles = parameters.get("conflicting_roles", [])
        agent_roles = context.get("agent_roles", [])
        
        # Check if agent has conflicting roles
        agent_role_set = set(agent_roles)
        for conflict_pair in conflicting_roles:
            if set(conflict_pair).issubset(agent_role_set):
                return {
                    "violated": True,
                    "reason": f"Conflicting roles: {conflict_pair}"
                }
        
        return {"violated": False, "reason": "No conflicting roles"}


class IdentityAccessManager:
    """Main identity and access management system."""
    
    def __init__(self, jwt_secret: Optional[str] = None):
        self.identities: Dict[str, AgentIdentity] = {}
        self.roles: Dict[str, Role] = {}
        self.access_requests: Dict[str, AccessRequest] = {}
        self.audit_events: List[AuditEvent] = []
        self.separation_of_duty = SeparationOfDuty()
        
        self.jwt_secret = jwt_secret or secrets.token_urlsafe(32)
        self.token_expiry = timedelta(hours=24)
        self.session_timeout = timedelta(minutes=30)
        
        self.logger = logging.getLogger("haai.identity_access")
        
        # Load default roles and policies
        self._load_default_roles()
        self._load_default_policies()
    
    def _load_default_roles(self) -> None:
        """Load default system roles."""
        # System Administrator
        admin_role = Role(
            role_id="system_admin",
            name="System Administrator",
            description="Full system access and control",
            permissions={"*"},
            access_levels={AccessLevel.SYSTEM},
            is_system_role=True
        )
        
        # Safety Officer
        safety_role = Role(
            role_id="safety_officer",
            name="Safety Officer",
            description="Safety monitoring and emergency controls",
            permissions={
                "safety_monitor", "emergency_stop", "safety_override",
                "incident_report", "safety_audit"
            },
            access_levels={AccessLevel.READ, AccessLevel.EXECUTE},
            constraints={"max_concurrent_operations": 5}
        )
        
        # Policy Administrator
        policy_role = Role(
            role_id="policy_admin",
            name="Policy Administrator",
            description="Policy management and compliance",
            permissions={
                "policy_create", "policy_update", "policy_delete",
                "policy_evaluate", "compliance_report", "audit_access"
            },
            access_levels={AccessLevel.READ, AccessLevel.WRITE, AccessLevel.EXECUTE}
        )
        
        # Operator
        operator_role = Role(
            role_id="operator",
            name="Operator",
            description="Standard operational access",
            permissions={
                "agent_execute", "reasoning_access", "tool_usage",
                "monitoring_access", "basic_configuration"
            },
            access_levels={AccessLevel.READ, AccessLevel.EXECUTE},
            constraints={"max_abstraction_depth": 8}
        )
        
        # Observer
        observer_role = Role(
            role_id="observer",
            name="Observer",
            description="Read-only access for monitoring",
            permissions={
                "read_access", "monitoring_view", "report_access"
            },
            access_levels={AccessLevel.READ}
        )
        
        # Add roles
        for role in [admin_role, safety_role, policy_role, operator_role, observer_role]:
            self.roles[role.role_id] = role
    
    def _load_default_policies(self) -> None:
        """Load default access policies."""
        # Add separation of duty constraints
        self.separation_of_duty.add_constraint(
            "critical_operation_maker_checker",
            SeparationDutyType.MAKER_CHECKER,
            {
                "critical_operations": [
                    "policy_update", "safety_override", "system_configuration"
                ]
            }
        )
        
        self.separation_of_duty.add_constraint(
            "high_risk_dual_control",
            SeparationDutyType.DUAL_CONTROL,
            {
                "required_approvals": 2,
                "operations": ["emergency_override", "critical_system_change"]
            }
        )
        
        self.separation_of_duty.add_constraint(
            "role_rotation",
            SeparationDutyType.ROTATION,
            {
                "max_duration_days": 90,
                "roles": ["system_admin", "safety_officer"]
            }
        )
    
    def create_identity(self, agent_id: str, name: str, 
                       authentication_method: AuthenticationMethod,
                       credentials: Dict[str, Any], roles: List[str]) -> str:
        """Create a new agent identity."""
        if agent_id in self.identities:
            raise ValueError(f"Identity {agent_id} already exists")
        
        # Validate roles exist
        for role_id in roles:
            if role_id not in self.roles:
                raise ValueError(f"Role {role_id} does not exist")
        
        # Hash passwords if using password authentication
        if authentication_method == AuthenticationMethod.PASSWORD:
            password = credentials.get("password")
            if password:
                credentials["password_hash"] = self._hash_password(password)
                del credentials["password"]
        
        identity = AgentIdentity(
            agent_id=agent_id,
            name=name,
            authentication_method=authentication_method,
            credentials=credentials,
            roles=set(roles)
        )
        
        self.identities[agent_id] = identity
        
        # Log creation
        self._log_audit_event(
            agent_id="system",
            event_type="identity_created",
            resource="identity",
            action="create",
            outcome="success",
            context={"target_agent_id": agent_id, "roles": roles}
        )
        
        self.logger.info(f"Created identity: {agent_id}")
        return agent_id
    
    def authenticate(self, agent_id: str, credentials: Dict[str, Any],
                    context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Authenticate an agent."""
        if agent_id not in self.identities:
            return {"success": False, "reason": "Identity not found"}
        
        identity = self.identities[agent_id]
        
        # Check if locked
        if identity.is_locked():
            return {"success": False, "reason": "Identity locked"}
        
        # Check if active
        if not identity.is_active:
            return {"success": False, "reason": "Identity inactive"}
        
        # Verify credentials
        if not self._verify_credentials(identity, credentials):
            identity.failed_login_attempts += 1
            
            # Lock after too many failed attempts
            if identity.failed_login_attempts >= 5:
                identity.locked_until = datetime.now() + timedelta(minutes=30)
                self.logger.warning(f"Identity {agent_id} locked due to failed attempts")
            
            self._log_audit_event(
                agent_id=agent_id,
                event_type="authentication_failed",
                resource="identity",
                action="authenticate",
                outcome="failed",
                context={"reason": "Invalid credentials"}
            )
            
            return {"success": False, "reason": "Invalid credentials"}
        
        # Reset failed attempts on success
        identity.failed_login_attempts = 0
        identity.last_login = datetime.now()
        
        # Generate JWT token
        token = self._generate_token(identity)
        
        # Log successful authentication
        self._log_audit_event(
            agent_id=agent_id,
            event_type="authentication_success",
            resource="identity",
            action="authenticate",
            outcome="success",
            context=context or {}
        )
        
        return {
            "success": True,
            "token": token,
            "expires_at": (datetime.now() + self.token_expiry).isoformat(),
            "roles": list(identity.roles),
            "permissions": self._get_identity_permissions(identity)
        }
    
    def authorize(self, agent_id: str, resource: str, action: str,
                 access_level: AccessLevel, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Authorize an operation."""
        if agent_id not in self.identities:
            return {"authorized": False, "reason": "Identity not found"}
        
        identity = self.identities[agent_id]
        
        # Check if identity is active
        if not identity.is_active:
            return {"authorized": False, "reason": "Identity inactive"}
        
        # Get identity permissions
        permissions = self._get_identity_permissions(identity)
        
        # Check basic permission
        required_permission = f"{resource}:{action}"
        has_permission = ("*" in permissions or 
                         required_permission in permissions or
                         f"{resource}:*" in permissions or
                         f"*:{action}" in permissions)
        
        if not has_permission:
            self._log_audit_event(
                agent_id=agent_id,
                event_type="authorization_denied",
                resource=resource,
                action=action,
                outcome="denied",
                context={"reason": "Insufficient permissions"}
            )
            
            return {"authorized": False, "reason": "Insufficient permissions"}
        
        # Check access level
        has_access_level = any(
            role.has_access_level(access_level)
            for role_id in identity.roles
            for role in [self.roles.get(role_id)]
            if role
        )
        
        if not has_access_level:
            return {"authorized": False, "reason": "Insufficient access level"}
        
        # Check separation of duties
        context = context or {}
        context["agent_roles"] = list(identity.roles)
        
        for constraint_id in self.separation_of_duty.constraints:
            sod_result = self.separation_of_duty.check_constraint(
                constraint_id, agent_id, action, context
            )
            
            if sod_result["violated"]:
                self._log_audit_event(
                    agent_id=agent_id,
                    event_type="authorization_denied",
                    resource=resource,
                    action=action,
                    outcome="denied",
                    context={"reason": f"Separation of duty violation: {sod_result['reason']}"}
                )
                
                return {
                    "authorized": False,
                    "reason": f"Separation of duty violation: {sod_result['reason']}"
                }
        
        # Log successful authorization
        self._log_audit_event(
            agent_id=agent_id,
            event_type="authorization_granted",
            resource=resource,
            action=action,
            outcome="granted",
            context=context
        )
        
        return {"authorized": True, "reason": "Authorization granted"}
    
    def request_access(self, agent_id: str, resource: str, action: str,
                      access_level: AccessLevel, justification: str = "",
                      expires_in_hours: int = 24) -> str:
        """Request access to a resource."""
        request_id = secrets.token_urlsafe(16)
        
        access_request = AccessRequest(
            request_id=request_id,
            agent_id=agent_id,
            resource=resource,
            action=action,
            access_level=access_level,
            justification=justification,
            expires_at=datetime.now() + timedelta(hours=expires_in_hours)
        )
        
        self.access_requests[request_id] = access_request
        
        # Log request
        self._log_audit_event(
            agent_id=agent_id,
            event_type="access_requested",
            resource=resource,
            action=action,
            outcome="pending",
            context={"request_id": request_id, "justification": justification}
        )
        
        self.logger.info(f"Access request created: {request_id}")
        return request_id
    
    def approve_request(self, request_id: str, approved_by: str,
                        approved: bool, denial_reason: str = "") -> None:
        """Approve or deny an access request."""
        if request_id not in self.access_requests:
            raise ValueError(f"Request {request_id} not found")
        
        request = self.access_requests[request_id]
        
        if request.approved is not None:
            raise ValueError(f"Request {request_id} already processed")
        
        request.approved = approved
        request.approved_by = approved_by
        request.approved_at = datetime.now()
        
        if not approved:
            request.denial_reason = denial_reason
        
        # Log approval/denial
        self._log_audit_event(
            agent_id=approved_by,
            event_type="request_processed",
            resource="access_request",
            action="approve" if approved else "deny",
            outcome="approved" if approved else "denied",
            context={
                "request_id": request_id,
                "target_agent_id": request.agent_id,
                "denial_reason": denial_reason
            }
        )
        
        self.logger.info(f"Access request {request_id} {'approved' if approved else 'denied'}")
    
    def _verify_credentials(self, identity: AgentIdentity, credentials: Dict[str, Any]) -> bool:
        """Verify identity credentials."""
        if identity.authentication_method == AuthenticationMethod.PASSWORD:
            password = credentials.get("password")
            password_hash = identity.credentials.get("password_hash")
            
            if not password or not password_hash:
                return False
            
            return self._verify_password(password, password_hash)
        
        elif identity.authentication_method == AuthenticationMethod.TOKEN:
            token = credentials.get("token")
            stored_token = identity.credentials.get("token")
            
            return token == stored_token
        
        elif identity.authentication_method == AuthenticationMethod.CERTIFICATE:
            # Simplified certificate verification
            certificate = credentials.get("certificate")
            stored_cert = identity.credentials.get("certificate")
            
            return certificate == stored_cert
        
        return True  # Other methods would need specific verification
    
    def _hash_password(self, password: str) -> str:
        """Hash a password."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against hash."""
        return self._hash_password(password) == password_hash
    
    def _generate_token(self, identity: AgentIdentity) -> str:
        """Generate JWT token for identity."""
        payload = {
            "agent_id": identity.agent_id,
            "roles": list(identity.roles),
            "permissions": self._get_identity_permissions(identity),
            "exp": datetime.now() + self.token_expiry,
            "iat": datetime.now()
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")
    
    def _get_identity_permissions(self, identity: AgentIdentity) -> Set[str]:
        """Get all permissions for an identity."""
        permissions = set()
        
        for role_id in identity.roles:
            role = self.roles.get(role_id)
            if role:
                permissions.update(role.permissions)
        
        return permissions
    
    def _log_audit_event(self, agent_id: str, event_type: str, resource: str,
                        action: str, outcome: str, context: Dict[str, Any]) -> None:
        """Log an audit event."""
        event = AuditEvent(
            event_id=secrets.token_urlsafe(16),
            agent_id=agent_id,
            event_type=event_type,
            resource=resource,
            action=action,
            outcome=outcome,
            context=context
        )
        
        self.audit_events.append(event)
        
        # Keep only last 10000 events in memory
        if len(self.audit_events) > 10000:
            self.audit_events = self.audit_events[-10000:]
    
    def get_identity(self, agent_id: str) -> Optional[AgentIdentity]:
        """Get an identity by ID."""
        return self.identities.get(agent_id)
    
    def get_role(self, role_id: str) -> Optional[Role]:
        """Get a role by ID."""
        return self.roles.get(role_id)
    
    def list_identities(self) -> List[AgentIdentity]:
        """List all identities."""
        return list(self.identities.values())
    
    def list_roles(self) -> List[Role]:
        """List all roles."""
        return list(self.roles.values())
    
    def get_access_requests(self, agent_id: Optional[str] = None) -> List[AccessRequest]:
        """Get access requests, optionally filtered by agent."""
        requests = list(self.access_requests.values())
        
        if agent_id:
            requests = [r for r in requests if r.agent_id == agent_id]
        
        return requests
    
    def get_audit_events(self, agent_id: Optional[str] = None,
                        event_type: Optional[str] = None,
                        limit: int = 100) -> List[AuditEvent]:
        """Get audit events, optionally filtered."""
        events = self.audit_events.copy()
        
        if agent_id:
            events = [e for e in events if e.agent_id == agent_id]
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        # Return most recent events
        return sorted(events, key=lambda e: e.timestamp, reverse=True)[:limit]
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get IAM system status."""
        active_identities = [i for i in self.identities.values() if i.is_active]
        locked_identities = [i for i in self.identities.values() if i.is_locked()]
        pending_requests = [r for r in self.access_requests.values() if r.approved is None]
        
        return {
            "total_identities": len(self.identities),
            "active_identities": len(active_identities),
            "locked_identities": len(locked_identities),
            "total_roles": len(self.roles),
            "pending_requests": len(pending_requests),
            "total_audit_events": len(self.audit_events),
            "separation_of_duty_constraints": len(self.separation_of_duty.constraints)
        }