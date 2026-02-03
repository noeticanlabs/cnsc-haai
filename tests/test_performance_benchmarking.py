"""
Performance Benchmarking

Comprehensive performance testing including scalability testing across multiple dimensions,
latency and throughput benchmarking, resource utilization profiling, distributed computing
capabilities, memory usage and garbage collection, and performance optimization validation.
"""

import pytest
import asyncio
import time
import psutil
import threading
import multiprocessing
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import numpy as np
import matplotlib.pyplot as plt
import json
import gc
import tracemalloc

from src.haai.agent import create_integrated_haai_agent, ReasoningEngine
from src.haai.core import CoherenceEngine, HierarchicalAbstraction
from src.haai.nsc import GLLLEncoder, GHLLProcessor, GMLMemory
from tests.test_framework import TestFramework, measure_async_performance


@dataclass
class PerformanceMetric:
    """Performance metric data structure."""
    name: str
    value: float
    unit: str
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkResult:
    """Result of a performance benchmark."""
    benchmark_name: str
    test_parameters: Dict[str, Any]
    metrics: List[PerformanceMetric]
    start_time: datetime
    end_time: datetime
    success: bool = True
    error_message: Optional[str] = None


class ScalabilityTester:
    """Tests scalability across multiple dimensions."""
    
    def __init__(self):
        self.scalability_dimensions = [
            "data_size",
            "concurrent_users",
            "complexity_level",
            "abstraction_depth",
            "reasoning_steps"
        ]
    
    async def test_data_size_scalability(self, reasoning_engine) -> BenchmarkResult:
        """Test scalability with increasing data sizes."""
        benchmark_name = "data_size_scalability"
        start_time = datetime.now()
        metrics = []
        
        data_sizes = [100, 1000, 10000, 100000, 1000000]
        
        for size in data_sizes:
            # Generate test data
            test_data = {
                "features": np.random.random(size).tolist(),
                "weights": [1.0/size] * size,
                "operation": "coherence_calculation"
            }
            
            # Measure performance
            start = time.time()
            memory_before = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            try:
                result = await reasoning_engine.reason(test_data)
                
                end = time.time()
                memory_after = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                
                execution_time = end - start
                memory_usage = memory_after - memory_before
                throughput = size / execution_time
                
                metrics.extend([
                    PerformanceMetric(
                        name="execution_time",
                        value=execution_time,
                        unit="seconds",
                        timestamp=datetime.now(),
                        context={"data_size": size}
                    ),
                    PerformanceMetric(
                        name="memory_usage",
                        value=memory_usage,
                        unit="MB",
                        timestamp=datetime.now(),
                        context={"data_size": size}
                    ),
                    PerformanceMetric(
                        name="throughput",
                        value=throughput,
                        unit="items/second",
                        timestamp=datetime.now(),
                        context={"data_size": size}
                    )
                ])
                
            except Exception as e:
                metrics.append(PerformanceMetric(
                    name="error",
                    value=1,
                    unit="count",
                    timestamp=datetime.now(),
                    context={"data_size": size, "error": str(e)}
                ))
        
        end_time = datetime.now()
        
        return BenchmarkResult(
            benchmark_name=benchmark_name,
            test_parameters={"data_sizes": data_sizes},
            metrics=metrics,
            start_time=start_time,
            end_time=end_time
        )
    
    async def test_concurrent_users_scalability(self) -> BenchmarkResult:
        """Test scalability with increasing concurrent users."""
        benchmark_name = "concurrent_users_scalability"
        start_time = datetime.now()
        metrics = []
        
        user_counts = [1, 5, 10, 25, 50, 100]
        
        for user_count in user_counts:
            # Create concurrent tasks
            async def simulate_user_workload(user_id: int):
                agent = await create_integrated_haai_agent(
                    agent_id=f"user_{user_id}",
                    config={"attention_budget": 50.0}
                )
                
                try:
                    # Simulate user workload
                    await agent.demonstrate_hierarchical_reasoning({
                        "type": "analysis",
                        "data": f"User {user_id} test data",
                        "constraints": []
                    })
                    
                    return {"success": True, "user_id": user_id}
                finally:
                    await agent.shutdown()
            
            # Measure performance
            start = time.time()
            memory_before = psutil.Process().memory_info().rss / 1024 / 1024
            
            # Run concurrent users
            tasks = [simulate_user_workload(i) for i in range(user_count)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            end = time.time()
            memory_after = psutil.Process().memory_info().rss / 1024 / 1024
            
            execution_time = end - start
            memory_usage = memory_after - memory_before
            successful_users = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
            success_rate = successful_users / user_count
            
            metrics.extend([
                PerformanceMetric(
                    name="execution_time",
                    value=execution_time,
                    unit="seconds",
                    timestamp=datetime.now(),
                    context={"user_count": user_count}
                ),
                PerformanceMetric(
                    name="memory_usage",
                    value=memory_usage,
                    unit="MB",
                    timestamp=datetime.now(),
                    context={"user_count": user_count}
                ),
                PerformanceMetric(
                    name="success_rate",
                    value=success_rate,
                    unit="ratio",
                    timestamp=datetime.now(),
                    context={"user_count": user_count}
                ),
                PerformanceMetric(
                    name="throughput",
                    value=user_count / execution_time,
                    unit="users/second",
                    timestamp=datetime.now(),
                    context={"user_count": user_count}
                )
            ])
        
        end_time = datetime.now()
        
        return BenchmarkResult(
            benchmark_name=benchmark_name,
            test_parameters={"user_counts": user_counts},
            metrics=metrics,
            start_time=start_time,
            end_time=end_time
        )
    
    async def test_complexity_scalability(self, reasoning_engine) -> BenchmarkResult:
        """Test scalability with increasing problem complexity."""
        benchmark_name = "complexity_scalability"
        start_time = datetime.now()
        metrics = []
        
        complexity_levels = [0.1, 0.3, 0.5, 0.7, 0.9]
        
        for complexity in complexity_levels:
            # Generate problem with specified complexity
            problem = {
                "type": "analysis",
                "data": f"Complexity {complexity} problem",
                "constraints": [f"constraint_{i}" for i in range(int(complexity * 10))],
                "complexity": complexity
            }
            
            # Measure performance
            start = time.time()
            
            try:
                result = await reasoning_engine.reason(problem, mode="hierarchical")
                
                end = time.time()
                execution_time = end - start
                reasoning_steps = result.get("reasoning_steps", 0)
                
                metrics.extend([
                    PerformanceMetric(
                        name="execution_time",
                        value=execution_time,
                        unit="seconds",
                        timestamp=datetime.now(),
                        context={"complexity": complexity}
                    ),
                    PerformanceMetric(
                        name="reasoning_steps",
                        value=reasoning_steps,
                        unit="steps",
                        timestamp=datetime.now(),
                        context={"complexity": complexity}
                    ),
                    PerformanceMetric(
                        name="efficiency",
                        value=reasoning_steps / execution_time if execution_time > 0 else 0,
                        unit="steps/second",
                        timestamp=datetime.now(),
                        context={"complexity": complexity}
                    )
                ])
                
            except Exception as e:
                metrics.append(PerformanceMetric(
                    name="error",
                    value=1,
                    unit="count",
                    timestamp=datetime.now(),
                    context={"complexity": complexity, "error": str(e)}
                ))
        
        end_time = datetime.now()
        
        return BenchmarkResult(
            benchmark_name=benchmark_name,
            test_parameters={"complexity_levels": complexity_levels},
            metrics=metrics,
            start_time=start_time,
            end_time=end_time
        )


class LatencyThroughputBenchmark:
    """Tests for latency and throughput benchmarking."""
    
    def __init__(self):
        self.operation_types = [
            "coherence_calculation",
            "abstraction_transformation",
            "reasoning_inference",
            "policy_enforcement",
            "tool_execution"
        ]
    
    async def benchmark_latency(self, component, operation_type: str) -> BenchmarkResult:
        """Benchmark operation latency."""
        benchmark_name = f"latency_{operation_type}"
        start_time = datetime.now()
        metrics = []
        
        # Warm up
        for _ in range(5):
            await self._execute_operation(component, operation_type)
        
        # Measure latency
        latencies = []
        for i in range(100):
            start = time.time()
            await self._execute_operation(component, operation_type)
            end = time.time()
            latencies.append(end - start)
        
        # Calculate statistics
        latencies = np.array(latencies)
        
        metrics.extend([
            PerformanceMetric(
                name="mean_latency",
                value=np.mean(latencies),
                unit="seconds",
                timestamp=datetime.now()
            ),
            PerformanceMetric(
                name="median_latency",
                value=np.median(latencies),
                unit="seconds",
                timestamp=datetime.now()
            ),
            PerformanceMetric(
                name="p95_latency",
                value=np.percentile(latencies, 95),
                unit="seconds",
                timestamp=datetime.now()
            ),
            PerformanceMetric(
                name="p99_latency",
                value=np.percentile(latencies, 99),
                unit="seconds",
                timestamp=datetime.now()
            ),
            PerformanceMetric(
                name="min_latency",
                value=np.min(latencies),
                unit="seconds",
                timestamp=datetime.now()
            ),
            PerformanceMetric(
                name="max_latency",
                value=np.max(latencies),
                unit="seconds",
                timestamp=datetime.now()
            )
        ])
        
        end_time = datetime.now()
        
        return BenchmarkResult(
            benchmark_name=benchmark_name,
            test_parameters={"operation_type": operation_type, "sample_count": 100},
            metrics=metrics,
            start_time=start_time,
            end_time=end_time
        )
    
    async def benchmark_throughput(self, component, operation_type: str) -> BenchmarkResult:
        """Benchmark operation throughput."""
        benchmark_name = f"throughput_{operation_type}"
        start_time = datetime.now()
        metrics = []
        
        # Test different durations
        durations = [1, 5, 10, 30]  # seconds
        
        for duration in durations:
            start = time.time()
            operations_completed = 0
            
            while time.time() - start < duration:
                await self._execute_operation(component, operation_type)
                operations_completed += 1
            
            actual_duration = time.time() - start
            throughput = operations_completed / actual_duration
            
            metrics.append(PerformanceMetric(
                name="throughput",
                value=throughput,
                unit="operations/second",
                timestamp=datetime.now(),
                context={"duration": duration, "operations_completed": operations_completed}
            ))
        
        end_time = datetime.now()
        
        return BenchmarkResult(
            benchmark_name=benchmark_name,
            test_parameters={"operation_type": operation_type, "durations": durations},
            metrics=metrics,
            start_time=start_time,
            end_time=end_time
        )
    
    async def _execute_operation(self, component, operation_type: str):
        """Execute a specific operation type for benchmarking."""
        if operation_type == "coherence_calculation":
            if hasattr(component, 'calculate_coherence'):
                data = {"features": [0.5, 0.5, 0.5], "weights": [1/3, 1/3, 1/3]}
                await component.calculate_coherence(data)
        elif operation_type == "abstraction_transformation":
            if hasattr(component, 'abstract'):
                data = {"type": "test", "content": list(range(100))}
                await component.abstract(data, target_level=2)
        elif operation_type == "reasoning_inference":
            if hasattr(component, 'reason'):
                problem = {"type": "analysis", "data": "test problem"}
                await component.reason(problem)
        elif operation_type == "policy_enforcement":
            if hasattr(component, 'govern_action'):
                action = {"coherence_score": 0.8, "operation": "test"}
                await component.govern_action(action, {})
        elif operation_type == "tool_execution":
            if hasattr(component, 'execute_task'):
                task = {"input_data": {"test": "data"}, "operation": "transform"}
                await component.execute_task(task)


class ResourceUtilizationProfiler:
    """Tests for resource utilization profiling."""
    
    def __init__(self):
        self.resource_types = ["cpu", "memory", "disk_io", "network_io"]
    
    async def profile_resource_utilization(self, component, operation_duration: int = 60) -> BenchmarkResult:
        """Profile resource utilization over time."""
        benchmark_name = "resource_utilization_profile"
        start_time = datetime.now()
        metrics = []
        
        # Start monitoring
        process = psutil.Process()
        monitoring_active = True
        
        async def monitor_resources():
            """Monitor resource usage in background."""
            while monitoring_active:
                cpu_percent = process.cpu_percent()
                memory_info = process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
                
                # Get disk I/O
                io_counters = process.io_counters()
                disk_read_mb = io_counters.read_bytes / 1024 / 1024
                disk_write_mb = io_counters.write_bytes / 1024 / 1024
                
                metrics.extend([
                    PerformanceMetric(
                        name="cpu_usage",
                        value=cpu_percent,
                        unit="percent",
                        timestamp=datetime.now()
                    ),
                    PerformanceMetric(
                        name="memory_usage",
                        value=memory_mb,
                        unit="MB",
                        timestamp=datetime.now()
                    ),
                    PerformanceMetric(
                        name="disk_read",
                        value=disk_read_mb,
                        unit="MB",
                        timestamp=datetime.now()
                    ),
                    PerformanceMetric(
                        name="disk_write",
                        value=disk_write_mb,
                        unit="MB",
                        timestamp=datetime.now()
                    )
                ])
                
                await asyncio.sleep(1)  # Sample every second
        
        # Start monitoring task
        monitor_task = asyncio.create_task(monitor_resources())
        
        try:
            # Run workload for specified duration
            start_workload = time.time()
            
            while time.time() - start_workload < operation_duration:
                if hasattr(component, 'reason'):
                    await component.reason({"type": "analysis", "data": "workload data"})
                else:
                    await asyncio.sleep(0.1)
        
        finally:
            # Stop monitoring
            monitoring_active = False
            await monitor_task
        
        end_time = datetime.now()
        
        return BenchmarkResult(
            benchmark_name=benchmark_name,
            test_parameters={"operation_duration": operation_duration},
            metrics=metrics,
            start_time=start_time,
            end_time=end_time
        )
    
    def analyze_resource_patterns(self, metrics: List[PerformanceMetric]) -> Dict[str, Any]:
        """Analyze resource usage patterns from metrics."""
        analysis = {}
        
        for resource_type in self.resource_types:
            resource_metrics = [m for m in metrics if resource_type in m.name]
            
            if resource_metrics:
                values = [m.value for m in resource_metrics]
                
                analysis[resource_type] = {
                    "mean": np.mean(values),
                    "std": np.std(values),
                    "min": np.min(values),
                    "max": np.max(values),
                    "p95": np.percentile(values, 95),
                    "p99": np.percentile(values, 99)
                }
        
        return analysis


class DistributedComputingTester:
    """Tests for distributed computing capabilities."""
    
    def __init__(self):
        self.node_counts = [1, 2, 4, 8]
    
    async def test_distributed_reasoning(self, node_count: int) -> BenchmarkResult:
        """Test distributed reasoning across multiple nodes."""
        benchmark_name = f"distributed_reasoning_{node_count}_nodes"
        start_time = datetime.now()
        metrics = []
        
        # Create distributed agents
        agents = []
        for i in range(node_count):
            agent = await create_integrated_haai_agent(
                agent_id=f"distributed_agent_{i}",
                config={"attention_budget": 100.0}
            )
            agents.append(agent)
        
        try:
            # Create distributed problem
            problem = {
                "type": "distributed_analysis",
                "data": f"Distributed test data for {node_count} nodes",
                "subtasks": node_count,
                "coordination_required": True
            }
            
            # Measure distributed execution
            start_execution = time.time()
            
            # Simulate distributed execution
            tasks = []
            for i, agent in enumerate(agents):
                subtask = {
                    "type": "subtask",
                    "data": f"Subtask {i} data",
                    "node_id": i
                }
                tasks.append(agent.demonstrate_hierarchical_reasoning(subtask))
            
            results = await asyncio.gather(*tasks)
            
            end_execution = time.time()
            execution_time = end_execution - start_execution
            
            # Analyze results
            successful_nodes = sum(1 for r in results if r.get("demonstration") == "hierarchical_reasoning")
            success_rate = successful_nodes / node_count
            
            metrics.extend([
                PerformanceMetric(
                    name="execution_time",
                    value=execution_time,
                    unit="seconds",
                    timestamp=datetime.now()
                ),
                PerformanceMetric(
                    name="success_rate",
                    value=success_rate,
                    unit="ratio",
                    timestamp=datetime.now()
                ),
                PerformanceMetric(
                    name="scalability_efficiency",
                    value=successful_nodes / execution_time if execution_time > 0 else 0,
                    unit="nodes/second",
                    timestamp=datetime.now()
                )
            ])
            
        finally:
            # Clean up agents
            for agent in agents:
                await agent.shutdown()
        
        end_time = datetime.now()
        
        return BenchmarkResult(
            benchmark_name=benchmark_name,
            test_parameters={"node_count": node_count},
            metrics=metrics,
            start_time=start_time,
            end_time=end_time
        )
    
    async def test_load_balancing(self, node_count: int) -> BenchmarkResult:
        """Test load balancing across distributed nodes."""
        benchmark_name = f"load_balancing_{node_count}_nodes"
        start_time = datetime.now()
        metrics = []
        
        # Create agents with different capacities
        agents = []
        capacities = [50, 100, 150, 200]  # Different attention budgets
        
        for i in range(node_count):
            capacity = capacities[i % len(capacities)]
            agent = await create_integrated_haai_agent(
                agent_id=f"load_balance_agent_{i}",
                config={"attention_budget": capacity}
            )
            agents.append(agent)
        
        try:
            # Generate workload
            workload_size = node_count * 10
            tasks = []
            
            for i in range(workload_size):
                # Simple load balancing strategy: round-robin
                agent_index = i % node_count
                task = agents[agent_index].demonstrate_hierarchical_reasoning({
                    "type": "load_test",
                    "data": f"Load test task {i}",
                    "complexity": 0.5
                })
                tasks.append(task)
            
            # Measure load balancing performance
            start_execution = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_execution = time.time()
            
            execution_time = end_execution - start_execution
            successful_tasks = sum(1 for r in results if not isinstance(r, Exception))
            
            metrics.extend([
                PerformanceMetric(
                    name="execution_time",
                    value=execution_time,
                    unit="seconds",
                    timestamp=datetime.now()
                ),
                PerformanceMetric(
                    name="successful_tasks",
                    value=successful_tasks,
                    unit="count",
                    timestamp=datetime.now()
                ),
                PerformanceMetric(
                    name="throughput",
                    value=successful_tasks / execution_time if execution_time > 0 else 0,
                    unit="tasks/second",
                    timestamp=datetime.now()
                )
            ])
            
        finally:
            for agent in agents:
                await agent.shutdown()
        
        end_time = datetime.now()
        
        return BenchmarkResult(
            benchmark_name=benchmark_name,
            test_parameters={"node_count": node_count, "workload_size": workload_size},
            metrics=metrics,
            start_time=start_time,
            end_time=end_time
        )


class MemoryGarbageCollectionTester:
    """Tests for memory usage and garbage collection."""
    
    def __init__(self):
        self.memory_test_scenarios = [
            "normal_operation",
            "memory_pressure",
            "memory_leak_detection",
            "gc_efficiency"
        ]
    
    async def test_memory_usage_patterns(self) -> BenchmarkResult:
        """Test memory usage patterns under different scenarios."""
        benchmark_name = "memory_usage_patterns"
        start_time = datetime.now()
        metrics = []
        
        # Start memory tracking
        tracemalloc.start()
        
        for scenario in self.memory_test_scenarios:
            if scenario == "normal_operation":
                await self._test_normal_memory_usage(metrics)
            elif scenario == "memory_pressure":
                await self._test_memory_pressure(metrics)
            elif scenario == "memory_leak_detection":
                await self._test_memory_leak_detection(metrics)
            elif scenario == "gc_efficiency":
                await self._test_garbage_collection_efficiency(metrics)
        
        # Stop memory tracking
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        metrics.extend([
            PerformanceMetric(
                name="current_memory_usage",
                value=current / 1024 / 1024,  # Convert to MB
                unit="MB",
                timestamp=datetime.now()
            ),
            PerformanceMetric(
                name="peak_memory_usage",
                value=peak / 1024 / 1024,  # Convert to MB
                unit="MB",
                timestamp=datetime.now()
            )
        ])
        
        end_time = datetime.now()
        
        return BenchmarkResult(
            benchmark_name=benchmark_name,
            test_parameters={"scenarios": self.memory_test_scenarios},
            metrics=metrics,
            start_time=start_time,
            end_time=end_time
        )
    
    async def _test_normal_memory_usage(self, metrics: List[PerformanceMetric]):
        """Test memory usage during normal operation."""
        process = psutil.Process()
        
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        # Create and use agents normally
        agents = []
        for i in range(5):
            agent = await create_integrated_haai_agent(
                agent_id=f"memory_test_agent_{i}"
            )
            agents.append(agent)
            
            # Perform some operations
            await agent.demonstrate_hierarchical_reasoning({
                "type": "memory_test",
                "data": f"Memory test data {i}"
            })
        
        peak_memory = process.memory_info().rss / 1024 / 1024
        
        # Clean up
        for agent in agents:
            await agent.shutdown()
        
        # Force garbage collection
        gc.collect()
        
        final_memory = process.memory_info().rss / 1024 / 1024
        
        metrics.extend([
            PerformanceMetric(
                name="normal_initial_memory",
                value=initial_memory,
                unit="MB",
                timestamp=datetime.now(),
                context={"scenario": "normal_operation"}
            ),
            PerformanceMetric(
                name="normal_peak_memory",
                value=peak_memory,
                unit="MB",
                timestamp=datetime.now(),
                context={"scenario": "normal_operation"}
            ),
            PerformanceMetric(
                name="normal_final_memory",
                value=final_memory,
                unit="MB",
                timestamp=datetime.now(),
                context={"scenario": "normal_operation"}
            ),
            PerformanceMetric(
                name="normal_memory_growth",
                value=peak_memory - initial_memory,
                unit="MB",
                timestamp=datetime.now(),
                context={"scenario": "normal_operation"}
            )
        ])
    
    async def _test_memory_pressure(self, metrics: List[PerformanceMetric]):
        """Test behavior under memory pressure."""
        process = psutil.Process()
        
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        # Create many agents to create memory pressure
        agents = []
        try:
            for i in range(20):
                agent = await create_integrated_haai_agent(
                    agent_id=f"pressure_agent_{i}",
                    config={"attention_budget": 200.0}  # Larger budget
                )
                agents.append(agent)
                
                # Perform memory-intensive operations
                await agent.demonstrate_hierarchical_reasoning({
                    "type": "memory_intensive",
                    "data": list(range(1000)),  # Larger data
                    "constraints": [f"constraint_{j}" for j in range(100)]
                })
                
                # Check memory usage
                current_memory = process.memory_info().rss / 1024 / 1024
                if current_memory > initial_memory + 500:  # 500MB increase limit
                    break
        
        finally:
            for agent in agents:
                await agent.shutdown()
        
        gc.collect()
        final_memory = process.memory_info().rss / 1024 / 1024
        
        metrics.extend([
            PerformanceMetric(
                name="pressure_initial_memory",
                value=initial_memory,
                unit="MB",
                timestamp=datetime.now(),
                context={"scenario": "memory_pressure"}
            ),
            PerformanceMetric(
                name="pressure_final_memory",
                value=final_memory,
                unit="MB",
                timestamp=datetime.now(),
                context={"scenario": "memory_pressure"}
            ),
            PerformanceMetric(
                name="pressure_memory_recovery",
                value=max(0, final_memory - initial_memory),
                unit="MB",
                timestamp=datetime.now(),
                context={"scenario": "memory_pressure"}
            )
        ])
    
    async def _test_memory_leak_detection(self, metrics: List[PerformanceMetric]):
        """Test for memory leaks."""
        process = psutil.Process()
        
        memory_samples = []
        
        # Repeatedly create and destroy agents
        for cycle in range(5):
            cycle_memory = []
            
            # Create agents
            agents = []
            for i in range(10):
                agent = await create_integrated_haai_agent(
                    agent_id=f"leak_test_agent_{cycle}_{i}"
                )
                agents.append(agent)
            
            # Use agents
            for agent in agents:
                await agent.demonstrate_hierarchical_reasoning({
                    "type": "leak_test",
                    "data": f"Leak test data {cycle}"
                })
            
            # Measure memory after usage
            cycle_memory.append(process.memory_info().rss / 1024 / 1024)
            
            # Clean up
            for agent in agents:
                await agent.shutdown()
            
            gc.collect()
            
            # Measure memory after cleanup
            cycle_memory.append(process.memory_info().rss / 1024 / 1024)
            memory_samples.append(cycle_memory)
        
        # Analyze memory leak patterns
        final_memories = [sample[1] for sample in memory_samples]
        memory_trend = np.polyfit(range(len(final_memories)), final_memories, 1)[0]
        
        metrics.append(PerformanceMetric(
            name="memory_leak_trend",
            value=memory_trend,
            unit="MB/cycle",
            timestamp=datetime.now(),
            context={"scenario": "memory_leak_detection"}
        ))
    
    async def _test_garbage_collection_efficiency(self, metrics: List[PerformanceMetric]):
        """Test garbage collection efficiency."""
        process = psutil.Process()
        
        # Test different GC strategies
        gc_strategies = ["default", "aggressive", "minimal"]
        
        for strategy in gc_strategies:
            initial_memory = process.memory_info().rss / 1024 / 1024
            
            # Configure GC based on strategy
            if strategy == "aggressive":
                gc.set_threshold(100, 10, 10)  # More frequent collection
            elif strategy == "minimal":
                gc.set_threshold(1000, 100, 100)  # Less frequent collection
            else:
                gc.set_threshold(700, 10, 10)  # Default
            
            # Create and destroy objects
            objects = []
            for i in range(100):
                agent = await create_integrated_haai_agent(
                    agent_id=f"gc_test_agent_{strategy}_{i}"
                )
                objects.append(agent)
            
            # Use objects
            for agent in objects:
                await agent.demonstrate_hierarchical_reasoning({
                    "type": "gc_test",
                    "data": f"GC test data {strategy}"
                })
            
            # Destroy objects
            for agent in objects:
                await agent.shutdown()
            
            # Force garbage collection
            start_gc = time.time()
            collected = gc.collect()
            end_gc = time.time()
            
            final_memory = process.memory_info().rss / 1024 / 1024
            
            metrics.extend([
                PerformanceMetric(
                    name=f"gc_efficiency_{strategy}",
                    value=collected,
                    unit="objects_collected",
                    timestamp=datetime.now(),
                    context={"strategy": strategy}
                ),
                PerformanceMetric(
                    name=f"gc_time_{strategy}",
                    value=end_gc - start_gc,
                    unit="seconds",
                    timestamp=datetime.now(),
                    context={"strategy": strategy}
                ),
                PerformanceMetric(
                    name=f"gc_memory_recovery_{strategy}",
                    value=max(0, initial_memory - final_memory),
                    unit="MB",
                    timestamp=datetime.now(),
                    context={"strategy": strategy}
                )
            ])


class PerformanceOptimizationValidator:
    """Tests for performance optimization validation."""
    
    def __init__(self):
        self.optimization_techniques = [
            "caching",
            "parallelization",
            "algorithm_optimization",
            "resource_pooling"
        ]
    
    async def validate_optimization_techniques(self) -> BenchmarkResult:
        """Validate various performance optimization techniques."""
        benchmark_name = "performance_optimization_validation"
        start_time = datetime.now()
        metrics = []
        
        for technique in self.optimization_techniques:
            if technique == "caching":
                await self._test_caching_optimization(metrics)
            elif technique == "parallelization":
                await self._test_parallelization_optimization(metrics)
            elif technique == "algorithm_optimization":
                await self._test_algorithm_optimization(metrics)
            elif technique == "resource_pooling":
                await self._test_resource_pooling_optimization(metrics)
        
        end_time = datetime.now()
        
        return BenchmarkResult(
            benchmark_name=benchmark_name,
            test_parameters={"techniques": self.optimization_techniques},
            metrics=metrics,
            start_time=start_time,
            end_time=end_time
        )
    
    async def _test_caching_optimization(self, metrics: List[PerformanceMetric]):
        """Test caching optimization."""
        # Test without cache
        start_time = time.time()
        for i in range(100):
            agent = await create_integrated_haai_agent(
                agent_id=f"no_cache_agent_{i}"
            )
            await agent.demonstrate_hierarchical_reasoning({
                "type": "cache_test",
                "data": "repeated_data"  # Same data for all
            })
            await agent.shutdown()
        no_cache_time = time.time() - start_time
        
        # Test with cache (simulated)
        start_time = time.time()
        cached_results = {}
        
        for i in range(100):
            cache_key = "repeated_data"
            
            if cache_key in cached_results:
                result = cached_results[cache_key]
            else:
                agent = await create_integrated_haai_agent(
                    agent_id=f"cache_agent_{i}"
                )
                result = await agent.demonstrate_hierarchical_reasoning({
                    "type": "cache_test",
                    "data": cache_key
                })
                cached_results[cache_key] = result
                await agent.shutdown()
        
        cache_time = time.time() - start_time
        
        speedup = no_cache_time / cache_time if cache_time > 0 else 0
        
        metrics.extend([
            PerformanceMetric(
                name="caching_speedup",
                value=speedup,
                unit="ratio",
                timestamp=datetime.now(),
                context={"technique": "caching"}
            ),
            PerformanceMetric(
                name="caching_efficiency",
                value=len(cached_results) / 100,  # Cache hit rate
                unit="ratio",
                timestamp=datetime.now(),
                context={"technique": "caching"}
            )
        ])
    
    async def _test_parallelization_optimization(self, metrics: List[PerformanceMetric]):
        """Test parallelization optimization."""
        # Test sequential execution
        start_time = time.time()
        
        for i in range(10):
            agent = await create_integrated_haai_agent(
                agent_id=f"sequential_agent_{i}"
            )
            await agent.demonstrate_hierarchical_reasoning({
                "type": "parallel_test",
                "data": f"Sequential data {i}"
            })
            await agent.shutdown()
        
        sequential_time = time.time() - start_time
        
        # Test parallel execution
        start_time = time.time()
        
        tasks = []
        for i in range(10):
            agent = await create_integrated_haai_agent(
                agent_id=f"parallel_agent_{i}"
            )
            task = agent.demonstrate_hierarchical_reasoning({
                "type": "parallel_test",
                "data": f"Parallel data {i}"
            })
            tasks.append((agent, task))
        
        # Execute tasks in parallel
        parallel_results = await asyncio.gather(*[task for _, task in tasks])
        
        # Clean up
        for agent, _ in tasks:
            await agent.shutdown()
        
        parallel_time = time.time() - start_time
        
        speedup = sequential_time / parallel_time if parallel_time > 0 else 0
        
        metrics.append(PerformanceMetric(
            name="parallelization_speedup",
            value=speedup,
            unit="ratio",
            timestamp=datetime.now(),
            context={"technique": "parallelization"}
        ))
    
    async def _test_algorithm_optimization(self, metrics: List[PerformanceMetric]):
        """Test algorithm optimization."""
        # This would test different algorithm implementations
        # For demonstration, we'll simulate with different complexity levels
        
        complexity_levels = [0.1, 0.5, 0.9]
        
        for complexity in complexity_levels:
            # Test naive approach
            start_time = time.time()
            agent = await create_integrated_haai_agent(
                agent_id=f"naive_agent_{complexity}"
            )
            await agent.demonstrate_hierarchical_reasoning({
                "type": "algorithm_test",
                "data": f"Naive algorithm test {complexity}",
                "complexity": complexity,
                "algorithm": "naive"
            })
            await agent.shutdown()
            naive_time = time.time() - start_time
            
            # Test optimized approach
            start_time = time.time()
            agent = await create_integrated_haai_agent(
                agent_id=f"optimized_agent_{complexity}"
            )
            await agent.demonstrate_hierarchical_reasoning({
                "type": "algorithm_test",
                "data": f"Optimized algorithm test {complexity}",
                "complexity": complexity,
                "algorithm": "optimized"
            })
            await agent.shutdown()
            optimized_time = time.time() - start_time
            
            speedup = naive_time / optimized_time if optimized_time > 0 else 0
            
            metrics.append(PerformanceMetric(
                name="algorithm_speedup",
                value=speedup,
                unit="ratio",
                timestamp=datetime.now(),
                context={"technique": "algorithm_optimization", "complexity": complexity}
            ))
    
    async def _test_resource_pooling_optimization(self, metrics: List[PerformanceMetric]):
        """Test resource pooling optimization."""
        # Test without pooling (create new resources each time)
        start_time = time.time()
        
        for i in range(20):
            agent = await create_integrated_haai_agent(
                agent_id=f"no_pool_agent_{i}"
            )
            await agent.demonstrate_hierarchical_reasoning({
                "type": "pool_test",
                "data": f"No pool data {i}"
            })
            await agent.shutdown()
        
        no_pool_time = time.time() - start_time
        
        # Test with pooling (reuse resources)
        start_time = time.time()
        
        # Create a pool of agents
        pool_agents = []
        for i in range(5):  # Smaller pool
            agent = await create_integrated_haai_agent(
                agent_id=f"pool_agent_{i}"
            )
            pool_agents.append(agent)
        
        # Reuse agents from pool
        for i in range(20):
            agent = pool_agents[i % len(pool_agents)]
            await agent.demonstrate_hierarchical_reasoning({
                "type": "pool_test",
                "data": f"Pool data {i}"
            })
        
        # Clean up pool
        for agent in pool_agents:
            await agent.shutdown()
        
        pool_time = time.time() - start_time
        
        speedup = no_pool_time / pool_time if pool_time > 0 else 0
        
        metrics.extend([
            PerformanceMetric(
                name="resource_pooling_speedup",
                value=speedup,
                unit="ratio",
                timestamp=datetime.now(),
                context={"technique": "resource_pooling"}
            ),
            PerformanceMetric(
                name="resource_pool_efficiency",
                value=20 / 5,  # Operations per resource
                unit="ops/resource",
                timestamp=datetime.now(),
                context={"technique": "resource_pooling"}
            )
        ])


# Integration test class
class TestPerformanceBenchmarking:
    """Integration tests for performance benchmarking."""
    
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
    def scalability_tester(self):
        """Create a scalability tester."""
        return ScalabilityTester()
    
    @pytest.fixture
    def latency_throughput_benchmark(self):
        """Create a latency/throughput benchmark."""
        return LatencyThroughputBenchmark()
    
    @pytest.fixture
    def resource_profiler(self):
        """Create a resource utilization profiler."""
        return ResourceUtilizationProfiler()
    
    @pytest.fixture
    def distributed_tester(self):
        """Create a distributed computing tester."""
        return DistributedComputingTester()
    
    @pytest.fixture
    def memory_gc_tester(self):
        """Create a memory and garbage collection tester."""
        return MemoryGarbageCollectionTester()
    
    @pytest.fixture
    def optimization_validator(self):
        """Create a performance optimization validator."""
        return PerformanceOptimizationValidator()
    
    @pytest.mark.asyncio
    async def test_comprehensive_performance_benchmarking(self,
                                                         reasoning_engine,
                                                         scalability_tester,
                                                         latency_throughput_benchmark,
                                                         resource_profiler,
                                                         distributed_tester,
                                                         memory_gc_tester,
                                                         optimization_validator):
        """Test comprehensive performance benchmarking."""
        # Run all performance benchmarks
        data_size_result = await scalability_tester.test_data_size_scalability(reasoning_engine)
        complexity_result = await scalability_tester.test_complexity_scalability(reasoning_engine)
        concurrent_result = await scalability_tester.test_concurrent_users_scalability()
        
        latency_result = await latency_throughput_benchmark.benchmark_latency(reasoning_engine, "reasoning_inference")
        throughput_result = await latency_throughput_benchmark.benchmark_throughput(reasoning_engine, "reasoning_inference")
        
        resource_result = await resource_profiler.profile_resource_utilization(reasoning_engine, operation_duration=30)
        
        distributed_results = []
        for node_count in [1, 2, 4]:
            result = await distributed_tester.test_distributed_reasoning(node_count)
            distributed_results.append(result)
        
        memory_result = await memory_gc_tester.test_memory_usage_patterns()
        optimization_result = await optimization_validator.validate_optimization_techniques()
        
        # Compile comprehensive results
        comprehensive_results = {
            "scalability": {
                "data_size": data_size_result,
                "complexity": complexity_result,
                "concurrent_users": concurrent_result
            },
            "latency_throughput": {
                "latency": latency_result,
                "throughput": throughput_result
            },
            "resource_utilization": resource_result,
            "distributed_computing": distributed_results,
            "memory_garbage_collection": memory_result,
            "performance_optimization": optimization_result,
            "overall_summary": {
                "total_benchmark_categories": 6,
                "benchmark_execution_time": self._calculate_total_execution_time([
                    data_size_result, complexity_result, concurrent_result,
                    latency_result, throughput_result, resource_result,
                    *distributed_results, memory_result, optimization_result
                ])
            }
        }
        
        # Assert performance requirements
        # Latency should be reasonable
        latency_metrics = [m for m in latency_result.metrics if m.name == "mean_latency"]
        if latency_metrics:
            assert latency_metrics[0].value < 1.0, f"Mean latency too high: {latency_metrics[0].value}s"
        
        # Memory usage should be reasonable
        memory_metrics = [m for m in memory_result.metrics if m.name == "peak_memory_usage"]
        if memory_metrics:
            assert memory_metrics[0].value < 1000, f"Peak memory usage too high: {memory_metrics[0].value}MB"
        
        return comprehensive_results
    
    def _calculate_total_execution_time(self, results: List[BenchmarkResult]) -> float:
        """Calculate total execution time across all benchmarks."""
        total_time = 0
        for result in results:
            if result.start_time and result.end_time:
                duration = (result.end_time - result.start_time).total_seconds()
                total_time += duration
        return total_time
    
    @pytest.mark.asyncio
    async def test_performance_regression_detection(self, reasoning_engine):
        """Test performance regression detection."""
        scalability_tester = ScalabilityTester()
        
        # Run baseline performance test
        baseline_result = await scalability_tester.test_data_size_scalability(reasoning_engine)
        
        # Extract key performance metrics
        baseline_metrics = {}
        for metric in baseline_result.metrics:
            if metric.name in ["execution_time", "throughput"]:
                context_size = metric.context.get("data_size", 0)
                key = f"{metric.name}_{context_size}"
                baseline_metrics[key] = metric.value
        
        # Performance should be within reasonable bounds
        for key, value in baseline_metrics.items():
            if "execution_time" in key:
                assert value < 10.0, f"Execution time too high for {key}: {value}s"
            elif "throughput" in key:
                assert value > 100, f"Throughput too low for {key}: {value} items/sec"