"""
Hierarchical Reasoning Benchmarks

Comprehensive benchmarks for testing multi-step planning, program induction,
causal discovery, constraint satisfaction, abstraction quality evaluation,
and level selection algorithms.
"""

import pytest
import asyncio
import time
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import json

from src.haai.agent import ReasoningEngine
from src.haai.core import CoherenceEngine, HierarchicalAbstraction
from tests.test_framework import TestFramework, measure_async_performance


class ProblemType(Enum):
    """Types of reasoning problems."""
    MULTI_STEP_PLANNING = "multi_step_planning"
    PROGRAM_INDUCTION = "program_induction"
    CAUSAL_DISCOVERY = "causal_discovery"
    CONSTRAINT_SATISFACTION = "constraint_satisfaction"
    ABSTRACTION_QUALITY = "abstraction_quality"
    LEVEL_SELECTION = "level_selection"


@dataclass
class ReasoningBenchmark:
    """Benchmark data for hierarchical reasoning tests."""
    name: str
    problem_type: ProblemType
    input_data: Dict[str, Any]
    expected_output: Dict[str, Any]
    complexity_level: float
    optimal_reasoning_mode: str
    expected_steps: int
    description: str


class MultiStepPlanningBenchmark:
    """Benchmarks for multi-step planning problems."""
    
    def __init__(self):
        self.planning_problems = self._create_planning_problems()
    
    def _create_planning_problems(self) -> List[ReasoningBenchmark]:
        """Create multi-step planning benchmark problems."""
        problems = []
        
        # Simple navigation problem
        problems.append(ReasoningBenchmark(
            name="simple_navigation",
            problem_type=ProblemType.MULTI_STEP_PLANNING,
            input_data={
                "start": (0, 0),
                "goal": (3, 3),
                "obstacles": [(1, 1), (2, 2)],
                "grid_size": (4, 4)
            },
            expected_output={
                "path_length": 8,
                "optimal_path": [(0, 0), (0, 1), (0, 2), (0, 3), (1, 3), (2, 3), (3, 3)],
                "steps": ["move_right", "move_right", "move_right", "move_down", "move_down", "move_down"]
            },
            complexity_level=0.3,
            optimal_reasoning_mode="sequential",
            expected_steps=6,
            description="Simple grid navigation with obstacles"
        ))
        
        # Complex logistics problem
        problems.append(ReasoningBenchmark(
            name="logistics_planning",
            problem_type=ProblemType.MULTI_STEP_PLANNING,
            input_data={
                "packages": [
                    {"id": "p1", "from": "A", "to": "C", "weight": 10},
                    {"id": "p2", "from": "B", "to": "D", "weight": 15},
                    {"id": "p3", "from": "A", "to": "D", "weight": 5}
                ],
                "vehicles": [
                    {"id": "v1", "capacity": 20, "location": "A"},
                    {"id": "v2", "capacity": 15, "location": "B"}
                ],
                "routes": {
                    "A-B": 5, "A-C": 10, "A-D": 15,
                    "B-C": 8, "B-D": 12,
                    "C-D": 6
                }
            },
            expected_output={
                "total_distance": "optimized",
                "vehicle_assignments": "optimal",
                "delivery_sequence": "efficient"
            },
            complexity_level=0.8,
            optimal_reasoning_mode="hierarchical",
            expected_steps=12,
            description="Complex logistics optimization problem"
        ))
        
        # Resource allocation problem
        problems.append(ReasoningBenchmark(
            name="resource_allocation",
            problem_type=ProblemType.MULTI_STEP_PLANNING,
            input_data={
                "resources": {
                    "cpu": 100,
                    "memory": 1024,
                    "storage": 10000
                },
                "tasks": [
                    {"id": "t1", "cpu": 20, "memory": 256, "priority": "high"},
                    {"id": "t2", "cpu": 30, "memory": 512, "priority": "medium"},
                    {"id": "t3", "cpu": 15, "memory": 128, "priority": "low"},
                    {"id": "t4", "cpu": 25, "memory": 384, "priority": "high"}
                ]
            },
            expected_output={
                "allocation_plan": "priority_optimized",
                "resource_utilization": "balanced",
                "task_scheduling": "efficient"
            },
            complexity_level=0.6,
            optimal_reasoning_mode="parallel",
            expected_steps=8,
            description="Multi-resource allocation with priorities"
        ))
        
        return problems
    
    async def evaluate_planning_performance(self, reasoning_engine: ReasoningEngine) -> Dict[str, Any]:
        """Evaluate planning performance across benchmark problems."""
        results = {
            "total_problems": len(self.planning_problems),
            "solved_problems": 0,
            "performance_metrics": [],
            "mode_effectiveness": {}
        }
        
        for problem in self.planning_problems:
            # Solve the problem
            start_time = time.time()
            solution = await reasoning_engine.reason(
                problem.input_data,
                mode=problem.optimal_reasoning_mode
            )
            solve_time = time.time() - start_time
            
            # Evaluate solution quality
            quality_score = self._evaluate_solution_quality(solution, problem.expected_output)
            
            # Record results
            problem_result = {
                "problem_name": problem.name,
                "complexity_level": problem.complexity_level,
                "solve_time": solve_time,
                "quality_score": quality_score,
                "reasoning_mode": problem.optimal_reasoning_mode,
                "expected_steps": problem.expected_steps,
                "actual_steps": solution.get("steps_count", 0)
            }
            
            results["performance_metrics"].append(problem_result)
            
            if quality_score >= 0.7:  # Consider solved if quality >= 70%
                results["solved_problems"] += 1
            
            # Track mode effectiveness
            mode = problem.optimal_reasoning_mode
            if mode not in results["mode_effectiveness"]:
                results["mode_effectiveness"][mode] = []
            results["mode_effectiveness"][mode].append(quality_score)
        
        # Calculate mode effectiveness averages
        for mode in results["mode_effectiveness"]:
            scores = results["mode_effectiveness"][mode]
            results["mode_effectiveness"][mode] = {
                "average_quality": np.mean(scores),
                "std_deviation": np.std(scores),
                "problem_count": len(scores)
            }
        
        return results
    
    def _evaluate_solution_quality(self, solution: Dict[str, Any], expected: Dict[str, Any]) -> float:
        """Evaluate the quality of a planning solution."""
        quality_score = 0.0
        criteria_count = 0
        
        # Check if solution contains expected structure
        for key, expected_value in expected.items():
            if key in solution:
                criteria_count += 1
                
                if isinstance(expected_value, str):
                    # For string expectations, check if solution is reasonable
                    if expected_value == "optimized" and solution[key] is not None:
                        quality_score += 1.0
                    elif expected_value == "efficient" and solution.get(key, {}).get("efficiency", 0) > 0.7:
                        quality_score += 1.0
                    elif expected_value == "optimal" and solution.get(key, {}).get("optimality", 0) > 0.8:
                        quality_score += 1.0
                elif isinstance(expected_value, (int, float)):
                    # For numerical expectations, check closeness
                    actual_value = solution[key]
                    if isinstance(actual_value, (int, float)):
                        diff = abs(actual_value - expected_value) / max(abs(expected_value), 1)
                        if diff < 0.1:  # Within 10%
                            quality_score += 1.0
                        elif diff < 0.2:  # Within 20%
                            quality_score += 0.5
        
        return quality_score / max(criteria_count, 1)


class ProgramInductionBenchmark:
    """Benchmarks for program induction and synthesis."""
    
    def __init__(self):
        self.induction_problems = self._create_induction_problems()
    
    def _create_induction_problems(self) -> List[ReasoningBenchmark]:
        """Create program induction benchmark problems."""
        problems = []
        
        # Simple function induction
        problems.append(ReasoningBenchmark(
            name="simple_function_induction",
            problem_type=ProblemType.PROGRAM_INDUCTION,
            input_data={
                "examples": [
                    {"input": [1, 2, 3], "output": 6},
                    {"input": [4, 5, 6], "output": 15},
                    {"input": [7, 8, 9], "output": 24}
                ],
                "domain": "arithmetic",
                "complexity": "simple"
            },
            expected_output={
                "function": "sum",
                "expression": "lambda x: sum(x)",
                "confidence": 0.9
            },
            complexity_level=0.4,
            optimal_reasoning_mode="sequential",
            expected_steps=3,
            description="Induce sum function from examples"
        ))
        
        # Complex pattern induction
        problems.append(ReasoningBenchmark(
            name="complex_pattern_induction",
            problem_type=ProblemType.PROGRAM_INDUCTION,
            input_data={
                "examples": [
                    {"input": [1, 2, 3, 4], "output": [2, 4, 6, 8]},
                    {"input": [5, 6, 7], "output": [10, 12, 14]},
                    {"input": [0, 1], "output": [0, 2]}
                ],
                "domain": "transformation",
                "complexity": "medium"
            },
            expected_output={
                "function": "double_elements",
                "expression": "lambda x: [i * 2 for i in x]",
                "confidence": 0.85
            },
            complexity_level=0.6,
            optimal_reasoning_mode="hierarchical",
            expected_steps=5,
            description="Induce element doubling transformation"
        ))
        
        # Recursive function induction
        problems.append(ReasoningBenchmark(
            name="recursive_function_induction",
            problem_type=ProblemType.PROGRAM_INDUCTION,
            input_data={
                "examples": [
                    {"input": 5, "output": 120},
                    {"input": 3, "output": 6},
                    {"input": 4, "output": 24},
                    {"input": 1, "output": 1}
                ],
                "domain": "mathematics",
                "complexity": "hard"
            },
            expected_output={
                "function": "factorial",
                "expression": "lambda n: 1 if n <= 1 else n * factorial(n-1)",
                "confidence": 0.8
            },
            complexity_level=0.8,
            optimal_reasoning_mode="hierarchical",
            expected_steps=7,
            description="Induce factorial function"
        ))
        
        return problems
    
    async def evaluate_induction_performance(self, reasoning_engine: ReasoningEngine) -> Dict[str, Any]:
        """Evaluate program induction performance."""
        results = {
            "total_problems": len(self.induction_problems),
            "solved_problems": 0,
            "induction_metrics": [],
            "confidence_distribution": []
        }
        
        for problem in self.induction_problems:
            # Solve induction problem
            start_time = time.time()
            solution = await reasoning_engine.reason(
                problem.input_data,
                mode=problem.optimal_reasoning_mode
            )
            solve_time = time.time() - start_time
            
            # Evaluate induction quality
            quality_score = self._evaluate_induction_quality(solution, problem.expected_output)
            
            # Extract confidence
            confidence = solution.get("confidence", 0.0)
            results["confidence_distribution"].append(confidence)
            
            # Record results
            problem_result = {
                "problem_name": problem.name,
                "complexity_level": problem.complexity_level,
                "solve_time": solve_time,
                "quality_score": quality_score,
                "confidence": confidence,
                "induced_function": solution.get("function", "unknown")
            }
            
            results["induction_metrics"].append(problem_result)
            
            if quality_score >= 0.6 and confidence >= 0.7:
                results["solved_problems"] += 1
        
        # Calculate confidence statistics
        if results["confidence_distribution"]:
            results["confidence_stats"] = {
                "mean": np.mean(results["confidence_distribution"]),
                "std": np.std(results["confidence_distribution"]),
                "min": np.min(results["confidence_distribution"]),
                "max": np.max(results["confidence_distribution"])
            }
        
        return results
    
    def _evaluate_induction_quality(self, solution: Dict[str, Any], expected: Dict[str, Any]) -> float:
        """Evaluate the quality of program induction."""
        quality_score = 0.0
        
        # Check function name match
        if solution.get("function") == expected.get("function"):
            quality_score += 0.4
        
        # Check expression similarity (simplified)
        solution_expr = solution.get("expression", "")
        expected_expr = expected.get("expression", "")
        
        if solution_expr and expected_expr:
            # Simple keyword matching for expression similarity
            common_keywords = set(solution_expr.split()) & set(expected_expr.split())
            total_keywords = set(solution_expr.split()) | set(expected_expr.split())
            if total_keywords:
                similarity = len(common_keywords) / len(total_keywords)
                quality_score += similarity * 0.6
        
        return quality_score


class CausalDiscoveryBenchmark:
    """Benchmarks for causal discovery problems."""
    
    def __init__(self):
        self.causal_problems = self._create_causal_problems()
    
    def _create_causal_problems(self) -> List[ReasoningBenchmark]:
        """Create causal discovery benchmark problems."""
        problems = []
        
        # Simple causal chain
        problems.append(ReasoningBenchmark(
            name="simple_causal_chain",
            problem_type=ProblemType.CAUSAL_DISCOVERY,
            input_data={
                "observations": [
                    {"A": 1, "B": 2, "C": 3},
                    {"A": 2, "B": 4, "C": 6},
                    {"A": 3, "B": 6, "C": 9},
                    {"A": 4, "B": 8, "C": 12}
                ],
                "variables": ["A", "B", "C"]
            },
            expected_output={
                "causal_graph": {"A": ["B"], "B": ["C"], "C": []},
                "strengths": {"A->B": 1.0, "B->C": 1.0},
                "confidence": 0.95
            },
            complexity_level=0.5,
            optimal_reasoning_mode="sequential",
            expected_steps=4,
            description="Discover simple A->B->C causal chain"
        ))
        
        # Complex causal network
        problems.append(ReasoningBenchmark(
            name="complex_causal_network",
            problem_type=ProblemType.CAUSAL_DISCOVERY,
            input_data={
                "observations": self._generate_complex_causal_data(),
                "variables": ["X", "Y", "Z", "W", "V"]
            },
            expected_output={
                "causal_graph": "complex_network",
                "confounding_factors": "identified",
                "intervention_predictions": "accurate"
            },
            complexity_level=0.9,
            optimal_reasoning_mode="hierarchical",
            expected_steps=8,
            description="Discover complex causal network with confounding"
        ))
        
        return problems
    
    def _generate_complex_causal_data(self) -> List[Dict[str, float]]:
        """Generate complex causal observation data."""
        observations = []
        np.random.seed(42)
        
        for _ in range(100):
            X = np.random.normal(0, 1)
            Y = 2 * X + np.random.normal(0, 0.1)
            Z = 0.5 * X + 0.3 * Y + np.random.normal(0, 0.1)
            W = 1.5 * Y + np.random.normal(0, 0.1)
            V = 0.8 * Z + 0.4 * W + np.random.normal(0, 0.1)
            
            observations.append({"X": X, "Y": Y, "Z": Z, "W": W, "V": V})
        
        return observations
    
    async def evaluate_causal_discovery(self, reasoning_engine: ReasoningEngine) -> Dict[str, Any]:
        """Evaluate causal discovery performance."""
        results = {
            "total_problems": len(self.causal_problems),
            "solved_problems": 0,
            "discovery_metrics": [],
            "graph_accuracy_scores": []
        }
        
        for problem in self.causal_problems:
            # Solve causal discovery
            start_time = time.time()
            solution = await reasoning_engine.reason(
                problem.input_data,
                mode=problem.optimal_reasoning_mode
            )
            solve_time = time.time() - start_time
            
            # Evaluate discovery quality
            quality_score = self._evaluate_causal_quality(solution, problem.expected_output)
            
            # Extract graph accuracy if available
            if "graph_accuracy" in solution:
                results["graph_accuracy_scores"].append(solution["graph_accuracy"])
            
            # Record results
            problem_result = {
                "problem_name": problem.name,
                "complexity_level": problem.complexity_level,
                "solve_time": solve_time,
                "quality_score": quality_score,
                "causal_edges_found": solution.get("causal_edges", 0),
                "confidence": solution.get("confidence", 0.0)
            }
            
            results["discovery_metrics"].append(problem_result)
            
            if quality_score >= 0.7:
                results["solved_problems"] += 1
        
        # Calculate graph accuracy statistics
        if results["graph_accuracy_scores"]:
            results["graph_accuracy_stats"] = {
                "mean": np.mean(results["graph_accuracy_scores"]),
                "std": np.std(results["graph_accuracy_scores"])
            }
        
        return results
    
    def _evaluate_causal_quality(self, solution: Dict[str, Any], expected: Dict[str, Any]) -> float:
        """Evaluate the quality of causal discovery."""
        quality_score = 0.0
        
        # Check if causal graph structure is reasonable
        if "causal_graph" in solution:
            solution_graph = solution["causal_graph"]
            
            if isinstance(expected["causal_graph"], dict):
                # Compare graph structures
                expected_graph = expected["causal_graph"]
                
                # Count matching edges
                matching_edges = 0
                total_edges = 0
                
                for source, targets in expected_graph.items():
                    total_edges += len(targets)
                    if source in solution_graph:
                        matching_edges += len(set(targets) & set(solution_graph[source]))
                
                if total_edges > 0:
                    quality_score += matching_edges / total_edges * 0.7
            
            elif isinstance(expected["causal_graph"], str):
                # For complex cases, check if solution is reasonable
                if solution_graph and len(solution_graph) > 0:
                    quality_score += 0.5
        
        # Check confidence
        confidence = solution.get("confidence", 0.0)
        quality_score += confidence * 0.3
        
        return quality_score


class AbstractionQualityEvaluator:
    """Evaluator for abstraction quality metrics."""
    
    def __init__(self):
        self.quality_tests = self._create_quality_tests()
    
    def _create_quality_tests(self) -> List[ReasoningBenchmark]:
        """Create abstraction quality evaluation tests."""
        tests = []
        
        # Information retention test
        tests.append(ReasoningBenchmark(
            name="information_retention",
            problem_type=ProblemType.ABSTRACTION_QUALITY,
            input_data={
                "original_data": list(range(1000)),
                "abstraction_levels": [0.1, 0.2, 0.3, 0.5, 0.7],
                "compression_method": "sampling"
            },
            expected_output={
                "retention_curve": "monotonic_decreasing",
                "optimal_compression": 0.3,
                "quality_threshold": 0.8
            },
            complexity_level=0.6,
            optimal_reasoning_mode="parallel",
            expected_steps=5,
            description="Evaluate information retention across compression levels"
        ))
        
        # Pattern preservation test
        tests.append(ReasoningBenchmark(
            name="pattern_preservation",
            problem_type=ProblemType.ABSTRACTION_QUALITY,
            input_data={
                "pattern_data": [1, 2, 1, 2, 1, 2, 1, 2] * 125,  # Repeating pattern
                "abstraction_methods": ["sampling", "clustering", "compression"]
            },
            expected_output={
                "pattern_scores": "high_for_clustering",
                "best_method": "clustering",
                "preservation_rate": 0.9
            },
            complexity_level=0.7,
            optimal_reasoning_mode="hierarchical",
            expected_steps=6,
            description="Evaluate pattern preservation in abstraction"
        ))
        
        return tests
    
    async def evaluate_abstraction_quality(self, reasoning_engine: ReasoningEngine) -> Dict[str, Any]:
        """Evaluate abstraction quality across test cases."""
        results = {
            "total_tests": len(self.quality_tests),
            "passed_tests": 0,
            "quality_metrics": [],
            "method_performance": {}
        }
        
        for test in self.quality_tests:
            # Run abstraction quality evaluation
            start_time = time.time()
            evaluation = await reasoning_engine.reason(
                test.input_data,
                mode=test.optimal_reasoning_mode
            )
            eval_time = time.time() - start_time
            
            # Evaluate quality
            quality_score = self._evaluate_quality_result(evaluation, test.expected_output)
            
            # Record results
            test_result = {
                "test_name": test.name,
                "complexity_level": test.complexity_level,
                "eval_time": eval_time,
                "quality_score": quality_score,
                "best_method": evaluation.get("best_method", "none"),
                "preservation_rate": evaluation.get("preservation_rate", 0.0)
            }
            
            results["quality_metrics"].append(test_result)
            
            if quality_score >= 0.7:
                results["passed_tests"] += 1
            
            # Track method performance
            method = evaluation.get("best_method", "unknown")
            if method not in results["method_performance"]:
                results["method_performance"][method] = []
            results["method_performance"][method].append(quality_score)
        
        # Calculate method performance averages
        for method in results["method_performance"]:
            scores = results["method_performance"][method]
            results["method_performance"][method] = {
                "average_quality": np.mean(scores),
                "test_count": len(scores)
            }
        
        return results
    
    def _evaluate_quality_result(self, evaluation: Dict[str, Any], expected: Dict[str, Any]) -> float:
        """Evaluate abstraction quality result."""
        quality_score = 0.0
        
        # Check preservation rate
        preservation_rate = evaluation.get("preservation_rate", 0.0)
        expected_rate = expected.get("preservation_rate", 0.8)
        
        if abs(preservation_rate - expected_rate) < 0.1:
            quality_score += 0.5
        elif abs(preservation_rate - expected_rate) < 0.2:
            quality_score += 0.3
        
        # Check method selection
        best_method = evaluation.get("best_method", "")
        expected_method = expected.get("best_method", "")
        
        if best_method == expected_method:
            quality_score += 0.3
        
        # Check overall quality
        overall_quality = evaluation.get("overall_quality", 0.0)
        quality_score += overall_quality * 0.2
        
        return quality_score


class LevelSelectionAlgorithmTester:
    """Tester for abstraction level selection and switching algorithms."""
    
    def __init__(self):
        self.selection_scenarios = self._create_selection_scenarios()
    
    def _create_selection_scenarios(self) -> List[ReasoningBenchmark]:
        """Create level selection test scenarios."""
        scenarios = []
        
        # Adaptive level selection
        scenarios.append(ReasoningBenchmark(
            name="adaptive_level_selection",
            problem_type=ProblemType.LEVEL_SELECTION,
            input_data={
                "task_complexity": 0.7,
                "available_levels": [1, 2, 3, 4],
                "performance_history": {
                    1: {"accuracy": 0.9, "speed": 0.3},
                    2: {"accuracy": 0.8, "speed": 0.5},
                    3: {"accuracy": 0.7, "speed": 0.7},
                    4: {"accuracy": 0.6, "speed": 0.9}
                },
                "constraints": {"min_accuracy": 0.75, "max_time": 0.8}
            },
            expected_output={
                "selected_level": 2,
                "selection_reason": "accuracy_speed_tradeoff",
                "expected_performance": {"accuracy": 0.8, "speed": 0.5}
            },
            complexity_level=0.5,
            optimal_reasoning_mode="adaptive",
            expected_steps=4,
            description="Adaptive level selection based on constraints"
        ))
        
        # Dynamic level switching
        scenarios.append(ReasoningBenchmark(
            name="dynamic_level_switching",
            problem_type=ProblemType.LEVEL_SELECTION,
            input_data={
                "current_level": 2,
                "performance_metrics": {
                    "current_accuracy": 0.65,  # Below expected
                    "current_speed": 0.7
                },
                "switching_costs": {
                    "2->1": 0.1, "2->3": 0.1, "2->4": 0.2
                },
                "improvement_potential": {
                    "1": {"accuracy_gain": 0.2, "speed_loss": 0.3},
                    "3": {"accuracy_loss": 0.1, "speed_gain": 0.2},
                    "4": {"accuracy_loss": 0.2, "speed_gain": 0.3}
                }
            },
            expected_output={
                "switch_decision": "switch_to_level_1",
                "reasoning": "accuracy_improvement_needed",
                "expected_benefit": 0.1
            },
            complexity_level=0.6,
            optimal_reasoning_mode="hierarchical",
            expected_steps=5,
            description="Dynamic level switching based on performance"
        ))
        
        return scenarios
    
    async def evaluate_level_selection(self, reasoning_engine: ReasoningEngine) -> Dict[str, Any]:
        """Evaluate level selection algorithm performance."""
        results = {
            "total_scenarios": len(self.selection_scenarios),
            "correct_selections": 0,
            "selection_metrics": [],
            "switching_efficiency": []
        }
        
        for scenario in self.selection_scenarios:
            # Run level selection
            start_time = time.time()
            selection = await reasoning_engine.reason(
                scenario.input_data,
                mode=scenario.optimal_reasoning_mode
            )
            selection_time = time.time() - start_time
            
            # Evaluate selection quality
            quality_score = self._evaluate_selection_quality(selection, scenario.expected_output)
            
            # Check if selected level matches expected
            selected_level = selection.get("selected_level", selection.get("switch_decision", ""))
            expected_level = scenario.expected_output.get("selected_level", "")
            
            correct_selection = (
                str(selected_level) == str(expected_level) or
                expected_level in str(selected_level)
            )
            
            if correct_selection:
                results["correct_selections"] += 1
            
            # Record results
            scenario_result = {
                "scenario_name": scenario.name,
                "complexity_level": scenario.complexity_level,
                "selection_time": selection_time,
                "quality_score": quality_score,
                "selected_level": selected_level,
                "expected_level": expected_level,
                "correct_selection": correct_selection
            }
            
            results["selection_metrics"].append(scenario_result)
            
            # Track switching efficiency
            if "switching_cost" in selection:
                results["switching_efficiency"].append(selection["switching_cost"])
        
        # Calculate selection accuracy
        results["selection_accuracy"] = results["correct_selections"] / results["total_scenarios"]
        
        # Calculate switching efficiency stats
        if results["switching_efficiency"]:
            results["switching_efficiency_stats"] = {
                "mean": np.mean(results["switching_efficiency"]),
                "std": np.std(results["switching_efficiency"])
            }
        
        return results
    
    def _evaluate_selection_quality(self, selection: Dict[str, Any], expected: Dict[str, Any]) -> float:
        """Evaluate level selection quality."""
        quality_score = 0.0
        
        # Check selection reasoning
        reasoning = selection.get("selection_reason", selection.get("reasoning", ""))
        expected_reasoning = expected.get("selection_reason", expected.get("reasoning", ""))
        
        if reasoning and expected_reasoning:
            if expected_reasoning in reasoning:
                quality_score += 0.4
        
        # Check expected performance
        expected_perf = expected.get("expected_performance", {})
        actual_perf = selection.get("expected_performance", {})
        
        if expected_perf and actual_perf:
            for metric, expected_value in expected_perf.items():
                if metric in actual_perf:
                    actual_value = actual_perf[metric]
                    if abs(actual_value - expected_value) < 0.1:
                        quality_score += 0.3
        
        # Check overall decision quality
        decision_quality = selection.get("decision_quality", 0.0)
        quality_score += decision_quality * 0.3
        
        return quality_score


# Integration test class
class TestHierarchicalReasoningBenchmarks:
    """Integration tests for hierarchical reasoning benchmarks."""
    
    @pytest.fixture
    async def reasoning_engine(self):
        """Create a reasoning engine for testing."""
        coherence_engine = CoherenceEngine()
        abstraction_framework = HierarchicalAbstraction()
        
        await coherence_engine.initialize()
        await abstraction_framework.initialize()
        
        engine = ReasoningEngine(coherence_engine, abstraction_framework)
        yield engine
        
        await coherence_engine.shutdown()
        await abstraction_framework.shutdown()
    
    @pytest.fixture
    def planning_benchmark(self):
        """Create multi-step planning benchmark."""
        return MultiStepPlanningBenchmark()
    
    @pytest.fixture
    def induction_benchmark(self):
        """Create program induction benchmark."""
        return ProgramInductionBenchmark()
    
    @pytest.fixture
    def causal_benchmark(self):
        """Create causal discovery benchmark."""
        return CausalDiscoveryBenchmark()
    
    @pytest.fixture
    def quality_evaluator(self):
        """Create abstraction quality evaluator."""
        return AbstractionQualityEvaluator()
    
    @pytest.fixture
    def level_tester(self):
        """Create level selection algorithm tester."""
        return LevelSelectionAlgorithmTester()
    
    @pytest.mark.asyncio
    async def test_comprehensive_reasoning_benchmarks(self,
                                                      reasoning_engine,
                                                      planning_benchmark,
                                                      induction_benchmark,
                                                      causal_benchmark,
                                                      quality_evaluator,
                                                      level_tester):
        """Test comprehensive hierarchical reasoning benchmarks."""
        # Run all benchmark evaluations
        planning_results = await planning_benchmark.evaluate_planning_performance(reasoning_engine)
        induction_results = await induction_benchmark.evaluate_induction_performance(reasoning_engine)
        causal_results = await causal_benchmark.evaluate_causal_discovery(reasoning_engine)
        quality_results = await quality_evaluator.evaluate_abstraction_quality(reasoning_engine)
        level_results = await level_tester.evaluate_level_selection(reasoning_engine)
        
        # Compile comprehensive results
        comprehensive_results = {
            "planning_benchmarks": planning_results,
            "program_induction": induction_results,
            "causal_discovery": causal_results,
            "abstraction_quality": quality_results,
            "level_selection": level_results,
            "overall_summary": {
                "total_benchmark_categories": 5,
                "overall_performance": self._calculate_overall_performance([
                    planning_results, induction_results, causal_results,
                    quality_results, level_results
                ])
            }
        }
        
        # Assert overall performance
        overall_perf = comprehensive_results["overall_summary"]["overall_performance"]
        assert overall_perf["average_solve_rate"] >= 0.6, \
            f"Overall solve rate too low: {overall_perf['average_solve_rate']}"
        
        return comprehensive_results
    
    def _calculate_overall_performance(self, results_list: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate overall performance metrics across benchmarks."""
        solve_rates = []
        quality_scores = []
        
        for results in results_list:
            # Extract solve rate
            if "solved_problems" in results and "total_problems" in results:
                solve_rate = results["solved_problems"] / results["total_problems"]
                solve_rates.append(solve_rate)
            elif "passed_tests" in results and "total_tests" in results:
                solve_rate = results["passed_tests"] / results["total_tests"]
                solve_rates.append(solve_rate)
            elif "correct_selections" in results and "total_scenarios" in results:
                solve_rate = results["correct_selections"] / results["total_scenarios"]
                solve_rates.append(solve_rate)
            
            # Extract average quality scores
            if "performance_metrics" in results:
                avg_quality = np.mean([m.get("quality_score", 0) for m in results["performance_metrics"]])
                quality_scores.append(avg_quality)
            elif "induction_metrics" in results:
                avg_quality = np.mean([m.get("quality_score", 0) for m in results["induction_metrics"]])
                quality_scores.append(avg_quality)
        
        return {
            "average_solve_rate": np.mean(solve_rates) if solve_rates else 0.0,
            "average_quality_score": np.mean(quality_scores) if quality_scores else 0.0
        }
    
    @pytest.mark.asyncio
    async def test_reasoning_performance_regression(self, reasoning_engine):
        """Test reasoning performance regression."""
        planning_benchmark = MultiStepPlanningBenchmark()
        
        # Measure performance
        start_time = time.time()
        results = await planning_benchmark.evaluate_planning_performance(reasoning_engine)
        total_time = time.time() - start_time
        
        # Performance should be reasonable
        assert total_time < 30.0, f"Reasoning benchmark took too long: {total_time}s"
        
        # Solve rate should be acceptable
        solve_rate = results["solved_problems"] / results["total_problems"]
        assert solve_rate >= 0.5, f"Reasoning solve rate too low: {solve_rate}"
        
        # Average solve time per problem should be reasonable
        if results["performance_metrics"]:
            avg_solve_time = np.mean([m["solve_time"] for m in results["performance_metrics"]])
            assert avg_solve_time < 5.0, f"Average solve time too high: {avg_solve_time}s"