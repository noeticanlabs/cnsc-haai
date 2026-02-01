"""
HAAI Testing Framework Core

Provides the foundational testing infrastructure for the HAAI system,
including test utilities, fixtures, and common testing patterns.
"""

import asyncio
import logging
import time
import uuid
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
import pytest
from datetime import datetime

# Configure test logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TestMetrics:
    """Metrics collected during test execution."""
    test_name: str
    start_time: float
    end_time: Optional[float] = None
    success: bool = False
    error_message: Optional[str] = None
    performance_data: Dict[str, Any] = field(default_factory=dict)
    coherence_data: Dict[str, Any] = field(default_factory=dict)
    resource_usage: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestConfiguration:
    """Configuration for test execution."""
    timeout_seconds: int = 30
    max_memory_mb: int = 1024
    coherence_threshold: float = 0.7
    performance_baseline: Dict[str, float] = field(default_factory=dict)
    enable_profiling: bool = True
    enable_logging: bool = True


class TestFramework:
    """
    Core testing framework for HAAI system validation.
    
    Provides utilities for:
    - Test lifecycle management
    - Performance measurement
    - Coherence validation
    - Resource monitoring
    - Error handling and reporting
    """
    
    def __init__(self, config: TestConfiguration = None):
        self.config = config or TestConfiguration()
        self.test_metrics: List[TestMetrics] = []
        self.current_test: Optional[TestMetrics] = None
        
    @asynccontextmanager
    async def test_context(self, test_name: str):
        """Context manager for test execution with metrics collection."""
        # Start test
        self.current_test = TestMetrics(
            test_name=test_name,
            start_time=time.time()
        )
        
        logger.info(f"🧪 Starting test: {test_name}")
        
        try:
            yield self.current_test
            # Test completed successfully
            self.current_test.end_time = time.time()
            self.current_test.success = True
            logger.info(f"✅ Test completed: {test_name}")
            
        except Exception as e:
            # Test failed
            self.current_test.end_time = time.time()
            self.current_test.success = False
            self.current_test.error_message = str(e)
            logger.error(f"❌ Test failed: {test_name} - {e}")
            raise
            
        finally:
            # Store metrics
            if self.current_test:
                self.test_metrics.append(self.current_test)
                self.current_test = None
    
    def record_performance_metric(self, key: str, value: Union[float, int]):
        """Record a performance metric for the current test."""
        if self.current_test:
            self.current_test.performance_data[key] = value
    
    def record_coherence_metric(self, key: str, value: Union[float, int]):
        """Record a coherence metric for the current test."""
        if self.current_test:
            self.current_test.coherence_data[key] = value
    
    def record_resource_usage(self, resource_type: str, value: Union[float, int]):
        """Record resource usage for the current test."""
        if self.current_test:
            self.current_test.resource_usage[resource_type] = value
    
    def get_test_summary(self) -> Dict[str, Any]:
        """Get summary of all executed tests."""
        total_tests = len(self.test_metrics)
        passed_tests = sum(1 for m in self.test_metrics if m.success)
        failed_tests = total_tests - passed_tests
        
        # Calculate performance statistics
        execution_times = [
            m.end_time - m.start_time 
            for m in self.test_metrics 
            if m.end_time is not None
        ]
        
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": passed_tests / total_tests if total_tests > 0 else 0,
            "average_execution_time": avg_execution_time,
            "test_details": [
                {
                    "name": m.test_name,
                    "success": m.success,
                    "execution_time": m.end_time - m.start_time if m.end_time else None,
                    "error": m.error_message,
                    "performance": m.performance_data,
                    "coherence": m.coherence_data,
                    "resources": m.resource_usage
                }
                for m in self.test_metrics
            ]
        }


class PropertyBasedTestGenerator:
    """
    Generates property-based tests for mathematical components.
    
    Creates test cases that verify mathematical properties and invariants
    across the HAAI system components.
    """
    
    def __init__(self, seed: int = None):
        import random
        self.random = random.Random(seed)
    
    def generate_coherence_test_cases(self, count: int = 100) -> List[Dict[str, Any]]:
        """Generate test cases for coherence validation."""
        test_cases = []
        
        for i in range(count):
            # Generate random coherence values
            coherence_score = self.random.uniform(0.0, 1.0)
            threshold = self.random.uniform(0.3, 0.9)
            
            # Generate random data
            data_size = self.random.randint(10, 1000)
            complexity = self.random.uniform(0.1, 1.0)
            
            test_cases.append({
                "id": f"coherence_test_{i}",
                "coherence_score": coherence_score,
                "threshold": threshold,
                "data_size": data_size,
                "complexity": complexity,
                "expected_decision": coherence_score >= threshold
            })
        
        return test_cases
    
    def generate_abstraction_test_cases(self, count: int = 100) -> List[Dict[str, Any]]:
        """Generate test cases for abstraction framework."""
        test_cases = []
        
        for i in range(count):
            # Generate hierarchical levels
            levels = self.random.randint(1, 5)
            
            # Generate abstraction parameters
            compression_ratio = self.random.uniform(0.1, 0.9)
            fidelity_threshold = self.random.uniform(0.5, 0.95)
            
            # Generate test data
            input_size = self.random.randint(100, 10000)
            
            test_cases.append({
                "id": f"abstraction_test_{i}",
                "levels": levels,
                "compression_ratio": compression_ratio,
                "fidelity_threshold": fidelity_threshold,
                "input_size": input_size,
                "expected_output_size": int(input_size * compression_ratio)
            })
        
        return test_cases
    
    def generate_reasoning_test_cases(self, count: int = 100) -> List[Dict[str, Any]]:
        """Generate test cases for reasoning engine."""
        test_cases = []
        
        reasoning_modes = ["sequential", "parallel", "hierarchical", "adaptive"]
        problem_types = ["analysis", "synthesis", "planning", "optimization"]
        
        for i in range(count):
            mode = self.random.choice(reasoning_modes)
            problem_type = self.random.choice(problem_types)
            
            # Generate problem parameters
            complexity = self.random.uniform(0.1, 1.0)
            constraints_count = self.random.randint(0, 5)
            
            test_cases.append({
                "id": f"reasoning_test_{i}",
                "mode": mode,
                "problem_type": problem_type,
                "complexity": complexity,
                "constraints_count": constraints_count
            })
        
        return test_cases


class PerformanceRegressionTester:
    """
    Tests for performance regression detection.
    
    Compares current performance against established baselines
    and detects performance degradation.
    """
    
    def __init__(self, baseline_file: str = "tests/performance_baselines.json"):
        self.baseline_file = baseline_file
        self.baselines = self._load_baselines()
    
    def _load_baselines(self) -> Dict[str, Dict[str, float]]:
        """Load performance baselines from file."""
        import json
        import os
        
        if os.path.exists(self.baseline_file):
            with open(self.baseline_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_baselines(self, measurements: Dict[str, Dict[str, float]]):
        """Save performance measurements as new baselines."""
        import json
        
        self.baselines.update(measurements)
        with open(self.baseline_file, 'w') as f:
            json.dump(self.baselines, f, indent=2)
    
    def check_regression(self, 
                        component: str, 
                        measurements: Dict[str, float],
                        tolerance: float = 0.1) -> Dict[str, Any]:
        """
        Check for performance regression against baselines.
        
        Args:
            component: Component name
            measurements: Current performance measurements
            tolerance: Allowed degradation tolerance (10% by default)
            
        Returns:
            Regression analysis results
        """
        if component not in self.baselines:
            return {
                "status": "no_baseline",
                "message": f"No baseline found for component {component}"
            }
        
        baseline = self.baselines[component]
        regressions = []
        improvements = []
        
        for metric, current_value in measurements.items():
            if metric in baseline:
                baseline_value = baseline[metric]
                change_ratio = (current_value - baseline_value) / baseline_value
                
                # For latency metrics, lower is better
                if "latency" in metric.lower() or "time" in metric.lower():
                    if change_ratio > tolerance:
                        regressions.append({
                            "metric": metric,
                            "baseline": baseline_value,
                            "current": current_value,
                            "degradation": f"{change_ratio * 100:.1f}%"
                        })
                    elif change_ratio < -tolerance:
                        improvements.append({
                            "metric": metric,
                            "baseline": baseline_value,
                            "current": current_value,
                            "improvement": f"{-change_ratio * 100:.1f}%"
                        })
                
                # For throughput metrics, higher is better
                elif "throughput" in metric.lower() or "rate" in metric.lower():
                    if change_ratio < -tolerance:
                        regressions.append({
                            "metric": metric,
                            "baseline": baseline_value,
                            "current": current_value,
                            "degradation": f"{-change_ratio * 100:.1f}%"
                        })
                    elif change_ratio > tolerance:
                        improvements.append({
                            "metric": metric,
                            "baseline": baseline_value,
                            "current": current_value,
                            "improvement": f"{change_ratio * 100:.1f}%"
                        })
        
        return {
            "status": "analyzed",
            "component": component,
            "regressions": regressions,
            "improvements": improvements,
            "has_regression": len(regressions) > 0
        }


# Test fixtures for pytest
@pytest.fixture
def test_framework():
    """Provide a test framework instance."""
    return TestFramework()


@pytest.fixture
def property_generator():
    """Provide a property-based test generator."""
    return PropertyBasedTestGenerator()


@pytest.fixture
def performance_tester():
    """Provide a performance regression tester."""
    return PerformanceRegressionTester()


@pytest.fixture
async def test_agent():
    """Provide a test HAAI agent."""
    from src.haai.agent import create_integrated_haai_agent
    
    agent = await create_integrated_haai_agent(
        agent_id=f"test_agent_{uuid.uuid4().hex[:8]}",
        config={"attention_budget": 100.0}
    )
    
    yield agent
    
    await agent.shutdown()


# Utility functions for testing
async def measure_async_performance(func: Callable, *args, **kwargs) -> Dict[str, Any]:
    """
    Measure performance of an async function.
    
    Returns:
        Dictionary with execution time, success status, and result
    """
    start_time = time.time()
    
    try:
        result = await func(*args, **kwargs)
        end_time = time.time()
        
        return {
            "success": True,
            "execution_time": end_time - start_time,
            "result": result,
            "error": None
        }
    except Exception as e:
        end_time = time.time()
        
        return {
            "success": False,
            "execution_time": end_time - start_time,
            "result": None,
            "error": str(e)
        }


def assert_coherence_threshold(coherence_score: float, threshold: float = 0.7):
    """Assert that coherence score meets minimum threshold."""
    assert coherence_score >= threshold, f"Coherence score {coherence_score} below threshold {threshold}"


def assert_performance_baseline(measurements: Dict[str, float], 
                              baselines: Dict[str, float],
                              tolerance: float = 0.1):
    """Assert that performance measurements meet baseline criteria."""
    for metric, value in measurements.items():
        if metric in baselines:
            baseline = baselines[metric]
            
            # For latency metrics (lower is better)
            if "latency" in metric.lower() or "time" in metric.lower():
                assert value <= baseline * (1 + tolerance), \
                    f"Latency metric {metric} {value} exceeds baseline {baseline} by more than {tolerance * 100}%"
            
            # For throughput metrics (higher is better)
            elif "throughput" in metric.lower() or "rate" in metric.lower():
                assert value >= baseline * (1 - tolerance), \
                    f"Throughput metric {metric} {value} below baseline {baseline} by more than {tolerance * 100}%"