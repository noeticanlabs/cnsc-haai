"""
HAAI Attention Allocation System

Implements hierarchical attention mechanism with budget management,
attention-based resource scheduling, learning and adaptation, and visualization.
"""

import asyncio
import logging
import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from datetime import datetime
import numpy as np


class AttentionType(Enum):
    """Types of attention allocation."""
    FOCUSED = "focused"
    DISTRIBUTED = "distributed"
    HIERARCHICAL = "hierarchical"
    ADAPTIVE = "adaptive"


class AttentionPriority(Enum):
    """Priority levels for attention allocation."""
    CRITICAL = 3
    HIGH = 2
    MEDIUM = 1
    LOW = 0


@dataclass
class AttentionDemand:
    """Represents a demand for attention resources."""
    demand_id: str
    source: str
    priority: AttentionPriority
    required_attention: float
    expected_coherence_gain: float
    computational_cost: float
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_attention_ratio(self) -> float:
        """Calculate attention-to-coherence ratio."""
        if self.computational_cost == 0:
            return float('inf')
        return self.expected_coherence_gain / self.computational_cost


@dataclass
class AttentionBudget:
    """Manages attention budget allocation and tracking."""
    total_budget: float
    allocated_budget: float = 0.0
    available_budget: float = field(init=False)
    allocation_history: List[Dict[str, Any]] = field(default_factory=list)
    budget_replenish_rate: float = 10.0  # Budget units per second
    last_replenish: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        self.available_budget = self.total_budget
    
    def allocate(self, amount: float, demand_id: str, source: str) -> bool:
        """Allocate attention budget if available."""
        if amount <= self.available_budget:
            self.available_budget -= amount
            self.allocated_budget += amount
            
            self.allocation_history.append({
                "timestamp": datetime.now().isoformat(),
                "demand_id": demand_id,
                "source": source,
                "amount": amount,
                "type": "allocation"
            })
            
            return True
        return False
    
    def release(self, amount: float, demand_id: str) -> None:
        """Release allocated attention budget."""
        self.available_budget += amount
        self.allocated_budget = max(0, self.allocated_budget - amount)
        
        self.allocation_history.append({
            "timestamp": datetime.now().isoformat(),
            "demand_id": demand_id,
            "amount": amount,
            "type": "release"
        })
    
    def replenish(self) -> None:
        """Replenish attention budget over time."""
        current_time = datetime.now()
        time_delta = (current_time - self.last_replenish).total_seconds()
        
        replenish_amount = self.budget_replenish_rate * time_delta
        self.available_budget = min(
            self.total_budget,
            self.available_budget + replenish_amount
        )
        
        self.last_replenish = current_time
    
    def get_utilization(self) -> float:
        """Get current budget utilization ratio."""
        return self.allocated_budget / self.total_budget if self.total_budget > 0 else 0.0


class HierarchicalAttention:
    """Implements hierarchical attention mechanism ℓ* = argmax_ℓ(-Δ𝔠 / Δcompute)."""
    
    def __init__(self, min_level: int = 0, max_level: int = 10):
        self.min_level = min_level
        self.max_level = max_level
        self.level_attention_weights: Dict[int, float] = {
            i: 1.0 / (i + 1) for i in range(min_level, max_level + 1)
        }
        self.coherence_history: Dict[int, List[float]] = {
            i: [] for i in range(min_level, max_level + 1)
        }
        self.compute_history: Dict[int, List[float]] = {
            i: [] for i in range(min_level, max_level + 1)
        }
    
    def select_optimal_level(self, demands: List[AttentionDemand]) -> int:
        """
        Select optimal abstraction level using ℓ* = argmax_ℓ(-Δ𝔠 / Δcompute).
        
        This implements the core hierarchical attention mechanism that maximizes
        coherence gain per computational cost.
        """
        level_scores = {}
        
        for level in range(self.min_level, self.max_level + 1):
            # Calculate expected coherence change (Δ𝔠)
            delta_coherence = self._calculate_expected_coherence_change(level, demands)
            
            # Calculate expected computational change (Δcompute)
            delta_compute = self._calculate_expected_compute_change(level, demands)
            
            # Calculate attention score: -Δ𝔠 / Δcompute
            if delta_compute > 0:
                score = -delta_coherence / delta_compute
            else:
                score = float('-inf') if delta_coherence < 0 else float('inf')
            
            level_scores[level] = score
        
        # Select level with maximum score
        optimal_level = max(level_scores.keys(), key=lambda l: level_scores[l])
        
        return optimal_level
    
    def _calculate_expected_coherence_change(self, level: int, 
                                           demands: List[AttentionDemand]) -> float:
        """Calculate expected coherence change for given level."""
        if not self.coherence_history[level]:
            # Default expected coherence gain based on level
            return 0.1 * (self.max_level - level + 1) / self.max_level
        
        # Use historical data to estimate coherence change
        recent_coherence = self.coherence_history[level][-10:]  # Last 10 measurements
        if recent_coherence:
            avg_coherence = sum(recent_coherence) / len(recent_coherence)
            # Expected change is difference from optimal coherence
            return 1.0 - avg_coherence
        
        return 0.0
    
    def _calculate_expected_compute_change(self, level: int, 
                                         demands: List[AttentionDemand]) -> float:
        """Calculate expected computational change for given level."""
        if not self.compute_history[level]:
            # Default computational cost based on level (higher levels = more complex)
            return 0.1 * (level + 1) / self.max_level
        
        # Use historical data to estimate computational cost
        recent_compute = self.compute_history[level][-10:]  # Last 10 measurements
        if recent_compute:
            return sum(recent_compute) / len(recent_compute)
        
        return 0.1
    
    def record_coherence_measurement(self, level: int, coherence: float) -> None:
        """Record coherence measurement for learning."""
        if level in self.coherence_history:
            self.coherence_history[level].append(coherence)
            if len(self.coherence_history[level]) > 100:
                self.coherence_history[level].pop(0)
    
    def record_compute_measurement(self, level: int, compute_cost: float) -> None:
        """Record computational cost for learning."""
        if level in self.compute_history:
            self.compute_history[level].append(compute_cost)
            if len(self.compute_history[level]) > 100:
                self.compute_history[level].pop(0)
    
    def get_level_statistics(self) -> Dict[int, Dict[str, float]]:
        """Get statistics for each abstraction level."""
        stats = {}
        
        for level in range(self.min_level, self.max_level + 1):
            coherence_data = self.coherence_history[level]
            compute_data = self.compute_history[level]
            
            level_stats = {
                "attention_weight": self.level_attention_weights[level],
                "coherence_samples": len(coherence_data),
                "compute_samples": len(compute_data)
            }
            
            if coherence_data:
                level_stats["avg_coherence"] = sum(coherence_data) / len(coherence_data)
                level_stats["min_coherence"] = min(coherence_data)
                level_stats["max_coherence"] = max(coherence_data)
            
            if compute_data:
                level_stats["avg_compute"] = sum(compute_data) / len(compute_data)
                level_stats["min_compute"] = min(compute_data)
                level_stats["max_compute"] = max(compute_data)
            
            stats[level] = level_stats
        
        return stats


class AttentionScheduler:
    """Schedules attention allocation based on demands and constraints."""
    
    def __init__(self, budget: AttentionBudget, 
                 hierarchical_attention: HierarchicalAttention):
        self.budget = budget
        self.hierarchical_attention = hierarchical_attention
        self.pending_demands: List[AttentionDemand] = []
        self.active_allocations: Dict[str, Dict[str, Any]] = {}
        self.allocation_strategies: Dict[str, Callable] = {
            "priority_based": self._priority_based_allocation,
            "coherence_optimized": self._coherence_optimized_allocation,
            "balanced": self._balanced_allocation
        }
        self.current_strategy = "coherence_optimized"
        
    def submit_demand(self, demand: AttentionDemand) -> bool:
        """Submit a new attention demand."""
        self.pending_demands.append(demand)
        # Sort demands by priority and timestamp
        self.pending_demands.sort(
            key=lambda d: (-d.priority.value, d.timestamp)
        )
        return True
    
    async def process_demands(self) -> Dict[str, Any]:
        """Process pending attention demands."""
        if not self.pending_demands:
            return {"allocations": [], "remaining_budget": self.budget.available_budget}
        
        # Replenish budget
        self.budget.replenish()
        
        # Select optimal abstraction level
        optimal_level = self.hierarchical_attention.select_optimal_level(
            self.pending_demands
        )
        
        # Apply allocation strategy
        allocation_strategy = self.allocation_strategies.get(
            self.current_strategy, 
            self._coherence_optimized_allocation
        )
        
        allocations = await allocation_strategy(self.pending_demands, optimal_level)
        
        # Execute allocations
        successful_allocations = []
        for allocation in allocations:
            demand_id = allocation["demand_id"]
            amount = allocation["amount"]
            demand = next((d for d in self.pending_demands if d.demand_id == demand_id), None)
            
            if demand and self.budget.allocate(amount, demand_id, demand.source):
                self.active_allocations[demand_id] = {
                    "demand": demand,
                    "allocated_amount": amount,
                    "allocated_at": datetime.now(),
                    "level": optimal_level
                }
                successful_allocations.append(allocation)
                
                # Remove from pending demands
                self.pending_demands.remove(demand)
        
        return {
            "allocations": successful_allocations,
            "optimal_level": optimal_level,
            "remaining_budget": self.budget.available_budget,
            "utilization": self.budget.get_utilization()
        }
    
    async def _priority_based_allocation(self, demands: List[AttentionDemand], 
                                       level: int) -> List[Dict[str, Any]]:
        """Allocate attention based on priority."""
        allocations = []
        
        for demand in demands:
            if self.budget.available_budget >= demand.required_attention:
                allocations.append({
                    "demand_id": demand.demand_id,
                    "amount": demand.required_attention,
                    "strategy": "priority_based"
                })
        
        return allocations
    
    async def _coherence_optimized_allocation(self, demands: List[AttentionDemand], 
                                            level: int) -> List[Dict[str, Any]]:
        """Allocate attention to maximize coherence gain."""
        allocations = []
        
        # Sort by attention ratio (coherence gain per computational cost)
        sorted_demands = sorted(
            demands,
            key=lambda d: d.get_attention_ratio(),
            reverse=True
        )
        
        for demand in sorted_demands:
            if self.budget.available_budget >= demand.required_attention:
                allocations.append({
                    "demand_id": demand.demand_id,
                    "amount": demand.required_attention,
                    "strategy": "coherence_optimized"
                })
        
        return allocations
    
    async def _balanced_allocation(self, demands: List[AttentionDemand], 
                                 level: int) -> List[Dict[str, Any]]:
        """Balance priority and coherence optimization."""
        allocations = []
        
        # Calculate balanced scores
        for demand in demands:
            priority_score = demand.priority.value / 3.0  # Normalize to 0-1
            coherence_score = min(1.0, demand.get_attention_ratio() / 10.0)
            demand.metadata["balanced_score"] = (priority_score + coherence_score) / 2.0
        
        # Sort by balanced score
        sorted_demands = sorted(
            demands,
            key=lambda d: d.metadata.get("balanced_score", 0),
            reverse=True
        )
        
        for demand in sorted_demands:
            if self.budget.available_budget >= demand.required_attention:
                allocations.append({
                    "demand_id": demand.demand_id,
                    "amount": demand.required_attention,
                    "strategy": "balanced"
                })
        
        return allocations
    
    def release_allocation(self, demand_id: str) -> bool:
        """Release an active allocation."""
        if demand_id in self.active_allocations:
            allocation = self.active_allocations[demand_id]
            self.budget.release(
                allocation["allocated_amount"],
                demand_id
            )
            del self.active_allocations[demand_id]
            return True
        return False
    
    def get_allocation_status(self) -> Dict[str, Any]:
        """Get current allocation status."""
        return {
            "pending_demands": len(self.pending_demands),
            "active_allocations": len(self.active_allocations),
            "available_budget": self.budget.available_budget,
            "budget_utilization": self.budget.get_utilization(),
            "strategy": self.current_strategy,
            "active_allocation_details": {
                demand_id: {
                    "source": allocation["demand"].source,
                    "allocated_amount": allocation["allocated_amount"],
                    "duration": (datetime.now() - allocation["allocated_at"]).total_seconds()
                }
                for demand_id, allocation in self.active_allocations.items()
            }
        }


class AttentionLearningSystem:
    """Learns and adapts attention allocation strategies."""
    
    def __init__(self, hierarchical_attention: HierarchicalAttention):
        self.hierarchical_attention = hierarchical_attention
        self.allocation_outcomes: List[Dict[str, Any]] = []
        self.strategy_performance: Dict[str, List[float]] = {}
        self.learning_rate = 0.1
        
    def record_allocation_outcome(self, allocation: Dict[str, Any], 
                                 outcome: Dict[str, Any]) -> None:
        """Record the outcome of an attention allocation."""
        outcome_record = {
            "timestamp": datetime.now().isoformat(),
            "allocation": allocation,
            "outcome": outcome,
            "coherence_improvement": outcome.get("coherence_improvement", 0.0),
            "efficiency": outcome.get("efficiency", 0.0)
        }
        
        self.allocation_outcomes.append(outcome_record)
        
        # Update strategy performance
        strategy = allocation.get("strategy", "unknown")
        if strategy not in self.strategy_performance:
            self.strategy_performance[strategy] = []
        
        performance = outcome_record["coherence_improvement"] * outcome_record["efficiency"]
        self.strategy_performance[strategy].append(performance)
        
        # Keep only recent performance data
        if len(self.strategy_performance[strategy]) > 100:
            self.strategy_performance[strategy].pop(0)
        
        if len(self.allocation_outcomes) > 1000:
            self.allocation_outcomes.pop(0)
    
    def get_strategy_recommendations(self) -> Dict[str, float]:
        """Get recommendations for allocation strategies based on performance."""
        recommendations = {}
        
        for strategy, performances in self.strategy_performance.items():
            if performances:
                avg_performance = sum(performances) / len(performances)
                recommendations[strategy] = avg_performance
        
        return recommendations
    
    def adapt_attention_weights(self) -> None:
        """Adapt hierarchical attention weights based on outcomes."""
        if not self.allocation_outcomes:
            return
        
        # Analyze recent outcomes by level
        level_performance = {}
        
        for outcome in self.allocation_outcomes[-50:]:  # Last 50 outcomes
            level = outcome["allocation"].get("level", 0)
            if level not in level_performance:
                level_performance[level] = []
            
            performance = outcome["coherence_improvement"] * outcome["efficiency"]
            level_performance[level].append(performance)
        
        # Update attention weights
        for level, performances in level_performance.items():
            if performances and level in self.hierarchical_attention.level_attention_weights:
                avg_performance = sum(performances) / len(performances)
                
                # Adjust weight based on performance
                current_weight = self.hierarchical_attention.level_attention_weights[level]
                adjustment = self.learning_rate * (avg_performance - 0.5)  # 0.5 is baseline
                
                new_weight = max(0.1, current_weight + adjustment)
                self.hierarchical_attention.level_attention_weights[level] = new_weight


class AttentionVisualizer:
    """Provides visualization and analysis of attention allocation."""
    
    def __init__(self, attention_system: "AttentionSystem"):
        self.attention_system = attention_system
        
    def generate_attention_report(self) -> Dict[str, Any]:
        """Generate comprehensive attention allocation report."""
        budget = self.attention_system.budget
        hierarchical = self.attention_system.hierarchical_attention
        scheduler = self.attention_system.scheduler
        learning = self.attention_system.learning_system
        
        return {
            "timestamp": datetime.now().isoformat(),
            "budget_status": {
                "total_budget": budget.total_budget,
                "available_budget": budget.available_budget,
                "allocated_budget": budget.allocated_budget,
                "utilization": budget.get_utilization(),
                "replenish_rate": budget.budget_replenish_rate
            },
            "hierarchical_analysis": hierarchical.get_level_statistics(),
            "scheduler_status": scheduler.get_allocation_status(),
            "learning_insights": {
                "strategy_recommendations": learning.get_strategy_recommendations(),
                "total_outcomes": len(learning.allocation_outcomes),
                "recent_performance": self._calculate_recent_performance()
            },
            "attention_patterns": self._analyze_attention_patterns()
        }
    
    def _calculate_recent_performance(self) -> Dict[str, float]:
        """Calculate recent performance metrics."""
        learning = self.attention_system.learning_system
        
        if not learning.allocation_outcomes:
            return {}
        
        recent_outcomes = learning.allocation_outcomes[-20:]  # Last 20 outcomes
        
        avg_coherence = sum(o["coherence_improvement"] for o in recent_outcomes) / len(recent_outcomes)
        avg_efficiency = sum(o["efficiency"] for o in recent_outcomes) / len(recent_outcomes)
        
        return {
            "avg_coherence_improvement": avg_coherence,
            "avg_efficiency": avg_efficiency,
            "overall_performance": avg_coherence * avg_efficiency
        }
    
    def _analyze_attention_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in attention allocation."""
        scheduler = self.attention_system.scheduler
        
        # Analyze demand patterns
        demand_sources = {}
        priority_distribution = {p.value: 0 for p in AttentionPriority}
        
        for demand in scheduler.pending_demands:
            source = demand.source
            demand_sources[source] = demand_sources.get(source, 0) + 1
            priority_distribution[demand.priority.value] += 1
        
        for allocation in scheduler.active_allocations.values():
            demand = allocation["demand"]
            source = demand.source
            demand_sources[source] = demand_sources.get(source, 0) + 1
            priority_distribution[demand.priority.value] += 1
        
        return {
            "demand_sources": demand_sources,
            "priority_distribution": priority_distribution,
            "allocation_efficiency": self._calculate_allocation_efficiency()
        }
    
    def _calculate_allocation_efficiency(self) -> float:
        """Calculate overall allocation efficiency."""
        scheduler = self.attention_system.scheduler
        learning = self.attention_system.learning_system
        
        if not learning.allocation_outcomes:
            return 0.0
        
        # Calculate efficiency as coherence improvement per attention unit
        total_coherence_gain = sum(o["coherence_improvement"] for o in learning.allocation_outcomes[-50:])
        total_attention_used = sum(
            a["allocation"]["amount"] for a in learning.allocation_outcomes[-50:]
        )
        
        if total_attention_used > 0:
            return total_coherence_gain / total_attention_used
        
        return 0.0


class AttentionSystem:
    """Main attention allocation system that integrates all components."""
    
    def __init__(self, total_budget: float = 100.0, 
                 min_level: int = 0, max_level: int = 10):
        self.logger = logging.getLogger("haai.attention_system")
        
        # Initialize components
        self.budget = AttentionBudget(total_budget=total_budget)
        self.hierarchical_attention = HierarchicalAttention(min_level, max_level)
        self.scheduler = AttentionScheduler(self.budget, self.hierarchical_attention)
        self.learning_system = AttentionLearningSystem(self.hierarchical_attention)
        self.visualizer = AttentionVisualizer(self)
        
        # System state
        self.is_running = False
        self.processing_task: Optional[asyncio.Task] = None
        
    async def start(self) -> None:
        """Start the attention allocation system."""
        if self.is_running:
            return
        
        self.is_running = True
        self.processing_task = asyncio.create_task(self._processing_loop())
        self.logger.info("Attention allocation system started")
    
    async def stop(self) -> None:
        """Stop the attention allocation system."""
        self.is_running = False
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Attention allocation system stopped")
    
    async def _processing_loop(self) -> None:
        """Main processing loop for attention allocation."""
        while self.is_running:
            try:
                # Process pending demands
                result = await self.scheduler.process_demands()
                
                # Record outcomes for learning (simplified)
                for allocation in result["allocations"]:
                    # Simulate outcome
                    outcome = {
                        "coherence_improvement": 0.1 * np.random.random(),
                        "efficiency": 0.8 + 0.2 * np.random.random()
                    }
                    self.learning_system.record_allocation_outcome(allocation, outcome)
                
                # Adapt attention weights periodically
                if len(self.learning_system.allocation_outcomes) % 10 == 0:
                    self.learning_system.adapt_attention_weights()
                
                await asyncio.sleep(0.1)  # Process every 100ms
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in attention processing loop: {e}")
                await asyncio.sleep(1.0)
    
    def request_attention(self, source: str, priority: AttentionPriority,
                         required_attention: float, expected_coherence_gain: float,
                         computational_cost: float, 
                         metadata: Optional[Dict[str, Any]] = None) -> str:
        """Request attention allocation."""
        demand = AttentionDemand(
            demand_id=f"demand_{int(time.time() * 1000000)}",
            source=source,
            priority=priority,
            required_attention=required_attention,
            expected_coherence_gain=expected_coherence_gain,
            computational_cost=computational_cost,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        success = self.scheduler.submit_demand(demand)
        if success:
            return demand.demand_id
        else:
            raise RuntimeError("Failed to submit attention demand")
    
    def release_attention(self, demand_id: str) -> bool:
        """Release allocated attention."""
        return self.scheduler.release_allocation(demand_id)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status."""
        return self.visualizer.generate_attention_report()
    
    def set_allocation_strategy(self, strategy: str) -> None:
        """Set the allocation strategy."""
        if strategy in self.scheduler.allocation_strategies:
            self.scheduler.current_strategy = strategy
            self.logger.info(f"Allocation strategy set to: {strategy}")
        else:
            raise ValueError(f"Unknown strategy: {strategy}")