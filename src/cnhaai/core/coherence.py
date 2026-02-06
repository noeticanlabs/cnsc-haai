"""
Coherence Budget System for CNHAAI

This module provides coherence tracking and budget management:
- CoherenceBudget: Tracks coherence degradation
- Methods for checking and updating budget
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import uuid4


@dataclass
class CoherenceBudget:
    """
    Manages coherence budget for reasoning.
    
    The coherence budget tracks the available "coherence capacity"
    for reasoning, degrading as contradictions or inconsistencies
    are encountered and improving through validation and recovery.
    
    Attributes:
        current: Current coherence level (0.0 to 1.0)
        initial: Initial coherence level
        minimum: Minimum allowed coherence level
        degradation_rate: Rate of degradation per contradiction
        recovery_rate: Rate of recovery per validation
        degradation_history: Record of degradation events
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
    
    def __post_init__(self):
        """Validate and normalize coherence values."""
        self.current = max(self.minimum, min(self.maximum, self.current))
        self.initial = max(self.minimum, min(self.maximum, self.initial))
    
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
            "recovery_history_count": len(self.recovery_history)
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
