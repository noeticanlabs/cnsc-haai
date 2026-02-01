"""
Comprehensive tests for HAAI Governance System

Tests all governance components including policy engine, identity management,
safety monitoring, enforcement, and audit systems.
"""

import asyncio
import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock

from src.haai.governance import (
    HAAIGovernanceIntegrator,
    GovernanceConfig,
    GovernanceMode,
    PolicyEngine,
    Policy,
    PolicyType,
    IdentityAccessManager,
    AuthenticationMethod,
    SafetyMonitoringSystem,
    SafetyLevel,
    AuditEvidenceSystem,
    ReceiptType,
    EvidenceType
)


class TestPolicyEngine:
    """Test the policy engine component."""
    
    def test_policy_creation(self):
        """Test creating and evaluating policies."""
        engine = PolicyEngine()
        
        # Create test policy
        policy = Policy(
            policy_id="test_policy",
            name="Test Policy",
            description="Test policy for unit testing",
            policy_type=PolicyType.SAFETY,
            status=engine.compliance_checker.PolicyStatus.ACTIVE,
            rules=[]
        )
        
        engine.add_policy(policy)
        
        # Verify policy was added
        retrieved_policy = engine.get_policy("test_policy")
        assert retrieved_policy is not None
        assert retrieved_policy.name == "Test Policy"
    
    def test_policy_evaluation(self):
        """Test policy evaluation."""
        engine = PolicyEngine()
        
        # Test context
        context = {
            "operation_type": "test_operation",
            "coherence_score": 0.8,
            "memory_usage_mb": 512
        }
        
        # Evaluate policies
        result = engine.evaluate_policies(context)
        
        assert "overall_compliant" in result
        assert "policy_results" in result
        assert "total_violations" in result


class TestIdentityAccessManager:
    """Test the identity and access management component."""
    
    def test_identity_creation(self):
        """Test creating agent identities."""
        iam = IdentityAccessManager()
        
        # Create test identity
        agent_id = iam.create_identity(
            agent_id="test_agent",
            name="Test Agent",
            authentication_method=AuthenticationMethod.TOKEN,
            credentials={"token": "test_token"},
            roles=["operator"]
        )
        
        assert agent_id == "test_agent"
        
        # Verify identity
        identity = iam.get_identity("test_agent")
        assert identity is not None
        assert identity.name == "Test Agent"
        assert "operator" in identity.roles
    
    def test_authentication(self):
        """Test agent authentication."""
        iam = IdentityAccessManager()
        
        # Create identity
        iam.create_identity(
            agent_id="test_agent",
            name="Test Agent",
            authentication_method=AuthenticationMethod.TOKEN,
            credentials={"token": "test_token"},
            roles=["operator"]
        )
        
        # Test authentication
        result = iam.authenticate(
            agent_id="test_agent",
            credentials={"token": "test_token"}
        )
        
        assert result["success"] is True
        assert "token" in result
        assert "permissions" in result
    
    def test_authorization(self):
        """Test agent authorization."""
        iam = IdentityAccessManager()
        
        # Create identity
        iam.create_identity(
            agent_id="test_agent",
            name="Test Agent",
            authentication_method=AuthenticationMethod.TOKEN,
            credentials={"token": "test_token"},
            roles=["operator"]
        )
        
        # Test authorization
        result = iam.authorize(
            agent_id="test_agent",
            resource="test_resource",
            action="read",
            access_level=iam.AccessLevel.READ
        )
        
        assert result["authorized"] is True


class TestSafetyMonitoringSystem:
    """Test the safety monitoring component."""
    
    def test_metric_creation(self):
        """Test creating safety metrics."""
        safety = SafetyMonitoringSystem()
        
        # Verify default metrics exist
        assert "coherence_score" in safety.metrics
        assert "resource_usage" in safety.metrics
        assert "abstraction_quality" in safety.metrics
    
    def test_metric_updates(self):
        """Test updating safety metrics."""
        safety = SafetyMonitoringSystem()
        
        # Update coherence score
        level = safety.update_metric("coherence_score", 0.6)
        assert level == SafetyLevel.WARNING
        
        # Check metric was updated
        metric = safety.metrics["coherence_score"]
        assert metric.current_value == 0.6
    
    def test_incident_detection(self):
        """Test safety incident detection."""
        safety = SafetyMonitoringSystem()
        
        # Trigger incident by dropping coherence
        safety.update_metric("coherence_score", 0.4)
        
        # Check for incidents
        incidents = safety.get_incidents(unresolved_only=True)
        assert len(incidents) > 0


class TestAuditEvidenceSystem:
    """Test the audit and evidence system."""
    
    def test_receipt_creation(self):
        """Test creating audit receipts."""
        audit = AuditEvidenceSystem()
        
        # Create receipt
        receipt_id = audit.create_receipt(
            receipt_type=ReceiptType.OPERATION,
            operation_id="test_operation",
            agent_id="test_agent",
            status="completed",
            outcome="success"
        )
        
        assert receipt_id is not None
        
        # Verify receipt
        receipt = audit.get_receipt(receipt_id)
        assert receipt is not None
        assert receipt.operation_id == "test_operation"
        assert receipt.agent_id == "test_agent"
    
    def test_evidence_addition(self):
        """Test adding evidence to receipts."""
        audit = AuditEvidenceSystem()
        
        # Create receipt
        receipt_id = audit.create_receipt(
            receipt_type=ReceiptType.OPERATION,
            operation_id="test_operation",
            agent_id="test_agent"
        )
        
        # Add evidence
        evidence_id = audit.add_evidence(
            receipt_id=receipt_id,
            evidence_type=EvidenceType.LOG_ENTRY,
            content="Test log entry",
            metadata={"source": "test"}
        )
        
        assert evidence_id is not None
        
        # Verify evidence
        receipt = audit.get_receipt(receipt_id)
        assert len(receipt.evidence) == 1
        assert receipt.evidence[0].content == "Test log entry"
    
    def test_receipt_integrity(self):
        """Test receipt integrity verification."""
        audit = AuditEvidenceSystem()
        
        # Create receipt
        receipt_id = audit.create_receipt(
            receipt_type=ReceiptType.OPERATION,
            operation_id="test_operation",
            agent_id="test_agent"
        )
        
        # Verify integrity
        integrity = audit.verify_receipt_integrity(receipt_id)
        assert integrity["valid"] is True


class TestIntegratedGovernance:
    """Test the integrated governance system."""
    
    @pytest.fixture
    async def governance(self):
        """Create governance system for testing."""
        config = GovernanceConfig(
            mode=GovernanceMode.STRICT,
            enable_real_time_enforcement=False  # Disable for testing
        )
        
        governance = HAAIGovernanceIntegrator(config)
        await governance.initialize()
        
        yield governance
        
        # Cleanup
        await governance.safety_monitoring.stop_monitoring()
    
    @pytest.mark.asyncio
    async def test_operation_governance(self, governance):
        """Test governing an operation."""
        operation = {
            "operation_id": "test_operation",
            "agent_id": "haai_core",
            "operation_type": "reasoning",
            "coherence_score": 0.9,
            "resource": "haai_operation",
            "action": "execute"
        }
        
        decision = await governance.govern_operation(operation)
        
        assert decision.operation_id == "test_operation"
        assert decision.agent_id == "haai_core"
        assert isinstance(decision.allowed, bool)
        assert decision.reason is not None
    
    @pytest.mark.asyncio
    async def test_operation_completion(self, governance):
        """Test completing an operation."""
        # First govern an operation
        operation = {
            "operation_id": "test_operation",
            "agent_id": "haai_core",
            "operation_type": "reasoning"
        }
        
        decision = await governance.govern_operation(operation)
        
        if decision.allowed:
            # Complete the operation
            result = {
                "coherence_score": 0.85,
                "abstraction_quality": 0.9,
                "success": True
            }
            
            completion = await governance.complete_operation("test_operation", result)
            assert completion["success"] is True
    
    def test_governance_status(self, governance):
        """Test getting governance status."""
        status = governance.get_governance_status()
        
        assert "mode" in status
        assert "active_operations" in status
        assert "policy_engine" in status
        assert "identity_manager" in status
        assert "safety_monitoring" in status
        assert "enforcement_coordinator" in status
        assert "audit_system" in status
    
    def test_mode_switching(self, governance):
        """Test switching governance modes."""
        original_mode = governance.mode
        
        # Switch to permissive mode
        governance.set_governance_mode(GovernanceMode.PERMISSIVE, "Testing")
        assert governance.mode == GovernanceMode.PERMISSIVE
        
        # Switch back
        governance.set_governance_mode(original_mode, "Testing complete")
        assert governance.mode == original_mode
    
    def test_emergency_override(self, governance):
        """Test emergency override functionality."""
        request_id = governance.request_emergency_override(
            reason="Test emergency",
            requested_by="test_user",
            duration_minutes=15
        )
        
        assert request_id is not None
        assert "override_" in request_id


class TestGovernanceIntegration:
    """Test governance integration with HAAI components."""
    
    @pytest.mark.asyncio
    async def test_haai_integration(self):
        """Test integration with HAAI agent."""
        # Create mock HAAI agent
        mock_agent = Mock()
        mock_agent.reasoning_engine = Mock()
        mock_agent.reasoning_engine.add_pre_execution_hook = Mock()
        mock_agent.reasoning_engine.add_post_execution_hook = Mock()
        mock_agent.learning_system = Mock()
        mock_agent.learning_system.add_learning_hook = Mock()
        mock_agent.attention_system = Mock()
        mock_agent.attention_system.add_allocation_hook = Mock()
        
        # Create governance system
        governance = HAAIGovernanceIntegrator()
        await governance.initialize()
        
        # Integrate with mock agent
        await governance.integrate_with_haai_agent(mock_agent)
        
        # Verify hooks were registered
        mock_agent.reasoning_engine.add_pre_execution_hook.assert_called()
        mock_agent.reasoning_engine.add_post_execution_hook.assert_called()
        mock_agent.learning_system.add_learning_hook.assert_called()
        mock_agent.attention_system.add_allocation_hook.assert_called()
        
        # Cleanup
        await governance.safety_monitoring.stop_monitoring()


class TestComplianceReporting:
    """Test compliance reporting functionality."""
    
    @pytest.mark.asyncio
    async def test_compliance_report_generation(self):
        """Test generating compliance reports."""
        governance = HAAIGovernanceIntegrator()
        await governance.initialize()
        
        # Generate report
        report = governance.generate_compliance_report("ISO_27001", days=7)
        
        assert "standard" in report
        assert "report_period" in report
        assert "compliance_status" in report
        assert "evidence_summary" in report
        
        # Cleanup
        await governance.safety_monitoring.stop_monitoring()


class TestPolicyConflicts:
    """Test policy conflict detection and resolution."""
    
    def test_policy_conflict_detection(self):
        """Test detecting policy conflicts."""
        engine = PolicyEngine()
        
        # Create conflicting policies
        policy1 = Policy(
            policy_id="conflict_policy_1",
            name="Conflict Policy 1",
            description="First conflicting policy",
            policy_type=PolicyType.SAFETY,
            status=engine.compliance_checker.PolicyStatus.ACTIVE,
            rules=[]
        )
        
        policy2 = Policy(
            policy_id="conflict_policy_2", 
            name="Conflict Policy 2",
            description="Second conflicting policy",
            policy_type=PolicyType.SAFETY,
            status=engine.compliance_checker.PolicyStatus.ACTIVE,
            rules=[]
        )
        
        # Add policies
        engine.add_policy(policy1)
        engine.add_policy(policy2)
        
        # Check for conflicts
        conflicts = engine.get_conflicts()
        assert isinstance(conflicts, list)


class TestSafetyIncidents:
    """Test safety incident handling."""
    
    @pytest.mark.asyncio
    async def test_safety_incident_lifecycle(self):
        """Test complete safety incident lifecycle."""
        safety = SafetyMonitoringSystem()
        
        # Trigger incident
        safety.update_metric("coherence_score", 0.3)
        
        # Get incidents
        incidents = safety.get_incidents(unresolved_only=True)
        assert len(incidents) > 0
        
        # Resolve incident
        incident_id = incidents[0].incident_id
        resolved = safety.resolve_incident(incident_id, "Test resolution")
        assert resolved is True
        
        # Verify resolution
        resolved_incidents = safety.get_incidents(unresolved_only=True)
        assert not any(i.incident_id == incident_id for i in resolved_incidents)


class TestEnforcementLevels:
    """Test multi-level enforcement."""
    
    @pytest.mark.asyncio
    async def test_gateway_enforcement(self):
        """Test gateway-level enforcement."""
        coordinator = HAAIGovernanceIntegrator().enforcement_coordinator
        
        # Test request
        request = {
            "request_id": "test_request",
            "operation_type": "test_operation",
            "agent_id": "test_agent"
        }
        
        result = await coordinator.enforce_request(request)
        
        assert "enforced" in result
        assert "allowed" in result
        assert "decisions" in result or "blocked_at" in result
    
    @pytest.mark.asyncio
    async def test_output_validation(self):
        """Test output-level enforcement."""
        coordinator = HAAIGovernanceIntegrator().enforcement_coordinator
        
        # Test result validation
        result = {
            "result_id": "test_result",
            "coherence_score": 0.9,
            "data": "test output"
        }
        
        context = {"operation_type": "test_operation"}
        
        validation = await coordinator.validate_result(result, context)
        
        assert "validated" in validation
        assert "approved" in validation
        assert "decision" in validation


# Performance Tests
class TestGovernancePerformance:
    """Test governance system performance."""
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test handling concurrent operations."""
        governance = HAAIGovernanceIntegrator()
        await governance.initialize()
        
        # Create multiple concurrent operations
        operations = []
        for i in range(10):
            operation = {
                "operation_id": f"concurrent_op_{i}",
                "agent_id": "haai_core",
                "operation_type": "reasoning",
                "coherence_score": 0.8 + (i * 0.01)
            }
            operations.append(governance.govern_operation(operation))
        
        # Wait for all to complete
        decisions = await asyncio.gather(*operations)
        
        # Verify all decisions were made
        assert len(decisions) == 10
        for decision in decisions:
            assert decision.operation_id.startswith("concurrent_op_")
        
        # Cleanup
        await governance.safety_monitoring.stop_monitoring()
    
    def test_memory_usage(self):
        """Test memory usage of governance components."""
        governance = HAAIGovernanceIntegrator()
        
        # Get initial status
        initial_status = governance.get_governance_status()
        
        # Simulate some operations
        for i in range(100):
            governance.governance_decisions.append({
                "decision_id": f"test_dec_{i}",
                "timestamp": datetime.now()
            })
        
        # Check status again
        final_status = governance.get_governance_status()
        
        # Verify decisions were tracked
        assert final_status["total_decisions"] >= initial_status["total_decisions"]


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])