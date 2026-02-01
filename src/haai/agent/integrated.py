"""
Integrated HAAI Agent

This module demonstrates the complete integration of all HAAI components:
- Agent Core Architecture with lifecycle management
- Reasoning Engine with hierarchical abstraction
- Attention Allocation System with optimization
- Learning and Adaptation with receipt-based learning
- Tool Integration Framework with safety validation
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any

from .core import HAAIAgent, AgentStatus
from .reasoning import ReasoningEngine, ReasoningMode
from .attention import AttentionSystem, AttentionPriority
from .learning import LearningSystem, ReceiptType
from .tools import ToolFramework
from ..core import CoherenceEngine, HierarchicalAbstraction
from ..nsc import NSCProcessor, GLLLEncoder, GHLLProcessor
from ..nsc.gml import GMLMemory


class IntegratedHAAIAgent(HAAIAgent):
    """
    Fully integrated HAAI Agent that demonstrates all revolutionary capabilities:
    - Coherence-governed reasoning
    - Multi-level abstraction with bidirectional consistency
    - Adaptive attention allocation
    - Receipt-based learning
    - Tool integration with safety validation
    """
    
    def __init__(self, agent_id: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        # Initialize base agent
        super().__init__(agent_id, config)
        
        # Initialize integrated components
        self.reasoning_engine: Optional[ReasoningEngine] = None
        self.attention_system: Optional[AttentionSystem] = None
        self.learning_system: Optional[LearningSystem] = None
        self.tool_framework: Optional[ToolFramework] = None
        
        # Integration state
        self.is_fully_initialized = False
        self.integration_metrics: Dict[str, Any] = {}
        
        # Override initialization to include all components
        asyncio.create_task(self._integrated_initialize())
    
    async def _integrated_initialize(self) -> None:
        """Initialize all integrated components."""
        try:
            self.logger.info("Initializing Integrated HAAI Agent")
            
            # Wait for base initialization
            while self.state.status == AgentStatus.INITIALIZING:
                await asyncio.sleep(0.1)
            
            # Initialize reasoning engine
            self.reasoning_engine = ReasoningEngine(
                self.coherence_engine,
                self.hierarchical_abstraction
            )
            
            # Initialize attention system
            self.attention_system = AttentionSystem(
                total_budget=self.config.get("attention_budget", 100.0),
                min_level=0,
                max_level=10
            )
            
            # Initialize learning system
            self.learning_system = LearningSystem()
            
            # Initialize tool framework
            self.tool_framework = ToolFramework()
            
            # Start all systems
            await self.attention_system.start()
            await self.learning_system.start_learning()
            await self.tool_framework.initialize()
            
            # Setup integration callbacks
            self._setup_integration_callbacks()
            
            # Mark as fully initialized
            self.is_fully_initialized = True
            
            self.logger.info("Integrated HAAI Agent fully initialized")
            await self._trigger_event("integrated_agent_ready", {
                "agent_id": self.agent_id,
                "components": ["reasoning", "attention", "learning", "tools"]
            })
            
        except Exception as e:
            self.logger.error(f"Failed to initialize integrated agent: {e}")
            self.state.error_log.append(f"Integration error|{datetime.now().isoformat()}|{str(e)}")
    
    def _setup_integration_callbacks(self) -> None:
        """Setup callbacks for component integration."""
        # Reasoning completion callback
        if self.reasoning_engine:
            self.reasoning_engine.add_event_callback("reasoning_completed", 
                                                self._on_reasoning_completed)
        
        # Learning recommendations callback
        if self.learning_system:
            self.learning_system.add_event_callback("learning_updated",
                                                self._on_learning_updated)
    
    async def _on_reasoning_completed(self, data: Dict[str, Any]) -> None:
        """Handle reasoning completion event."""
        # Create learning receipt
        self.learning_system.add_learning_receipt(
            receipt_type=ReceiptType.REASONING_RECEIPT,
            context=data.get("context", {}),
            action=data.get("action", {}),
            outcome=data.get("outcome", {}),
            reward=data.get("reward", 0.0),
            metadata={"integration_event": True}
        )
    
    async def _on_learning_updated(self, data: Dict[str, Any]) -> None:
        """Handle learning update event."""
        # Update attention thresholds based on learning
        if self.attention_system and "thresholds" in data:
            thresholds = data["thresholds"]
            for threshold_name, value in thresholds.items():
                # Update attention system thresholds
                pass  # Implementation would depend on attention system interface
    
    async def demonstrate_hierarchical_reasoning(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """Demonstrate hierarchical reasoning capabilities."""
        if not self.is_fully_initialized:
            raise RuntimeError("Agent not fully initialized")
        
        self.logger.info(f"Demonstrating hierarchical reasoning for: {problem.get('type', 'unknown')}")
        
        # Request attention for reasoning task
        attention_request_id = self.attention_system.request_attention(
            source="hierarchical_reasoning",
            priority=AttentionPriority.HIGH,
            required_attention=20.0,
            expected_coherence_gain=0.8,
            computational_cost=0.3,
            metadata={"problem_type": problem.get("type")}
        )
        
        try:
            # Execute reasoning with different modes
            results = {}
            
            # Sequential reasoning
            self.reasoning_engine.set_reasoning_mode(ReasoningMode.SEQUENTIAL)
            sequential_result = await self.reasoning_engine.reason(problem)
            results["sequential"] = sequential_result
            
            # Parallel reasoning
            self.reasoning_engine.set_reasoning_mode(ReasoningMode.PARALLEL)
            parallel_result = await self.reasoning_engine.reason(problem)
            results["parallel"] = parallel_result
            
            # Hierarchical reasoning
            self.reasoning_engine.set_reasoning_mode(ReasoningMode.HIERARCHICAL)
            hierarchical_result = await self.reasoning_engine.reason(problem)
            results["hierarchical"] = hierarchical_result
            
            # Adaptive reasoning (best mode)
            self.reasoning_engine.set_reasoning_mode(ReasoningMode.ADAPTIVE)
            adaptive_result = await self.reasoning_engine.reason(problem)
            results["adaptive"] = adaptive_result
            
            # Compare results
            comparison = self._compare_reasoning_results(results)
            
            # Create learning receipt
            best_mode = comparison["best_mode"]
            best_result = results[best_mode]
            
            self.learning_system.add_learning_receipt(
                receipt_type=ReceiptType.REASONING_RECEIPT,
                context={"problem": problem, "demonstration": True},
                action={"reasoning_modes": list(results.keys())},
                outcome={"best_mode": best_mode, "comparison": comparison},
                reward=best_result.get("metrics", {}).get("avg_coherence", 0.0),
                metadata={"hierarchical_reasoning_demo": True}
            )
            
            return {
                "demonstration": "hierarchical_reasoning",
                "problem": problem,
                "results": results,
                "comparison": comparison,
                "best_mode": best_mode,
                "attention_used": attention_request_id
            }
            
        finally:
            # Release attention
            self.attention_system.release_attention(attention_request_id)
    
    def _compare_reasoning_results(self, results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Compare results from different reasoning modes."""
        comparison = {}
        best_mode = None
        best_score = -1.0
        
        for mode, result in results.items():
            metrics = result.get("metrics", {})
            coherence = metrics.get("avg_coherence", 0.0)
            quality = metrics.get("avg_abstraction_quality", 0.0)
            time_score = metrics.get("total_execution_time", 1.0)
            
            # Combined score (higher is better)
            combined_score = (coherence * quality) / (time_score + 1.0)
            
            comparison[mode] = {
                "coherence": coherence,
                "quality": quality,
                "execution_time": time_score,
                "combined_score": combined_score
            }
            
            if combined_score > best_score:
                best_score = combined_score
                best_mode = mode
        
        comparison["best_mode"] = best_mode
        comparison["best_score"] = best_score
        
        return comparison
    
    async def demonstrate_attention_allocation(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Demonstrate adaptive attention allocation."""
        if not self.is_fully_initialized:
            raise RuntimeError("Agent not fully initialized")
        
        self.logger.info(f"Demonstrating attention allocation for {len(tasks)} tasks")
        
        # Submit attention demands for all tasks
        demand_ids = []
        for i, task in enumerate(tasks):
            priority = AttentionPriority.HIGH if task.get("priority", "high") == "high" else AttentionPriority.MEDIUM
            
            demand_id = self.attention_system.request_attention(
                source=f"task_{i}",
                priority=priority,
                required_attention=task.get("attention_required", 10.0),
                expected_coherence_gain=task.get("coherence_gain", 0.5),
                computational_cost=task.get("compute_cost", 0.2),
                metadata={"task": task}
            )
            demand_ids.append(demand_id)
        
        # Wait for attention processing
        await asyncio.sleep(1.0)
        
        # Get attention system status
        attention_status = self.attention_system.get_system_status()
        
        # Process tasks with allocated attention
        task_results = []
        for i, (task, demand_id) in enumerate(zip(tasks, demand_ids)):
            # Simulate task processing
            await asyncio.sleep(0.1)
            
            task_result = {
                "task_id": i,
                "demand_id": demand_id,
                "completed": True,
                "attention_allocated": attention_status["budget_status"]["allocated_budget"],
                "coherence_improvement": 0.1 + (i * 0.05)  # Simulated improvement
            }
            task_results.append(task_result)
            
            # Release attention
            self.attention_system.release_attention(demand_id)
        
        # Create learning receipt
        total_coherence_gain = sum(r["coherence_improvement"] for r in task_results)
        self.learning_system.add_learning_receipt(
            receipt_type=ReceiptType.ATTENTION_RECEIPT,
            context={"task_count": len(tasks), "demonstration": True},
            action={"attention_allocation": "adaptive"},
            outcome={"tasks_completed": len(task_results), "coherence_gain": total_coherence_gain},
            reward=total_coherence_gain / len(tasks) if tasks else 0.0,
            metadata={"attention_allocation_demo": True}
        )
        
        return {
            "demonstration": "attention_allocation",
            "tasks": tasks,
            "results": task_results,
            "attention_status": attention_status,
            "total_coherence_gain": total_coherence_gain
        }
    
    async def demonstrate_tool_integration(self, operations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Demonstrate tool integration with safety validation."""
        if not self.is_fully_initialized:
            raise RuntimeError("Agent not fully initialized")
        
        self.logger.info(f"Demonstrating tool integration for {len(operations)} operations")
        
        operation_results = []
        
        for i, operation in enumerate(operations):
            # Execute operation using tool framework
            result = await self.tool_framework.execute_task(
                input_data=operation.get("input_data", {}),
                operation=operation.get("operation", "transform"),
                domain=operation.get("domain", "general"),
                constraints=operation.get("constraints", {})
            )
            
            operation_results.append({
                "operation_id": i,
                "operation": operation,
                "result": result,
                "timestamp": datetime.now().isoformat()
            })
            
            # Create learning receipt
            self.learning_system.add_learning_receipt(
                receipt_type=ReceiptType.TOOL_RECEIPT,
                context={"operation": operation, "demonstration": True},
                action={"tool_execution": True},
                outcome={"result": result},
                reward=1.0 if result.get("success", False) else 0.0,
                metadata={"tool_integration_demo": True}
            )
        
        # Get tool framework status
        framework_status = self.tool_framework.get_framework_status()
        
        return {
            "demonstration": "tool_integration",
            "operations": operations,
            "results": operation_results,
            "framework_status": framework_status,
            "success_rate": sum(1 for r in operation_results if r["result"].get("success", False)) / len(operation_results)
        }
    
    async def demonstrate_adaptive_learning(self, experiences: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Demonstrate adaptive learning from experiences."""
        if not self.is_fully_initialized:
            raise RuntimeError("Agent not fully initialized")
        
        self.logger.info(f"Demonstrating adaptive learning from {len(experiences)} experiences")
        
        # Process experiences through learning system
        for i, experience in enumerate(experiences):
            self.learning_system.add_learning_receipt(
                receipt_type=ReceiptType.ABSTRACTION_RECEIPT,
                context=experience.get("context", {}),
                action=experience.get("action", {}),
                outcome=experience.get("outcome", {}),
                reward=experience.get("reward", 0.0),
                metadata={"experience_id": i, "demonstration": True}
            )
        
        # Wait for learning to process
        await asyncio.sleep(2.0)
        
        # Get learning recommendations
        learning_recommendations = {}
        for experience in experiences:
            context = experience.get("context", {})
            recommendations = self.learning_system.get_learning_recommendations(context)
            learning_recommendations[experience.get("id", i)] = recommendations
        
        # Get learning summary
        learning_summary = self.learning_system.get_learning_summary()
        
        return {
            "demonstration": "adaptive_learning",
            "experiences": experiences,
            "recommendations": learning_recommendations,
            "learning_summary": learning_summary
        }
    
    async def comprehensive_demonstration(self) -> Dict[str, Any]:
        """Run comprehensive demonstration of all HAAI capabilities."""
        if not self.is_fully_initialized:
            raise RuntimeError("Agent not fully initialized")
        
        self.logger.info("Starting comprehensive HAAI demonstration")
        
        start_time = time.time()
        demonstration_results = {}
        
        try:
            # 1. Hierarchical Reasoning Demonstration
            reasoning_problem = {
                "type": "analysis",
                "data": "Sample complex problem requiring multi-level abstraction",
                "constraints": ["coherence_check", "validation"],
                "required_depth": 5
            }
            
            reasoning_demo = await self.demonstrate_hierarchical_reasoning(reasoning_problem)
            demonstration_results["reasoning"] = reasoning_demo
            
            # 2. Attention Allocation Demonstration
            attention_tasks = [
                {"priority": "high", "attention_required": 15.0, "coherence_gain": 0.8, "compute_cost": 0.3},
                {"priority": "medium", "attention_required": 10.0, "coherence_gain": 0.6, "compute_cost": 0.2},
                {"priority": "medium", "attention_required": 8.0, "coherence_gain": 0.5, "compute_cost": 0.15}
            ]
            
            attention_demo = await self.demonstrate_attention_allocation(attention_tasks)
            demonstration_results["attention"] = attention_demo
            
            # 3. Tool Integration Demonstration
            tool_operations = [
                {
                    "input_data": {"type": "json", "data": {"key": "value"}},
                    "operation": "transform",
                    "domain": "data_processing"
                },
                {
                    "input_data": {"type": "json", "data": {"field": "test"}},
                    "operation": "validate",
                    "domain": "data_quality"
                }
            ]
            
            tool_demo = await self.demonstrate_tool_integration(tool_operations)
            demonstration_results["tools"] = tool_demo
            
            # 4. Adaptive Learning Demonstration
            learning_experiences = [
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
            
            learning_demo = await self.demonstrate_adaptive_learning(learning_experiences)
            demonstration_results["learning"] = learning_demo
            
            # Calculate overall metrics
            total_time = time.time() - start_time
            
            overall_metrics = {
                "total_demonstration_time": total_time,
                "components_demonstrated": len(demonstration_results),
                "reasoning_success": reasoning_demo.get("comparison", {}).get("best_score", 0.0),
                "attention_efficiency": attention_demo.get("total_coherence_gain", 0.0),
                "tool_success_rate": tool_demo.get("success_rate", 0.0),
                "learning_adaptations": len(learning_demo.get("recommendations", {})),
                "overall_coherence": self.state.coherence_score,
                "agent_health": self.health_checker.health_score
            }
            
            demonstration_results["overall_metrics"] = overall_metrics
            demonstration_results["demonstration_successful"] = True
            
            self.logger.info(f"Comprehensive demonstration completed in {total_time:.2f}s")
            
            return demonstration_results
            
        except Exception as e:
            self.logger.error(f"Comprehensive demonstration failed: {e}")
            return {
                "demonstration_successful": False,
                "error": str(e),
                "partial_results": demonstration_results,
                "total_time": time.time() - start_time
            }
    
    async def shutdown(self) -> None:
        """Shutdown integrated agent and all components."""
        self.logger.info("Shutting down Integrated HAAI Agent")
        
        # Shutdown integrated components
        if self.attention_system:
            await self.attention_system.stop()
        
        if self.learning_system:
            await self.learning_system.stop_learning()
        
        if self.tool_framework:
            await self.tool_framework.shutdown()
        
        # Shutdown base agent
        await super().shutdown()
        
        self.logger.info("Integrated HAAI Agent shutdown complete")


# Factory function for creating integrated agents
async def create_integrated_haai_agent(agent_id: Optional[str] = None,
                                     config: Optional[Dict[str, Any]] = None) -> IntegratedHAAIAgent:
    """Create and initialize an integrated HAAI agent."""
    agent = IntegratedHAAIAgent(agent_id, config)
    
    # Wait for full initialization
    while not agent.is_fully_initialized:
        await asyncio.sleep(0.1)
    
    return agent