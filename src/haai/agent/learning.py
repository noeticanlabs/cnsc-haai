"""
HAAI Learning and Adaptation System

Implements receipt-based learning, abstraction strategy optimization,
adaptive threshold tuning, meta-learning for level selection, and experience replay.
"""

import asyncio
import logging
import math
import time
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict, deque


class LearningMode(Enum):
    """Different learning modes."""
    ONLINE = "online"
    BATCH = "batch"
    REINFORCEMENT = "reinforcement"
    META_LEARNING = "meta_learning"


class ReceiptType(Enum):
    """Types of learning receipts."""
    REASONING_RECEIPT = "reasoning_receipt"
    ABSTRACTION_RECEIPT = "abstraction_receipt"
    ATTENTION_RECEIPT = "attention_receipt"
    TOOL_RECEIPT = "tool_receipt"
    COHERENCE_RECEIPT = "coherence_receipt"


@dataclass
class LearningReceipt:
    """Receipt that captures learning experience."""
    receipt_id: str
    receipt_type: ReceiptType
    timestamp: datetime
    context: Dict[str, Any]
    action: Dict[str, Any]
    outcome: Dict[str, Any]
    reward: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert receipt to dictionary."""
        return {
            "receipt_id": self.receipt_id,
            "receipt_type": self.receipt_type.value,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
            "action": self.action,
            "outcome": self.outcome,
            "reward": self.reward,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LearningReceipt":
        """Create receipt from dictionary."""
        return cls(
            receipt_id=data["receipt_id"],
            receipt_type=ReceiptType(data["receipt_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            context=data["context"],
            action=data["action"],
            outcome=data["outcome"],
            reward=data["reward"],
            metadata=data.get("metadata", {})
        )


@dataclass
class AbstractionStrategy:
    """Represents an abstraction strategy with its parameters and performance."""
    strategy_id: str
    parameters: Dict[str, Any]
    performance_history: List[float] = field(default_factory=list)
    usage_count: int = 0
    last_updated: datetime = field(default_factory=datetime.now)
    
    def get_average_performance(self) -> float:
        """Get average performance of the strategy."""
        if not self.performance_history:
            return 0.0
        return sum(self.performance_history) / len(self.performance_history)
    
    def update_performance(self, performance: float) -> None:
        """Update strategy performance."""
        self.performance_history.append(performance)
        self.usage_count += 1
        self.last_updated = datetime.now()
        
        # Keep only recent performance history
        if len(self.performance_history) > 100:
            self.performance_history.pop(0)


class ReceiptBasedLearning:
    """Core receipt-based learning system."""
    
    def __init__(self, max_receipts: int = 10000):
        self.max_receipts = max_receipts
        self.receipts: deque = deque(maxlen=max_receipts)
        self.receipt_index: Dict[str, LearningReceipt] = {}
        self.receipt_patterns: Dict[str, List[LearningReceipt]] = defaultdict(list)
        self.learning_rate = 0.1
        self.discount_factor = 0.95
        
    def add_receipt(self, receipt: LearningReceipt) -> None:
        """Add a new learning receipt."""
        self.receipts.append(receipt)
        self.receipt_index[receipt.receipt_id] = receipt
        
        # Index by patterns
        pattern_key = self._generate_pattern_key(receipt.context, receipt.action)
        self.receipt_patterns[pattern_key].append(receipt)
        
        # Keep pattern history manageable
        if len(self.receipt_patterns[pattern_key]) > 100:
            self.receipt_patterns[pattern_key].pop(0)
    
    def _generate_pattern_key(self, context: Dict[str, Any], 
                            action: Dict[str, Any]) -> str:
        """Generate pattern key for receipt indexing."""
        # Simplified pattern generation - in practice would be more sophisticated
        context_type = context.get("type", "unknown")
        action_type = action.get("type", "unknown")
        complexity_level = context.get("complexity_level", 0)
        
        return f"{context_type}_{action_type}_{complexity_level}"
    
    def find_similar_receipts(self, context: Dict[str, Any], 
                            action: Dict[str, Any], 
                            max_similar: int = 10) -> List[LearningReceipt]:
        """Find receipts similar to given context and action."""
        pattern_key = self._generate_pattern_key(context, action)
        
        if pattern_key not in self.receipt_patterns:
            return []
        
        similar_receipts = self.receipt_patterns[pattern_key]
        
        # Sort by recency and reward
        sorted_receipts = sorted(
            similar_receipts,
            key=lambda r: (r.timestamp, r.reward),
            reverse=True
        )
        
        return sorted_receipts[:max_similar]
    
    def predict_outcome(self, context: Dict[str, Any], 
                       action: Dict[str, Any]) -> Dict[str, Any]:
        """Predict outcome based on similar receipts."""
        similar_receipts = self.find_similar_receipts(context, action)
        
        if not similar_receipts:
            return {"predicted_reward": 0.0, "confidence": 0.0, "similar_count": 0}
        
        # Calculate weighted average of outcomes
        total_weight = 0.0
        weighted_reward = 0.0
        
        for receipt in similar_receipts:
            # Weight by recency and similarity (simplified)
            recency_weight = math.exp(- (datetime.now() - receipt.timestamp).total_seconds() / 3600.0)
            similarity_weight = receipt.reward  # Simplified similarity
            
            weight = recency_weight * similarity_weight
            total_weight += weight
            weighted_reward += receipt.reward * weight
        
        predicted_reward = weighted_reward / total_weight if total_weight > 0 else 0.0
        confidence = min(1.0, len(similar_receipts) / 10.0)
        
        return {
            "predicted_reward": predicted_reward,
            "confidence": confidence,
            "similar_count": len(similar_receipts),
            "sample_receipts": [r.receipt_id for r in similar_receipts[:3]]
        }
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """Get learning system statistics."""
        receipt_counts = defaultdict(int)
        reward_sum = defaultdict(float)
        
        for receipt in self.receipts:
            receipt_counts[receipt.receipt_type.value] += 1
            reward_sum[receipt.receipt_type.value] += receipt.reward
        
        stats = {
            "total_receipts": len(self.receipts),
            "receipt_types": dict(receipt_counts),
            "average_rewards": {
                receipt_type: (reward_sum[receipt_type] / receipt_counts[receipt_type] 
                             if receipt_counts[receipt_type] > 0 else 0.0)
                for receipt_type in receipt_counts
            },
            "pattern_count": len(self.receipt_patterns),
            "learning_rate": self.learning_rate
        }
        
        return stats


class AbstractionOptimizer:
    """Optimizes abstraction strategies based on learning receipts."""
    
    def __init__(self, receipt_learning: ReceiptBasedLearning):
        self.receipt_learning = receipt_learning
        self.strategies: Dict[str, AbstractionStrategy] = {}
        self.current_strategy: Optional[str] = None
        self.optimization_history: List[Dict[str, Any]] = []
        
    def register_strategy(self, strategy_id: str, parameters: Dict[str, Any]) -> None:
        """Register a new abstraction strategy."""
        self.strategies[strategy_id] = AbstractionStrategy(
            strategy_id=strategy_id,
            parameters=parameters
        )
        
        if self.current_strategy is None:
            self.current_strategy = strategy_id
    
    def select_strategy(self, context: Dict[str, Any]) -> str:
        """Select best strategy for given context."""
        if not self.strategies:
            raise ValueError("No strategies registered")
        
        # Evaluate each strategy for the current context
        strategy_scores = {}
        
        for strategy_id, strategy in self.strategies.items():
            score = self._evaluate_strategy(strategy, context)
            strategy_scores[strategy_id] = score
        
        # Select strategy with highest score
        best_strategy_id = max(strategy_scores.keys(), 
                              key=lambda s: strategy_scores[s])
        
        self.current_strategy = best_strategy_id
        return best_strategy_id
    
    def _evaluate_strategy(self, strategy: AbstractionStrategy, 
                          context: Dict[str, Any]) -> float:
        """Evaluate strategy performance for given context."""
        # Base score from historical performance
        base_score = strategy.get_average_performance()
        
        # Context-specific adjustments
        context_type = context.get("type", "unknown")
        complexity = context.get("complexity", 0.5)
        
        # Predict performance using similar receipts
        mock_action = {"type": "abstraction", "strategy": strategy.strategy_id}
        prediction = self.receipt_learning.predict_outcome(context, mock_action)
        
        predicted_score = prediction["predicted_reward"]
        confidence = prediction["confidence"]
        
        # Combine scores with confidence weighting
        combined_score = (base_score * (1 - confidence) + 
                         predicted_score * confidence)
        
        # Adjust for complexity
        if complexity > 0.7 and strategy.parameters.get("depth", 1) < 3:
            combined_score *= 0.8  # Penalize shallow strategies for complex problems
        elif complexity < 0.3 and strategy.parameters.get("depth", 1) > 5:
            combined_score *= 0.8  # Penalize deep strategies for simple problems
        
        return combined_score
    
    def update_strategy_performance(self, strategy_id: str, 
                                  performance: float) -> None:
        """Update strategy performance based on execution results."""
        if strategy_id in self.strategies:
            self.strategies[strategy_id].update_performance(performance)
    
    def optimize_parameters(self, strategy_id: str) -> Dict[str, Any]:
        """Optimize parameters for a given strategy."""
        if strategy_id not in self.strategies:
            raise ValueError(f"Strategy {strategy_id} not found")
        
        strategy = self.strategies[strategy_id]
        current_params = strategy.parameters.copy()
        
        # Get recent receipts for this strategy
        relevant_receipts = [
            r for r in self.receipt_learning.receipts
            if r.action.get("strategy") == strategy_id
            and (datetime.now() - r.timestamp).total_seconds() < 3600  # Last hour
        ]
        
        if len(relevant_receipts) < 5:
            return current_params  # Not enough data for optimization
        
        # Analyze performance patterns
        performance_by_params = defaultdict(list)
        
        for receipt in relevant_receipts:
            params_key = self._simplify_params(receipt.action.get("parameters", {}))
            performance_by_params[params_key].append(receipt.reward)
        
        # Find best performing parameter combinations
        best_params = None
        best_performance = -float('inf')
        
        for params_key, performances in performance_by_params.items():
            avg_performance = sum(performances) / len(performances)
            if avg_performance > best_performance:
                best_performance = avg_performance
                best_params = params_key
        
        if best_params:
            # Update strategy parameters with best performing combination
            optimized_params = current_params.copy()
            optimized_params.update(best_params)
            
            strategy.parameters = optimized_params
            strategy.last_updated = datetime.now()
            
            # Record optimization
            self.optimization_history.append({
                "timestamp": datetime.now().isoformat(),
                "strategy_id": strategy_id,
                "old_params": current_params,
                "new_params": optimized_params,
                "performance_improvement": best_performance - strategy.get_average_performance()
            })
            
            return optimized_params
        
        return current_params
    
    def _simplify_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Simplify parameters for pattern matching."""
        # Extract key parameters for optimization
        simplified = {}
        
        key_params = ["depth", "granularity", "compression", "threshold"]
        for param in key_params:
            if param in params:
                simplified[param] = params[param]
        
        return simplified
    
    def get_optimization_summary(self) -> Dict[str, Any]:
        """Get summary of optimization activities."""
        return {
            "total_strategies": len(self.strategies),
            "current_strategy": self.current_strategy,
            "optimization_count": len(self.optimization_history),
            "strategy_performance": {
                strategy_id: {
                    "avg_performance": strategy.get_average_performance(),
                    "usage_count": strategy.usage_count,
                    "last_updated": strategy.last_updated.isoformat()
                }
                for strategy_id, strategy in self.strategies.items()
            }
        }


class AdaptiveThresholdTuner:
    """Dynamically tunes thresholds based on learning receipts."""
    
    def __init__(self, receipt_learning: ReceiptBasedLearning):
        self.receipt_learning = receipt_learning
        self.thresholds: Dict[str, float] = {
            "coherence_threshold": 0.7,
            "attention_threshold": 0.5,
            "abstraction_threshold": 0.6,
            "learning_threshold": 0.8
        }
        self.threshold_history: Dict[str, List[Tuple[datetime, float]]] = defaultdict(list)
        self.tuning_learning_rate = 0.05
        
    def get_threshold(self, threshold_name: str) -> float:
        """Get current threshold value."""
        return self.thresholds.get(threshold_name, 0.5)
    
    def update_threshold(self, threshold_name: str, new_value: float) -> None:
        """Update threshold value."""
        old_value = self.thresholds.get(threshold_name, 0.5)
        self.thresholds[threshold_name] = max(0.0, min(1.0, new_value))
        
        # Record change
        self.threshold_history[threshold_name].append(
            (datetime.now(), self.thresholds[threshold_name])
        )
        
        # Keep history manageable
        if len(self.threshold_history[threshold_name]) > 100:
            self.threshold_history[threshold_name].pop(0)
    
    def tune_thresholds(self) -> Dict[str, float]:
        """Tune thresholds based on recent performance."""
        tuning_results = {}
        
        for threshold_name in self.thresholds:
            new_value = self._calculate_optimal_threshold(threshold_name)
            if new_value is not None:
                self.update_threshold(threshold_name, new_value)
                tuning_results[threshold_name] = new_value
        
        return tuning_results
    
    def _calculate_optimal_threshold(self, threshold_name: str) -> Optional[float]:
        """Calculate optimal threshold value based on receipts."""
        # Get recent receipts relevant to this threshold
        relevant_receipts = [
            r for r in self.receipt_learning.receipts
            if threshold_name in r.context or threshold_name in r.action
            and (datetime.now() - r.timestamp).total_seconds() < 7200  # Last 2 hours
        ]
        
        if len(relevant_receipts) < 10:
            return None  # Not enough data
        
        # Analyze performance at different threshold levels
        threshold_performance = defaultdict(list)
        
        for receipt in relevant_receipts:
            threshold_used = receipt.context.get(threshold_name) or receipt.action.get(threshold_name)
            if threshold_used is not None:
                threshold_performance[round(threshold_used, 2)].append(receipt.reward)
        
        if not threshold_performance:
            return None
        
        # Find threshold with best average performance
        best_threshold = None
        best_performance = -float('inf')
        
        for threshold, performances in threshold_performance.items():
            avg_performance = sum(performances) / len(performances)
            if avg_performance > best_performance and len(performances) >= 3:
                best_performance = avg_performance
                best_threshold = threshold
        
        if best_threshold is not None:
            # Smooth transition to new threshold
            current_value = self.thresholds[threshold_name]
            smoothed_value = (current_value * (1 - self.tuning_learning_rate) + 
                            best_threshold * self.tuning_learning_rate)
            return smoothed_value
        
        return None
    
    def get_threshold_analysis(self) -> Dict[str, Any]:
        """Get analysis of threshold performance."""
        analysis = {}
        
        for threshold_name, current_value in self.thresholds.items():
            history = self.threshold_history[threshold_name]
            
            analysis[threshold_name] = {
                "current_value": current_value,
                "history_length": len(history),
                "volatility": self._calculate_volatility(history) if len(history) > 1 else 0.0,
                "trend": self._calculate_trend(history) if len(history) > 5 else "stable"
            }
        
        return analysis
    
    def _calculate_volatility(self, history: List[Tuple[datetime, float]]) -> float:
        """Calculate volatility of threshold changes."""
        if len(history) < 2:
            return 0.0
        
        values = [value for _, value in history]
        mean_value = sum(values) / len(values)
        
        variance = sum((value - mean_value) ** 2 for value in values) / len(values)
        return math.sqrt(variance)
    
    def _calculate_trend(self, history: List[Tuple[datetime, float]]) -> str:
        """Calculate trend of threshold changes."""
        if len(history) < 6:
            return "insufficient_data"
        
        # Simple linear trend calculation
        recent_values = [value for _, value in history[-6:]]
        older_values = [value for _, value in history[-12:-6]] if len(history) >= 12 else recent_values[:3]
        
        recent_avg = sum(recent_values) / len(recent_values)
        older_avg = sum(older_values) / len(older_values)
        
        if recent_avg > older_avg * 1.05:
            return "increasing"
        elif recent_avg < older_avg * 0.95:
            return "decreasing"
        else:
            return "stable"


class MetaLearningSystem:
    """Meta-learning for level selection and strategy adaptation."""
    
    def __init__(self, receipt_learning: ReceiptBasedLearning):
        self.receipt_learning = receipt_learning
        self.meta_policies: Dict[str, Dict[str, Any]] = {}
        self.task_embeddings: Dict[str, np.ndarray] = {}
        self.performance_history: List[Dict[str, Any]] = []
        self.adaptation_rate = 0.1
        
    def learn_meta_policy(self, task_type: str, receipts: List[LearningReceipt]) -> None:
        """Learn meta-policy for specific task type."""
        if len(receipts) < 5:
            return  # Not enough data
        
        # Extract features from receipts
        features = []
        rewards = []
        
        for receipt in receipts:
            feature_vector = self._extract_features(receipt)
            features.append(feature_vector)
            rewards.append(receipt.reward)
        
        # Simple policy learning - in practice would use more sophisticated ML
        features_array = np.array(features)
        rewards_array = np.array(rewards)
        
        # Learn simple linear policy
        if len(features_array) > 0 and features_array.shape[1] > 0:
            # Compute weights that maximize reward
            try:
                # Simple correlation-based approach
                correlations = np.corrcoef(features_array.T, rewards_array)[-1, :-1]
                policy_weights = correlations / (np.sum(np.abs(correlations)) + 1e-8)
                
                self.meta_policies[task_type] = {
                    "weights": policy_weights.tolist(),
                    "feature_names": self._get_feature_names(),
                    "performance": float(np.mean(rewards_array)),
                    "sample_count": len(receipts),
                    "last_updated": datetime.now().isoformat()
                }
            except Exception as e:
                logging.warning(f"Failed to learn meta-policy for {task_type}: {e}")
    
    def _extract_features(self, receipt: LearningReceipt) -> np.ndarray:
        """Extract features from receipt for meta-learning."""
        context = receipt.context
        action = receipt.action
        
        features = [
            context.get("complexity", 0.5),
            context.get("novelty", 0.5),
            action.get("abstraction_level", 0),
            action.get("attention_allocated", 0.5),
            len(context.get("constraints", [])) / 10.0,  # Normalized
            receipt.reward  # Include reward as feature
        ]
        
        return np.array(features)
    
    def _get_feature_names(self) -> List[str]:
        """Get names of features used in meta-learning."""
        return [
            "complexity",
            "novelty", 
            "abstraction_level",
            "attention_allocated",
            "constraint_count",
            "reward"
        ]
    
    def predict_optimal_action(self, task_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Predict optimal action using meta-policy."""
        if task_type not in self.meta_policies:
            return self._default_prediction()
        
        policy = self.meta_policies[task_type]
        weights = np.array(policy["weights"])
        
        # Extract features from current context
        mock_receipt = LearningReceipt(
            receipt_id="mock",
            receipt_type=ReceiptType.REASONING_RECEIPT,
            timestamp=datetime.now(),
            context=context,
            action={},
            outcome={},
            reward=0.0
        )
        
        features = self._extract_features(mock_receipt)
        
        # Calculate action scores
        if len(weights) == len(features):
            score = np.dot(weights, features)
            
            # Convert score to action recommendations
            return {
                "recommended_abstraction_level": int(max(0, min(10, score * 5))),
                "recommended_attention": max(0.1, min(1.0, score)),
                "confidence": min(1.0, policy["sample_count"] / 50.0),
                "policy_performance": policy["performance"]
            }
        
        return self._default_prediction()
    
    def _default_prediction(self) -> Dict[str, Any]:
        """Return default prediction when no meta-policy is available."""
        return {
            "recommended_abstraction_level": 3,
            "recommended_attention": 0.5,
            "confidence": 0.1,
            "policy_performance": 0.0
        }
    
    def update_meta_policies(self) -> None:
        """Update all meta-policies with recent receipts."""
        # Group receipts by task type
        receipts_by_task = defaultdict(list)
        
        for receipt in self.receipt_learning.receipts:
            task_type = receipt.context.get("type", "unknown")
            receipts_by_task[task_type].append(receipt)
        
        # Update policies for each task type
        for task_type, receipts in receipts_by_task.items():
            # Use recent receipts for learning
            recent_receipts = [
                r for r in receipts
                if (datetime.now() - r.timestamp).total_seconds() < 86400  # Last 24 hours
            ]
            
            if recent_receipts:
                self.learn_meta_policy(task_type, recent_receipts)
    
    def get_meta_learning_summary(self) -> Dict[str, Any]:
        """Get summary of meta-learning system."""
        return {
            "learned_policies": len(self.meta_policies),
            "policy_details": {
                task_type: {
                    "performance": policy["performance"],
                    "sample_count": policy["sample_count"],
                    "last_updated": policy["last_updated"]
                }
                for task_type, policy in self.meta_policies.items()
            },
            "adaptation_rate": self.adaptation_rate,
            "total_receipts_processed": len(self.receipt_learning.receipts)
        }


class ExperienceReplay:
    """Experience replay system for learning from past experiences."""
    
    def __init__(self, replay_buffer_size: int = 5000):
        self.replay_buffer_size = replay_buffer_size
        self.experience_buffer: deque = deque(maxlen=replay_buffer_size)
        self.priorities: deque = deque(maxlen=replay_buffer_size)
        self.alpha = 0.6  # Priority exponent
        self.beta = 0.4   # Importance sampling exponent
        
    def add_experience(self, receipt: LearningReceipt, priority: float = 1.0) -> None:
        """Add experience to replay buffer."""
        self.experience_buffer.append(receipt)
        self.priorities.append(priority)
    
    def sample_batch(self, batch_size: int) -> List[Tuple[LearningReceipt, float]]:
        """Sample a batch of experiences with priority-based sampling."""
        if len(self.experience_buffer) < batch_size:
            return []
        
        # Calculate sampling probabilities based on priorities
        priorities_array = np.array(self.priorities)
        probs = priorities_array ** self.alpha
        probs = probs / np.sum(probs)
        
        # Sample indices
        indices = np.random.choice(
            len(self.experience_buffer),
            size=min(batch_size, len(self.experience_buffer)),
            replace=False,
            p=probs
        )
        
        # Calculate importance sampling weights
        weights = (len(self.experience_buffer) * probs[indices]) ** (-self.beta)
        weights = weights / np.max(weights)  # Normalize
        
        batch = []
        for i, idx in enumerate(indices):
            batch.append((self.experience_buffer[idx], weights[i]))
        
        return batch
    
    def update_priorities(self, receipt_ids: List[str], new_priorities: List[float]) -> None:
        """Update priorities for specific experiences."""
        for receipt_id, new_priority in zip(receipt_ids, new_priorities):
            for i, receipt in enumerate(self.experience_buffer):
                if receipt.receipt_id == receipt_id:
                    self.priorities[i] = new_priority
                    break
    
    def get_buffer_statistics(self) -> Dict[str, Any]:
        """Get statistics about the replay buffer."""
        if not self.experience_buffer:
            return {"size": 0, "utilization": 0.0}
        
        return {
            "size": len(self.experience_buffer),
            "utilization": len(self.experience_buffer) / self.replay_buffer_size,
            "avg_priority": np.mean(self.priorities) if self.priorities else 0.0,
            "max_priority": np.max(self.priorities) if self.priorities else 0.0,
            "min_priority": np.min(self.priorities) if self.priorities else 0.0
        }


class LearningSystem:
    """Main learning system that integrates all learning components."""
    
    def __init__(self):
        self.logger = logging.getLogger("haai.learning_system")
        
        # Initialize learning components
        self.receipt_learning = ReceiptBasedLearning()
        self.abstraction_optimizer = AbstractionOptimizer(self.receipt_learning)
        self.threshold_tuner = AdaptiveThresholdTuner(self.receipt_learning)
        self.meta_learning = MetaLearningSystem(self.receipt_learning)
        self.experience_replay = ExperienceReplay()
        
        # Learning state
        self.is_learning = False
        self.learning_task: Optional[asyncio.Task] = None
        self.learning_mode = LearningMode.ONLINE
        
        # Performance tracking
        self.performance_metrics: Dict[str, List[float]] = defaultdict(list)
        
    async def start_learning(self) -> None:
        """Start the learning system."""
        if self.is_learning:
            return
        
        self.is_learning = True
        self.learning_task = asyncio.create_task(self._learning_loop())
        self.logger.info("Learning system started")
    
    async def stop_learning(self) -> None:
        """Stop the learning system."""
        self.is_learning = False
        if self.learning_task:
            self.learning_task.cancel()
            try:
                await self.learning_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Learning system stopped")
    
    async def _learning_loop(self) -> None:
        """Main learning loop."""
        while self.is_learning:
            try:
                # Periodic learning activities
                await self._periodic_learning()
                
                # Sleep between learning cycles
                await asyncio.sleep(10.0)  # Learn every 10 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in learning loop: {e}")
                await asyncio.sleep(5.0)
    
    async def _periodic_learning(self) -> None:
        """Perform periodic learning activities."""
        # Tune thresholds
        threshold_updates = self.threshold_tuner.tune_thresholds()
        if threshold_updates:
            self.logger.info(f"Thresholds tuned: {threshold_updates}")
        
        # Update meta-policies
        self.meta_learning.update_meta_policies()
        
        # Optimize abstraction strategies
        for strategy_id in list(self.abstraction_optimizer.strategies.keys()):
            self.abstraction_optimizer.optimize_parameters(strategy_id)
        
        # Sample from experience replay for additional learning
        if len(self.experience_replay.experience_buffer) > 100:
            batch = self.experience_replay.sample_batch(32)
            if batch:
                await self._learn_from_experience_batch(batch)
    
    async def _learn_from_experience_batch(self, batch: List[Tuple[LearningReceipt, float]]) -> None:
        """Learn from a batch of experiences."""
        # Simplified batch learning - in practice would be more sophisticated
        total_reward = 0.0
        for receipt, weight in batch:
            total_reward += receipt.reward * weight
        
        avg_reward = total_reward / len(batch) if batch else 0.0
        self.performance_metrics["batch_learning"].append(avg_reward)
    
    def add_learning_receipt(self, receipt_type: ReceiptType, context: Dict[str, Any],
                           action: Dict[str, Any], outcome: Dict[str, Any],
                           reward: float, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add a new learning receipt."""
        receipt = LearningReceipt(
            receipt_id=f"receipt_{int(time.time() * 1000000)}",
            receipt_type=receipt_type,
            timestamp=datetime.now(),
            context=context,
            action=action,
            outcome=outcome,
            reward=reward,
            metadata=metadata or {}
        )
        
        # Add to receipt learning system
        self.receipt_learning.add_receipt(receipt)
        
        # Add to experience replay with priority based on reward
        priority = max(0.1, abs(reward))
        self.experience_replay.add_experience(receipt, priority)
        
        # Track performance
        self.performance_metrics[receipt_type.value].append(reward)
        
        # Keep performance history manageable
        if len(self.performance_metrics[receipt_type.value]) > 1000:
            self.performance_metrics[receipt_type.value].pop(0)
        
        self.logger.debug(f"Added learning receipt: {receipt.receipt_id}, reward: {reward}")
        return receipt.receipt_id
    
    def get_learning_recommendations(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get learning-based recommendations for given context."""
        recommendations = {}
        
        # Meta-learning recommendations
        task_type = context.get("type", "unknown")
        meta_recommendations = self.meta_learning.predict_optimal_action(task_type, context)
        recommendations["meta_learning"] = meta_recommendations
        
        # Abstraction strategy recommendations
        if self.abstraction_optimizer.strategies:
            best_strategy = self.abstraction_optimizer.select_strategy(context)
            recommendations["abstraction_strategy"] = best_strategy
        
        # Threshold recommendations
        recommendations["thresholds"] = {
            name: self.threshold_tuner.get_threshold(name)
            for name in self.threshold_tuner.thresholds
        }
        
        return recommendations
    
    def get_learning_summary(self) -> Dict[str, Any]:
        """Get comprehensive learning system summary."""
        return {
            "receipt_learning": self.receipt_learning.get_learning_statistics(),
            "abstraction_optimizer": self.abstraction_optimizer.get_optimization_summary(),
            "threshold_tuner": self.threshold_tuner.get_threshold_analysis(),
            "meta_learning": self.meta_learning.get_meta_learning_summary(),
            "experience_replay": self.experience_replay.get_buffer_statistics(),
            "performance_metrics": {
                metric: {
                    "avg": sum(values) / len(values) if values else 0.0,
                    "min": min(values) if values else 0.0,
                    "max": max(values) if values else 0.0,
                    "count": len(values)
                }
                for metric, values in self.performance_metrics.items()
            },
            "learning_mode": self.learning_mode.value,
            "is_learning": self.is_learning
        }
    
    def set_learning_mode(self, mode: LearningMode) -> None:
        """Set the learning mode."""
        self.learning_mode = mode
        self.logger.info(f"Learning mode set to: {mode.value}")
    
    def export_learning_data(self, filepath: str) -> None:
        """Export learning data to file."""
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "receipts": [receipt.to_dict() for receipt in self.receipt_learning.receipts],
            "strategies": {
                strategy_id: {
                    "parameters": strategy.parameters,
                    "performance_history": strategy.performance_history,
                    "usage_count": strategy.usage_count
                }
                for strategy_id, strategy in self.abstraction_optimizer.strategies.items()
            },
            "thresholds": self.threshold_tuner.thresholds,
            "meta_policies": self.meta_learning.meta_policies,
            "performance_metrics": dict(self.performance_metrics)
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        self.logger.info(f"Learning data exported to {filepath}")
    
    def import_learning_data(self, filepath: str) -> None:
        """Import learning data from file."""
        with open(filepath, 'r') as f:
            import_data = json.load(f)
        
        # Import receipts
        for receipt_data in import_data.get("receipts", []):
            receipt = LearningReceipt.from_dict(receipt_data)
            self.receipt_learning.add_receipt(receipt)
        
        # Import strategies
        for strategy_id, strategy_data in import_data.get("strategies", {}).items():
            self.abstraction_optimizer.register_strategy(
                strategy_id, 
                strategy_data["parameters"]
            )
            strategy = self.abstraction_optimizer.strategies[strategy_id]
            strategy.performance_history = strategy_data["performance_history"]
            strategy.usage_count = strategy_data["usage_count"]
        
        # Import thresholds
        for threshold_name, threshold_value in import_data.get("thresholds", {}).items():
            self.threshold_tuner.update_threshold(threshold_name, threshold_value)
        
        # Import meta-policies
        self.meta_learning.meta_policies.update(import_data.get("meta_policies", {}))
        
        # Import performance metrics
        self.performance_metrics.update(import_data.get("performance_metrics", {}))
        
        self.logger.info(f"Learning data imported from {filepath}")