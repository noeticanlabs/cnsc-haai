"""
Clock Arbitration System

Provides temporal clocks for computing dt (delta time) values in TGS.
Each clock measures a different dimension of temporal risk:

- ConsistencyClock: Measures contradiction risk introduced by delta
- CommitmentClock: Measures obligation load and intent instability
- CausalityClock: Enforces temporal ordering and evidence availability
- ResourceClock: Limits based on remaining budgets
- TaintClock: Penalizes untrusted or weakly-provenanced input
- DriftClock: Measures coherence drift from prior state

The ClockRegistry manages all clock instances and performs dt arbitration.

Also provides affine time parameterization for proper time conversion:
- AffineReparam: Affine reparameterization matching UFE.Reparam
- Clock: Time governance with affine parameterization
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4
from datetime import datetime


@dataclass
class AffineReparam:
    """
    Affine reparameterization matching UFE.Reparam.

    Ensures clock is affine: φ(τ) = φ(0) + φ'(0) * τ (φ'' ≡ 0)
    This is required for proper time parameterization.

    Mathematical definition:
    - φ(τ) = φ(0) + φ'(0) * τ
    - φ'(τ) = φ'(0) (constant for affine)
    - φ''(τ) = 0 (required for affine)

    Attributes:
        phi_0: φ(0) - Initial time offset
        phi_prime_0: φ'(0) - Rate (must be > 0 for monotonic time)
        phi_double_prime: φ''(τ) - Must be 0 for affine
    """

    phi_0: float = 0.0  # φ(0)
    phi_prime_0: float = 1.0  # φ'(0) > 0 (monotonic)
    phi_double_prime: float = 0.0  # Must be 0 for affine

    def phi(self, tau: float) -> float:
        """
        Compute φ(τ) = φ(0) + φ'(0) * τ

        Args:
            tau: Proper time parameter

        Returns:
            Coordinate time
        """
        return self.phi_0 + self.phi_prime_0 * tau

    def phi_prime(self, tau: float) -> float:
        """
        Compute φ'(τ) = φ'(0) (constant for affine).

        Args:
            tau: Proper time parameter (ignored for affine)

        Returns:
            Constant rate φ'(0)
        """
        return self.phi_prime_0

    def is_affine(self) -> bool:
        """Check φ'' ≡ 0 (required for affine)."""
        return self.phi_double_prime == 0.0

    def to_proper_time(self, coordinate_time: float) -> float:
        """
        Convert coordinate time to proper time.

        τ = (t - φ(0)) / φ'(0)

        Args:
            coordinate_time: Coordinate time value

        Returns:
            Proper time
        """
        return (coordinate_time - self.phi_0) / self.phi_prime_0

    def to_coordinate_time(self, proper_time: float) -> float:
        """
        Convert proper time to coordinate time.

        t = φ(0) + φ'(0) * τ

        Args:
            proper_time: Proper time value

        Returns:
            Coordinate time
        """
        return self.phi(proper_time)

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            "phi_0": self.phi_0,
            "phi_prime_0": self.phi_prime_0,
            "phi_double_prime": self.phi_double_prime,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> "AffineReparam":
        """Create from dictionary."""
        return cls(
            phi_0=data.get("phi_0", 0.0),
            phi_prime_0=data.get("phi_prime_0", 1.0),
            phi_double_prime=data.get("phi_double_prime", 0.0),
        )


class Clock:
    """
    Time governance with affine parameterization.

    Provides proper time tracking with affine reparameterization support.
    """

    def __init__(self, reparam: Optional[AffineReparam] = None):
        """
        Initialize Clock.

        Args:
            reparam: Affine reparameterization (default: identity)
        """
        self.reparam = reparam or AffineReparam()
        self._start_time: Optional[datetime] = None
        self._start_proper_time: float = 0.0

    def start(self) -> None:
        """Start clock with affine parameterization."""
        self._start_time = datetime.utcnow()
        self._start_proper_time = 0.0

    def now(self) -> float:
        """
        Get proper time (affine parameter) in seconds.

        Returns:
            Proper time τ since clock start
        """
        if self._start_time is None:
            raise RuntimeError("Clock not started. Call start() first.")

        elapsed = (datetime.utcnow() - self._start_time).total_seconds()
        return self.reparam.to_proper_time(elapsed)

    def elapsed(self) -> float:
        """Alias for now() - returns proper time elapsed."""
        return self.now()

    def to_proper_time(self, coordinate_time: float) -> float:
        """Convert coordinate time to proper time."""
        return self.reparam.to_proper_time(coordinate_time)

    def to_coordinate_time(self, proper_time: float) -> float:
        """Convert proper time to coordinate time."""
        return self.reparam.to_coordinate_time(proper_time)

    def is_affine(self) -> bool:
        """Check if reparameterization is affine."""
        return self.reparam.is_affine()

    def get_reparam(self) -> AffineReparam:
        """Get the current reparameterization."""
        return self.reparam

    def set_reparam(self, reparam: AffineReparam) -> None:
        """Set a new reparameterization."""
        self.reparam = reparam

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "reparam": self.reparam.to_dict(),
            "is_running": self._start_time is not None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Clock":
        """Create from dictionary."""
        reparam_data = data.get("reparam", {})
        reparam = AffineReparam.from_dict(reparam_data)
        clock = cls(reparam=reparam)
        if not data.get("is_running", False):
            clock._start_time = None
        return clock


class ClockID(str):
    """Unique identifier for a clock."""

    def __new__(cls, value: str):
        instance = super().__new__(cls, value)
        return instance


class BaseClock(ABC):
    """Base class for all temporal clocks."""

    @property
    @abstractmethod
    def clock_id(self) -> ClockID:
        """Return unique clock identifier."""
        pass

    @property
    @abstractmethod
    def weight(self) -> float:
        """Return clock weight for arbitration (default 1.0)."""
        pass

    @abstractmethod
    def compute_dt(self, proposal: "Proposal", state: Dict[str, Any]) -> float:
        """
        Compute dt contribution for this clock.

        Args:
            proposal: The proposal being evaluated
            state: Current cognitive state

        Returns:
            dt value (0.0 to 1.0, where 1.0 = maximum temporal risk)
        """
        pass


class ConsistencyClock(BaseClock):
    """Measures contradiction risk introduced by delta."""

    @property
    def clock_id(self) -> ClockID:
        return ClockID("consistency")

    @property
    def weight(self) -> float:
        return 1.0

    def compute_dt(self, proposal: "Proposal", state: Dict[str, Any]) -> float:
        """Compute consistency-based dt from proposal deltas."""
        dt = 0.0

        for delta in proposal.delta_ops:
            if delta.operation == DeltaOperationType.REVISE_BELIEF:
                # Check for contradiction with existing beliefs
                existing = state.get("beliefs", {})
                target = delta.target
                if target in existing:
                    # High dt for belief revision
                    dt += 0.3
                else:
                    # Lower dt for new belief
                    dt += 0.1
            elif delta.operation == DeltaOperationType.ADD_BELIEF:
                # New beliefs have low contradiction risk
                dt += 0.05

        # Cap at 1.0
        return min(dt, 1.0)


class CommitmentClock(BaseClock):
    """Measures obligation load and intent instability."""

    @property
    def clock_id(self) -> ClockID:
        return ClockID("commitment")

    @property
    def weight(self) -> float:
        return 1.0

    def compute_dt(self, proposal: "Proposal", state: Dict[str, Any]) -> float:
        """Compute commitment-based dt from obligations."""
        dt = 0.0

        # Check current obligation load
        obligations = state.get("obligations", [])
        obligation_count = len(obligations)

        # Base dt from obligation count
        if obligation_count > 10:
            dt += 0.4
        elif obligation_count > 5:
            dt += 0.2
        elif obligation_count > 0:
            dt += 0.1

        # Check for intent instability
        intents = state.get("intents", [])
        recent_changes = sum(1 for intent in intents if intent.get("stability", 1.0) < 0.5)

        if recent_changes > 0:
            dt += min(recent_changes * 0.15, 0.5)

        return min(dt, 1.0)


class CausalityClock(BaseClock):
    """Enforces temporal ordering and evidence availability."""

    @property
    def clock_id(self) -> ClockID:
        return ClockID("causality")

    @property
    def weight(self) -> float:
        return 1.5  # Higher weight for causality

    def compute_dt(self, proposal: "Proposal", state: Dict[str, Any]) -> float:
        """Compute causality-based dt from evidence and ordering."""
        dt = 0.0

        # Check evidence availability
        evidence_refs = proposal.evidence_refs
        if evidence_refs:
            available = sum(
                1
                for ref in evidence_refs
                if state.get("evidence", {}).get(ref, {}).get("available", False)
            )
            if available < len(evidence_refs):
                dt += 0.3 * (1 - available / max(len(evidence_refs), 1))

        # Check temporal ordering
        current_time = state.get("logical_time", 0)
        for delta in proposal.delta_ops:
            if hasattr(delta, "prerequisites"):
                # Check if prerequisites are met
                unmet = [
                    prereq
                    for prereq in delta.prerequisites
                    if state.get("events", {}).get(prereq, {}).get("time", 0) > current_time
                ]
                if unmet:
                    dt += 0.4 * (len(unmet) / max(len(delta.prerequisites), 1))

        return min(dt, 1.0)


class ResourceClock(BaseClock):
    """Limits based on remaining budgets."""

    @property
    def clock_id(self) -> ClockID:
        return ClockID("resource")

    @property
    def weight(self) -> float:
        return 1.0

    def compute_dt(self, proposal: "Proposal", state: Dict[str, Any]) -> float:
        """Compute resource-based dt from budget utilization."""
        dt = 0.0

        budgets = state.get("budgets", {})
        cost_estimate = proposal.cost_estimate if proposal.cost_estimate else {}

        for resource, remaining in budgets.items():
            allocated = cost_estimate.get(resource, 0)
            utilization = allocated / max(remaining, 1)

            if utilization > 0.9:
                dt += 0.4
            elif utilization > 0.7:
                dt += 0.2
            elif utilization > 0.5:
                dt += 0.1

        return min(dt, 1.0)


class TaintClock(BaseClock):
    """Penalizes untrusted or weakly-provenanced input."""

    @property
    def clock_id(self) -> ClockID:
        return ClockID("taint")

    @property
    def weight(self) -> float:
        return 1.2  # Higher weight for taint

    def compute_dt(self, proposal: "Proposal", state: Dict[str, Any]) -> float:
        """Compute taint-based dt from provenance assessment."""
        taint = proposal.taint_class

        dt_map = {
            TaintClass.TRUSTED: 0.0,
            TaintClass.EXTERNAL: 0.2,
            TaintClass.SPECULATIVE: 0.5,
            TaintClass.UNTRUSTED: 0.8,
        }

        base_dt = dt_map.get(taint, 0.5)

        # Add penalty for weak provenance
        provenance_depth = 0
        for delta in proposal.delta_ops:
            if delta.provenance:
                depth = delta.provenance.count("->") + 1
                provenance_depth = max(provenance_depth, depth)

        if provenance_depth < 2 and taint != TaintClass.TRUSTED:
            base_dt += 0.2

        return min(base_dt, 1.0)


class DriftClock(BaseClock):
    """Measures coherence drift from prior state."""

    @property
    def clock_id(self) -> ClockID:
        return ClockID("drift")

    @property
    def weight(self) -> float:
        return 1.0

    def compute_dt(self, proposal: "Proposal", state: Dict[str, Any]) -> float:
        """Compute drift-based dt from state changes."""
        dt = 0.0

        # Count delta operations
        delta_count = len(proposal.delta_ops)

        if delta_count > 20:
            dt += 0.4
        elif delta_count > 10:
            dt += 0.2
        elif delta_count > 5:
            dt += 0.1

        # Check for phase changes
        current_phase = state.get("phase", "unknown")
        target_phase = None

        for delta in proposal.delta_ops:
            if delta.operation == DeltaOperationType.PHASE_TRANSITION:
                target_phase = delta.payload.get("phase")
                break

        if target_phase and target_phase != current_phase:
            dt += 0.3

        # Check tag changes
        tag_deltas = sum(
            1
            for delta in proposal.delta_ops
            if delta.operation in (DeltaOperationType.ADD_TAG, DeltaOperationType.REMOVE_TAG)
        )

        if tag_deltas > 5:
            dt += 0.2

        return min(dt, 1.0)


@dataclass
class ClockResult:
    """Result from a single clock computation."""

    clock_id: ClockID
    dt: float
    weight: float
    weighted_dt: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.weighted_dt = self.dt * self.weight


class ClockRegistry:
    """
    Manages all clock instances and performs dt arbitration.

    The registry:
    1. Registers clock instances
    2. Computes weighted dt from all clocks
    3. Returns dt with clock attribution
    """

    def __init__(self):
        self._clocks: Dict[ClockID, BaseClock] = {}
        self._default_weight: float = 1.0

    def register_clock(self, clock: BaseClock) -> None:
        """Register a clock with the registry."""
        self._clocks[clock.clock_id] = clock

    def unregister_clock(self, clock_id: ClockID) -> Optional[BaseClock]:
        """Unregister a clock and return it."""
        return self._clocks.pop(clock_id, None)

    def get_clock(self, clock_id: ClockID) -> Optional[BaseClock]:
        """Get a registered clock."""
        return self._clocks.get(clock_id)

    def list_clocks(self) -> List[ClockID]:
        """List all registered clock IDs."""
        return list(self._clocks.keys())

    def compute_dt(
        self, proposal: "Proposal", state: Dict[str, Any]
    ) -> Tuple[float, Dict[ClockID, float]]:
        """
        Compute dt via clock arbitration.

        Args:
            proposal: The proposal being evaluated
            state: Current cognitive state

        Returns:
            Tuple of (total_dt, clock_dts) where clock_dts maps clock_id to its dt contribution
        """
        clock_results: List[ClockResult] = []

        for clock in self._clocks.values():
            dt = clock.compute_dt(proposal, state)
            result = ClockResult(
                clock_id=clock.clock_id,
                dt=dt,
                weight=clock.weight,
            )
            clock_results.append(result)

        # Compute weighted total dt
        total_weighted_dt = sum(r.weighted_dt for r in clock_results)
        max_possible_weight = sum(r.weight for r in clock_results)

        # Normalize to [0, 1]
        if max_possible_weight > 0:
            total_dt = total_weighted_dt / max_possible_weight
        else:
            total_dt = 0.0

        # Return individual clock dts
        clock_dts = {r.clock_id: r.dt for r in clock_results}

        return min(total_dt, 1.0), clock_dts


# Import Proposal for type hints
from cnsc.haai.tgs.proposal import (
    Proposal,
    DeltaOperationType,
    TaintClass,
)
