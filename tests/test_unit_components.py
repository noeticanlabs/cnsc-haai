"""
Unit Tests for HAAI Components

Comprehensive unit tests for all individual components of the HAAI system:
- Coherence Engine
- Hierarchical Abstraction Framework
- NSC Stack (GLLL, GHLL, GML)
- Agent System Components
- Governance System
"""

import pytest
import asyncio
import time
import uuid
from typing import Dict, Any, List
import numpy as np

from src.haai.core import CoherenceEngine, HierarchicalAbstraction, ResidualProcessor, GateController
from src.haai.nsc import GLLLProcessor, GHLLProcessor, GMLProcessor, NSCCore
from src.haai.agent import ReasoningEngine, AttentionSystem, LearningSystem, ToolFramework
from src.haai.governance import CGLGovernance, PolicyEngine, EnforcementPoint

from tests.test_framework import (
    TestFramework, TestConfiguration, PropertyBasedTestGenerator,
    measure_async_performance, assert_coherence_threshold
)


class TestCoherenceEngine:
    """Unit tests for the Coherence Engine."""
    
    @pytest.fixture
    async def coherence_engine(self):
        """Create a coherence engine for testing."""
        engine = CoherenceEngine()
        await engine.initialize()
        yield engine
        await engine.shutdown()
    
    @pytest.mark.asyncio
    async def test_coherence_calculation(self, coherence_engine):
        """Test basic coherence calculation."""
        # Test data
        data = {
            "features": [0.1, 0.2, 0.3, 0.4],
            "weights": [0.25, 0.25, 0.25, 0.25]
        }
        
        coherence_score = await coherence_engine.calculate_coherence(data)
        
        assert isinstance(coherence_score, float)
        assert 0.0 <= coherence_score <= 1.0
        assert_coherence_threshold(coherence_score, 0.5)
    
    @pytest.mark.asyncio
    async def test_coherence_threshold_detection(self, coherence_engine):
        """Test coherence threshold detection."""
        # Test with high coherence data
        high_coherence_data = {
            "features": [0.5, 0.5, 0.5, 0.5],
            "weights": [0.25, 0.25, 0.25, 0.25]
        }
        
        high_score = await coherence_engine.calculate_coherence(high_coherence_data)
        assert high_score > 0.8
        
        # Test with low coherence data
        low_coherence_data = {
            "features": [0.1, 0.9, 0.1, 0.9],
            "weights": [0.25, 0.25, 0.25, 0.25]
        }
        
        low_score = await coherence_engine.calculate_coherence(low_coherence_data)
        assert low_score < 0.5
    
    @pytest.mark.asyncio
    async def test_coherence_budget_management(self, coherence_engine):
        """Test coherence budget management."""
        initial_budget = coherence_engine.get_budget()
        
        # Consume some budget
        consumption = 10.0
        success = coherence_engine.consume_budget(consumption)
        
        assert success is True
        assert coherence_engine.get_budget() == initial_budget - consumption
        
        # Try to consume more than available
        excess_consumption = initial_budget * 2
        success = coherence_engine.consume_budget(excess_consumption)
        
        assert success is False
    
    @pytest.mark.asyncio
    async def test_envelope_breach_detection(self, coherence_engine):
        """Test envelope breach detection."""
        # Set up envelope parameters
        coherence_engine.set_envelope_threshold(0.7)
        
        # Test within envelope
        normal_data = {"features": [0.6, 0.6, 0.6], "weights": [1/3, 1/3, 1/3]}
        result = await coherence_engine.check_envelope(normal_data)
        
        assert result["within_envelope"] is True
        assert result["breach_detected"] is False
        
        # Test envelope breach
        breach_data = {"features": [0.1, 0.1, 0.9], "weights": [1/3, 1/3, 1/3]}
        result = await coherence_engine.check_envelope(breach_data)
        
        assert result["within_envelope"] is False
        assert result["breach_detected"] is True
        assert "breach_magnitude" in result


class TestHierarchicalAbstraction:
    """Unit tests for the Hierarchical Abstraction Framework."""
    
    @pytest.fixture
    async def abstraction_framework(self):
        """Create an abstraction framework for testing."""
        framework = HierarchicalAbstraction()
        await framework.initialize()
        yield framework
        await framework.shutdown()
    
    @pytest.mark.asyncio
    async def test_level_creation(self, abstraction_framework):
        """Test creation of abstraction levels."""
        level_config = {
            "level": 2,
            "compression_ratio": 0.5,
            "fidelity_threshold": 0.8
        }
        
        level_id = await abstraction_framework.create_level(level_config)
        
        assert level_id is not None
        assert abstraction_framework.level_exists(level_id)
    
    @pytest.mark.asyncio
    async def test_abstraction_transformation(self, abstraction_framework):
        """Test data abstraction transformation."""
        # Create test data
        input_data = {
            "type": "raw_data",
            "content": list(range(100)),  # 100 data points
            "metadata": {"source": "test"}
        }
        
        # Perform abstraction
        result = await abstraction_framework.abstract(input_data, target_level=2)
        
        assert "abstracted_data" in result
        assert "compression_ratio" in result
        assert "fidelity_score" in result
        
        # Check compression
        assert len(result["abstracted_data"]) < len(input_data["content"])
        assert result["compression_ratio"] < 1.0
    
    @pytest.mark.asyncio
    async def test_level_switching(self, abstraction_framework):
        """Test abstraction level switching."""
        # Create multiple levels
        levels = []
        for i in range(3):
            config = {"level": i, "compression_ratio": 0.7 - i * 0.1}
            level_id = await abstraction_framework.create_level(config)
            levels.append(level_id)
        
        # Test switching between levels
        current_level = levels[0]
        for target_level in levels[1:]:
            switch_result = await abstraction_framework.switch_level(
                current_level, target_level
            )
            
            assert switch_result["success"] is True
            assert "transition_cost" in switch_result
            current_level = target_level
    
    @pytest.mark.asyncio
    async def test_abstraction_quality_metrics(self, abstraction_framework):
        """Test abstraction quality evaluation."""
        # Create test data with known structure
        input_data = {
            "type": "structured_data",
            "content": {
                "patterns": ["A", "B", "A", "C", "B", "A"],
                "values": [1, 2, 1, 3, 2, 1]
            }
        }
        
        # Abstract and evaluate quality
        result = await abstraction_framework.abstract_and_evaluate(input_data)
        
        assert "abstracted_data" in result
        assert "quality_metrics" in result
        
        quality = result["quality_metrics"]
        assert "information_retention" in quality
        assert "pattern_preservation" in quality
        assert "compression_efficiency" in quality
        
        # Quality should be reasonable
        assert quality["information_retention"] > 0.5
        assert quality["pattern_preservation"] > 0.5


class TestNSCStack:
    """Unit tests for the NSC Stack components."""
    
    @pytest.fixture
    async def glll_processor(self):
        """Create a GLLL processor for testing."""
        processor = GLLLProcessor()
        await processor.initialize()
        yield processor
        await processor.shutdown()
    
    @pytest.fixture
    async def ghll_processor(self):
        """Create a GHLL processor for testing."""
        processor = GHLLProcessor()
        await processor.initialize()
        yield processor
        await processor.shutdown()
    
    @pytest.fixture
    async def gml_processor(self):
        """Create a GML processor for testing."""
        processor = GMLProcessor()
        await processor.initialize()
        yield processor
        await processor.shutdown()
    
    @pytest.mark.asyncio
    async def test_glll_glyph_encoding(self, glll_processor):
        """Test GLLL glyph encoding."""
        # Test glyph data
        glyph_data = {
            "type": "hadamard_glyph",
            "components": [1, -1, 1, -1],
            "metadata": {"dimension": 4}
        }
        
        encoded = await glll_processor.encode_glyph(glyph_data)
        
        assert "encoded_data" in encoded
        assert "encoding_efficiency" in encoded
        assert encoded["encoding_success"] is True
    
    @pytest.mark.asyncio
    async def test_ghll_semantic_processing(self, ghll_processor):
        """Test GHLL semantic processing."""
        # Test semantic data
        semantic_data = {
            "type": "noetica_expression",
            "expression": "lambda x: f(g(x))",
            "context": {"domain": "functional_programming"}
        }
        
        processed = await ghll_processor.process_semantic(semantic_data)
        
        assert "processed_expression" in processed
        assert "semantic_analysis" in processed
        assert "type_inference" in processed
    
    @pytest.mark.asyncio
    async def test_gml_temporal_operations(self, gml_processor):
        """Test GML temporal operations."""
        # Test temporal data
        temporal_data = {
            "type": "phaseloom_thread",
            "events": [
                {"timestamp": 0, "action": "start"},
                {"timestamp": 1, "action": "process"},
                {"timestamp": 2, "action": "complete"}
            ]
        }
        
        result = await gml_processor.process_temporal(temporal_data)
        
        assert "temporal_analysis" in result
        assert "thread_state" in result
        assert "receipts" in result


class TestAgentComponents:
    """Unit tests for Agent System components."""
    
    @pytest.fixture
    async def reasoning_engine(self):
        """Create a reasoning engine for testing."""
        from src.haai.core import CoherenceEngine, HierarchicalAbstraction
        
        coherence_engine = CoherenceEngine()
        abstraction_framework = HierarchicalAbstraction()
        
        await coherence_engine.initialize()
        await abstraction_framework.initialize()
        
        engine = ReasoningEngine(coherence_engine, abstraction_framework)
        yield engine
        
        await coherence_engine.shutdown()
        await abstraction_framework.shutdown()
    
    @pytest.fixture
    async def attention_system(self):
        """Create an attention system for testing."""
        system = AttentionSystem(total_budget=100.0)
        await system.start()
        yield system
        await system.stop()
    
    @pytest.fixture
    async def learning_system(self):
        """Create a learning system for testing."""
        system = LearningSystem()
        await system.start_learning()
        yield system
        await system.stop_learning()
    
    @pytest.mark.asyncio
    async def test_reasoning_modes(self, reasoning_engine):
        """Test different reasoning modes."""
        problem = {
            "type": "analysis",
            "data": "Test problem for reasoning",
            "constraints": []
        }
        
        # Test sequential reasoning
        result = await reasoning_engine.reason(problem, mode="sequential")
        assert result["success"] is True
        assert "reasoning_steps" in result
        assert result["mode"] == "sequential"
        
        # Test parallel reasoning
        result = await reasoning_engine.reason(problem, mode="parallel")
        assert result["success"] is True
        assert "parallel_tasks" in result
        assert result["mode"] == "parallel"
        
        # Test hierarchical reasoning
        result = await reasoning_engine.reason(problem, mode="hierarchical")
        assert result["success"] is True
        assert "hierarchy_levels" in result
        assert result["mode"] == "hierarchical"
    
    @pytest.mark.asyncio
    async def test_attention_allocation(self, attention_system):
        """Test attention allocation mechanisms."""
        from src.haai.agent.attention import AttentionPriority
        
        # Request attention for high priority task
        demand_id = attention_system.request_attention(
            source="test_source",
            priority=AttentionPriority.HIGH,
            required_attention=20.0,
            expected_coherence_gain=0.8,
            computational_cost=0.3
        )
        
        assert demand_id is not None
        
        # Wait for allocation
        await asyncio.sleep(0.1)
        
        # Check allocation status
        status = attention_system.get_demand_status(demand_id)
        assert status["allocated"] is True
        
        # Release attention
        released = attention_system.release_attention(demand_id)
        assert released is True
    
    @pytest.mark.asyncio
    async def test_learning_receipt_processing(self, learning_system):
        """Test learning receipt processing."""
        from src.haai.agent.learning import ReceiptType
        
        # Add learning receipt
        receipt_id = learning_system.add_learning_receipt(
            receipt_type=ReceiptType.REASONING_RECEIPT,
            context={"problem_type": "analysis", "complexity": 0.7},
            action={"mode": "hierarchical"},
            outcome={"success": True, "coherence": 0.85},
            reward=0.85
        )
        
        assert receipt_id is not None
        
        # Get learning recommendations
        recommendations = learning_system.get_learning_recommendations({
            "problem_type": "analysis",
            "complexity": 0.7
        })
        
        assert "meta_learning" in recommendations
        assert "thresholds" in recommendations
        assert "strategies" in recommendations


class TestGovernanceSystem:
    """Unit tests for Governance System components."""
    
    @pytest.fixture
    async def governance_system(self):
        """Create a governance system for testing."""
        system = CGLGovernance()
        await system.initialize()
        yield system
        await system.shutdown()
    
    @pytest.mark.asyncio
    async def test_policy_enforcement(self, governance_system):
        """Test policy enforcement."""
        # Create test policy
        policy = {
            "id": "test_policy",
            "name": "Test Coherence Policy",
            "rules": [
                {
                    "condition": "coherence_score < 0.7",
                    "action": "reject",
                    "reason": "Coherence below threshold"
                }
            ]
        }
        
        # Add policy
        policy_id = await governance_system.add_policy(policy)
        assert policy_id is not None
        
        # Test compliant action
        compliant_action = {
            "coherence_score": 0.8,
            "memory_usage_mb": 512,
            "operation": "test_operation"
        }
        
        result = governance_system.govern_action(compliant_action, {})
        assert result["approved"] is True
        assert len(result["violations"]) == 0
        
        # Test non-compliant action
        non_compliant_action = {
            "coherence_score": 0.5,  # Below threshold
            "memory_usage_mb": 512,
            "operation": "test_operation"
        }
        
        result = governance_system.govern_action(non_compliant_action, {})
        assert result["approved"] is False
        assert len(result["violations"]) > 0
    
    @pytest.mark.asyncio
    async def test_audit_trail_integrity(self, governance_system):
        """Test audit trail integrity."""
        # Perform governed action
        action = {
            "coherence_score": 0.8,
            "memory_usage_mb": 512,
            "operation": "audit_test"
        }
        
        context = {
            "agent_id": "test_agent",
            "timestamp": time.time()
        }
        
        result = governance_system.govern_action(action, context)
        
        # Check audit trail
        audit_entries = governance_system.get_audit_trail(
            agent_id="test_agent",
            limit=10
        )
        
        assert len(audit_entries) > 0
        
        # Verify audit entry integrity
        latest_entry = audit_entries[0]
        assert "action" in latest_entry
        assert "decision" in latest_entry
        assert "timestamp" in latest_entry
        assert "agent_id" in latest_entry
        assert latest_entry["agent_id"] == "test_agent"


class TestPropertyBasedValidation:
    """Property-based tests for mathematical components."""
    
    @pytest.mark.asyncio
    async def test_coherence_properties(self, property_generator):
        """Test coherence mathematical properties."""
        test_cases = property_generator.generate_coherence_test_cases(50)
        
        coherence_engine = CoherenceEngine()
        await coherence_engine.initialize()
        
        for case in test_cases:
            # Test coherence calculation
            data = {
                "features": [case["coherence_score"]] * 4,
                "weights": [0.25] * 4
            }
            
            calculated_coherence = await coherence_engine.calculate_coherence(data)
            
            # Coherence should be in valid range
            assert 0.0 <= calculated_coherence <= 1.0
            
            # Decision should match expected
            decision = calculated_coherence >= case["threshold"]
            assert decision == case["expected_decision"]
        
        await coherence_engine.shutdown()
    
    @pytest.mark.asyncio
    async def test_abstraction_properties(self, property_generator):
        """Test abstraction mathematical properties."""
        test_cases = property_generator.generate_abstraction_test_cases(30)
        
        abstraction_framework = HierarchicalAbstraction()
        await abstraction_framework.initialize()
        
        for case in test_cases:
            # Create test data
            input_data = {
                "type": "test_data",
                "content": list(range(case["input_size"]))
            }
            
            # Perform abstraction
            result = await abstraction_framework.abstract(
                input_data, 
                target_level=case["levels"]
            )
            
            # Compression ratio should be reasonable
            actual_compression = len(result["abstracted_data"]) / case["input_size"]
            assert actual_compression <= case["compression_ratio"] + 0.1  # Allow tolerance
            
            # Fidelity should be above threshold
            assert result["fidelity_score"] >= case["fidelity_threshold"] - 0.1
        
        await abstraction_framework.shutdown()


# Performance regression tests
class TestPerformanceRegression:
    """Performance regression tests for critical components."""
    
    @pytest.mark.asyncio
    async def test_coherence_calculation_performance(self, performance_tester):
        """Test coherence calculation performance regression."""
        coherence_engine = CoherenceEngine()
        await coherence_engine.initialize()
        
        # Measure performance
        measurements = {}
        
        for size in [100, 1000, 10000]:
            data = {
                "features": list(np.random.random(size)),
                "weights": [1.0/size] * size
            }
            
            start_time = time.time()
            await coherence_engine.calculate_coherence(data)
            execution_time = time.time() - start_time
            
            measurements[f"coherence_calculation_size_{size}"] = execution_time
        
        # Check for regression
        regression_result = performance_tester.check_regression(
            "coherence_engine",
            measurements
        )
        
        # If no baseline exists, save current measurements
        if regression_result["status"] == "no_baseline":
            performance_tester.save_baselines({"coherence_engine": measurements})
        else:
            # Assert no significant regression
            assert not regression_result["has_regression"], \
                f"Performance regression detected: {regression_result['regressions']}"
        
        await coherence_engine.shutdown()