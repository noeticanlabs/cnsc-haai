"""
Coherence Validation Framework

Comprehensive testing framework for validating coherence measures,
envelope breach detection, budget management, and signal processing.
"""

import pytest
import asyncio
import time
import numpy as np
from typing import Dict, Any, List, Tuple
import matplotlib.pyplot as plt
from dataclasses import dataclass
from datetime import datetime

from src.haai.core import CoherenceEngine
from tests.test_framework import TestFramework, TestConfiguration, measure_async_performance


@dataclass
class CoherenceBenchmark:
    """Benchmark data for coherence validation."""
    name: str
    input_data: Dict[str, Any]
    expected_coherence_range: Tuple[float, float]
    description: str
    complexity_level: float
    data_size: int


class CoherenceValidationFramework:
    """
    Framework for validating coherence measures and related functionality.
    
    Provides comprehensive testing for:
    - Coherence measure validation against known benchmarks
    - Envelope breach detection and response
    - Coherence budget management under load
    - Risk state transitions and hysteresis
    - Coherence signal processing validation
    """
    
    def __init__(self):
        self.benchmarks = self._create_benchmarks()
        self.validation_results: List[Dict[str, Any]] = []
    
    def _create_benchmarks(self) -> List[CoherenceBenchmark]:
        """Create known coherence benchmarks for validation."""
        benchmarks = []
        
        # Perfect coherence benchmark
        benchmarks.append(CoherenceBenchmark(
            name="perfect_coherence",
            input_data={
                "features": [0.5, 0.5, 0.5, 0.5],
                "weights": [0.25, 0.25, 0.25, 0.25]
            },
            expected_coherence_range=(0.95, 1.0),
            description="Perfectly coherent data with uniform values",
            complexity_level=0.1,
            data_size=4
        ))
        
        # High coherence benchmark
        benchmarks.append(CoherenceBenchmark(
            name="high_coherence",
            input_data={
                "features": [0.6, 0.65, 0.7, 0.75],
                "weights": [0.25, 0.25, 0.25, 0.25]
            },
            expected_coherence_range=(0.8, 0.95),
            description="High coherence with similar values",
            complexity_level=0.3,
            data_size=4
        ))
        
        # Medium coherence benchmark
        benchmarks.append(CoherenceBenchmark(
            name="medium_coherence",
            input_data={
                "features": [0.3, 0.5, 0.7, 0.9],
                "weights": [0.25, 0.25, 0.25, 0.25]
            },
            expected_coherence_range=(0.5, 0.8),
            description="Medium coherence with varied values",
            complexity_level=0.6,
            data_size=4
        ))
        
        # Low coherence benchmark
        benchmarks.append(CoherenceBenchmark(
            name="low_coherence",
            input_data={
                "features": [0.1, 0.9, 0.1, 0.9],
                "weights": [0.25, 0.25, 0.25, 0.25]
            },
            expected_coherence_range=(0.0, 0.5),
            description="Low coherence with alternating values",
            complexity_level=0.9,
            data_size=4
        ))
        
        # Large dataset benchmark
        large_features = np.random.normal(0.5, 0.1, 1000).tolist()
        benchmarks.append(CoherenceBenchmark(
            name="large_dataset_coherence",
            input_data={
                "features": large_features,
                "weights": [1.0/1000] * 1000
            },
            expected_coherence_range=(0.7, 0.9),
            description="Large dataset with normal distribution",
            complexity_level=0.4,
            data_size=1000
        ))
        
        return benchmarks
    
    async def validate_coherence_measures(self, coherence_engine: CoherenceEngine) -> Dict[str, Any]:
        """Validate coherence measures against known benchmarks."""
        validation_results = {
            "total_benchmarks": len(self.benchmarks),
            "passed_benchmarks": 0,
            "failed_benchmarks": 0,
            "benchmark_results": [],
            "accuracy_metrics": {}
        }
        
        for benchmark in self.benchmarks:
            # Calculate coherence
            coherence_score = await coherence_engine.calculate_coherence(benchmark.input_data)
            
            # Check if within expected range
            min_expected, max_expected = benchmark.expected_coherence_range
            within_range = min_expected <= coherence_score <= max_expected
            
            # Calculate deviation from center of expected range
            expected_center = (min_expected + max_expected) / 2
            deviation = abs(coherence_score - expected_center)
            
            result = {
                "benchmark_name": benchmark.name,
                "description": benchmark.description,
                "calculated_coherence": coherence_score,
                "expected_range": benchmark.expected_coherence_range,
                "within_range": within_range,
                "deviation": deviation,
                "complexity_level": benchmark.complexity_level,
                "data_size": benchmark.data_size
            }
            
            validation_results["benchmark_results"].append(result)
            
            if within_range:
                validation_results["passed_benchmarks"] += 1
            else:
                validation_results["failed_benchmarks"] += 1
        
        # Calculate accuracy metrics
        validation_results["accuracy_metrics"] = {
            "pass_rate": validation_results["passed_benchmarks"] / validation_results["total_benchmarks"],
            "average_deviation": np.mean([r["deviation"] for r in validation_results["benchmark_results"]]),
            "max_deviation": max([r["deviation"] for r in validation_results["benchmark_results"]])
        }
        
        return validation_results


class EnvelopeBreachTester:
    """Tests for envelope breach detection and response."""
    
    def __init__(self):
        self.breach_scenarios = self._create_breach_scenarios()
    
    def _create_breach_scenarios(self) -> List[Dict[str, Any]]:
        """Create envelope breach test scenarios."""
        scenarios = []
        
        # Gradual breach scenario
        scenarios.append({
            "name": "gradual_breach",
            "description": "Coherence gradually decreases below threshold",
            "data_sequence": [
                {"features": [0.8, 0.8, 0.8, 0.8], "weights": [0.25, 0.25, 0.25, 0.25]},
                {"features": [0.7, 0.7, 0.7, 0.7], "weights": [0.25, 0.25, 0.25, 0.25]},
                {"features": [0.6, 0.6, 0.6, 0.6], "weights": [0.25, 0.25, 0.25, 0.25]},
                {"features": [0.5, 0.5, 0.5, 0.5], "weights": [0.25, 0.25, 0.25, 0.25]},
                {"features": [0.4, 0.4, 0.4, 0.4], "weights": [0.25, 0.25, 0.25, 0.25]}
            ],
            "threshold": 0.6,
            "expected_breach_point": 4  # Breach should occur at 4th data point
        })
        
        # Sudden breach scenario
        scenarios.append({
            "name": "sudden_breach",
            "description": "Sudden coherence drop below threshold",
            "data_sequence": [
                {"features": [0.9, 0.9, 0.9, 0.9], "weights": [0.25, 0.25, 0.25, 0.25]},
                {"features": [0.9, 0.9, 0.9, 0.9], "weights": [0.25, 0.25, 0.25, 0.25]},
                {"features": [0.1, 0.1, 0.1, 0.1], "weights": [0.25, 0.25, 0.25, 0.25]}
            ],
            "threshold": 0.5,
            "expected_breach_point": 3  # Breach should occur at 3rd data point
        })
        
        # Oscillating breach scenario
        scenarios.append({
            "name": "oscillating_breach",
            "description": "Coherence oscillates around threshold",
            "data_sequence": [
                {"features": [0.7, 0.7, 0.7, 0.7], "weights": [0.25, 0.25, 0.25, 0.25]},
                {"features": [0.4, 0.4, 0.4, 0.4], "weights": [0.25, 0.25, 0.25, 0.25]},
                {"features": [0.8, 0.8, 0.8, 0.8], "weights": [0.25, 0.25, 0.25, 0.25]},
                {"features": [0.3, 0.3, 0.3, 0.3], "weights": [0.25, 0.25, 0.25, 0.25]}
            ],
            "threshold": 0.5,
            "expected_breach_points": [2, 4]  # Breaches at 2nd and 4th points
        })
        
        return scenarios
    
    async def test_envelope_breach_detection(self, coherence_engine: CoherenceEngine) -> Dict[str, Any]:
        """Test envelope breach detection across scenarios."""
        test_results = {
            "total_scenarios": len(self.breach_scenarios),
            "passed_scenarios": 0,
            "failed_scenarios": 0,
            "scenario_results": []
        }
        
        for scenario in self.breach_scenarios:
            scenario_result = await self._run_breach_scenario(coherence_engine, scenario)
            test_results["scenario_results"].append(scenario_result)
            
            if scenario_result["test_passed"]:
                test_results["passed_scenarios"] += 1
            else:
                test_results["failed_scenarios"] += 1
        
        return test_results
    
    async def _run_breach_scenario(self, coherence_engine: CoherenceEngine, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single envelope breach scenario."""
        coherence_engine.set_envelope_threshold(scenario["threshold"])
        
        breach_points = []
        coherence_scores = []
        
        for i, data in enumerate(scenario["data_sequence"]):
            coherence_score = await coherence_engine.calculate_coherence(data)
            coherence_scores.append(coherence_score)
            
            # Check envelope status
            envelope_result = await coherence_engine.check_envelope(data)
            
            if envelope_result["breach_detected"]:
                breach_points.append(i + 1)  # 1-indexed
        
        # Evaluate results
        if "expected_breach_point" in scenario:
            expected = [scenario["expected_breach_point"]]
        else:
            expected = scenario["expected_breach_points"]
        
        test_passed = breach_points == expected
        
        return {
            "scenario_name": scenario["name"],
            "description": scenario["description"],
            "threshold": scenario["threshold"],
            "coherence_scores": coherence_scores,
            "expected_breach_points": expected,
            "actual_breach_points": breach_points,
            "test_passed": test_passed
        }


class BudgetManagementTester:
    """Tests for coherence budget management under load."""
    
    def __init__(self):
        self.load_scenarios = self._create_load_scenarios()
    
    def _create_load_scenarios(self) -> List[Dict[str, Any]]:
        """Create budget management load scenarios."""
        scenarios = []
        
        # Light load scenario
        scenarios.append({
            "name": "light_load",
            "description": "Light computational load",
            "initial_budget": 100.0,
            "operations": [
                {"cost": 5.0, "count": 10},
                {"cost": 10.0, "count": 5}
            ],
            "expected_remaining": 25.0
        })
        
        # Heavy load scenario
        scenarios.append({
            "name": "heavy_load",
            "description": "Heavy computational load",
            "initial_budget": 100.0,
            "operations": [
                {"cost": 15.0, "count": 5},
                {"cost": 20.0, "count": 3}
            ],
            "expected_remaining": 5.0
        })
        
        # Overload scenario
        scenarios.append({
            "name": "overload",
            "description": "Budget exceeded scenario",
            "initial_budget": 50.0,
            "operations": [
                {"cost": 30.0, "count": 2},
                {"cost": 10.0, "count": 3}
            ],
            "expected_failures": 1  # One operation should fail
        })
        
        return scenarios
    
    async def test_budget_management(self, coherence_engine: CoherenceEngine) -> Dict[str, Any]:
        """Test budget management under various load scenarios."""
        test_results = {
            "total_scenarios": len(self.load_scenarios),
            "passed_scenarios": 0,
            "failed_scenarios": 0,
            "scenario_results": []
        }
        
        for scenario in self.load_scenarios:
            scenario_result = await self._run_budget_scenario(coherence_engine, scenario)
            test_results["scenario_results"].append(scenario_result)
            
            if scenario_result["test_passed"]:
                test_results["passed_scenarios"] += 1
            else:
                test_results["failed_scenarios"] += 1
        
        return test_results
    
    async def _run_budget_scenario(self, coherence_engine: CoherenceEngine, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single budget management scenario."""
        # Reset budget
        coherence_engine.set_budget(scenario["initial_budget"])
        
        successful_operations = 0
        failed_operations = 0
        total_consumed = 0.0
        
        for operation in scenario["operations"]:
            cost = operation["cost"]
            count = operation["count"]
            
            for _ in range(count):
                success = coherence_engine.consume_budget(cost)
                if success:
                    successful_operations += 1
                    total_consumed += cost
                else:
                    failed_operations += 1
        
        final_budget = coherence_engine.get_budget()
        expected_remaining = scenario.get("expected_remaining", 
                                         scenario["initial_budget"] - total_consumed)
        expected_failures = scenario.get("expected_failures", 0)
        
        test_passed = (
            abs(final_budget - expected_remaining) < 0.01 and
            failed_operations == expected_failures
        )
        
        return {
            "scenario_name": scenario["name"],
            "description": scenario["description"],
            "initial_budget": scenario["initial_budget"],
            "successful_operations": successful_operations,
            "failed_operations": failed_operations,
            "total_consumed": total_consumed,
            "final_budget": final_budget,
            "expected_remaining": expected_remaining,
            "expected_failures": expected_failures,
            "test_passed": test_passed
        }


class RiskStateTransitionTester:
    """Tests for risk state transitions and hysteresis."""
    
    def __init__(self):
        self.transition_scenarios = self._create_transition_scenarios()
    
    def _create_transition_scenarios(self) -> List[Dict[str, Any]]:
        """Create risk state transition scenarios."""
        scenarios = []
        
        # Normal to elevated risk scenario
        scenarios.append({
            "name": "normal_to_elevated",
            "description": "Transition from normal to elevated risk state",
            "initial_state": "normal",
            "coherence_sequence": [0.9, 0.8, 0.7, 0.6, 0.5],
            "thresholds": {"elevated": 0.6, "high": 0.4},
            "expected_transitions": ["normal", "normal", "normal", "elevated", "elevated"]
        })
        
        # Hysteresis scenario
        scenarios.append({
            "name": "hysteresis_test",
            "description": "Test hysteresis in state transitions",
            "initial_state": "normal",
            "coherence_sequence": [0.9, 0.7, 0.5, 0.7, 0.9],
            "thresholds": {"elevated": 0.6, "normal_recovery": 0.8},
            "expected_transitions": ["normal", "normal", "elevated", "elevated", "normal"]
        })
        
        # Rapid escalation scenario
        scenarios.append({
            "name": "rapid_escalation",
            "description": "Rapid escalation through risk states",
            "initial_state": "normal",
            "coherence_sequence": [0.9, 0.5, 0.3, 0.1],
            "thresholds": {"elevated": 0.6, "high": 0.4, "critical": 0.2},
            "expected_transitions": ["normal", "elevated", "high", "critical"]
        })
        
        return scenarios
    
    async def test_risk_state_transitions(self, coherence_engine: CoherenceEngine) -> Dict[str, Any]:
        """Test risk state transitions and hysteresis."""
        test_results = {
            "total_scenarios": len(self.transition_scenarios),
            "passed_scenarios": 0,
            "failed_scenarios": 0,
            "scenario_results": []
        }
        
        for scenario in self.transition_scenarios:
            scenario_result = await self._run_transition_scenario(coherence_engine, scenario)
            test_results["scenario_results"].append(scenario_result)
            
            if scenario_result["test_passed"]:
                test_results["passed_scenarios"] += 1
            else:
                test_results["failed_scenarios"] += 1
        
        return test_results
    
    async def _run_transition_scenario(self, coherence_engine: CoherenceEngine, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single risk state transition scenario."""
        current_state = scenario["initial_state"]
        actual_transitions = [current_state]
        
        # Configure thresholds
        thresholds = scenario["thresholds"]
        coherence_engine.set_risk_thresholds(thresholds)
        
        for coherence_value in scenario["coherence_sequence"]:
            # Simulate coherence change
            new_state = coherence_engine.determine_risk_state(coherence_value, current_state)
            
            # Apply hysteresis if needed
            if current_state == "elevated" and new_state == "normal":
                if coherence_value < thresholds.get("normal_recovery", 0.8):
                    new_state = "elevated"  # Stay in elevated due to hysteresis
            
            current_state = new_state
            actual_transitions.append(current_state)
        
        test_passed = actual_transitions == scenario["expected_transitions"]
        
        return {
            "scenario_name": scenario["name"],
            "description": scenario["description"],
            "coherence_sequence": scenario["coherence_sequence"],
            "thresholds": scenario["thresholds"],
            "expected_transitions": scenario["expected_transitions"],
            "actual_transitions": actual_transitions,
            "test_passed": test_passed
        }


class SignalProcessingValidator:
    """Tests for coherence signal processing validation."""
    
    def __init__(self):
        self.signal_scenarios = self._create_signal_scenarios()
    
    def _create_signal_scenarios(self) -> List[Dict[str, Any]]:
        """Create signal processing test scenarios."""
        scenarios = []
        
        # Noisy signal scenario
        scenarios.append({
            "name": "noisy_signal",
            "description": "Signal with high noise content",
            "signal": np.sin(np.linspace(0, 10, 100)) + np.random.normal(0, 0.2, 100),
            "expected_snr_range": (5, 15),
            "filter_type": "lowpass"
        })
        
        # Clean signal scenario
        scenarios.append({
            "name": "clean_signal",
            "description": "Clean periodic signal",
            "signal": np.sin(np.linspace(0, 10, 100)),
            "expected_snr_range": (20, 50),
            "filter_type": "none"
        })
        
        # Burst noise scenario
        scenarios.append({
            "name": "burst_noise",
            "description": "Signal with burst noise",
            "signal": self._create_burst_noise_signal(),
            "expected_snr_range": (3, 10),
            "filter_type": "median"
        })
        
        return scenarios
    
    def _create_burst_noise_signal(self) -> np.ndarray:
        """Create a signal with burst noise."""
        base_signal = np.sin(np.linspace(0, 10, 100))
        noise = np.zeros(100)
        
        # Add burst noise at specific intervals
        for start in [20, 50, 80]:
            noise[start:start+5] = np.random.normal(0, 0.5, 5)
        
        return base_signal + noise
    
    async def test_signal_processing(self, coherence_engine: CoherenceEngine) -> Dict[str, Any]:
        """Test coherence signal processing."""
        test_results = {
            "total_scenarios": len(self.signal_scenarios),
            "passed_scenarios": 0,
            "failed_scenarios": 0,
            "scenario_results": []
        }
        
        for scenario in self.signal_scenarios:
            scenario_result = await self._run_signal_scenario(coherence_engine, scenario)
            test_results["scenario_results"].append(scenario_result)
            
            if scenario_result["test_passed"]:
                test_results["passed_scenarios"] += 1
            else:
                test_results["failed_scenarios"] += 1
        
        return test_results
    
    async def _run_signal_scenario(self, coherence_engine: CoherenceEngine, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single signal processing scenario."""
        signal = scenario["signal"]
        
        # Process signal
        processed_result = await coherence_engine.process_coherence_signal(
            signal, 
            filter_type=scenario["filter_type"]
        )
        
        # Calculate SNR
        snr = processed_result["signal_to_noise_ratio"]
        
        # Check if SNR is in expected range
        min_snr, max_snr = scenario["expected_snr_range"]
        snr_in_range = min_snr <= snr <= max_snr
        
        test_passed = snr_in_range
        
        return {
            "scenario_name": scenario["name"],
            "description": scenario["description"],
            "filter_type": scenario["filter_type"],
            "signal_to_noise_ratio": snr,
            "expected_snr_range": scenario["expected_snr_range"],
            "snr_in_range": snr_in_range,
            "test_passed": test_passed,
            "processing_metrics": processed_result.get("metrics", {})
        }


# Integration test class
class TestCoherenceValidation:
    """Integration tests for coherence validation framework."""
    
    @pytest.fixture
    async def coherence_engine(self):
        """Create a coherence engine for testing."""
        engine = CoherenceEngine()
        await engine.initialize()
        yield engine
        await engine.shutdown()
    
    @pytest.fixture
    def validation_framework(self):
        """Create a coherence validation framework."""
        return CoherenceValidationFramework()
    
    @pytest.fixture
    def envelope_tester(self):
        """Create an envelope breach tester."""
        return EnvelopeBreachTester()
    
    @pytest.fixture
    def budget_tester(self):
        """Create a budget management tester."""
        return BudgetManagementTester()
    
    @pytest.fixture
    def transition_tester(self):
        """Create a risk state transition tester."""
        return RiskStateTransitionTester()
    
    @pytest.fixture
    def signal_validator(self):
        """Create a signal processing validator."""
        return SignalProcessingValidator()
    
    @pytest.mark.asyncio
    async def test_comprehensive_coherence_validation(self, 
                                                      coherence_engine,
                                                      validation_framework,
                                                      envelope_tester,
                                                      budget_tester,
                                                      transition_tester,
                                                      signal_validator):
        """Test comprehensive coherence validation."""
        # Run all validation tests
        coherence_results = await validation_framework.validate_coherence_measures(coherence_engine)
        envelope_results = await envelope_tester.test_envelope_breach_detection(coherence_engine)
        budget_results = await budget_tester.test_budget_management(coherence_engine)
        transition_results = await transition_tester.test_risk_state_transitions(coherence_engine)
        signal_results = await signal_validator.test_signal_processing(coherence_engine)
        
        # Compile comprehensive results
        comprehensive_results = {
            "coherence_measures": coherence_results,
            "envelope_breaches": envelope_results,
            "budget_management": budget_results,
            "risk_transitions": transition_results,
            "signal_processing": signal_results,
            "overall_summary": {
                "total_test_categories": 5,
                "overall_pass_rate": self._calculate_overall_pass_rate([
                    coherence_results, envelope_results, budget_results, 
                    transition_results, signal_results
                ])
            }
        }
        
        # Assert overall quality
        assert comprehensive_results["overall_summary"]["overall_pass_rate"] >= 0.8, \
            "Overall coherence validation pass rate should be at least 80%"
        
        return comprehensive_results
    
    def _calculate_overall_pass_rate(self, results_list: List[Dict[str, Any]]) -> float:
        """Calculate overall pass rate across multiple test categories."""
        total_passed = 0
        total_tests = 0
        
        for results in results_list:
            if "passed_benchmarks" in results:
                total_passed += results["passed_benchmarks"]
                total_tests += results["total_benchmarks"]
            elif "passed_scenarios" in results:
                total_passed += results["passed_scenarios"]
                total_tests += results["total_scenarios"]
        
        return total_passed / total_tests if total_tests > 0 else 0.0
    
    @pytest.mark.asyncio
    async def test_coherence_validation_performance(self, coherence_engine):
        """Test performance of coherence validation."""
        validation_framework = CoherenceValidationFramework()
        
        # Measure validation performance
        start_time = time.time()
        results = await validation_framework.validate_coherence_measures(coherence_engine)
        validation_time = time.time() - start_time
        
        # Performance should be reasonable
        assert validation_time < 5.0, f"Coherence validation took too long: {validation_time}s"
        
        # All benchmarks should be processed
        assert results["total_benchmarks"] == len(validation_framework.benchmarks)
        
        # Pass rate should be high
        assert results["accuracy_metrics"]["pass_rate"] >= 0.8, \
            f"Coherence validation pass rate too low: {results['accuracy_metrics']['pass_rate']}"