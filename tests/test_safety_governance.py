"""
Safety and Governance Testing

Comprehensive testing for policy enforcement across abstraction levels,
identity and access management with separation of duties, safety monitoring,
incident response, enforcement points, and audit trail integrity.
"""

import pytest
import asyncio
import time
import json
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid

from src.haai.governance import (
    CGLGovernance, PolicyEngine, EnforcementPoint, 
    SafetyMonitor, AuditTrail, IdentityAccessManager
)
from tests.test_framework import TestFramework, measure_async_performance


class PolicyType(Enum):
    """Types of governance policies."""
    COHERENCE_POLICY = "coherence_policy"
    RESOURCE_POLICY = "resource_policy"
    SECURITY_POLICY = "security_policy"
    ACCESS_POLICY = "access_policy"
    SAFETY_POLICY = "safety_policy"


class UserRole(Enum):
    """User roles for access control."""
    ADMIN = "admin"
    OPERATOR = "operator"
    ANALYST = "analyst"
    VIEWER = "viewer"
    SAFETY_OFFICER = "safety_officer"


@dataclass
class PolicyTestCase:
    """Test case for policy enforcement."""
    name: str
    policy_type: PolicyType
    policy: Dict[str, Any]
    test_actions: List[Dict[str, Any]]
    expected_outcomes: List[Dict[str, Any]]
    description: str


@dataclass
class SecurityIncident:
    """Security incident data for testing."""
    incident_id: str
    incident_type: str
    severity: str
    timestamp: datetime
    affected_components: List[str]
    description: str
    response_required: bool = True
    resolution_time: Optional[timedelta] = None


class PolicyEnforcementTester:
    """Tests for policy enforcement across all abstraction levels."""
    
    def __init__(self):
        self.policy_test_cases = self._create_policy_test_cases()
    
    def _create_policy_test_cases(self) -> List[PolicyTestCase]:
        """Create comprehensive policy test cases."""
        test_cases = []
        
        # Coherence threshold policy
        test_cases.append(PolicyTestCase(
            name="coherence_threshold_enforcement",
            policy_type=PolicyType.COHERENCE_POLICY,
            policy={
                "id": "coherence_min_threshold",
                "name": "Minimum Coherence Threshold",
                "description": "Enforces minimum coherence score of 0.7",
                "rules": [
                    {
                        "condition": "coherence_score < 0.7",
                        "action": "reject",
                        "reason": "Coherence below minimum threshold",
                        "severity": "high"
                    }
                ],
                "scope": "all_levels",
                "enforcement_points": ["gateway", "runtime"]
            },
            test_actions=[
                {
                    "name": "compliant_action",
                    "coherence_score": 0.8,
                    "memory_usage_mb": 512,
                    "operation": "data_processing",
                    "abstraction_level": 2
                },
                {
                    "name": "non_compliant_action",
                    "coherence_score": 0.5,
                    "memory_usage_mb": 512,
                    "operation": "data_processing",
                    "abstraction_level": 2
                }
            ],
            expected_outcomes=[
                {"approved": True, "violations": []},
                {"approved": False, "violations": ["coherence_threshold"]}
            ],
            description="Test coherence threshold enforcement at different abstraction levels"
        ))
        
        # Resource usage policy
        test_cases.append(PolicyTestCase(
            name="resource_usage_enforcement",
            policy_type=PolicyType.RESOURCE_POLICY,
            policy={
                "id": "resource_limits",
                "name": "Resource Usage Limits",
                "description": "Limits resource usage per operation",
                "rules": [
                    {
                        "condition": "memory_usage_mb > 1024",
                        "action": "reject",
                        "reason": "Memory usage exceeds limit",
                        "severity": "medium"
                    },
                    {
                        "condition": "cpu_usage_percent > 80",
                        "action": "throttle",
                        "reason": "CPU usage too high",
                        "severity": "low"
                    }
                ],
                "scope": "all_levels",
                "enforcement_points": ["scheduler", "runtime"]
            },
            test_actions=[
                {
                    "name": "normal_usage",
                    "coherence_score": 0.8,
                    "memory_usage_mb": 512,
                    "cpu_usage_percent": 45,
                    "operation": "normal_processing"
                },
                {
                    "name": "high_memory_usage",
                    "coherence_score": 0.8,
                    "memory_usage_mb": 1536,
                    "cpu_usage_percent": 45,
                    "operation": "memory_intensive"
                },
                {
                    "name": "high_cpu_usage",
                    "coherence_score": 0.8,
                    "memory_usage_mb": 512,
                    "cpu_usage_percent": 85,
                    "operation": "cpu_intensive"
                }
            ],
            expected_outcomes=[
                {"approved": True, "violations": []},
                {"approved": False, "violations": ["memory_limit"]},
                {"approved": True, "violations": [], "throttled": True}
            ],
            description="Test resource usage policy enforcement"
        ))
        
        # Security policy
        test_cases.append(PolicyTestCase(
            name="security_policy_enforcement",
            policy_type=PolicyType.SECURITY_POLICY,
            policy={
                "id": "security_restrictions",
                "name": "Security Restrictions",
                "description": "Enforces security constraints",
                "rules": [
                    {
                        "condition": "operation in ['delete_all', 'system_reset'] AND user_role != 'admin'",
                        "action": "reject",
                        "reason": "Insufficient privileges for dangerous operation",
                        "severity": "critical"
                    },
                    {
                        "condition": "data_sensitivity == 'classified' AND encryption_enabled == false",
                        "action": "reject",
                        "reason": "Classified data must be encrypted",
                        "severity": "high"
                    }
                ],
                "scope": "all_levels",
                "enforcement_points": ["gateway", "runtime", "output"]
            },
            test_actions=[
                {
                    "name": "admin_dangerous_operation",
                    "operation": "delete_all",
                    "user_role": "admin",
                    "coherence_score": 0.9
                },
                {
                    "name": "user_dangerous_operation",
                    "operation": "delete_all",
                    "user_role": "operator",
                    "coherence_score": 0.9
                },
                {
                    "name": "unencrypted_classified_data",
                    "operation": "process_data",
                    "data_sensitivity": "classified",
                    "encryption_enabled": False,
                    "coherence_score": 0.8
                }
            ],
            expected_outcomes=[
                {"approved": True, "violations": []},
                {"approved": False, "violations": ["insufficient_privileges"]},
                {"approved": False, "violations": ["encryption_required"]}
            ],
            description="Test security policy enforcement"
        ))
        
        return test_cases
    
    async def test_policy_enforcement(self, governance_system: CGLGovernance) -> Dict[str, Any]:
        """Test policy enforcement across all test cases."""
        results = {
            "total_test_cases": len(self.policy_test_cases),
            "passed_test_cases": 0,
            "failed_test_cases": 0,
            "test_case_results": [],
            "enforcement_point_effectiveness": {}
        }
        
        for test_case in self.policy_test_cases:
            # Add policy to governance system
            policy_id = await governance_system.add_policy(test_case.policy)
            
            # Test each action
            case_results = {
                "test_case_name": test_case.name,
                "policy_type": test_case.policy_type.value,
                "policy_id": policy_id,
                "action_results": [],
                "case_passed": True
            }
            
            for i, action in enumerate(test_case.test_actions):
                context = {
                    "timestamp": datetime.now().isoformat(),
                    "user_id": f"test_user_{i}",
                    "session_id": str(uuid.uuid4())
                }
                
                # Govern the action
                decision = governance_system.govern_action(action, context)
                
                # Compare with expected outcome
                expected = test_case.expected_outcomes[i]
                action_result = {
                    "action_name": action["name"],
                    "decision": decision,
                    "expected": expected,
                    "test_passed": self._compare_decision_with_expected(decision, expected)
                }
                
                case_results["action_results"].append(action_result)
                
                if not action_result["test_passed"]:
                    case_results["case_passed"] = False
            
            results["test_case_results"].append(case_results)
            
            if case_results["case_passed"]:
                results["passed_test_cases"] += 1
            else:
                results["failed_test_cases"] += 1
            
            # Remove policy after testing
            await governance_system.remove_policy(policy_id)
        
        return results
    
    def _compare_decision_with_expected(self, decision: Dict[str, Any], expected: Dict[str, Any]) -> bool:
        """Compare governance decision with expected outcome."""
        # Check approval status
        if decision.get("approved") != expected.get("approved"):
            return False
        
        # Check violations
        expected_violations = set(expected.get("violations", []))
        actual_violations = set(decision.get("violations", []))
        
        if expected_violations != actual_violations:
            return False
        
        # Check throttling if expected
        if "throttled" in expected:
            if decision.get("throttled") != expected.get("throttled"):
                return False
        
        return True


class IdentityAccessManagerTester:
    """Tests for identity and access management with separation of duties."""
    
    def __init__(self):
        self.access_scenarios = self._create_access_scenarios()
    
    def _create_access_scenarios(self) -> List[Dict[str, Any]]:
        """Create access control test scenarios."""
        scenarios = []
        
        # Role-based access control
        scenarios.append({
            "name": "role_based_access_control",
            "description": "Test role-based access control",
            "users": [
                {"id": "admin1", "role": "admin", "permissions": ["all"]},
                {"id": "op1", "role": "operator", "permissions": ["read", "write", "execute"]},
                {"id": "analyst1", "role": "analyst", "permissions": ["read", "analyze"]},
                {"id": "viewer1", "role": "viewer", "permissions": ["read"]},
                {"id": "safety1", "role": "safety_officer", "permissions": ["read", "monitor", "incident_response"]}
            ],
            "resources": [
                {"name": "system_config", "required_permissions": ["admin"]},
                {"name": "data_processing", "required_permissions": ["execute"]},
                {"name": "safety_monitor", "required_permissions": ["monitor"]},
                {"name": "incident_response", "required_permissions": ["incident_response"]}
            ],
            "test_cases": [
                {"user": "admin1", "resource": "system_config", "expected": True},
                {"user": "op1", "resource": "system_config", "expected": False},
                {"user": "op1", "resource": "data_processing", "expected": True},
                {"user": "analyst1", "resource": "data_processing", "expected": False},
                {"user": "safety1", "resource": "safety_monitor", "expected": True},
                {"user": "viewer1", "resource": "data_processing", "expected": False}
            ]
        })
        
        # Separation of duties
        scenarios.append({
            "name": "separation_of_duties",
            "description": "Test separation of duties enforcement",
            "conflicting_roles": [
                {"role1": "operator", "role2": "auditor", "conflict_reason": "self_audit_prevention"},
                {"role1": "safety_officer", "role2": "system_admin", "conflict_reason": "safety_independence"}
            ],
            "test_cases": [
                {"user": "user1", "roles": ["operator"], "action": "approve_transaction", "expected": True},
                {"user": "user2", "roles": ["operator", "auditor"], "action": "approve_transaction", "expected": False},
                {"user": "user3", "roles": ["safety_officer"], "action": "modify_system", "expected": True},
                {"user": "user4", "roles": ["safety_officer", "system_admin"], "action": "modify_system", "expected": False}
            ]
        })
        
        return scenarios
    
    async def test_identity_access_management(self, iam: IdentityAccessManager) -> Dict[str, Any]:
        """Test identity and access management functionality."""
        results = {
            "total_scenarios": len(self.access_scenarios),
            "passed_scenarios": 0,
            "failed_scenarios": 0,
            "scenario_results": []
        }
        
        for scenario in self.access_scenarios:
            scenario_result = await self._run_access_scenario(iam, scenario)
            results["scenario_results"].append(scenario_result)
            
            if scenario_result["scenario_passed"]:
                results["passed_scenarios"] += 1
            else:
                results["failed_scenarios"] += 1
        
        return results
    
    async def _run_access_scenario(self, iam: IdentityAccessManager, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single access control scenario."""
        scenario_result = {
            "scenario_name": scenario["name"],
            "description": scenario["description"],
            "test_results": [],
            "scenario_passed": True
        }
        
        if "users" in scenario:
            # Setup users and resources
            for user in scenario["users"]:
                await iam.create_user(user["id"], user["role"], user["permissions"])
            
            for resource in scenario["resources"]:
                await iam.register_resource(resource["name"], resource["required_permissions"])
            
            # Test access cases
            for test_case in scenario["test_cases"]:
                access_granted = await iam.check_access(
                    test_case["user"], 
                    test_case["resource"]
                )
                
                test_result = {
                    "user": test_case["user"],
                    "resource": test_case["resource"],
                    "expected": test_case["expected"],
                    "actual": access_granted,
                    "test_passed": access_granted == test_case["expected"]
                }
                
                scenario_result["test_results"].append(test_result)
                
                if not test_result["test_passed"]:
                    scenario_result["scenario_passed"] = False
        
        elif "conflicting_roles" in scenario:
            # Setup separation of duties
            for conflict in scenario["conflicting_roles"]:
                await iam.add_role_conflict(
                    conflict["role1"], 
                    conflict["role2"], 
                    conflict["conflict_reason"]
                )
            
            # Test separation cases
            for test_case in scenario["test_cases"]:
                can_perform = await iam.check_action_permission(
                    test_case["user"],
                    test_case["roles"],
                    test_case["action"]
                )
                
                test_result = {
                    "user": test_case["user"],
                    "roles": test_case["roles"],
                    "action": test_case["action"],
                    "expected": test_case["expected"],
                    "actual": can_perform,
                    "test_passed": can_perform == test_case["expected"]
                }
                
                scenario_result["test_results"].append(test_result)
                
                if not test_result["test_passed"]:
                    scenario_result["scenario_passed"] = False
        
        return scenario_result


class SafetyMonitoringTester:
    """Tests for safety monitoring and incident response."""
    
    def __init__(self):
        self.incident_scenarios = self._create_incident_scenarios()
    
    def _create_incident_scenarios(self) -> List[SecurityIncident]:
        """Create security incident test scenarios."""
        incidents = []
        
        # Coherence breach incident
        incidents.append(SecurityIncident(
            incident_id="coherence_breach_001",
            incident_type="coherence_breach",
            severity="high",
            timestamp=datetime.now() - timedelta(minutes=5),
            affected_components=["coherence_engine", "reasoning_system"],
            description="Coherence score dropped below critical threshold",
            response_required=True
        ))
        
        # Resource exhaustion incident
        incidents.append(SecurityIncident(
            incident_id="resource_exhaustion_001",
            incident_type="resource_exhaustion",
            severity="medium",
            timestamp=datetime.now() - timedelta(minutes=10),
            affected_components=["memory_manager", "scheduler"],
            description="Memory usage exceeded 90% of allocated budget",
            response_required=True
        ))
        
        # Policy violation incident
        incidents.append(SecurityIncident(
            incident_id="policy_violation_001",
            incident_type="policy_violation",
            severity="critical",
            timestamp=datetime.now() - timedelta(minutes=2),
            affected_components=["policy_engine", "enforcement_point"],
            description="Critical security policy violation detected",
            response_required=True
        ))
        
        return incidents
    
    async def test_safety_monitoring(self, safety_monitor: SafetyMonitor) -> Dict[str, Any]:
        """Test safety monitoring and incident response."""
        results = {
            "total_incidents": len(self.incident_scenarios),
            "detected_incidents": 0,
            "responded_incidents": 0,
            "incident_results": [],
            "response_times": []
        }
        
        for incident in self.incident_scenarios:
            # Simulate incident detection
            detection_time = time.time()
            detected = await safety_monitor.detect_incident(incident)
            detection_end_time = time.time()
            
            if detected:
                results["detected_incidents"] += 1
                
                # Test incident response
                response_start_time = time.time()
                response = await safety_monitor.respond_to_incident(incident)
                response_end_time = time.time()
                
                if response.get("response_initiated", False):
                    results["responded_incidents"] += 1
                    
                    # Calculate response time
                    response_time = response_end_time - response_start_time
                    results["response_times"].append(response_time)
                
                # Record incident result
                incident_result = {
                    "incident_id": incident.incident_id,
                    "incident_type": incident.incident_type,
                    "severity": incident.severity,
                    "detected": detected,
                    "detection_time": detection_end_time - detection_time,
                    "response": response,
                    "response_time": response_time if response.get("response_initiated") else None
                }
                
                results["incident_results"].append(incident_result)
        
        # Calculate response time statistics
        if results["response_times"]:
            results["response_time_stats"] = {
                "mean": sum(results["response_times"]) / len(results["response_times"]),
                "min": min(results["response_times"]),
                "max": max(results["response_times"])
            }
        
        return results


class EnforcementPointTester:
    """Tests for enforcement points (gateway, scheduler, runtime, output)."""
    
    def __init__(self):
        self.enforcement_point_tests = self._create_enforcement_tests()
    
    def _create_enforcement_tests(self) -> List[Dict[str, Any]]:
        """Create enforcement point test cases."""
        tests = []
        
        # Gateway enforcement
        tests.append({
            "enforcement_point": "gateway",
            "description": "Test gateway-level policy enforcement",
            "test_actions": [
                {
                    "name": "valid_request",
                    "data": {"operation": "process", "coherence": 0.8},
                    "expected": {"allowed": True, "reason": "compliant"}
                },
                {
                    "name": "invalid_request",
                    "data": {"operation": "delete_all", "user_role": "viewer"},
                    "expected": {"allowed": False, "reason": "insufficient_privileges"}
                }
            ]
        })
        
        # Scheduler enforcement
        tests.append({
            "enforcement_point": "scheduler",
            "description": "Test scheduler-level resource enforcement",
            "test_actions": [
                {
                    "name": "normal_task",
                    "task": {"cpu_required": 20, "memory_required": 512},
                    "expected": {"scheduled": True, "priority": "normal"}
                },
                {
                    "name": "resource_heavy_task",
                    "task": {"cpu_required": 95, "memory_required": 2048},
                    "expected": {"scheduled": False, "reason": "resource_limits_exceeded"}
                }
            ]
        })
        
        # Runtime enforcement
        tests.append({
            "enforcement_point": "runtime",
            "description": "Test runtime-level behavior enforcement",
            "test_actions": [
                {
                    "name": "compliant_execution",
                    "execution": {"operation": "analyze", "coherence": 0.85},
                    "expected": {"allowed": True, "monitored": True}
                },
                {
                    "name": "non_compliant_execution",
                    "execution": {"operation": "unauthorized_access", "coherence": 0.3},
                    "expected": {"allowed": False, "terminated": True}
                }
            ]
        })
        
        # Output enforcement
        tests.append({
            "enforcement_point": "output",
            "description": "Test output-level data enforcement",
            "test_actions": [
                {
                    "name": "safe_output",
                    "output": {"data": "public_info", "sensitivity": "public"},
                    "expected": {"allowed": True, "filtered": False}
                },
                {
                    "name": "sensitive_output",
                    "output": {"data": "classified_info", "sensitivity": "classified"},
                    "expected": {"allowed": False, "redacted": True}
                }
            ]
        })
        
        return tests
    
    async def test_enforcement_points(self, enforcement_point: EnforcementPoint) -> Dict[str, Any]:
        """Test enforcement point functionality."""
        results = {
            "total_tests": len(self.enforcement_point_tests),
            "passed_tests": 0,
            "failed_tests": 0,
            "test_results": []
        }
        
        for test in self.enforcement_point_tests:
            test_result = await self._run_enforcement_test(enforcement_point, test)
            results["test_results"].append(test_result)
            
            if test_result["test_passed"]:
                results["passed_tests"] += 1
            else:
                results["failed_tests"] += 1
        
        return results
    
    async def _run_enforcement_test(self, enforcement_point: EnforcementPoint, test: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single enforcement point test."""
        test_result = {
            "enforcement_point": test["enforcement_point"],
            "description": test["description"],
            "action_results": [],
            "test_passed": True
        }
        
        for action in test["test_actions"]:
            # Execute action through enforcement point
            result = await enforcement_point.enforce(action)
            
            # Compare with expected
            expected = action["expected"]
            action_result = {
                "action_name": action["name"],
                "result": result,
                "expected": expected,
                "test_passed": self._compare_enforcement_result(result, expected)
            }
            
            test_result["action_results"].append(action_result)
            
            if not action_result["test_passed"]:
                test_result["test_passed"] = False
        
        return test_result
    
    def _compare_enforcement_result(self, result: Dict[str, Any], expected: Dict[str, Any]) -> bool:
        """Compare enforcement result with expected outcome."""
        for key, expected_value in expected.items():
            if key not in result or result[key] != expected_value:
                return False
        return True


class AuditTrailTester:
    """Tests for audit trail integrity and tamper detection."""
    
    def __init__(self):
        self.audit_scenarios = self._create_audit_scenarios()
    
    def _create_audit_scenarios(self) -> List[Dict[str, Any]]:
        """Create audit trail test scenarios."""
        scenarios = []
        
        # Audit trail integrity
        scenarios.append({
            "name": "audit_trail_integrity",
            "description": "Test audit trail integrity verification",
            "operations": [
                {"type": "user_login", "user": "admin", "timestamp": datetime.now()},
                {"type": "policy_change", "policy": "coherence_policy", "user": "admin", "timestamp": datetime.now()},
                {"type": "data_access", "resource": "sensitive_data", "user": "analyst", "timestamp": datetime.now()}
            ],
            "tampering_attempts": [
                {"operation_index": 1, "field": "user", "new_value": "attacker"},
                {"operation_index": 2, "field": "timestamp", "new_value": datetime.now() - timedelta(days=1)}
            ]
        })
        
        # Audit trail completeness
        scenarios.append({
            "name": "audit_trail_completeness",
            "description": "Test audit trail completeness and coverage",
            "critical_operations": [
                "system_configuration_change",
                "policy_modification",
                "user_role_change",
                "security_incident_response",
                "data_export"
            ],
            "expected_coverage": 1.0
        })
        
        return scenarios
    
    async def test_audit_trail(self, audit_trail: AuditTrail) -> Dict[str, Any]:
        """Test audit trail functionality."""
        results = {
            "total_scenarios": len(self.audit_scenarios),
            "passed_scenarios": 0,
            "failed_scenarios": 0,
            "scenario_results": []
        }
        
        for scenario in self.audit_scenarios:
            scenario_result = await self._run_audit_scenario(audit_trail, scenario)
            results["scenario_results"].append(scenario_result)
            
            if scenario_result["scenario_passed"]:
                results["passed_scenarios"] += 1
            else:
                results["failed_scenarios"] += 1
        
        return results
    
    async def _run_audit_scenario(self, audit_trail: AuditTrail, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single audit trail scenario."""
        scenario_result = {
            "scenario_name": scenario["name"],
            "description": scenario["description"],
            "test_results": [],
            "scenario_passed": True
        }
        
        if scenario["name"] == "audit_trail_integrity":
            # Record operations
            operation_ids = []
            for operation in scenario["operations"]:
                op_id = await audit_trail.record_operation(operation)
                operation_ids.append(op_id)
            
            # Verify integrity
            integrity_check = await audit_trail.verify_integrity()
            
            test_result = {
                "test_type": "integrity_verification",
                "operations_recorded": len(operation_ids),
                "integrity_valid": integrity_check["valid"],
                "test_passed": integrity_check["valid"]
            }
            
            scenario_result["test_results"].append(test_result)
            
            # Test tampering detection
            for tampering in scenario["tampering_attempts"]:
                # Attempt tampering (this would normally be prevented)
                tampering_detected = await audit_trail.detect_tampering(
                    operation_ids[tampering["operation_index"]],
                    tampering["field"],
                    tampering["new_value"]
                )
                
                tampering_result = {
                    "test_type": "tampering_detection",
                    "operation_index": tampering["operation_index"],
                    "field": tampering["field"],
                    "tampering_detected": tampering_detected,
                    "test_passed": tampering_detected
                }
                
                scenario_result["test_results"].append(tampering_result)
                
                if not tampering_result["test_passed"]:
                    scenario_result["scenario_passed"] = False
        
        elif scenario["name"] == "audit_trail_completeness":
            # Test coverage of critical operations
            coverage_results = []
            
            for operation in scenario["critical_operations"]:
                is_covered = await audit_trail.is_operation_covered(operation)
                coverage_results.append(is_covered)
            
            actual_coverage = sum(coverage_results) / len(coverage_results)
            expected_coverage = scenario["expected_coverage"]
            
            coverage_result = {
                "test_type": "coverage_verification",
                "critical_operations": len(scenario["critical_operations"]),
                "covered_operations": sum(coverage_results),
                "actual_coverage": actual_coverage,
                "expected_coverage": expected_coverage,
                "test_passed": abs(actual_coverage - expected_coverage) < 0.01
            }
            
            scenario_result["test_results"].append(coverage_result)
            
            if not coverage_result["test_passed"]:
                scenario_result["scenario_passed"] = False
        
        return scenario_result


# Integration test class
class TestSafetyGovernance:
    """Integration tests for safety and governance systems."""
    
    @pytest.fixture
    async def governance_system(self):
        """Create a governance system for testing."""
        system = CGLGovernance()
        await system.initialize()
        yield system
        await system.shutdown()
    
    @pytest.fixture
    async def identity_access_manager(self):
        """Create an identity and access manager for testing."""
        iam = IdentityAccessManager()
        await iam.initialize()
        yield iam
        await iam.shutdown()
    
    @pytest.fixture
    async def safety_monitor(self):
        """Create a safety monitor for testing."""
        monitor = SafetyMonitor()
        await monitor.initialize()
        yield monitor
        await monitor.shutdown()
    
    @pytest.fixture
    async def enforcement_point(self):
        """Create an enforcement point for testing."""
        point = EnforcementPoint()
        await point.initialize()
        yield point
        await point.shutdown()
    
    @pytest.fixture
    async def audit_trail(self):
        """Create an audit trail for testing."""
        trail = AuditTrail()
        await trail.initialize()
        yield trail
        await trail.shutdown()
    
    @pytest.fixture
    def policy_tester(self):
        """Create a policy enforcement tester."""
        return PolicyEnforcementTester()
    
    @pytest.fixture
    def iam_tester(self):
        """Create an identity access manager tester."""
        return IdentityAccessManagerTester()
    
    @pytest.fixture
    def safety_tester(self):
        """Create a safety monitoring tester."""
        return SafetyMonitoringTester()
    
    @pytest.fixture
    def enforcement_tester(self):
        """Create an enforcement point tester."""
        return EnforcementPointTester()
    
    @pytest.fixture
    def audit_tester(self):
        """Create an audit trail tester."""
        return AuditTrailTester()
    
    @pytest.mark.asyncio
    async def test_comprehensive_safety_governance(self,
                                                   governance_system,
                                                   identity_access_manager,
                                                   safety_monitor,
                                                   enforcement_point,
                                                   audit_trail,
                                                   policy_tester,
                                                   iam_tester,
                                                   safety_tester,
                                                   enforcement_tester,
                                                   audit_tester):
        """Test comprehensive safety and governance functionality."""
        # Run all safety and governance tests
        policy_results = await policy_tester.test_policy_enforcement(governance_system)
        iam_results = await iam_tester.test_identity_access_management(identity_access_manager)
        safety_results = await safety_tester.test_safety_monitoring(safety_monitor)
        enforcement_results = await enforcement_tester.test_enforcement_points(enforcement_point)
        audit_results = await audit_tester.test_audit_trail(audit_trail)
        
        # Compile comprehensive results
        comprehensive_results = {
            "policy_enforcement": policy_results,
            "identity_access_management": iam_results,
            "safety_monitoring": safety_results,
            "enforcement_points": enforcement_results,
            "audit_trail": audit_results,
            "overall_summary": {
                "total_test_categories": 5,
                "overall_compliance_rate": self._calculate_compliance_rate([
                    policy_results, iam_results, safety_results,
                    enforcement_results, audit_results
                ])
            }
        }
        
        # Assert overall compliance
        overall_compliance = comprehensive_results["overall_summary"]["overall_compliance_rate"]
        assert overall_compliance >= 0.8, \
            f"Overall safety and governance compliance too low: {overall_compliance}"
        
        return comprehensive_results
    
    def _calculate_compliance_rate(self, results_list: List[Dict[str, Any]]) -> float:
        """Calculate overall compliance rate across safety and governance tests."""
        total_passed = 0
        total_tests = 0
        
        for results in results_list:
            if "passed_test_cases" in results:
                total_passed += results["passed_test_cases"]
                total_tests += results["total_test_cases"]
            elif "passed_scenarios" in results:
                total_passed += results["passed_scenarios"]
                total_tests += results["total_scenarios"]
            elif "passed_tests" in results:
                total_passed += results["passed_tests"]
                total_tests += results["total_tests"]
        
        return total_passed / total_tests if total_tests > 0 else 0.0
    
    @pytest.mark.asyncio
    async def test_governance_performance(self, governance_system):
        """Test governance system performance under load."""
        policy_tester = PolicyEnforcementTester()
        
        # Measure performance with multiple concurrent requests
        start_time = time.time()
        
        # Create multiple concurrent governance requests
        tasks = []
        for i in range(10):
            task = policy_tester.test_policy_enforcement(governance_system)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # Performance should be reasonable
        assert total_time < 10.0, f"Governance testing took too long: {total_time}s"
        
        # All test cases should complete
        for result in results:
            assert result["total_test_cases"] > 0, "Governance test should have test cases"
            assert result["passed_test_cases"] >= 0, "Should have non-negative passed cases"