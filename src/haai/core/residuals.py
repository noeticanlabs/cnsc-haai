"""
Residual calculation and coherence functional implementation.

Implements the core residual calculations for hierarchical abstraction consistency
and the coherence functional that governs the system.
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import time
import logging

from .abstraction import LevelState, CrossLevelMap

logger = logging.getLogger(__name__)


@dataclass
class ResidualMetrics:
    """Container for residual metrics at a specific level."""
    level: int
    reconstruction_residual: float = 0.0
    constraint_violation: float = 0.0
    cross_level_disagreement: float = 0.0
    reasoning_thrash: float = 0.0
    total_residual: float = 0.0
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary for serialization."""
        return {
            'level': self.level,
            'reconstruction_residual': self.reconstruction_residual,
            'constraint_violation': self.constraint_violation,
            'cross_level_disagreement': self.cross_level_disagreement,
            'reasoning_thrash': self.reasoning_thrash,
            'total_residual': self.total_residual,
            'timestamp': self.timestamp
        }


class ResidualCalculator(ABC):
    """Abstract base class for residual calculation strategies."""
    
    @abstractmethod
    def calculate_reconstruction_residual(self, original: LevelState, reconstructed: LevelState) -> float:
        """Calculate reconstruction residual r^rec_ℓ = |z_{ℓ-1} - D_ℓ(z_ℓ)|."""
        pass
    
    @abstractmethod
    def calculate_constraint_violation(self, state: LevelState, constraints: Dict[str, Any]) -> float:
        """Calculate constraint violation residual r^cons_ℓ."""
        pass
    
    @abstractmethod
    def calculate_cross_level_disagreement(self, predictions: Dict[int, Any], evidence: Dict[int, Any]) -> float:
        """Calculate cross-level disagreement residual r^x_ℓ."""
        pass


class StandardResidualCalculator(ResidualCalculator):
    """Standard implementation of residual calculations."""
    
    def __init__(self, normalization_factors: Optional[Dict[str, float]] = None):
        self.normalization_factors = normalization_factors or {
            'reconstruction': 1.0,
            'constraint': 1.0,
            'disagreement': 1.0,
            'thrash': 1.0
        }
    
    def calculate_reconstruction_residual(self, original: LevelState, reconstructed: LevelState) -> float:
        """
        Calculate reconstruction residual using L2 norm.
        
        r^rec_ℓ = |z_{ℓ-1} - D_ℓ(z_ℓ)|
        """
        if original.data.shape != reconstructed.data.shape:
            logger.warning(f"Shape mismatch in reconstruction: {original.data.shape} vs {reconstructed.data.shape}")
            # Try to reshape if possible
            min_size = min(original.data.size, reconstructed.data.size)
            orig_flat = original.data.flatten()[:min_size]
            recon_flat = reconstructed.data.flatten()[:min_size]
        else:
            orig_flat = original.data.flatten()
            recon_flat = reconstructed.data.flatten()
        
        # Calculate L2 norm of difference
        diff = orig_flat - recon_flat
        residual = np.linalg.norm(diff) / (len(diff) ** 0.5)  # Normalized by sqrt(N)
        
        return float(residual * self.normalization_factors['reconstruction'])
    
    def calculate_constraint_violation(self, state: LevelState, constraints: Dict[str, Any]) -> float:
        """
        Calculate constraint violation residual.
        
        Checks various types of constraints:
        - Type constraints
        - Range constraints  
        - Logical constraints
        - Physical constraints
        """
        violation = 0.0
        data = state.data
        
        # Range constraints
        if 'min_value' in constraints:
            min_violation = np.sum(np.maximum(0, constraints['min_value'] - data))
            violation += min_violation
        
        if 'max_value' in constraints:
            max_violation = np.sum(np.maximum(0, data - constraints['max_value']))
            violation += max_violation
        
        # Type constraints (e.g., positivity, integrality)
        if 'positivity' in constraints and constraints['positivity']:
            positivity_violation = np.sum(np.maximum(0, -data))
            violation += positivity_violation
        
        if 'integrality' in constraints and constraints['integrality']:
            # Measure deviation from nearest integers
            rounded = np.round(data)
            integrality_violation = np.sum(np.abs(data - rounded))
            violation += integrality_violation
        
        # Physical constraints (e.g., conservation laws)
        if 'conservation' in constraints:
            for cons_law in constraints['conservation']:
                if 'sum' in cons_law:
                    actual_sum = np.sum(data)
                    expected_sum = cons_law['sum']
                    violation += abs(actual_sum - expected_sum)
        
        return float(violation * self.normalization_factors['constraint'])
    
    def calculate_cross_level_disagreement(self, predictions: Dict[int, Any], evidence: Dict[int, Any]) -> float:
        """
        Calculate cross-level disagreement residual.
        
        Measures how much predictions at higher levels disagree with evidence at lower levels.
        """
        disagreement = 0.0
        comparison_count = 0
        
        for level, pred in predictions.items():
            if level - 1 in evidence:
                ev = evidence[level - 1]
                
                # Compare prediction with evidence
                if isinstance(pred, np.ndarray) and isinstance(ev, np.ndarray):
                    # Ensure same shape for comparison
                    min_size = min(pred.size, ev.size)
                    pred_flat = pred.flatten()[:min_size]
                    ev_flat = ev.flatten()[:min_size]
                    
                    # Calculate normalized disagreement
                    diff = np.abs(pred_flat - ev_flat)
                    level_disagreement = np.mean(diff) / (np.mean(ev_flat) + 1e-10)
                    disagreement += level_disagreement
                    comparison_count += 1
                elif isinstance(pred, (int, float)) and isinstance(ev, (int, float)):
                    level_disagreement = abs(pred - ev) / (abs(ev) + 1e-10)
                    disagreement += level_disagreement
                    comparison_count += 1
        
        if comparison_count > 0:
            disagreement /= comparison_count
        
        return float(disagreement * self.normalization_factors['disagreement'])


class ReasoningThrashDetector:
    """Detects reasoning thrash (wasted branching, nonproductive loops)."""
    
    def __init__(self, window_size: int = 10, thrash_threshold: float = 0.8):
        self.window_size = window_size
        self.thrash_threshold = thrash_threshold
        self.reasoning_history: List[Dict[str, Any]] = []
        self.level_states: Dict[int, List[LevelState]] = {}
    
    def record_reasoning_step(self, step_info: Dict[str, Any]) -> None:
        """Record a reasoning step for thrash detection."""
        step_info['timestamp'] = time.time()
        self.reasoning_history.append(step_info)
        
        # Maintain sliding window
        if len(self.reasoning_history) > self.window_size:
            self.reasoning_history.pop(0)
    
    def record_level_state(self, level: int, state: LevelState) -> None:
        """Record state at a specific level."""
        if level not in self.level_states:
            self.level_states[level] = []
        
        self.level_states[level].append(state)
        
        # Maintain sliding window per level
        if len(self.level_states[level]) > self.window_size:
            self.level_states[level].pop(0)
    
    def calculate_thrash_residual(self) -> float:
        """
        Calculate reasoning thrash residual.
        
        Detects:
        - Oscillations between states
        - Repeated similar operations
        - Lack of progress toward goals
        """
        if len(self.reasoning_history) < 3:
            return 0.0
        
        thrash_score = 0.0
        
        # Detect oscillations
        oscillation_score = self._detect_oscillations()
        thrash_score += oscillation_score
        
        # Detect repeated operations
        repetition_score = self._detect_repetitions()
        thrash_score += repetition_score
        
        # Detect lack of progress
        progress_score = self._detect_lack_of_progress()
        thrash_score += progress_score
        
        return min(thrash_score, 1.0)  # Cap at 1.0
    
    def _detect_oscillations(self) -> float:
        """Detect oscillating patterns in reasoning."""
        if len(self.reasoning_history) < 4:
            return 0.0
        
        oscillations = 0
        total_comparisons = 0
        
        for i in range(len(self.reasoning_history) - 2):
            step1 = self.reasoning_history[i]
            step2 = self.reasoning_history[i + 1]
            step3 = self.reasoning_history[i + 2]
            
            # Check for A -> B -> A pattern
            if (step1.get('operation') == step3.get('operation') and 
                step1.get('operation') != step2.get('operation')):
                oscillations += 1
            
            total_comparisons += 1
        
        return oscillations / max(total_comparisons, 1)
    
    def _detect_repetitions(self) -> float:
        """Detect repeated similar operations."""
        if len(self.reasoning_history) < 2:
            return 0.0
        
        repetitions = 0
        total_comparisons = 0
        
        for i in range(len(self.reasoning_history) - 1):
            step1 = self.reasoning_history[i]
            step2 = self.reasoning_history[i + 1]
            
            # Check for similar operations
            if (step1.get('operation') == step2.get('operation') and
                step1.get('level') == step2.get('level')):
                repetitions += 1
            
            total_comparisons += 1
        
        return repetitions / max(total_comparisons, 1)
    
    def _detect_lack_of_progress(self) -> float:
        """Detect lack of progress toward goals."""
        progress_scores = []
        
        for level, states in self.level_states.items():
            if len(states) < 2:
                continue
            
            # Measure change in states
            for i in range(len(states) - 1):
                state1 = states[i]
                state2 = states[i + 1]
                
                # Calculate normalized change
                if isinstance(state1.data, np.ndarray) and isinstance(state2.data, np.ndarray):
                    change = np.linalg.norm(state2.data - state1.data)
                    normalized_change = change / (np.linalg.norm(state1.data) + 1e-10)
                    progress_scores.append(normalized_change)
        
        if not progress_scores:
            return 0.0
        
        # High thrash if progress is consistently low
        avg_progress = np.mean(progress_scores)
        return max(0.0, 1.0 - avg_progress * 10)  # Scale factor


class CoherenceFunctional:
    """
    Implements the coherence functional that governs the hierarchical abstraction system.
    
    𝔠 = Σℓ(w^rec_ℓ(r^rec_ℓ)² + w^cons_ℓ(r^cons_ℓ)² + w^x_ℓ(r^x_ℓ)²) + w^search·r^search
    """
    
    def __init__(self, weights: Optional[Dict[str, Dict[str, float]]] = None):
        """
        Initialize coherence functional with weights.
        
        Args:
            weights: Dictionary of weights per level and residual type
                    Format: {level: {'reconstruction': w, 'constraint': w, 'disagreement': w}}
        """
        self.weights = weights or {}
        self.default_weights = {
            'reconstruction': 1.0,
            'constraint': 1.0,
            'disagreement': 1.0
        }
        self.search_weight = 1.0
        
        self.residual_calculator = StandardResidualCalculator()
        self.thrash_detector = ReasoningThrashDetector()
        
        self.functional_history: List[Dict[str, Any]] = []
    
    def calculate_coherence_debt(self, 
                              residuals: Dict[int, ResidualMetrics],
                              thrash_residual: float = 0.0) -> float:
        """
        Calculate total coherence debt.
        
        Args:
            residuals: Residual metrics per level
            thrash_residual: Reasoning thrash residual
            
        Returns:
            Total coherence debt
        """
        total_debt = 0.0
        
        for level, residual in residuals.items():
            level_weights = self.weights.get(level, self.default_weights)
            
            # Calculate weighted sum of squared residuals
            level_debt = (
                level_weights.get('reconstruction', 1.0) * residual.reconstruction_residual ** 2 +
                level_weights.get('constraint', 1.0) * residual.constraint_violation ** 2 +
                level_weights.get('disagreement', 1.0) * residual.cross_level_disagreement ** 2
            )
            
            total_debt += level_debt
        
        # Add search/thrash component
        total_debt += self.search_weight * thrash_residual
        
        # Record in history
        self.functional_history.append({
            'timestamp': time.time(),
            'total_debt': total_debt,
            'residuals': {level: r.to_dict() for level, r in residuals.items()},
            'thrash_residual': thrash_residual,
            'num_levels': len(residuals)
        })
        
        # Maintain history size
        if len(self.functional_history) > 1000:
            self.functional_history.pop(0)
        
        return total_debt
    
    def calculate_level_residuals(self,
                               level: int,
                               original_state: LevelState,
                               reconstructed_state: Optional[LevelState] = None,
                               constraints: Optional[Dict[str, Any]] = None,
                               predictions: Optional[Dict[int, Any]] = None,
                               evidence: Optional[Dict[int, Any]] = None) -> ResidualMetrics:
        """
        Calculate all residual metrics for a specific level.
        """
        residuals = ResidualMetrics(level=level)
        
        # Reconstruction residual
        if reconstructed_state is not None:
            residuals.reconstruction_residual = self.residual_calculator.calculate_reconstruction_residual(
                original_state, reconstructed_state
            )
        
        # Constraint violation residual
        if constraints is not None:
            residuals.constraint_violation = self.residual_calculator.calculate_constraint_violation(
                original_state, constraints
            )
        
        # Cross-level disagreement residual
        if predictions is not None and evidence is not None:
            level_predictions = {level: original_state.data}
            level_predictions.update(predictions)
            residuals.cross_level_disagreement = self.residual_calculator.calculate_cross_level_disagreement(
                level_predictions, evidence
            )
        
        # Calculate total residual
        level_weights = self.weights.get(level, self.default_weights)
        residuals.total_residual = (
            level_weights.get('reconstruction', 1.0) * residuals.reconstruction_residual ** 2 +
            level_weights.get('constraint', 1.0) * residuals.constraint_violation ** 2 +
            level_weights.get('disagreement', 1.0) * residuals.cross_level_disagreement ** 2
        ) ** 0.5  # Square root for RMS-like measure
        
        return residuals
    
    def update_thrash_detection(self, step_info: Dict[str, Any], level_states: Optional[Dict[int, LevelState]] = None) -> float:
        """Update thrash detection and return current thrash residual."""
        self.thrash_detector.record_reasoning_step(step_info)
        
        if level_states:
            for level, state in level_states.items():
                self.thrash_detector.record_level_state(level, state)
        
        return self.thrash_detector.calculate_thrash_residual()
    
    def get_debt_trend(self, window_size: int = 10) -> Dict[str, Any]:
        """Analyze trend in coherence debt over recent history."""
        if len(self.functional_history) < window_size:
            return {"trend": "insufficient_data"}
        
        recent_debts = [entry['total_debt'] for entry in self.functional_history[-window_size:]]
        
        # Calculate trend
        if len(recent_debts) >= 2:
            slope = np.polyfit(range(len(recent_debts)), recent_debts, 1)[0]
            current_debt = recent_debts[-1]
            avg_debt = np.mean(recent_debts)
            
            trend_direction = "increasing" if slope > 0.01 else "decreasing" if slope < -0.01 else "stable"
            
            return {
                "trend": trend_direction,
                "slope": slope,
                "current_debt": current_debt,
                "average_debt": avg_debt,
                "debt_variance": np.var(recent_debts),
                "debt_range": (min(recent_debts), max(recent_debts))
            }
        
        return {"trend": "unknown"}
    
    def set_weights(self, level: int, weights: Dict[str, float]) -> None:
        """Set weights for a specific level."""
        self.weights[level] = weights.copy()
        logger.info(f"Updated weights for level {level}: {weights}")
    
    def set_search_weight(self, weight: float) -> None:
        """Set weight for search/thrash component."""
        self.search_weight = weight
        logger.info(f"Updated search weight: {weight}")
    
    def get_coherence_summary(self) -> Dict[str, Any]:
        """Get summary of current coherence state."""
        if not self.functional_history:
            return {"status": "no_data"}
        
        latest = self.functional_history[-1]
        trend = self.get_debt_trend()
        
        return {
            "current_debt": latest['total_debt'],
            "num_levels": latest['num_levels'],
            "thrash_residual": latest['thrash_residual'],
            "debt_trend": trend,
            "functional_history_size": len(self.functional_history),
            "weights": self.weights,
            "search_weight": self.search_weight
        }