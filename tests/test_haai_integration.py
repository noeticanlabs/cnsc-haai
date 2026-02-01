"""
Comprehensive HAAI Integration Tests

Tests all major components of the HAAI system:
- Agent Core Architecture
- Reasoning Engine
- Attention Allocation System
- Learning and Adaptation
- Tool Integration Framework
- Integrated Agent Functionality
"""

import asyncio
import pytest
import logging
import time
from datetime import datetime

from src.haai.agent import (
    IntegratedHAAIAgent, 
    create_integrated_haai_agent,
    HAAIAgent,
    ReasoningEngine,
    AttentionSystem,
    LearningSystem,
    ToolFramework
)
from src.haai.agent.reasoning import ReasoningMode
from src.haai.agent.attention import AttentionPriority
from src.haai.agent.learning import ReceiptType
from src.haai.governance import CGLGovernance, Policy


# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestHAAIIntegration:
    """Test suite for HAAI integration."""
    
    @pytest.fixture
    async def integrated_agent(self):
        """Create an integrated HAAI agent for testing."""
        agent = await create_integrated_haai_agent(
            agent_id="test_agent",
            config={"attention_budget": 100.0}
        )
        yield agent
        await agent.shutdown()
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, integrated_agent):
        """Test that integrated agent initializes correctly."""
        assert integrated_agent is not None
        assert integrated_agent.agent_id == "test_agent"
        assert integrated_agent.is_fully_initialized is True
        assert integrated_agent.state.status.value == "active"
        
        # Check components are initialized
        assert integrated_agent.reasoning_engine is not None
        assert integrated_agent.attention_system is not None
        assert integrated_agent.learning_system is not None
        assert integrated_agent.tool_framework is not None
    
    @pytest.mark.asyncio
    async def test_hierarchical_reasoning(self, integrated_agent):
        """Test hierarchical reasoning capabilities."""
        problem = {
            "type": "analysis",
            "data": "Test problem for hierarchical reasoning",
            "constraints": ["coherence_check"],
            "required_depth": 3
        }
        
        result = await integrated_agent.demonstrate_hierarchical_reasoning(problem)
        
        assert result["demonstration"] == "hierarchical_reasoning"
        assert "results" in result
        assert "comparison" in result
        assert "best_mode" in result
        
        # Check that different reasoning modes were tested
        results = result["results"]
        assert "sequential" in results
        assert "parallel" in results
        assert "hierarchical" in results
        assert "adaptive" in results
        
        # Check that best mode was selected
        best_mode = result["best_mode"]
        assert best_mode in results
        
        logger.info(f"Hierarchical reasoning test passed. Best mode: {best_mode}")
    
    @pytest.mark.asyncio
    async def test_attention_allocation(self, integrated_agent):
        """Test attention allocation system."""
        tasks = [
            {"priority": "high", "attention_required": 15.0, "coherence_gain": 0.8},
            {"priority": "medium", "attention_required": 10.0, "coherence_gain": 0.6},
            {"priority": "low", "attention_required": 5.0, "coherence_gain": 0.3}
        ]
        
        result = await integrated_agent.demonstrate_attention_allocation(tasks)
        
        assert result["demonstration"] == "attention_allocation"
        assert "tasks" in result
        assert "results" in result
        assert "attention_status" in result
        
        # Check that all tasks were processed
        assert len(result["results"]) == len(tasks)
        
        # Check attention system status
        attention_status = result["attention_status"]
        assert "budget_status" in attention_status
        assert "hierarchical_analysis" in attention_status
        
        logger.info(f"Attention allocation test passed. Processed {len(tasks)} tasks")
    
    @pytest.mark.asyncio
    async def test_tool_integration(self, integrated_agent):
        """Test tool integration framework."""
        operations = [
            {
                "input_data": {"type": "json", "data": {"key": "test_value"}},
                "operation": "transform",
                "domain": "data_processing"
            },
            {
                "input_data": {"type": "json", "data": {"field": "validation_test"}},
                "operation": "validate",
                "domain": "data_quality"
            }
        ]
        
        result = await integrated_agent.demonstrate_tool_integration(operations)
        
        assert result["demonstration"] == "tool_integration"
        assert "operations" in result
        assert "results" in result
        assert "framework_status" in result
        assert "success_rate" in result
        
        # Check that operations were executed
        assert len(result["results"]) == len(operations)
        
        # Check success rate
        success_rate = result["success_rate"]
        assert 0 <= success_rate <= 1
        
        logger.info(f"Tool integration test passed. Success rate: {success_rate}")
    
    @pytest.mark.asyncio
    async def test_adaptive_learning(self, integrated_agent):
        """Test adaptive learning system."""
        experiences = [
            {
                "id": "exp1",
                "context": {"type": "reasoning", "complexity": 0.7},
                "action": {"mode": "hierarchical"},
                "outcome": {"success": True, "coherence": 0.85},
                "reward": 0.85
            },
            {
                "id": "exp2",
                "context": {"type": "attention", "priority": "high"},
                "action": {"allocation": "focused"},
                "outcome": {"success": True, "efficiency": 0.9},
                "reward": 0.9
            }
        ]
        
        result = await integrated_agent.demonstrate_adaptive_learning(experiences)
        
        assert result["demonstration"] == "adaptive_learning"
        assert "experiences" in result
        assert "recommendations" in result
        assert "learning_summary" in result
        
        # Check that recommendations were generated
        recommendations = result["recommendations"]
        assert len(recommendations) > 0
        
        # Check learning summary
        learning_summary = result["learning_summary"]
        assert "receipt_learning" in learning_summary
        assert "abstraction_optimizer" in learning_summary
        assert "threshold_tuner" in learning_summary
        
        logger.info(f"Adaptive learning test passed. Generated {len(recommendations)} recommendations")
    
    @pytest.mark.asyncio
    async def test_comprehensive_demonstration(self, integrated_agent):
        """Test comprehensive demonstration of all capabilities."""
        result = await integrated_agent.comprehensive_demonstration()
        
        assert result["demonstration_successful"] is True
        assert "reasoning" in result
        assert "attention" in result
        assert "tools" in result
        assert "learning" in result
        assert "overall_metrics" in result
        
        # Check overall metrics
        metrics = result["overall_metrics"]
        assert "total_demonstration_time" in metrics
        assert "components_demonstrated" in metrics
        assert "overall_coherence" in metrics
        assert "agent_health" in metrics
        
        # Verify all components were demonstrated
        assert metrics["components_demonstrated"] == 4
        
        # Check coherence and health scores
        assert 0 <= metrics["overall_coherence"] <= 1
        assert 0 <= metrics["agent_health"] <= 1
        
        logger.info(f"Comprehensive demonstration test passed. Time: {metrics['total_demonstration_time']:.2f}s")


class TestIndividualComponents:
    """Test individual HAAI components."""
    
    @pytest.mark.asyncio
    async def test_reasoning_engine_standalone(self):
        """Test reasoning engine as standalone component."""
        from src.haai.core import CoherenceEngine, HierarchicalAbstraction
        
        coherence_engine = CoherenceEngine()
        hierarchical_abstraction = HierarchicalAbstraction()
        
        await coherence_engine.initialize()
        await hierarchical_abstraction.initialize()
        
        reasoning_engine = ReasoningEngine(coherence_engine, hierarchical_abstraction)
        
        problem = {
            "type": "analysis",
            "data": "Test problem for reasoning engine",
            "constraints": []
        }
        
        result = await reasoning_engine.reason(problem)
        
        assert "success" in result
        assert "metrics" in result
        assert "reasoning_steps" in result
        
        logger.info("Standalone reasoning engine test passed")
    
    @pytest.mark.asyncio
    async def test_attention_system_standalone(self):
        """Test attention system as standalone component."""
        attention_system = AttentionSystem(total_budget=50.0)
        
        await attention_system.start()
        
        # Request attention
        demand_id = attention_system.request_attention(
            source="test",
            priority=AttentionPriority.HIGH,
            required_attention=10.0,
            expected_coherence_gain=0.7,
            computational_cost=0.2
        )
        
        assert demand_id is not None
        
        # Wait for processing
        await asyncio.sleep(0.5)
        
        # Get status
        status = attention_system.get_system_status()
        assert "budget_status" in status
        assert "hierarchical_analysis" in status
        
        # Release attention
        released = attention_system.release_attention(demand_id)
        assert released is True
        
        await attention_system.stop()
        
        logger.info("Standalone attention system test passed")
    
    @pytest.mark.asyncio
    async def test_learning_system_standalone(self):
        """Test learning system as standalone component."""
        learning_system = LearningSystem()
        
        await learning_system.start_learning()
        
        # Add learning receipt
        receipt_id = learning_system.add_learning_receipt(
            receipt_type=ReceiptType.REASONING_RECEIPT,
            context={"type": "test", "complexity": 0.5},
            action={"mode": "sequential"},
            outcome={"success": True, "coherence": 0.8},
            reward=0.8
        )
        
        assert receipt_id is not None
        
        # Get recommendations
        recommendations = learning_system.get_learning_recommendations({
            "type": "test",
            "complexity": 0.5
        })
        
        assert "meta_learning" in recommendations
        assert "thresholds" in recommendations
        
        # Get summary
        summary = learning_system.get_learning_summary()
        assert "receipt_learning" in summary
        assert "abstraction_optimizer" in summary
        
        await learning_system.stop_learning()
        
        logger.info("Standalone learning system test passed")
    
    @pytest.mark.asyncio
    async def test_tool_framework_standalone(self):
        """Test tool framework as standalone component."""
        tool_framework = ToolFramework()
        
        await tool_framework.initialize()
        
        # Execute a task
        result = await tool_framework.execute_task(
            input_data={"type": "json", "data": {"test": "value"}},
            operation="transform",
            domain="data_processing"
        )
        
        assert "success" in result
        assert "tool_id" in result
        assert "execution_id" in result
        
        # Get framework status
        status = tool_framework.get_framework_status()
        assert "registry" in status
        assert "selector" in status
        assert "executor" in status
        
        await tool_framework.shutdown()
        
        logger.info("Standalone tool framework test passed")
    
    @pytest.mark.asyncio
    async def test_governance_system(self):
        """Test CGL governance system."""
        governance = CGLGovernance()
        
        await governance.initialize()
        
        # Test governing an action
        action = {
            "coherence_score": 0.8,
            "memory_usage_mb": 512,
            "operation": "test_action"
        }
        
        context = {
            "agent_id": "test_agent",
            "timestamp": datetime.now().isoformat()
        }
        
        result = governance.govern_action(action, context)
        
        assert "governed" in result
        assert "approved" in result
        assert "compliance" in result
        
        # Should be approved (coherence > 0.7, memory < 1024)
        assert result["approved"] is True
        
        # Test with non-compliant action
        bad_action = {
            "coherence_score": 0.5,  # Below threshold
            "memory_usage_mb": 2048,  # Above limit
            "operation": "bad_action"
        }
        
        bad_result = governance.govern_action(bad_action, context)
        assert bad_result["approved"] is False
        assert "violations" in bad_result
        
        await governance.shutdown()
        
        logger.info("Governance system test passed")


class TestPerformanceAndScalability:
    """Test performance and scalability aspects."""
    
    @pytest.mark.asyncio
    async def test_concurrent_reasoning(self):
        """Test concurrent reasoning operations."""
        from src.haai.core import CoherenceEngine, HierarchicalAbstraction
        
        coherence_engine = CoherenceEngine()
        hierarchical_abstraction = HierarchicalAbstraction()
        
        await coherence_engine.initialize()
        await hierarchical_abstraction.initialize()
        
        reasoning_engine = ReasoningEngine(coherence_engine, hierarchical_abstraction)
        
        # Create multiple reasoning tasks
        tasks = []
        for i in range(5):
            problem = {
                "type": "analysis",
                "data": f"Test problem {i}",
                "constraints": []
            }
            tasks.append(reasoning_engine.reason(problem))
        
        # Execute concurrently
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        execution_time = time.time() - start_time
        
        # Check all completed successfully
        assert len(results) == 5
        for result in results:
            assert "success" in result
        
        # Check performance (should be faster than sequential)
        assert execution_time < 5.0  # Should complete in under 5 seconds
        
        logger.info(f"Concurrent reasoning test passed. Time: {execution_time:.2f}s")
    
    @pytest.mark.asyncio
    async def test_memory_usage(self):
        """Test memory usage and cleanup."""
        agent = await create_integrated_haai_agent(
            agent_id="memory_test_agent"
        )
        
        # Get initial memory state
        initial_state = agent.get_state_snapshot()
        
        # Run some operations
        await agent.demonstrate_hierarchical_reasoning({
            "type": "analysis",
            "data": "Memory test problem"
        })
        
        # Check memory usage
        current_state = agent.get_state_snapshot()
        resource_usage = current_state["resource_usage"]
        
        # Should have reasonable memory usage
        assert resource_usage["memory_mb"] < 1000  # Less than 1GB
        
        await agent.shutdown()
        
        logger.info("Memory usage test passed")


# Integration test runner
async def run_integration_tests():
    """Run all integration tests."""
    logger.info("Starting HAAI Integration Tests")
    
    # Create test agent
    agent = await create_integrated_haai_agent(
        agent_id="integration_test_agent",
        config={"attention_budget": 100.0}
    )
    
    try:
        # Run comprehensive demonstration
        logger.info("Running comprehensive demonstration...")
        result = await agent.comprehensive_demonstration()
        
        if result["demonstration_successful"]:
            logger.info("✅ Comprehensive demonstration PASSED")
            
            # Print summary
            metrics = result["overall_metrics"]
            logger.info(f"📊 Demonstration Summary:")
            logger.info(f"   Total Time: {metrics['total_demonstration_time']:.2f}s")
            logger.info(f"   Components Demonstrated: {metrics['components_demonstrated']}")
            logger.info(f"   Overall Coherence: {metrics['overall_coherence']:.3f}")
            logger.info(f"   Agent Health: {metrics['agent_health']:.3f}")
            logger.info(f"   Reasoning Success: {metrics['reasoning_success']:.3f}")
            logger.info(f"   Attention Efficiency: {metrics['attention_efficiency']:.3f}")
            logger.info(f"   Tool Success Rate: {metrics['tool_success_rate']:.3f}")
            logger.info(f"   Learning Adaptations: {metrics['learning_adaptations']}")
            
        else:
            logger.error("❌ Comprehensive demonstration FAILED")
            logger.error(f"Error: {result.get('error', 'Unknown error')}")
    
    finally:
        await agent.shutdown()
    
    logger.info("HAAI Integration Tests completed")


if __name__ == "__main__":
    # Run integration tests directly
    asyncio.run(run_integration_tests())