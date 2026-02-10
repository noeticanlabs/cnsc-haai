"""
Coherence Budget System for CNHAAI

This module provides coherence tracking and budget management:
- VectorResidual: Two-component residual matching UFE.ObserverResidual
- CoherenceBudget: Tracks coherence degradation with vector residuals
- Methods for checking and updating budget

Mathematical alignment with Lean 4 UFE formalization:
- dynamical: ∇_u u (structural/geometric residual)
- clock: g(u,u) + 1 (temporal/timelike residual)
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import uuid4
import math


@dataclass
class VectorResidual:
    """
    Two-component residual matching UFE.ObserverResidual.
    
    Represents the observer residual in the universal frame equation:
    - dynamical: ∇_u u (structural/geometric residual)
    - clock: g(u,u) + 1 (temporal/timelike residual)
    
    The norm is computed as sqrt(dynamical² + clock²).
    """
    dynamical: float = 0.0   # ∇_u u (structural/geometric residual)
    clock: float = 0.0        # g(u,u) + 1 (temporal/timelike residual)
    
    def norm(self) -> float:
        """observerResidualNorm: sqrt(dynamical² + clock²)"""
        return math.sqrt(self.dynamical**2 + self.clock**2)
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            "dynamical": self.dynamical,
            "clock": self.clock,
            "norm": self.norm(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> 'VectorResidual':
        """Create from dictionary."""
        return cls(
            dynamical=data.get("dynamical", 0.0),
            clock=data.get("clock", 0.0),
        )


@dataclass
class CoherenceBudget:
    """
    Manages coherence budget for reasoning.
    
    The coherence budget tracks the available "coherence capacity"
    for reasoning, degrading as contradictions or inconsistencies
    are encountered and improving through validation and recovery.
    
    Uses vector residuals matching the Lean 4 UFE formalization:
    - dynamical_residual: ∇_u u component
    - clock_residual: g(u,u) + 1 component
    
    Attributes:
        current: Current coherence level (0.0 to 1.0)
        initial: Initial coherence level
        minimum: Minimum allowed coherence level
        degradation_rate: Rate of degradation per contradiction
        recovery_rate: Rate of recovery per validation
        degradation_history: Record of degradation events
        recovery_history: Record of recovery events
        last_update: Timestamp of last update
    """
    current: float = 1.0
    initial: float = 1.0
    minimum: float = 0.0
    maximum: float = 1.0
    degradation_rate: float = 0.1
    recovery_rate: float = 0.05
    degradation_history: List[Dict[str, Any]] = field(default_factory=list)
    recovery_history: List[Dict[str, Any]] = field(default_factory=list)
    last_update: datetime = field(default_factory=datetime.utcnow)
    
    # Vector residuals (UFE alignment)
    dynamical_residual: float = 0.0
    clock_residual: float = 0.0
    
    def __post_init__(self):
        """Validate and normalize coherence values."""
        self.current = max(self.minimum, min(self.maximum, self.current))
        self.initial = max(self.minimum, min(self.maximum, self.initial))
    
    @property
    def residual(self) -> VectorResidual:
        """Get the current vector residual."""
        return VectorResidual(
            dynamical=self.dynamical_residual,
            clock=self.clock_residual
        )
    
    def norm(self) -> float:
        """Compute L2 norm of residual vector."""
        return self.residual.norm()
    
    @property
    def coherence_from_residual(self) -> float:
        """Compute coherence level from residual norm."""
        return max(0.0, 1.0 - self.norm())
    
    def is_healthy(self) -> bool:
        """Check if coherence is above healthy threshold."""
        return self.current >= 0.5
    
    def is_critical(self) -> bool:
        """Check if coherence is at critical level."""
        return self.current < 0.3
    
    def is_degraded(self) -> bool:
        """Check if coherence is degraded."""
        return self.current < 1.0
    
    def check(self) -> Dict[str, Any]:
        """
        Check current coherence status.
        
        Returns:
            Dictionary with coherence status
        """
        return {
            "current": self.current,
            "status": self._get_status(),
            "is_healthy": self.is_healthy(),
            "is_critical": self.is_critical(),
            "is_degraded": self.is_degraded(),
            "headroom": self.maximum - self.current,
            "degradation_count": len(self.degradation_history),
            "recovery_count": len(self.recovery_history)
        }
    
    def _get_status(self) -> str:
        """Get human-readable status."""
        if self.current >= 0.9:
            return "optimal"
        elif self.current >= 0.7:
            return "healthy"
        elif self.current >= 0.5:
            return "acceptable"
        elif self.current >= 0.3:
            return "degraded"
        else:
            return "critical"
    
    def degrade(
        self,
        amount: Optional[float] = None,
        reason: str = "contradiction",
        metadata: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Degrade coherence by the specified amount.
        
        Args:
            amount: Amount to degrade (uses degradation_rate if not specified)
            reason: Reason for degradation
            metadata: Additional metadata
            
        Returns:
            New coherence level
        """
        if amount is None:
            amount = self.degradation_rate
        
        old_value = self.current
        self.current = max(self.minimum, self.current - amount)
        self.last_update = datetime.utcnow()
        
        # Record degradation
        self.degradation_history.append({
            "timestamp": self.last_update.isoformat(),
            "old_value": old_value,
            "new_value": self.current,
            "amount": amount,
            "reason": reason,
            "metadata": metadata or {}
        })
        
        return self.current
    
    def degrade_with_residuals(
        self,
        dynamical: float = 0.0,
        clock: float = 0.0,
        reason: str = "contradiction",
        metadata: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Degrade coherence with separate dynamical and clock residuals.
        
        This matches the UFE formalization where residuals have two components:
        - dynamical: ∇_u u (structural/geometric)
        - clock: g(u,u) + 1 (temporal)
        
        Args:
            dynamical: Dynamical residual component
            clock: Clock residual component
            reason: Reason for degradation
            metadata: Additional metadata
            
        Returns:
            New coherence level derived from residual norm
        """
        old_dynamical = self.dynamical_residual
        old_clock = self.clock_residual
        
        # Accumulate residuals
        self.dynamical_residual = max(0.0, self.dynamical_residual + dynamical)
        self.clock_residual = max(0.0, self.clock_residual + clock)
        
        # Update coherence from residual norm
        self.current = self.coherence_from_residual
        self.last_update = datetime.utcnow()
        
        # Record degradation with residual info
        self.degradation_history.append({
            "timestamp": self.last_update.isoformat(),
            "old_dynamical": old_dynamical,
            "old_clock": old_clock,
            "new_dynamical": self.dynamical_residual,
            "new_clock": self.clock_residual,
            "residual_norm": self.norm(),
            "coherence": self.current,
            "reason": reason,
            "metadata": metadata or {}
        })
        
        return self.current
    
    def get_residual_info(self) -> Dict[str, Any]:
        """Get current residual information."""
        return {
            "dynamical": self.dynamical_residual,
            "clock": self.clock_residual,
            "norm": self.norm(),
            "coherence": self.current,
        }
    
    def recover(
        self,
        amount: Optional[float] = None,
        reason: str = "validation",
        metadata: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Recover coherence by the specified amount.
        
        Args:
            amount: Amount to recover (uses recovery_rate if not specified)
            reason: Reason for recovery
            metadata: Additional metadata
            
        Returns:
            New coherence level
        """
        if amount is None:
            amount = self.recovery_rate
        
        old_value = self.current
        self.current = min(self.maximum, self.current + amount)
        self.last_update = datetime.utcnow()
        
        # Record recovery
        self.recovery_history.append({
            "timestamp": self.last_update.isoformat(),
            "old_value": old_value,
            "new_value": self.current,
            "amount": amount,
            "reason": reason,
            "metadata": metadata or {}
        })
        
        return self.current
    
    def apply_degradation_factor(self, factor: float) -> float:
        """
        Apply a multiplicative degradation factor.
        
        Args:
            factor: Factor to multiply current coherence by
            
        Returns:
            New coherence level
        """
        old_value = self.current
        self.current = max(self.minimum, self.current * factor)
        self.last_update = datetime.utcnow()
        
        if self.current != old_value:
            self.degradation_history.append({
                "timestamp": self.last_update.isoformat(),
                "old_value": old_value,
                "new_value": self.current,
                "factor": factor,
                "reason": "multiplicative_degradation"
            })
        
        return self.current
    
    def can_proceed(self, required_level: float = 0.5) -> bool:
        """
        Check if reasoning can proceed at required level.
        
        Args:
            required_level: Minimum coherence required
            
        Returns:
            True if reasoning can proceed
        """
        return self.current >= required_level
    
    def needs_recovery(self, threshold: float = 0.5) -> bool:
        """
        Check if recovery is needed.
        
        Args:
            threshold: Threshold for requiring recovery
            
        Returns:
            True if recovery is needed
        """
        return self.current < threshold
    
    def snapshot(self) -> Dict[str, Any]:
        """Create a snapshot of current coherence state."""
        return {
            "current": self.current,
            "initial": self.initial,
            "minimum": self.minimum,
            "maximum": self.maximum,
            "status": self._get_status(),
            "timestamp": self.last_update.isoformat(),
            "degradation_history_count": len(self.degradation_history),
            "recovery_history_count": len(self.recovery_history),
            "dynamical_residual": self.dynamical_residual,
            "clock_residual": self.clock_residual,
            "residual_norm": self.norm(),
        }
    
    def reset(self, level: Optional[float] = None) -> float:
        """
        Reset coherence to initial or specified level.
        
        Args:
            level: Level to reset to (uses initial if not specified)
            
        Returns:
            New coherence level
        """
        self.current = level if level is not None else self.initial
        self.current = max(self.minimum, min(self.maximum, self.current))
        self.last_update = datetime.utcnow()
        return self.current
    
    def get_degradation_rate_summary(self) -> Dict[str, Any]:
        """Get summary of degradation patterns."""
        if not self.degradation_history:
            return {"total_degradation": 0, "average_amount": 0, "reasons": {}}
        
        total = sum(d["amount"] for d in self.degradation_history)
        reasons = {}
        for d in self.degradation_history:
            reason = d["reason"]
            if reason not in reasons:
                reasons[reason] = {"count": 0, "total_amount": 0}
            reasons[reason]["count"] += 1
            reasons[reason]["total_amount"] += d["amount"]
        
        return {
            "total_degradation": total,
            "average_amount": total / len(self.degradation_history),
            "event_count": len(self.degradation_history),
            "by_reason": reasons
        }
