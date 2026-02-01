"""
Gate and rail system implementation.

Implements hard gates for non-negotiable constraints, soft gates for debt budget management,
and rails for bounded corrective actions as defined in the HAAI specification.
"""

import numpy as np
from typing import Dict, List, Optional, Any, Callable, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import time
import logging

from .residuals import ResidualMetrics, CoherenceFunctional
from .abstraction import LevelState

logger = logging.getLogger(__name__)


class GateType(Enum):
    """Types of gates in the system."""
    HARD = "hard"          # Non-negotiable constraints
    SOFT = "soft"          # Debt budget management
    HYSTERESIS = "hysteresis"  # Gates with hysteresis behavior


class RailType(Enum):
    """Types of rails for corrective actions."""
    REDUCE_STEP_SIZE = "reduce_step_size"
    REQUEST_EVIDENCE = "request_evidence"
    INVOKE_TOOL = "invoke_tool"
    TIGHTEN_CONSTRAINTS = "tighten_constraints"
    REVERT = "revert"
    THROTTLE = "throttle"
    ESCALATE = "escalate"


@dataclass
class GateDecision:
    """Result of gate evaluation."""
    gate_name: str
    gate_type: GateType
    passed: bool
    confidence: float
    reason: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'gate_name': self.gate_name,
            'gate_type': self.gate_type.value,
            'passed': self.passed,
            'confidence': self.confidence,
            'reason': self.reason,
            'timestamp': self.timestamp,
            'metadata': self.metadata
        }


@dataclass
class RailAction:
    """Corrective action prescribed by a rail."""
    rail_type: RailType
    action_name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'rail_type': self.rail_type.value,
            'action_name': self.action_name,
            'parameters': self.parameters,
            'priority': self.priority,
            'timestamp': self.timestamp
        }


class Gate(ABC):
    """Abstract base class for gates."""
    
    def __init__(self, name: str, gate_type: GateType):
        self.name = name
        self.gate_type = gate_type
        self.decision_history: List[GateDecision] = []
        self.is_active = True
    
    @abstractmethod
    def evaluate(self, context: Dict[str, Any]) -> GateDecision:
        """Evaluate the gate with given context."""
        pass
    
    def record_decision(self, decision: GateDecision) -> None:
        """Record gate decision for audit trail."""
        self.decision_history.append(decision)
        
        # Maintain history size
        if len(self.decision_history) > 1000:
            self.decision_history.pop(0)
    
    def get_pass_rate(self, window_size: int = 100) -> float:
        """Get recent pass rate for this gate."""
        if not self.decision_history:
            return 1.0
        
        recent_decisions = self.decision_history[-window_size:]
        passed_count = sum(1 for d in recent_decisions if d.passed)
        return passed_count / len(recent_decisions)


class HardGate(Gate):
    """Hard gate for non-negotiable constraints."""
    
    def __init__(self, name: str, constraint_func: Callable[[Dict[str, Any]], bool], 
                 reason_template: str = "Hard constraint violated"):
        super().__init__(name, GateType.HARD)
        self.constraint_func = constraint_func
        self.reason_template = reason_template
    
    def evaluate(self, context: Dict[str, Any]) -> GateDecision:
        """Evaluate hard constraint."""
        try:
            passed = self.constraint_func(context)
            confidence = 1.0  # Hard gates are always certain
            reason = self.reason_template if not passed else "Hard constraint satisfied"
            
            decision = GateDecision(
                gate_name=self.name,
                gate_type=self.gate_type,
                passed=passed,
                confidence=confidence,
                reason=reason,
                metadata={'context_keys': list(context.keys())}
            )
            
            self.record_decision(decision)
            return decision
            
        except Exception as e:
            logger.error(f"Error in hard gate {self.name}: {e}")
            decision = GateDecision(
                gate_name=self.name,
                gate_type=self.gate_type,
                passed=False,
                confidence=0.0,
                reason=f"Gate evaluation error: {str(e)}",
                metadata={'error': str(e)}
            )
            self.record_decision(decision)
            return decision


class SoftGate(Gate):
    """Soft gate for debt budget management."""
    
    def __init__(self, name: str, max_debt: float, hysteresis_factor: float = 0.1):
        super().__init__(name, GateType.SOFT)
        self.max_debt = max_debt
        self.hysteresis_factor = hysteresis_factor
        self.current_threshold = max_debt
        self.last_decision_time = 0.0
    
    def evaluate(self, context: Dict[str, Any]) -> GateDecision:
        """Evaluate soft gate with hysteresis."""
        current_debt = context.get('coherence_debt', 0.0)
        current_time = time.time()
        
        # Apply hysteresis
        time_since_last = current_time - self.last_decision_time
        if time_since_last > 1.0:  # Reset hysteresis after 1 second
            self.current_threshold = self.max_debt
        
        passed = current_debt <= self.current_threshold
        
        # Adjust threshold with hysteresis
        if not passed:
            self.current_threshold *= (1.0 - self.hysteresis_factor)
        else:
            self.current_threshold = min(self.max_debt, 
                                      self.current_threshold * (1.0 + self.hysteresis_factor * 0.5))
        
        # Calculate confidence based on distance from threshold
        distance_from_threshold = abs(current_debt - self.current_threshold)
        confidence = min(1.0, distance_from_threshold / (self.max_debt * 0.1))
        
        reason = f"Debt {current_debt:.3f} {'within' if passed else 'exceeds'} threshold {self.current_threshold:.3f}"
        
        decision = GateDecision(
            gate_name=self.name,
            gate_type=self.gate_type,
            passed=passed,
            confidence=confidence,
            reason=reason,
            metadata={
                'current_debt': current_debt,
                'threshold': self.current_threshold,
                'max_debt': self.max_debt
            }
        )
        
        self.last_decision_time = current_time
        self.record_decision(decision)
        return decision


class HysteresisGate(Gate):
    """Gate with hysteresis behavior to prevent rapid switching."""
    
    def __init__(self, name: str, condition_func: Callable[[Dict[str, Any]], float],
                 activation_threshold: float = 0.5, deactivation_threshold: float = 0.3):
        super().__init__(name, GateType.HYSTERESIS)
        self.condition_func = condition_func
        self.activation_threshold = activation_threshold
        self.deactivation_threshold = deactivation_threshold
        self.is_activated = False
    
    def evaluate(self, context: Dict[str, Any]) -> GateDecision:
        """Evaluate hysteresis gate."""
        try:
            condition_value = self.condition_func(context)
            
            # Hysteresis logic
            if self.is_activated:
                passed = condition_value >= self.deactivation_threshold
                if not passed:
                    self.is_activated = False
            else:
                passed = condition_value >= self.activation_threshold
                if passed:
                    self.is_activated = True
            
            confidence = abs(condition_value - self.activation_threshold) / abs(self.activation_threshold - self.deactivation_threshold)
            confidence = min(1.0, max(0.0, confidence))
            
            state_str = "activated" if self.is_activated else "deactivated"
            reason = f"Condition {condition_value:.3f}, gate {state_str}"
            
            decision = GateDecision(
                gate_name=self.name,
                gate_type=self.gate_type,
                passed=passed,
                confidence=confidence,
                reason=reason,
                metadata={
                    'condition_value': condition_value,
                    'activation_threshold': self.activation_threshold,
                    'deactivation_threshold': self.deactivation_threshold,
                    'is_activated': self.is_activated
                }
            )
            
            self.record_decision(decision)
            return decision
            
        except Exception as e:
            logger.error(f"Error in hysteresis gate {self.name}: {e}")
            decision = GateDecision(
                gate_name=self.name,
                gate_type=self.gate_type,
                passed=False,
                confidence=0.0,
                reason=f"Gate evaluation error: {str(e)}",
                metadata={'error': str(e)}
            )
            self.record_decision(decision)
            return decision


class Rail(ABC):
    """Abstract base class for rails."""
    
    def __init__(self, name: str, rail_type: RailType, priority: int = 0):
        self.name = name
        self.rail_type = rail_type
        self.priority = priority
        self.action_history: List[RailAction] = []
        self.is_active = True
    
    @abstractmethod
    def should_trigger(self, context: Dict[str, Any], gate_decisions: List[GateDecision]) -> bool:
        """Determine if this rail should trigger."""
        pass
    
    @abstractmethod
    def generate_action(self, context: Dict[str, Any]) -> RailAction:
        """Generate the corrective action."""
        pass
    
    def execute_action(self, action: RailAction) -> bool:
        """Execute the corrective action."""
        try:
            # Default implementation - subclasses should override
            self.action_history.append(action)
            logger.info(f"Executed rail action: {action.action_name}")
            return True
        except Exception as e:
            logger.error(f"Error executing rail action {action.action_name}: {e}")
            return False


class StepSizeRail(Rail):
    """Rail that reduces step size when coherence is low."""
    
    def __init__(self, name: str, reduction_factor: float = 0.5, min_step_size: float = 0.01):
        super().__init__(name, RailType.REDUCE_STEP_SIZE)
        self.reduction_factor = reduction_factor
        self.min_step_size = min_step_size
    
    def should_trigger(self, context: Dict[str, Any], gate_decisions: List[GateDecision]) -> bool:
        """Trigger when coherence debt is high or gates are failing."""
        coherence_debt = context.get('coherence_debt', 0.0)
        failed_gates = [d for d in gate_decisions if not d.passed]
        
        return coherence_debt > 0.5 or len(failed_gates) > 0
    
    def generate_action(self, context: Dict[str, Any]) -> RailAction:
        """Generate step size reduction action."""
        current_step_size = context.get('step_size', 1.0)
        new_step_size = max(self.min_step_size, current_step_size * self.reduction_factor)
        
        return RailAction(
            rail_type=self.rail_type,
            action_name="reduce_step_size",
            parameters={
                'old_step_size': current_step_size,
                'new_step_size': new_step_size,
                'reduction_factor': self.reduction_factor
            },
            priority=self.priority
        )


class EvidenceRequestRail(Rail):
    """Rail that requests additional evidence when uncertainty is high."""
    
    def __init__(self, name: str, uncertainty_threshold: float = 0.7):
        super().__init__(name, RailType.REQUEST_EVIDENCE)
        self.uncertainty_threshold = uncertainty_threshold
    
    def should_trigger(self, context: Dict[str, Any], gate_decisions: List[GateDecision]) -> bool:
        """Trigger when uncertainty is high."""
        uncertainty = context.get('uncertainty', 0.0)
        low_confidence_gates = [d for d in gate_decisions if d.confidence < (1.0 - self.uncertainty_threshold)]
        
        return uncertainty > self.uncertainty_threshold or len(low_confidence_gates) > 0
    
    def generate_action(self, context: Dict[str, Any]) -> RailAction:
        """Generate evidence request action."""
        current_level = context.get('current_level', 0)
        target_level = max(0, current_level - 1)  # Go to lower level for evidence
        
        return RailAction(
            rail_type=self.rail_type,
            action_name="request_evidence",
            parameters={
                'target_level': target_level,
                'evidence_type': 'ground_truth',
                'urgency': 'high'
            },
            priority=self.priority + 1  # Higher priority for evidence requests
        )


class ToolInvocationRail(Rail):
    """Rail that invokes tools when specific conditions are met."""
    
    def __init__(self, name: str, tool_name: str, condition_func: Callable[[Dict[str, Any]], bool]):
        super().__init__(name, RailType.INVOKE_TOOL)
        self.tool_name = tool_name
        self.condition_func = condition_func
    
    def should_trigger(self, context: Dict[str, Any], gate_decisions: List[GateDecision]) -> bool:
        """Trigger when condition is met."""
        try:
            return self.condition_func(context)
        except Exception as e:
            logger.error(f"Error in tool rail condition: {e}")
            return False
    
    def generate_action(self, context: Dict[str, Any]) -> RailAction:
        """Generate tool invocation action."""
        tool_params = context.get('tool_parameters', {})
        
        return RailAction(
            rail_type=self.rail_type,
            action_name="invoke_tool",
            parameters={
                'tool_name': self.tool_name,
                'parameters': tool_params
            },
            priority=self.priority
        )


class GateSystem:
    """Manages and coordinates all gates in the system."""
    
    def __init__(self):
        self.gates: Dict[str, Gate] = {}
        self.evaluation_history: List[Dict[str, Any]] = []
    
    def register_gate(self, gate: Gate) -> None:
        """Register a new gate."""
        self.gates[gate.name] = gate
        logger.info(f"Registered gate: {gate.name} ({gate.gate_type.value})")
    
    def evaluate_all_gates(self, context: Dict[str, Any]) -> List[GateDecision]:
        """Evaluate all active gates."""
        decisions = []
        
        for gate in self.gates.values():
            if gate.is_active:
                decision = gate.evaluate(context)
                decisions.append(decision)
        
        # Record evaluation
        self.evaluation_history.append({
            'timestamp': time.time(),
            'context': context,
            'decisions': [d.to_dict() for d in decisions],
            'passed_count': sum(1 for d in decisions if d.passed),
            'failed_count': sum(1 for d in decisions if not d.passed)
        })
        
        # Maintain history size
        if len(self.evaluation_history) > 1000:
            self.evaluation_history.pop(0)
        
        return decisions
    
    def get_gate_summary(self) -> Dict[str, Any]:
        """Get summary of gate system state."""
        gate_stats = {}
        
        for name, gate in self.gates.items():
            gate_stats[name] = {
                'type': gate.gate_type.value,
                'active': gate.is_active,
                'pass_rate': gate.get_pass_rate(),
                'decision_count': len(gate.decision_history)
            }
        
        return {
            'total_gates': len(self.gates),
            'active_gates': sum(1 for g in self.gates.values() if g.is_active),
            'gate_stats': gate_stats,
            'evaluation_count': len(self.evaluation_history)
        }


class RailSystem:
    """Manages and coordinates all rails in the system."""
    
    def __init__(self):
        self.rails: Dict[str, Rail] = {}
        self.action_history: List[Dict[str, Any]] = []
    
    def register_rail(self, rail: Rail) -> None:
        """Register a new rail."""
        self.rails[rail.name] = rail
        logger.info(f"Registered rail: {rail.name} ({rail.rail_type.value})")
    
    def evaluate_rails(self, context: Dict[str, Any], gate_decisions: List[GateDecision]) -> List[RailAction]:
        """Evaluate all rails and return triggered actions."""
        triggered_actions = []
        
        for rail in self.rails.values():
            if rail.is_active and rail.should_trigger(context, gate_decisions):
                action = rail.generate_action(context)
                triggered_actions.append(action)
        
        # Sort by priority (higher priority first)
        triggered_actions.sort(key=lambda a: a.priority, reverse=True)
        
        # Record rail evaluation
        self.action_history.append({
            'timestamp': time.time(),
            'context': context,
            'gate_decisions': [d.to_dict() for d in gate_decisions],
            'triggered_actions': [a.to_dict() for a in triggered_actions],
            'rails_evaluated': len(self.rails)
        })
        
        # Maintain history size
        if len(self.action_history) > 1000:
            self.action_history.pop(0)
        
        return triggered_actions
    
    def execute_actions(self, actions: List[RailAction]) -> List[bool]:
        """Execute a list of rail actions."""
        results = []
        
        for action in actions:
            rail = self.rails.get(action.action_name)
            if rail:
                success = rail.execute_action(action)
                results.append(success)
            else:
                logger.warning(f"Rail not found for action: {action.action_name}")
                results.append(False)
        
        return results
    
    def get_rail_summary(self) -> Dict[str, Any]:
        """Get summary of rail system state."""
        rail_stats = {}
        
        for name, rail in self.rails.items():
            rail_stats[name] = {
                'type': rail.rail_type.value,
                'active': rail.is_active,
                'priority': rail.priority,
                'action_count': len(rail.action_history)
            }
        
        return {
            'total_rails': len(self.rails),
            'active_rails': sum(1 for r in self.rails.values() if r.is_active),
            'rail_stats': rail_stats,
            'action_history_count': len(self.action_history)
        }


class GateRailCoordinator:
    """Coordinates gates and rails for complete governance."""
    
    def __init__(self):
        self.gate_system = GateSystem()
        self.rail_system = RailSystem()
        self.coordinator_history: List[Dict[str, Any]] = []
    
    def evaluate_and_act(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate gates and trigger appropriate rails."""
        # Evaluate all gates
        gate_decisions = self.gate_system.evaluate_all_gates(context)
        
        # Evaluate rails based on gate decisions
        triggered_actions = self.rail_system.evaluate_rails(context, gate_decisions)
        
        # Execute actions
        execution_results = self.rail_system.execute_actions(triggered_actions)
        
        # Record coordination event
        self.coordinator_history.append({
            'timestamp': time.time(),
            'context': context,
            'gate_decisions': [d.to_dict() for d in gate_decisions],
            'triggered_actions': [a.to_dict() for a in triggered_actions],
            'execution_results': execution_results,
            'overall_success': all(execution_results) if execution_results else True
        })
        
        # Maintain history size
        if len(self.coordinator_history) > 1000:
            self.coordinator_history.pop(0)
        
        return {
            'gate_decisions': gate_decisions,
            'triggered_actions': triggered_actions,
            'execution_results': execution_results,
            'overall_success': all(execution_results) if execution_results else True,
            'failed_gates': [d for d in gate_decisions if not d.passed],
            'successful_actions': sum(execution_results) if execution_results else 0
        }
    
    def setup_default_gates_and_rails(self, max_debt: float = 1.0) -> None:
        """Set up default gates and rails for basic governance."""
        # Default hard gates
        non_negative_gate = HardGate(
            "non_negative_values",
            lambda ctx: np.all(ctx.get('data', np.array([])) >= 0),
            "Negative values detected"
        )
        self.gate_system.register_gate(non_negative_gate)
        
        finite_values_gate = HardGate(
            "finite_values",
            lambda ctx: np.all(np.isfinite(ctx.get('data', np.array([])))),
            "Non-finite values detected"
        )
        self.gate_system.register_gate(finite_values_gate)
        
        # Default soft gate
        debt_gate = SoftGate("coherence_debt", max_debt)
        self.gate_system.register_gate(debt_gate)
        
        # Default rails
        step_size_rail = StepSizeRail("adaptive_step_size")
        self.rail_system.register_rail(step_size_rail)
        
        evidence_rail = EvidenceRequestRail("evidence_request")
        self.rail_system.register_rail(evidence_rail)
    
    def get_coordination_summary(self) -> Dict[str, Any]:
        """Get summary of coordinator state."""
        if not self.coordinator_history:
            return {"status": "no_history"}
        
        latest = self.coordinator_history[-1]
        gate_summary = self.gate_system.get_gate_summary()
        rail_summary = self.rail_system.get_rail_summary()
        
        return {
            'latest_evaluation': {
                'timestamp': latest['timestamp'],
                'overall_success': latest['overall_success'],
                'failed_gates_count': len(latest['failed_gates']),
                'triggered_actions_count': len(latest['triggered_actions']),
                'successful_actions_count': latest['successful_actions']
            },
            'gate_summary': gate_summary,
            'rail_summary': rail_summary,
            'coordination_history_count': len(self.coordinator_history)
        }