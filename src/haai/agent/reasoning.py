"""
HAAI Reasoning Engine

Implements hierarchical reasoning with abstraction quality evaluation,
level selection algorithms, reasoning path optimization, and parallelization.
"""

import asyncio
import logging
import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from datetime import datetime

from ..core import CoherenceEngine, HierarchicalAbstraction


class ReasoningMode(Enum):
    """Different reasoning modes available to the agent."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HIERARCHICAL = "hierarchical"
    ADAPTIVE = "adaptive"


class ReasoningStepType(Enum):
    """Types of reasoning steps."""
    ABSTRACTION = "abstraction"
    REFINEMENT = "refinement"
    CONSISTENCY_CHECK = "consistency_check"
    INFERENCE = "inference"
    VALIDATION = "validation"
    SYNTHESIS = "synthesis"


@dataclass
class ReasoningStep:
    """A single step in the reasoning process."""
    step_id: str
    step_type: ReasoningStepType
    level: int
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    execution_time: float = 0.0
    coherence_score: float = 1.0
    abstraction_quality: float = 1.0
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert reasoning step to dictionary."""
        return {
            "step_id": self.step_id,
            "step_type": self.step_type.value,
            "level": self.level,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "execution_time": self.execution_time,
            "coherence_score": self.coherence_score,
            "abstraction_quality": self.abstraction_quality,
            "dependencies": self.dependencies,
            "metadata": self.metadata
        }


@dataclass
class AbstractionQuality:
    """Metrics for evaluating abstraction quality."""
    information_retention: float  # How much information is preserved
    complexity_reduction: float    # How much complexity is reduced
    coherence_maintenance: float  # How well coherence is maintained
    computational_efficiency: float # Computational cost vs benefit
    overall_quality: float         # Weighted overall score
    
    def calculate_overall(self, weights: Optional[Dict[str, float]] = None) -> float:
        """Calculate overall quality score."""
        if weights is None:
            weights = {
                "information_retention": 0.3,
                "complexity_reduction": 0.25,
                "coherence_maintenance": 0.25,
                "computational_efficiency": 0.2
            }
        
        self.overall_quality = (
            self.information_retention * weights["information_retention"] +
            self.complexity_reduction * weights["complexity_reduction"] +
            self.coherence_maintenance * weights["coherence_maintenance"] +
            self.computational_efficiency * weights["computational_efficiency"]
        )
        
        return self.overall_quality


class LevelSelector:
    """Selects optimal abstraction levels for reasoning tasks."""
    
    def __init__(self, min_level: int = 0, max_level: int = 10):
        self.min_level = min_level
        self.max_level = max_level
        self.level_performance: Dict[int, List[float]] = {i: [] for i in range(min_level, max_level + 1)}
        self.task_complexity_history: List[Tuple[float, int]] = []
        
    def select_level(self, task_complexity: float, 
                    coherence_threshold: float = 0.7) -> int:
        """Select optimal abstraction level for given task complexity."""
        
        # Base selection on complexity
        if task_complexity < 0.3:
            base_level = self.min_level + 1
        elif task_complexity < 0.7:
            base_level = self.min_level + 3
        else:
            base_level = self.max_level - 1
        
        # Adjust based on historical performance
        adjusted_level = self._adjust_based_on_performance(base_level, task_complexity)
        
        # Ensure level is within bounds
        selected_level = max(self.min_level, min(self.max_level, adjusted_level))
        
        # Record selection for learning
        self.task_complexity_history.append((task_complexity, selected_level))
        if len(self.task_complexity_history) > 1000:
            self.task_complexity_history.pop(0)
        
        return selected_level
    
    def _adjust_based_on_performance(self, base_level: int, task_complexity: float) -> int:
        """Adjust level selection based on historical performance."""
        if len(self.level_performance[base_level]) < 5:
            return base_level
        
        avg_performance = sum(self.level_performance[base_level]) / len(self.level_performance[base_level])
        
        if avg_performance < 0.6:
            # Try different levels
            if base_level > self.min_level:
                return base_level - 1
            elif base_level < self.max_level:
                return base_level + 1
        
        return base_level
    
    def record_performance(self, level: int, performance: float) -> None:
        """Record performance metrics for a level."""
        if level in self.level_performance:
            self.level_performance[level].append(performance)
            if len(self.level_performance[level]) > 100:
                self.level_performance[level].pop(0)
    
    def get_level_statistics(self) -> Dict[int, Dict[str, float]]:
        """Get performance statistics for each level."""
        stats = {}
        for level, performances in self.level_performance.items():
            if performances:
                stats[level] = {
                    "avg_performance": sum(performances) / len(performances),
                    "min_performance": min(performances),
                    "max_performance": max(performances),
                    "sample_count": len(performances)
                }
        return stats


class ReasoningPathOptimizer:
    """Optimizes reasoning paths for efficiency and coherence."""
    
    def __init__(self):
        self.path_history: List[List[ReasoningStep]] = []
        self.path_performance: List[float] = []
        
    def optimize_path(self, steps: List[ReasoningStep], 
                     constraints: Optional[Dict[str, Any]] = None) -> List[ReasoningStep]:
        """Optimize reasoning path based on historical performance and constraints."""
        if constraints is None:
            constraints = {}
        
        # Analyze current path
        path_analysis = self._analyze_path(steps)
        
        # Identify optimization opportunities
        optimizations = self._identify_optimizations(path_analysis, constraints)
        
        # Apply optimizations
        optimized_steps = self._apply_optimizations(steps, optimizations)
        
        return optimized_steps
    
    def _analyze_path(self, steps: List[ReasoningStep]) -> Dict[str, Any]:
        """Analyze reasoning path for bottlenecks and inefficiencies."""
        total_time = sum(step.execution_time for step in steps)
        avg_coherence = sum(step.coherence_score for step in steps) / len(steps) if steps else 0
        avg_quality = sum(step.abstraction_quality for step in steps) / len(steps) if steps else 0
        
        # Find bottleneck steps
        bottleneck_threshold = total_time / len(steps) * 1.5 if steps else 0
        bottlenecks = [step for step in steps if step.execution_time > bottleneck_threshold]
        
        # Find low coherence steps
        low_coherence_threshold = 0.7
        low_coherence_steps = [step for step in steps if step.coherence_score < low_coherence_threshold]
        
        return {
            "total_time": total_time,
            "avg_coherence": avg_coherence,
            "avg_quality": avg_quality,
            "bottlenecks": bottlenecks,
            "low_coherence_steps": low_coherence_steps,
            "step_count": len(steps)
        }
    
    def _identify_optimizations(self, analysis: Dict[str, Any], 
                               constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify specific optimizations to apply."""
        optimizations = []
        
        # Parallelization opportunities
        if analysis["step_count"] > 3:
            optimizations.append({
                "type": "parallelization",
                "steps": [step.step_id for step in analysis["bottlenecks"][:2]]
            })
        
        # Level adjustment for low coherence steps
        if analysis["low_coherence_steps"]:
            optimizations.append({
                "type": "level_adjustment",
                "steps": [step.step_id for step in analysis["low_coherence_steps"]],
                "adjustment": "decrease_level"
            })
        
        # Step elimination for redundant steps
        if analysis["step_count"] > 5:
            optimizations.append({
                "type": "step_elimination",
                "criteria": "redundant_abstraction"
            })
        
        return optimizations
    
    def _apply_optimizations(self, steps: List[ReasoningStep], 
                           optimizations: List[Dict[str, Any]]) -> List[ReasoningStep]:
        """Apply identified optimizations to the reasoning path."""
        optimized_steps = steps.copy()
        
        for optimization in optimizations:
            if optimization["type"] == "parallelization":
                # Mark steps for parallel execution
                step_ids = optimization["steps"]
                for step in optimized_steps:
                    if step.step_id in step_ids:
                        step.metadata["parallel"] = True
            
            elif optimization["type"] == "level_adjustment":
                # Adjust abstraction levels
                step_ids = optimization["steps"]
                adjustment = optimization["adjustment"]
                for step in optimized_steps:
                    if step.step_id in step_ids:
                        if adjustment == "decrease_level":
                            step.level = max(0, step.level - 1)
                        elif adjustment == "increase_level":
                            step.level = step.level + 1
        
        return optimized_steps
    
    def record_path_performance(self, path: List[ReasoningStep], performance: float) -> None:
        """Record performance of a reasoning path."""
        self.path_history.append(path)
        self.path_performance.append(performance)
        
        # Keep only recent history
        if len(self.path_history) > 1000:
            self.path_history.pop(0)
            self.path_performance.pop(0)


class ParallelReasoningManager:
    """Manages parallel execution of reasoning steps."""
    
    def __init__(self, max_concurrent_tasks: int = 4):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.execution_semaphore = asyncio.Semaphore(max_concurrent_tasks)
        
    async def execute_parallel_steps(self, steps: List[ReasoningStep]) -> List[ReasoningStep]:
        """Execute reasoning steps in parallel where possible."""
        # Identify parallelizable steps
        parallel_groups = self._identify_parallel_groups(steps)
        
        # Execute each group sequentially, but steps within groups in parallel
        completed_steps = []
        for group in parallel_groups:
            group_results = await asyncio.gather(
                *[self._execute_single_step(step) for step in group],
                return_exceptions=True
            )
            
            for result in group_results:
                if isinstance(result, Exception):
                    logging.error(f"Error in parallel step execution: {result}")
                else:
                    completed_steps.append(result)
        
        return completed_steps
    
    def _identify_parallel_groups(self, steps: List[ReasoningStep]) -> List[List[ReasoningStep]]:
        """Identify groups of steps that can be executed in parallel."""
        # Simple dependency-based grouping
        groups = []
        remaining_steps = steps.copy()
        
        while remaining_steps:
            # Find steps with no unmet dependencies
            ready_steps = []
            completed_step_ids = set()
            
            for group in groups:
                for step in group:
                    completed_step_ids.add(step.step_id)
            
            for step in remaining_steps:
                if all(dep_id in completed_step_ids for dep_id in step.dependencies):
                    ready_steps.append(step)
            
            if not ready_steps:
                # Circular dependency or error
                logging.warning("Circular dependency detected in reasoning steps")
                ready_steps = [remaining_steps[0]]
            
            groups.append(ready_steps)
            
            # Remove ready steps from remaining
            for step in ready_steps:
                remaining_steps.remove(step)
        
        return groups
    
    async def _execute_single_step(self, step: ReasoningStep) -> ReasoningStep:
        """Execute a single reasoning step."""
        async with self.execution_semaphore:
            start_time = time.time()
            
            try:
                # Simulate step execution
                await asyncio.sleep(0.1 * (step.level + 1))
                
                # Update step with execution results
                step.execution_time = time.time() - start_time
                step.coherence_score = min(1.0, 0.8 + (10 - step.level) * 0.02)
                step.abstraction_quality = min(1.0, 0.7 + step.level * 0.03)
                step.output_data = {
                    "result": f"executed_{step.step_type.value}",
                    "level": step.level,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logging.error(f"Error executing step {step.step_id}: {e}")
                step.execution_time = time.time() - start_time
                step.coherence_score = 0.0
                step.abstraction_quality = 0.0
                step.output_data = {"error": str(e)}
            
            return step


class ReasoningEngine:
    """Main reasoning engine that orchestrates all reasoning components."""
    
    def __init__(self, coherence_engine: CoherenceEngine, 
                 hierarchical_abstraction: HierarchicalAbstraction):
        self.coherence_engine = coherence_engine
        self.hierarchical_abstraction = hierarchical_abstraction
        
        # Initialize components
        self.level_selector = LevelSelector()
        self.path_optimizer = ReasoningPathOptimizer()
        self.parallel_manager = ParallelReasoningManager()
        
        # Reasoning state
        self.current_reasoning_path: List[ReasoningStep] = []
        self.reasoning_history: List[List[ReasoningStep]] = []
        self.performance_metrics: Dict[str, List[float]] = {
            "execution_time": [],
            "coherence_score": [],
            "abstraction_quality": [],
            "path_efficiency": []
        }
        
        # Configuration
        self.mode = ReasoningMode.ADAPTIVE
        self.coherence_threshold = 0.7
        self.max_reasoning_depth = 10
        
        self.logger = logging.getLogger("haai.reasoning_engine")
    
    async def reason(self, problem: Dict[str, Any], 
                    context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Main reasoning method that processes a problem and returns results."""
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting reasoning for problem: {problem.get('type', 'unknown')}")
            
            # Analyze problem complexity
            complexity = self._analyze_problem_complexity(problem)
            
            # Select reasoning mode
            mode = self._select_reasoning_mode(complexity, context)
            
            # Select abstraction level
            level = self.level_selector.select_level(complexity, self.coherence_threshold)
            
            # Create initial reasoning plan
            reasoning_plan = await self._create_reasoning_plan(problem, level, mode)
            
            # Optimize reasoning path
            optimized_plan = self.path_optimizer.optimize_path(reasoning_plan)
            
            # Execute reasoning
            if mode == ReasoningMode.PARALLEL:
                executed_steps = await self.parallel_manager.execute_parallel_steps(optimized_plan)
            else:
                executed_steps = await self._execute_sequential(optimized_plan)
            
            # Validate and synthesize results
            result = await self._synthesize_results(executed_steps, problem)
            
            # Record performance
            execution_time = time.time() - start_time
            self._record_performance(executed_steps, execution_time, complexity)
            
            # Update learning systems
            self.level_selector.record_performance(level, result.get("success_rate", 0.0))
            self.path_optimizer.record_path_performance(executed_steps, result.get("success_rate", 0.0))
            
            self.logger.info(f"Reasoning completed in {execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Reasoning failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time
            }
    
    def _analyze_problem_complexity(self, problem: Dict[str, Any]) -> float:
        """Analyze problem complexity on a scale of 0-1."""
        complexity_factors = {
            "input_size": len(str(problem.get("data", ""))) / 10000.0,  # Normalize by 10k chars
            "constraint_count": len(problem.get("constraints", [])) / 10.0,  # Normalize by 10 constraints
            "abstraction_depth": problem.get("required_depth", 5) / 10.0,  # Normalize by max depth
            "novelty": problem.get("novelty_score", 0.5)
        }
        
        # Weighted average
        weights = {"input_size": 0.2, "constraint_count": 0.2, "abstraction_depth": 0.3, "novelty": 0.3}
        
        complexity = sum(
            complexity_factors[factor] * weights[factor] 
            for factor in complexity_factors
        )
        
        return min(1.0, max(0.0, complexity))
    
    def _select_reasoning_mode(self, complexity: float, 
                              context: Optional[Dict[str, Any]]) -> ReasoningMode:
        """Select optimal reasoning mode based on complexity and context."""
        if self.mode == ReasoningMode.ADAPTIVE:
            if complexity < 0.3:
                return ReasoningMode.SEQUENTIAL
            elif complexity > 0.7:
                return ReasoningMode.PARALLEL
            else:
                return ReasoningMode.HIERARCHICAL
        
        return self.mode
    
    async def _create_reasoning_plan(self, problem: Dict[str, Any], level: int, 
                                   mode: ReasoningMode) -> List[ReasoningStep]:
        """Create initial reasoning plan."""
        steps = []
        step_counter = 0
        
        # Input processing step
        steps.append(ReasoningStep(
            step_id=f"step_{step_counter}",
            step_type=ReasoningStepType.ABSTRACTION,
            level=level,
            input_data={"problem": problem, "mode": mode.value},
            dependencies=[]
        ))
        step_counter += 1
        
        # Analysis steps based on problem type
        problem_type = problem.get("type", "general")
        if problem_type == "analysis":
            steps.extend(self._create_analysis_steps(step_counter, level))
            step_counter += len(steps) - 1
        elif problem_type == "synthesis":
            steps.extend(self._create_synthesis_steps(step_counter, level))
            step_counter += len(steps) - 1
        
        # Consistency checking
        steps.append(ReasoningStep(
            step_id=f"step_{step_counter}",
            step_type=ReasoningStepType.CONSISTENCY_CHECK,
            level=level,
            input_data={"previous_steps": [s.step_id for s in steps[:-1]]},
            dependencies=[s.step_id for s in steps[:-1]]
        ))
        step_counter += 1
        
        # Validation step
        steps.append(ReasoningStep(
            step_id=f"step_{step_counter}",
            step_type=ReasoningStepType.VALIDATION,
            level=level,
            input_data={"all_steps": [s.step_id for s in steps[:-1]]},
            dependencies=[s.step_id for s in steps[:-1]]
        ))
        
        return steps
    
    def _create_analysis_steps(self, start_id: int, level: int) -> List[ReasoningStep]:
        """Create steps specific to analysis problems."""
        steps = []
        
        steps.append(ReasoningStep(
            step_id=f"step_{start_id}",
            step_type=ReasoningStepType.INFERENCE,
            level=level,
            input_data={"operation": "decompose"},
            dependencies=[]
        ))
        
        steps.append(ReasoningStep(
            step_id=f"step_{start_id + 1}",
            step_type=ReasoningStepType.INFERENCE,
            level=level + 1,
            input_data={"operation": "analyze_components"},
            dependencies=[f"step_{start_id}"]
        ))
        
        return steps
    
    def _create_synthesis_steps(self, start_id: int, level: int) -> List[ReasoningStep]:
        """Create steps specific to synthesis problems."""
        steps = []
        
        steps.append(ReasoningStep(
            step_id=f"step_{start_id}",
            step_type=ReasoningStepType.REFINEMENT,
            level=level,
            input_data={"operation": "gather_components"},
            dependencies=[]
        ))
        
        steps.append(ReasoningStep(
            step_id=f"step_{start_id + 1}",
            step_type=ReasoningStepType.SYNTHESIS,
            level=level - 1 if level > 0 else level,
            input_data={"operation": "combine_results"},
            dependencies=[f"step_{start_id}"]
        ))
        
        return steps
    
    async def _execute_sequential(self, steps: List[ReasoningStep]) -> List[ReasoningStep]:
        """Execute reasoning steps sequentially."""
        executed_steps = []
        
        for step in steps:
            executed_step = await self.parallel_manager._execute_single_step(step)
            executed_steps.append(executed_step)
        
        return executed_steps
    
    async def _synthesize_results(self, steps: List[ReasoningStep], 
                                original_problem: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize results from executed reasoning steps."""
        if not steps:
            return {"success": False, "error": "No reasoning steps executed"}
        
        # Collect outputs
        outputs = [step.output_data for step in steps if step.output_data]
        
        # Calculate metrics
        avg_coherence = sum(step.coherence_score for step in steps) / len(steps)
        avg_quality = sum(step.abstraction_quality for step in steps) / len(steps)
        total_time = sum(step.execution_time for step in steps)
        
        # Check coherence threshold
        success = avg_coherence >= self.coherence_threshold
        
        # Create result
        result = {
            "success": success,
            "problem_type": original_problem.get("type", "unknown"),
            "reasoning_steps": [step.to_dict() for step in steps],
            "metrics": {
                "avg_coherence": avg_coherence,
                "avg_abstraction_quality": avg_quality,
                "total_execution_time": total_time,
                "step_count": len(steps)
            },
            "outputs": outputs,
            "synthesis": {
                "summary": f"Processed {len(steps)} reasoning steps",
                "confidence": avg_coherence * avg_quality,
                "recommendations": self._generate_recommendations(steps)
            }
        }
        
        return result
    
    def _generate_recommendations(self, steps: List[ReasoningStep]) -> List[str]:
        """Generate recommendations based on reasoning performance."""
        recommendations = []
        
        # Check for bottlenecks
        avg_time = sum(step.execution_time for step in steps) / len(steps)
        slow_steps = [step for step in steps if step.execution_time > avg_time * 1.5]
        if slow_steps:
            recommendations.append(f"Consider parallelization for {len(slow_steps)} bottleneck steps")
        
        # Check for low coherence
        low_coherence_steps = [step for step in steps if step.coherence_score < 0.7]
        if low_coherence_steps:
            recommendations.append(f"Adjust abstraction levels for {len(low_coherence_steps)} low-coherence steps")
        
        # Check level distribution
        levels = [step.level for step in steps]
        if max(levels) - min(levels) > 5:
            recommendations.append("Consider reducing abstraction level span for better coherence")
        
        return recommendations
    
    def _record_performance(self, steps: List[ReasoningStep], execution_time: float, 
                          complexity: float) -> None:
        """Record performance metrics for learning."""
        if not steps:
            return
        
        avg_coherence = sum(step.coherence_score for step in steps) / len(steps)
        avg_quality = sum(step.abstraction_quality for step in steps) / len(steps)
        
        # Path efficiency (quality vs time tradeoff)
        path_efficiency = (avg_coherence * avg_quality) / (execution_time + 1.0)
        
        self.performance_metrics["execution_time"].append(execution_time)
        self.performance_metrics["coherence_score"].append(avg_coherence)
        self.performance_metrics["abstraction_quality"].append(avg_quality)
        self.performance_metrics["path_efficiency"].append(path_efficiency)
        
        # Keep only recent metrics
        for metric in self.performance_metrics:
            if len(self.performance_metrics[metric]) > 1000:
                self.performance_metrics[metric].pop(0)
    
    def get_performance_summary(self) -> Dict[str, Dict[str, float]]:
        """Get summary of performance metrics."""
        summary = {}
        
        for metric, values in self.performance_metrics.items():
            if values:
                summary[metric] = {
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "count": len(values)
                }
        
        return summary
    
    def set_reasoning_mode(self, mode: ReasoningMode) -> None:
        """Set the reasoning mode."""
        self.mode = mode
        self.logger.info(f"Reasoning mode set to: {mode.value}")
    
    def set_coherence_threshold(self, threshold: float) -> None:
        """Set the coherence threshold for successful reasoning."""
        self.coherence_threshold = max(0.0, min(1.0, threshold))
        self.logger.info(f"Coherence threshold set to: {self.coherence_threshold}")