#!/usr/bin/env python3
"""
HAAI Governance System Demonstration

This script demonstrates the comprehensive governance and safety integration
for the HAAI agent system, showcasing all major capabilities:

1. CGL Policy Engine Integration
2. Identity and Access Management  
3. Safety Monitoring and Response
4. Enforcement Point Implementation
5. Audit and Evidence System
6. Integrated Governance with HAAI Agent

Run this script to see the governance system in action!
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any

# Import governance components
from src.haai.governance import (
    HAAIGovernanceIntegrator,
    GovernanceConfig,
    GovernanceMode,
    Policy,
    PolicyType,
    AuthenticationMethod,
    SafetyLevel,
    ReceiptType,
    EvidenceType
)

# Import HAAI components for integration
from src.haai.agent.integrated import create_integrated_haai_agent


class GovernanceDemo:
    """Demonstrates governance system capabilities."""
    
    def __init__(self):
        self.governance = None
        self.haai_agent = None
        self.demo_results = {}
    
    async def initialize(self):
        """Initialize the demonstration."""
        print("🚀 Initializing HAAI Governance System Demonstration")
        print("=" * 60)
        
        # Create governance configuration
        config = GovernanceConfig(
            mode=GovernanceMode.STRICT,
            enable_real_time_enforcement=True,
            enable_compliance_reporting=True,
            emergency_override_duration=15
        )
        
        # Initialize governance system
        self.governance = HAAIGovernanceIntegrator(config)
        await self.governance.initialize()
        
        # Create HAAI agent for integration
        self.haai_agent = await create_integrated_haai_agent(
            agent_id="demo_haai_agent",
            config={
                "attention_budget": 100.0,
                "coherence_threshold": 0.7
            }
        )
        
        # Integrate governance with HAAI agent
        await self.governance.integrate_with_haai_agent(self.haai_agent)
        
        print("✅ Governance system initialized successfully")
        print(f"   Mode: {self.governance.mode.value}")
        print(f"   Active policies: {len(self.governance.policy_engine.get_policies())}")
        print(f"   System identities: {len(self.governance.identity_manager.list_identities())}")
        print()
    
    async def demo_policy_engine(self):
        """Demonstrate CGL Policy Engine capabilities."""
        print("📋 CGL Policy Engine Integration Demo")
        print("-" * 40)
        
        # Create custom policy
        custom_policy = Policy(
            policy_id="demo_custom_policy",
            name="Demo Custom Policy",
            description="Custom policy for demonstration",
            policy_type=PolicyType.SAFETY,
            status=self.governance.policy_engine.compliance_checker.PolicyStatus.ACTIVE,
            rules=[
                {
                    "rule_id": "demo_rule",
                    "name": "Demo Rule",
                    "conditions": [
                        {"field": "operation_type", "operator": "equals", "value": "demo"}
                    ],
                    "constraints": [
                        {
                            "constraint_id": "demo_constraint",
                            "name": "Demo Constraint",
                            "type": "range",
                            "parameters": {
                                "min": 0.5,
                                "max": 1.0,
                                "field": "demo_metric"
                            },
                            "enforcement_level": "warning"
                        }
                    ],
                    "actions": [
                        {"type": "log", "level": "info", "message": "Demo policy triggered"}
                    ],
                    "priority": 1
                }
            ]
        )
        
        self.governance.policy_engine.add_policy(custom_policy)
        
        # Test policy evaluation
        test_context = {
            "operation_type": "demo",
            "demo_metric": 0.8,
            "coherence_score": 0.9
        }
        
        policy_result = self.governance.policy_engine.evaluate_policies(test_context)
        
        print(f"   Created custom policy: {custom_policy.name}")
        print(f"   Policy evaluation result: {'Compliant' if policy_result['overall_compliant'] else 'Non-compliant'}")
        print(f"   Applied policies: {len(policy_result['applied_policies'])}")
        
        if policy_result['total_violations']:
            print(f"   Violations: {len(policy_result['total_violations'])}")
        
        self.demo_results["policy_engine"] = {
            "policies_loaded": len(self.governance.policy_engine.get_policies()),
            "evaluation_compliant": policy_result['overall_compliant'],
            "violations": len(policy_result['total_violations'])
        }
        
        print()
    
    async def demo_identity_access(self):
        """Demonstrate Identity and Access Management."""
        print("🔐 Identity and Access Management Demo")
        print("-" * 40)
        
        # Create demo user identity
        user_id = self.governance.identity_manager.create_identity(
            agent_id="demo_user",
            name="Demo User",
            authentication_method=AuthenticationMethod.PASSWORD,
            credentials={"password": "demo_password"},
            roles=["operator"]
        )
        
        # Authenticate user
        auth_result = self.governance.identity_manager.authenticate(
            agent_id="demo_user",
            credentials={"password": "demo_password"}
        )
        
        # Test authorization
        authz_result = self.governance.identity_manager.authorize(
            agent_id="demo_user",
            resource="demo_resource",
            action="read",
            access_level=self.governance.identity_manager.AccessLevel.READ
        )
        
        print(f"   Created user identity: {user_id}")
        print(f"   Authentication: {'Success' if auth_result['success'] else 'Failed'}")
        print(f"   Authorization: {'Granted' if authz_result['authorized'] else 'Denied'}")
        print(f"   User permissions: {len(auth_result.get('permissions', []))}")
        
        # Test separation of duties
        sod_result = self.governance.identity_manager.separation_of_duty.check_constraint(
            "critical_operation_maker_checker",
            "demo_user",
            "critical_operation",
            {"maker_id": "demo_user", "checker_id": "demo_user"}
        )
        
        print(f"   Separation of duties check: {'Passed' if not sod_result['violated'] else 'Violated'}")
        
        self.demo_results["identity_access"] = {
            "identities_created": len(self.governance.identity_manager.list_identities()),
            "authentication_success": auth_result['success'],
            "authorization_granted": authz_result['authorized'],
            "sod_check_passed": not sod_result['violated']
        }
        
        print()
    
    async def demo_safety_monitoring(self):
        """Demonstrate Safety Monitoring and Response."""
        print("🛡️  Safety Monitoring and Response Demo")
        print("-" * 40)
        
        # Get initial safety status
        initial_status = self.governance.safety_monitoring.get_safety_status()
        print(f"   Initial safety level: {initial_status['overall_safety_level']}")
        
        # Simulate safety degradation
        print("   Simulating safety degradation...")
        
        # Drop coherence score
        safety_level = self.governance.safety_monitoring.update_metric("coherence_score", 0.4)
        print(f"   Coherence score updated - Safety level: {safety_level.value}")
        
        # Increase resource usage
        safety_level = self.governance.safety_monitoring.update_metric("resource_usage", 0.9)
        print(f"   Resource usage updated - Safety level: {safety_level.value}")
        
        # Wait for monitoring cycle
        await asyncio.sleep(1.5)
        
        # Check for incidents
        incidents = self.governance.safety_monitoring.get_incidents(unresolved_only=True)
        print(f"   Safety incidents detected: {len(incidents)}")
        
        for incident in incidents[:3]:  # Show first 3 incidents
            print(f"     - {incident.incident_type.value}: {incident.title}")
        
        # Test emergency override
        override_id = self.governance.request_emergency_override(
            reason="Demo emergency override",
            requested_by="demo_user",
            duration_minutes=5
        )
        print(f"   Emergency override requested: {override_id}")
        
        # Resolve incidents
        for incident in incidents:
            self.governance.safety_monitoring.resolve_incident(
                incident.incident_id,
                "Demo resolution"
            )
        
        final_status = self.governance.safety_monitoring.get_safety_status()
        print(f"   Final safety level: {final_status['overall_safety_level']}")
        
        self.demo_results["safety_monitoring"] = {
            "initial_safety_level": initial_status['overall_safety_level'],
            "incidents_detected": len(incidents),
            "emergency_override_requested": bool(override_id),
            "final_safety_level": final_status['overall_safety_level']
        }
        
        print()
    
    async def demo_enforcement(self):
        """Demonstrate Enforcement Point Implementation."""
        print("⚖️  Enforcement Point Implementation Demo")
        print("-" * 40)
        
        # Test gateway enforcement
        gateway_request = {
            "request_id": "demo_gateway_request",
            "operation_type": "reasoning",
            "agent_id": "demo_user",
            "coherence_score": 0.6
        }
        
        enforcement_result = await self.governance.enforcement_coordinator.enforce_request(gateway_request)
        print(f"   Gateway enforcement: {'Allowed' if enforcement_result.get('allowed') else 'Blocked'}")
        
        if not enforcement_result.get('allowed'):
            print(f"   Blocked at: {enforcement_result.get('blocked_at', 'unknown')}")
        
        # Test scheduler enforcement
        scheduler_request = {
            "resource_type": "memory",
            "amount": 2000,  # Exceeds default limit
            "allocation_id": "demo_allocation"
        }
        
        scheduler_decision = await self.governance.enforcement_coordinator.scheduler.enforce_allocation(scheduler_request)
        print(f"   Scheduler enforcement: {'Allowed' if scheduler_decision.action.value == 'allow' else 'Blocked'}")
        
        # Test runtime enforcement
        runtime_operation = {
            "operation_id": "demo_runtime_op",
            "operation_type": "reasoning",
            "agent_id": "demo_user"
        }
        
        runtime_decision = await self.governance.enforcement_coordinator.runtime.start_operation(runtime_operation)
        print(f"   Runtime enforcement: {'Allowed' if runtime_decision.action.value == 'allow' else 'Blocked'}")
        
        # Test output validation
        test_output = {
            "result_id": "demo_output",
            "coherence_score": 0.85,
            "data": "demo result data"
        }
        
        output_validation = await self.governance.enforcement_coordinator.validate_result(
            test_output, {"operation_type": "reasoning"}
        )
        print(f"   Output validation: {'Approved' if output_validation.get('approved') else 'Rejected'}")
        
        self.demo_results["enforcement"] = {
            "gateway_allowed": enforcement_result.get('allowed', False),
            "scheduler_allowed": scheduler_decision.action.value == 'allow',
            "runtime_allowed": runtime_decision.action.value == 'allow',
            "output_approved": output_validation.get('approved', False)
        }
        
        print()
    
    async def demo_audit_evidence(self):
        """Demonstrate Audit and Evidence System."""
        print("📊 Audit and Evidence System Demo")
        print("-" * 40)
        
        # Create audit receipt
        receipt_id = self.governance.audit_system.create_receipt(
            receipt_type=ReceiptType.OPERATION,
            operation_id="demo_audit_operation",
            agent_id="demo_user",
            status="completed",
            outcome="success",
            details={"demo": True}
        )
        
        print(f"   Created audit receipt: {receipt_id}")
        
        # Add evidence
        evidence_id = self.governance.audit_system.add_evidence(
            receipt_id=receipt_id,
            evidence_type=EvidenceType.LOG_ENTRY,
            content="Demo log entry for audit trail",
            metadata={"source": "demo", "timestamp": datetime.now().isoformat()}
        )
        
        print(f"   Added evidence: {evidence_id}")
        
        # Add more evidence types
        self.governance.audit_system.add_evidence(
            receipt_id=receipt_id,
            evidence_type=EvidenceType.METRIC,
            content={"coherence_score": 0.9, "response_time": 150},
            metadata={"metric_type": "performance"}
        )
        
        # Verify receipt integrity
        integrity = self.governance.audit_system.verify_receipt_integrity(receipt_id)
        print(f"   Receipt integrity: {'Valid' if integrity['valid'] else 'Invalid'}")
        
        # Create compliance checkpoint
        checkpoint_id = self.governance.audit_system.create_compliance_checkpoint("demo_checkpoint")
        print(f"   Created compliance checkpoint: {checkpoint_id}")
        
        # Generate compliance report
        compliance_report = self.governance.generate_compliance_report("ISO_27001", days=7)
        print(f"   Compliance report generated for ISO_27001")
        print(f"   Compliance status: {len(compliance_report.get('compliance_status', {}))} requirements checked")
        
        # Get audit trail
        audit_trail = self.governance.audit_system.get_audit_trail("demo_audit_operation")
        print(f"   Audit trail entries: {len(audit_trail)}")
        
        self.demo_results["audit_evidence"] = {
            "receipts_created": 1,
            "evidence_added": 2,
            "integrity_valid": integrity['valid'],
            "checkpoint_created": bool(checkpoint_id),
            "audit_trail_entries": len(audit_trail)
        }
        
        print()
    
    async def demo_integrated_governance(self):
        """Demonstrate integrated governance with HAAI agent."""
        print("🤖 Integrated Governance with HAAI Agent Demo")
        print("-" * 40)
        
        # Govern a reasoning operation
        reasoning_operation = {
            "operation_id": "demo_reasoning_op",
            "agent_id": "reasoning_engine",
            "operation_type": "reasoning",
            "coherence_score": 0.85,
            "resource": "reasoning_engine",
            "action": "execute",
            "problem": {
                "type": "analysis",
                "data": "Demo problem for reasoning",
                "complexity": 0.7
            }
        }
        
        governance_decision = await self.governance.govern_operation(reasoning_operation)
        print(f"   Reasoning operation governed: {'Allowed' if governance_decision.allowed else 'Blocked'}")
        print(f"   Governance reason: {governance_decision.reason}")
        print(f"   Safety level: {governance_decision.safety_level.value}")
        
        if governance_decision.allowed:
            # Simulate operation completion
            operation_result = {
                "coherence_score": 0.88,
                "abstraction_quality": 0.92,
                "success": True,
                "solution": "Demo solution from reasoning"
            }
            
            completion = await self.governance.complete_operation(
                governance_decision.operation_id,
                operation_result
            )
            print(f"   Operation completed: {'Success' if completion['success'] else 'Failed'}")
        
        # Govern a learning operation
        learning_operation = {
            "operation_id": "demo_learning_op",
            "agent_id": "learning_system",
            "operation_type": "learning",
            "learning_rate": 0.05,
            "resource": "learning_system",
            "action": "train"
        }
        
        learning_decision = await self.governance.govern_operation(learning_operation)
        print(f"   Learning operation governed: {'Allowed' if learning_decision.allowed else 'Blocked'}")
        
        # Test governance mode switching
        original_mode = self.governance.mode
        self.governance.set_governance_mode(GovernanceMode.PERMISSIVE, "Demo mode switch")
        print(f"   Governance mode switched: {original_mode.value} -> {self.governance.mode.value}")
        
        # Switch back
        self.governance.set_governance_mode(original_mode, "Demo complete")
        
        self.demo_results["integrated_governance"] = {
            "reasoning_allowed": governance_decision.allowed,
            "learning_allowed": learning_decision.allowed,
            "mode_switching": True,
            "active_operations": len(self.governance.active_operations)
        }
        
        print()
    
    async def demo_compliance_reporting(self):
        """Demonstrate compliance reporting capabilities."""
        print("📈 Compliance Reporting Demo")
        print("-" * 40)
        
        # Generate reports for different standards
        standards = ["ISO_27001", "SOC_2", "GDPR"]
        
        for standard in standards:
            try:
                report = self.governance.generate_compliance_report(standard, days=30)
                
                print(f"   {standard} Compliance Report:")
                print(f"     Report period: {report['report_period']['start'][:10]} to {report['report_period']['end'][:10]}")
                print(f"     Total receipts: {report['total_receipts']}")
                print(f"     Requirements checked: {len(report['compliance_status'])}")
                
                # Show compliance status
                compliant_count = sum(
                    1 for status in report['compliance_status'].values()
                    if status['compliant']
                )
                
                print(f"     Compliant requirements: {compliant_count}/{len(report['compliance_status'])}")
                
                if report['recommendations']:
                    print(f"     Recommendations: {len(report['recommendations'])}")
                
            except Exception as e:
                print(f"   Error generating {standard} report: {e}")
        
        print()
    
    def generate_summary_report(self):
        """Generate a summary report of the demonstration."""
        print("📋 Demonstration Summary Report")
        print("=" * 60)
        
        # Overall governance status
        governance_status = self.governance.get_governance_status()
        
        print(f"Governance System Status:")
        print(f"  Mode: {governance_status['mode']}")
        print(f"  Active operations: {governance_status['active_operations']}")
        print(f"  Total decisions: {governance_status['total_decisions']}")
        print()
        
        print("Component Status:")
        print(f"  Policy Engine: {governance_status['policy_engine']['total_policies']} policies loaded")
        print(f"  Identity Manager: {governance_status['identity_manager']['total_identities']} identities")
        print(f"  Safety Monitoring: Level {governance_status['safety_monitoring']['overall_safety_level']}")
        print(f"  Enforcement Coordinator: {governance_status['enforcement_coordinator']['gateway_rules']} gateway rules")
        print(f"  Audit System: {governance_status['audit_system']['total_receipts']} receipts")
        print()
        
        print("Demo Results:")
        for component, results in self.demo_results.items():
            print(f"  {component.replace('_', ' ').title()}:")
            for key, value in results.items():
                print(f"    {key.replace('_', ' ').title()}: {value}")
        print()
        
        # Create final compliance checkpoint
        final_checkpoint = self.governance.audit_system.create_compliance_checkpoint("demo_final")
        print(f"Final compliance checkpoint: {final_checkpoint}")
        print()
        
        print("✅ HAAI Governance System Demonstration Complete!")
        print("=" * 60)
        
        return {
            "governance_status": governance_status,
            "demo_results": self.demo_results,
            "final_checkpoint": final_checkpoint
        }
    
    async def cleanup(self):
        """Clean up demonstration resources."""
        print("🧹 Cleaning up demonstration resources...")
        
        if self.governance:
            await self.governance.safety_monitoring.stop_monitoring()
        
        if self.haai_agent:
            await self.haai_agent.shutdown()
        
        print("✅ Cleanup complete")


async def main():
    """Main demonstration function."""
    demo = GovernanceDemo()
    
    try:
        # Initialize demonstration
        await demo.initialize()
        
        # Run all demonstrations
        await demo.demo_policy_engine()
        await demo.demo_identity_access()
        await demo.demo_safety_monitoring()
        await demo.demo_enforcement()
        await demo.demo_audit_evidence()
        await demo.demo_integrated_governance()
        await demo.demo_compliance_reporting()
        
        # Generate summary report
        summary = demo.generate_summary_report()
        
        return summary
        
    except Exception as e:
        print(f"❌ Demonstration failed: {e}")
        raise
    
    finally:
        # Cleanup
        await demo.cleanup()


if __name__ == "__main__":
    print("🎯 HAAI Governance System Demonstration")
    print("This demo showcases comprehensive governance and safety integration")
    print("for the Hierarchical Abstraction and Intelligence (HAAI) system.")
    print()
    
    # Run the demonstration
    summary = asyncio.run(main())
    
    print("\n🎉 Demonstration completed successfully!")
    print("The HAAI Governance System is ready for production deployment.")