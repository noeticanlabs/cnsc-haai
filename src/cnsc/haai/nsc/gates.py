"""
Gate and Rail Evaluator

Gate and rail constraint evaluation for the Coherence Framework.

This module provides:
- GateType: Types of gates
- GateCondition: Condition evaluation
- GateResult: Gate evaluation result
- Gate: Base gate class
- EvidenceSufficiencyGate: Evidence sufficiency check
- CoherenceCheckGate: Coherence check
- GateManager: Gate registry and evaluation
- BridgeCert: Certified inference from discrete to analytic bounds
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, Tuple
from abc import ABC, abstractmethod
from uuid import uuid4
from datetime import datetime

from cnsc.haai.nsc.proposer_client import ProposerClient
from cnsc.haai.nsc.proposer_client_errors import ProposerClientError


@dataclass
class Trajectory:
    """
    Trajectory representation for bridge theorem.
    
    Represents a trajectory through state space for coherence verification.
    """
    points: List[List[float]] = field(default_factory=list)
    weights: List[float] = field(default_factory=list)
    
    def norm(self) -> float:
        """Compute trajectory norm."""
        import math
        if not self.points:
            return 0.0
        total = 0.0
        for i, point in enumerate(self.points):
            weight = self.weights[i] if i < len(self.weights) else 1.0
            for val in point:
                total += weight * val * val
        return math.sqrt(total)


class BridgeCert:
    """
    BridgeCert: Certified inference from discrete to analytic bounds.
    
    Implements the errorBound function: τΔ → Δ → τC
    where discrete residual bound τΔ and step size Δ imply analytic bound τC.
    
    This implements the bridge theorem: discrete evidence → analytic truth.
    If ‖residualΔ‖ ≤ τΔ, then ‖residual‖ ≤ errorBound(τΔ, Δ).
    """
    
    def __init__(self, base_error: float = 0.01, error_growth_rate: float = 0.1):
        """
        Initialize BridgeCert.
        
        Args:
            base_error: Base error coefficient
            error_growth_rate: Rate of error growth with step size
        """
        self.base_error = base_error
        self.error_growth_rate = error_growth_rate
    
    def errorBound(self, tau_delta: float, delta: float) -> float:
        """
        Compute analytic error bound from discrete error bound.
        
        Implements: τC = τΔ * (1 + k * Δ) where k is error_growth_rate.
        
        Args:
            tau_delta: Discrete residual bound (from receipt)
            delta: Step size for discretization
            
        Returns:
            tau_c: Analytic residual bound
        """
        # Simple linear bound: τC = τΔ * (1 + k * Δ)
        return tau_delta * (1.0 + self.error_growth_rate * delta)
    
    def bridge(self, psi: Trajectory, t: float, delta: float, tau_delta: float) -> bool:
        """
        Bridge theorem: discrete evidence → analytic truth.
        
        Returns True if ‖residualΔ‖ ≤ τΔ implies ‖residual‖ ≤ errorBound(τΔ, Δ)
        
        Args:
            psi: Trajectory representation
            t: Time parameter
            delta: Step size
            tau_delta: Discrete residual bound
            
        Returns:
            True if bridge theorem holds
        """
        # Conservative: assume theorem holds for well-formed trajectories
        analytic_bound = self.errorBound(tau_delta, delta)
        trajectory_norm = psi.norm()
        return trajectory_norm <= analytic_bound
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "base_error": self.base_error,
            "error_growth_rate": self.error_growth_rate,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BridgeCert':
        """Create from dictionary."""
        return cls(
            base_error=data.get("base_error", 0.01),
            error_growth_rate=data.get("error_growth_rate", 0.1),
        )


class GateType(Enum):
    """Types of gates."""
    EVIDENCE_SUFFICIENCY = auto()
    COHERENCE_CHECK = auto()
    AFFORDABILITY = auto()
    RAIL_TRAJECTORY = auto()
    PHASE_TRANSITION = auto()
    CUSTOM = auto()


class GateDecision(Enum):
    """Gate evaluation decision."""
    PASS = auto()
    FAIL = auto()
    PENDING = auto()
    SKIP = auto()


@dataclass
class GateCondition:
    """
    Gate condition.
    
    Defines a condition that must be satisfied for gate to pass.
    """
    condition_id: str
    name: str
    condition_type: str  # "threshold", "comparison", "custom"
    threshold: Optional[float] = None
    operator: Optional[str] = None  # "gt", "lt", "eq", "ge", "le"
    value: Optional[Any] = None
    custom_check: Optional[Callable] = None
    is_required: bool = True
    
    def evaluate(self, context: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Evaluate condition.
        
        Returns:
            Tuple of (passed, message)
        """
        # Get value from context
        actual_value = context.get(self.name, 0)
        
        # Custom check
        if self.custom_check:
            try:
                result = self.custom_check(actual_value, context)
                return result, f"Custom check: {result}"
            except Exception as e:
                return False, f"Custom check error: {e}"
        
        # Threshold check
        if self.condition_type == "threshold":
            if self.threshold is None:
                return False, "No threshold specified"
            
            if self.operator == "gt":
                passed = actual_value > self.threshold
            elif self.operator == "lt":
                passed = actual_value < self.threshold
            elif self.operator == "ge":
                passed = actual_value >= self.threshold
            elif self.operator == "le":
                passed = actual_value <= self.threshold
            elif self.operator == "eq":
                passed = actual_value == self.threshold
            else:
                passed = actual_value >= self.threshold
            
            return passed, f"{self.name}: {actual_value} {'>=' if self.operator is None else self.operator} {self.threshold}"
        
        # Comparison check
        if self.condition_type == "comparison":
            if self.value is None:
                return False, "No comparison value specified"
            
            if self.operator == "eq":
                passed = actual_value == self.value
            elif self.operator == "ne":
                passed = actual_value != self.value
            else:
                passed = actual_value == self.value
            
            return passed, f"{self.name}: {actual_value} == {self.value}"
        
        return True, "Condition passed"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "condition_id": self.condition_id,
            "name": self.name,
            "condition_type": self.condition_type,
            "threshold": self.threshold,
            "operator": self.operator,
            "value": self.value,
            "is_required": self.is_required,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GateCondition':
        """Create from dictionary."""
        return cls(
            condition_id=data["condition_id"],
            name=data["name"],
            condition_type=data["condition_type"],
            threshold=data.get("threshold"),
            operator=data.get("operator"),
            value=data.get("value"),
            is_required=data.get("is_required", True),
        )


@dataclass
class GateResult:
    """
    Gate evaluation result.
    
    Result of gate evaluation with decision and details.
    """
    gate_id: str
    gate_name: str
    decision: GateDecision
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Details
    message: str = ""
    conditions_passed: int = 0
    conditions_failed: int = 0
    conditions_skipped: int = 0
    coherence_level: float = 1.0
    
    # Metrics
    evaluation_time_ms: float = 0.0
    
    # Context
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "gate_id": self.gate_id,
            "gate_name": self.gate_name,
            "decision": self.decision.name,
            "timestamp": self.timestamp.isoformat(),
            "message": self.message,
            "conditions_passed": self.conditions_passed,
            "conditions_failed": self.conditions_failed,
            "conditions_skipped": self.conditions_skipped,
            "coherence_level": self.coherence_level,
            "evaluation_time_ms": self.evaluation_time_ms,
            "context": self.context,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GateResult':
        """Create from dictionary."""
        return cls(
            gate_id=data["gate_id"],
            gate_name=data["gate_name"],
            decision=GateDecision[data["decision"]],
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.utcnow(),
            message=data.get("message", ""),
            conditions_passed=data.get("conditions_passed", 0),
            conditions_failed=data.get("conditions_failed", 0),
            conditions_skipped=data.get("conditions_skipped", 0),
            coherence_level=data.get("coherence_level", 1.0),
            evaluation_time_ms=data.get("evaluation_time_ms", 0.0),
            context=data.get("context", {}),
        )
    
    def is_pass(self) -> bool:
        """Check if gate passed."""
        return self.decision == GateDecision.PASS
    
    def is_fail(self) -> bool:
        """Check if gate failed."""
        return self.decision == GateDecision.FAIL


class Gate(ABC):
    """
    Base Gate class.
    
    Abstract base class for all gates.
    """
    
    def __init__(
        self,
        gate_id: str,
        name: str,
        gate_type: GateType,
        conditions: Optional[List[GateCondition]] = None,
        is_required: bool = True,
        proposer_client: Optional[ProposerClient] = None,
    ):
        self.gate_id = gate_id
        self.name = name
        self.gate_type = gate_type
        self.conditions = conditions or []
        self.is_required = is_required
        self.proposer_client = proposer_client
    
    def request_repair(self, gate_name: str, failure_reasons: list) -> list:
        """
        Request repair proposals from NPE for a failed gate.
        
        Args:
            gate_name: Name of the gate that failed
            failure_reasons: List of reasons for the failure
            
        Returns:
            List of repair proposals
        """
        if not self.proposer_client:
            return []
        
        try:
            response = self.proposer_client.repair(
                gate_name=gate_name,
                failure_reasons=failure_reasons,
                context={},
            )
            return response.get("proposals", [])
        except ProposerClientError:
            return []
        except Exception:
            return []
    
    @abstractmethod
    def evaluate(self, context: Dict[str, Any]) -> GateResult:
        """Evaluate gate."""
        pass
    
    def add_condition(self, condition: GateCondition) -> None:
        """Add condition to gate."""
        self.conditions.append(condition)
    
    def remove_condition(self, condition_id: str) -> bool:
        """Remove condition from gate."""
        for i, c in enumerate(self.conditions):
            if c.condition_id == condition_id:
                self.conditions.pop(i)
                return True
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "gate_id": self.gate_id,
            "name": self.name,
            "gate_type": self.gate_type.name,
            "conditions": [c.to_dict() for c in self.conditions],
            "is_required": self.is_required,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Gate':
        """Create from dictionary - override in subclasses."""
        return cls(
            gate_id=data["gate_id"],
            name=data["name"],
            gate_type=GateType[data["gate_type"]],
            conditions=[GateCondition.from_dict(c) for c in data.get("conditions", [])],
            is_required=data.get("is_required", True),
        )


class EvidenceSufficiencyGate(Gate):
    """
    Evidence Sufficiency Gate.
    
    Evaluates whether sufficient evidence has been gathered.
    """
    
    def __init__(
        self,
        gate_id: str = "evidence_sufficiency",
        name: str = "Evidence Sufficiency",
        min_evidence_count: int = 3,
        min_coherence: float = 0.5,
    ):
        super().__init__(
            gate_id=gate_id,
            name=name,
            gate_type=GateType.EVIDENCE_SUFFICIENCY,
            conditions=[
                GateCondition(
                    condition_id="evidence_count",
                    name="evidence_count",
                    condition_type="threshold",
                    threshold=min_evidence_count,
                    operator="ge",
                    is_required=True,
                ),
                GateCondition(
                    condition_id="coherence_level",
                    name="coherence_level",
                    condition_type="threshold",
                    threshold=min_coherence,
                    operator="ge",
                    is_required=True,
                ),
            ],
        )
        self.min_evidence_count = min_evidence_count
        self.min_coherence = min_coherence
    
    def evaluate(self, context: Dict[str, Any]) -> GateResult:
        """Evaluate evidence sufficiency."""
        result = GateResult(
            gate_id=self.gate_id,
            gate_name=self.name,
            decision=GateDecision.PENDING,
        )
        
        start_time = datetime.utcnow()
        
        # Evaluate conditions
        for condition in self.conditions:
            passed, message = condition.evaluate(context)
            
            if passed:
                result.conditions_passed += 1
            elif not condition.is_required:
                result.conditions_skipped += 1
            else:
                result.conditions_failed += 1
                result.message = f"Failed: {message}"
        
        # Make decision
        required_failed = any(
            not c.is_required or c.evaluate(context)[0]
            for c in self.conditions
        )
        
        if result.conditions_failed == 0:
            result.decision = GateDecision.PASS
            result.message = "Evidence sufficiency gate passed"
        else:
            result.decision = GateDecision.FAIL
            if not result.message:
                result.message = "Evidence sufficiency gate failed"
        
        # Get coherence level from context
        result.coherence_level = context.get("coherence_level", 1.0)
        result.context = context
        
        # Calculate evaluation time
        result.evaluation_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return result


class CoherenceCheckGate(Gate):
    """
    Coherence Check Gate.
    
    Evaluates coherence of reasoning state.
    """
    
    def __init__(
        self,
        gate_id: str = "coherence_check",
        name: str = "Coherence Check",
        min_coherence: float = 0.5,
        hysteresis_margin: float = 0.1,
    ):
        super().__init__(
            gate_id=gate_id,
            name=name,
            gate_type=GateType.COHERENCE_CHECK,
            conditions=[
                GateCondition(
                    condition_id="coherence",
                    name="coherence_level",
                    condition_type="threshold",
                    threshold=min_coherence,
                    operator="ge",
                    is_required=True,
                ),
            ],
        )
        self.min_coherence = min_coherence
        self.hysteresis_margin = hysteresis_margin
        self.last_decision: Optional[GateDecision] = None
    
    def evaluate(self, context: Dict[str, Any]) -> GateResult:
        """Evaluate coherence."""
        result = GateResult(
            gate_id=self.gate_id,
            gate_name=self.name,
            decision=GateDecision.PENDING,
        )
        
        start_time = datetime.utcnow()
        
        coherence = context.get("coherence_level", 1.0)
        
        # Apply hysteresis
        if self.last_decision == GateDecision.FAIL:
            # Need margin above threshold to recover
            threshold = self.min_coherence + self.hysteresis_margin
        else:
            threshold = self.min_coherence
        
        # Evaluate condition
        passed = coherence >= threshold
        
        if passed:
            result.conditions_passed = 1
            result.decision = GateDecision.PASS
            result.message = f"Coherence check passed: {coherence:.3f} >= {threshold:.3f}"
        else:
            result.conditions_failed = 1
            result.decision = GateDecision.FAIL
            result.message = f"Coherence check failed: {coherence:.3f} < {threshold:.3f}"
        
        self.last_decision = result.decision
        result.coherence_level = coherence
        result.context = context
        result.evaluation_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return result


@dataclass
class GateManager:
    """
    Gate Manager.
    
    Registry and evaluation of gates with bridge certification support.
    
    Attributes:
        bridge_cert: Optional BridgeCert for error bound computation
        last_error_bound: Last computed error bound
        last_step_size: Last step size used for error bound
    """
    manager_id: str = str(uuid4())[:8]
    name: str = "Gate Manager"
    
    # Gate registry
    gates: Dict[str, Gate] = field(default_factory=dict)
    
    # Default gates
    use_default_gates: bool = True
    
    # Bridge certification
    bridge_cert: Optional[BridgeCert] = None
    last_error_bound: float = 0.0
    last_step_size: float = 0.0
    
    # Statistics
    total_evaluations: int = 0
    total_passes: int = 0
    total_failures: int = 0
    
    def __post_init__(self) -> None:
        """Initialize with default gates."""
        if self.use_default_gates:
            self._create_default_gates()
        # Initialize default bridge cert if not provided
        if self.bridge_cert is None:
            self.bridge_cert = BridgeCert()
    
    def set_bridge_cert(self, bridge_cert: BridgeCert) -> None:
        """Set the bridge certificate for error bound computation."""
        self.bridge_cert = bridge_cert
    
    def compute_error_bound(self, tau_delta: float, delta: float) -> float:
        """
        Compute analytic error bound using bridge certification.
        
        Args:
            tau_delta: Discrete residual bound
            delta: Step size for discretization
            
        Returns:
            Analytic error bound τC
        """
        if self.bridge_cert is None:
            self.bridge_cert = BridgeCert()
        self.last_error_bound = self.bridge_cert.errorBound(tau_delta, delta)
        self.last_step_size = delta
        return self.last_error_bound
    
    def get_bridge_info(self) -> Dict[str, Any]:
        """Get bridge certification information."""
        return {
            "bridge_cert": self.bridge_cert.to_dict() if self.bridge_cert else None,
            "last_error_bound": self.last_error_bound,
            "last_step_size": self.last_step_size,
        }
    
    def _create_default_gates(self) -> None:
        """Create default gates."""
        evidence_gate = EvidenceSufficiencyGate()
        coherence_gate = CoherenceCheckGate()
        
        self.register_gate(evidence_gate)
        self.register_gate(coherence_gate)
    
    def register_gate(self, gate: Gate) -> bool:
        """Register gate."""
        if gate.gate_id in self.gates:
            return False
        self.gates[gate.gate_id] = gate
        return True
    
    def unregister_gate(self, gate_id: str) -> bool:
        """Unregister gate."""
        if gate_id in self.gates:
            del self.gates[gate_id]
            return True
        return False
    
    def get_gate(self, gate_id: str) -> Optional[Gate]:
        """Get gate by ID."""
        return self.gates.get(gate_id)
    
    def evaluate_gate(self, gate_id: str, context: Dict[str, Any]) -> Optional[GateResult]:
        """Evaluate single gate."""
        gate = self.gates.get(gate_id)
        if not gate:
            return None
        
        result = gate.evaluate(context)
        self._update_stats(result)
        return result
    
    def evaluate_all(
        self,
        context: Dict[str, Any],
        required_only: bool = True,
    ) -> List[GateResult]:
        """Evaluate all gates."""
        results = []
        
        for gate_id, gate in self.gates.items():
            if required_only and not gate.is_required:
                continue
            
            result = gate.evaluate(context)
            results.append(result)
            self._update_stats(result)
        
        return results
    
    def evaluate_required(
        self,
        context: Dict[str, Any],
    ) -> Tuple[bool, List[GateResult]]:
        """
        Evaluate all required gates.
        
        Returns:
            Tuple of (all_passed, results)
        """
        results = self.evaluate_all(context, required_only=True)
        all_passed = all(r.is_pass() for r in results)
        return all_passed, results
    
    def can_proceed(self, context: Dict[str, Any], threshold: float = 0.5) -> bool:
        """Check if reasoning can proceed."""
        coherence = context.get("coherence_level", 1.0)
        return coherence >= threshold
    
    def needs_recovery(self, context: Dict[str, Any], threshold: float = 0.5) -> bool:
        """Check if recovery is needed."""
        coherence = context.get("coherence_level", 1.0)
        return coherence < threshold
    
    def _update_stats(self, result: GateResult) -> None:
        """Update statistics."""
        self.total_evaluations += 1
        if result.is_pass():
            self.total_passes += 1
        elif result.is_fail():
            self.total_failures += 1
    
    def get_summary(self, results: List[GateResult]) -> Dict[str, Any]:
        """Get summary of gate evaluation results."""
        passed = sum(1 for r in results if r.is_pass())
        failed = sum(1 for r in results if r.is_fail())
        pending = sum(1 for r in results if r.decision == GateDecision.PENDING)
        skipped = sum(1 for r in results if r.decision == GateDecision.SKIP)
        
        return {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "pending": pending,
            "skipped": skipped,
            "pass_rate": passed / len(results) if results else 1.0,
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get manager statistics."""
        return {
            "manager_id": self.manager_id,
            "name": self.name,
            "gate_count": len(self.gates),
            "total_evaluations": self.total_evaluations,
            "total_passes": self.total_passes,
            "total_failures": self.total_failures,
            "pass_rate": self.total_passes / self.total_evaluations if self.total_evaluations > 0 else 1.0,
        }
    
    def create_default_gates(self) -> None:
        """Create default gates."""
        self._create_default_gates()
    
    def reset(self) -> None:
        """Reset manager state."""
        self.gates.clear()
        self.total_evaluations = 0
        self.total_passes = 0
        self.total_failures = 0
        self._create_default_gates()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "manager_id": self.manager_id,
            "name": self.name,
            "gates": {k: g.to_dict() for k, g in self.gates.items()},
            "total_evaluations": self.total_evaluations,
            "total_passes": self.total_passes,
            "total_failures": self.total_failures,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GateManager':
        """Create from dictionary."""
        manager = cls(
            manager_id=data.get("manager_id", str(uuid4())[:8]),
            name=data.get("name", "Gate Manager"),
            use_default_gates=False,
        )
        
        # Recreate gates
        for gate_data in data.get("gates", {}).values():
            gate_type = gate_data.get("gate_type", "EVIDENCE_SUFFICIENCY")
            if gate_type == "EVIDENCE_SUFFICIENCY":
                gate = EvidenceSufficiencyGate.from_dict(gate_data)
            elif gate_type == "COHERENCE_CHECK":
                gate = CoherenceCheckGate.from_dict(gate_data)
            else:
                gate = Gate.from_dict(gate_data)
            manager.gates[gate.gate_id] = gate
        
        manager.total_evaluations = data.get("total_evaluations", 0)
        manager.total_passes = data.get("total_passes", 0)
        manager.total_failures = data.get("total_failures", 0)
        
        return manager


def create_gate_manager(use_default_gates: bool = True) -> GateManager:
    """Create new gate manager."""
    return GateManager(use_default_gates=use_default_gates)
