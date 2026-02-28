"""
Risk Functional V Implementation

This module implements the deterministic risk functional V: X → Q≥0

Per docs/ats/10_mathematical_core/risk_functional_V.md:
- V : X → Q≥0
- Deterministic, fixed-point domain
- No floats allowed
- Monotone guard semantics

===============================================================================
VERIFICATION REGIME: RV RECOMPUTES V (Regime 1)
===============================================================================

Per Gap B: Risk witness regime

The ATS kernel uses Regime 1: RV recomputes V from committed state.
This means:
- RV must have access to state data (or StateCore) sufficient to compute V
- No witnesses/bounds are needed - RV computes exact risk
- The receipt contains state_hash_before/after, and RV can recompute V

This is simpler than Regime 2 (verify bounds) and provides stronger guarantees.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict

from .numeric import QFixed
from .types import State, BeliefState, MemoryState, PlanState, PolicyState, IOState, StateCore

# Standard weights for risk aggregation
# Per docs/ats/30_ats_runtime/risk_witness_generation.md
# Each weight = 0.2 = 2e17 in QFixed
DEFAULT_WEIGHTS = {
    "belief": QFixed(200000000000000000),  # 0.2
    "memory": QFixed(200000000000000000),  # 0.2
    "plan": QFixed(200000000000000000),  # 0.2
    "policy": QFixed(200000000000000000),  # 0.2
    "io": QFixed(200000000000000000),  # 0.2
}


class RiskFunctional:
    """
    Risk functional V: X → Q≥0

    V(x) measures "coherence distance" from ideal state.
    Lower is better (0 = perfect coherence).
    """

    def __init__(self, weights: Dict[str, QFixed] = None):
        """
        Initialize risk functional with weights.

        Args:
            weights: Dictionary of component weights (default: equal weights)
        """
        self.weights = weights or DEFAULT_WEIGHTS

    def compute(self, state_or_core) -> QFixed:
        """
        Compute V(state) or V(state_core).

        Supports both State and StateCore for Regime 1 verification.
        V(x) = w₁·V_belief + w₂·V_memory + w₃·V_plan + w₄·V_policy + w₅·V_io

        Per docs/ats/10_mathematical_core/risk_functional_V.md

        Args:
            state_or_core: Either State or StateCore (both have belief/memory/plan/policy/io)

        Returns:
            Risk value V(state) in QFixed(18)
        """
        # Support both State and StateCore
        from .types import StateCore

        if isinstance(state_or_core, StateCore):
            state = state_or_core
        else:
            state = state_or_core
        risk_belief = self._compute_belief_risk(state.belief)
        risk_memory = self._compute_memory_risk(state.memory)
        risk_plan = self._compute_plan_risk(state.plan)
        risk_policy = self._compute_policy_risk(state.policy)
        risk_io = self._compute_io_risk(state.io)

        # Aggregate with weights
        total = (
            self.weights["belief"] * risk_belief
            + self.weights["memory"] * risk_memory
            + self.weights["plan"] * risk_plan
            + self.weights["policy"] * risk_policy
            + self.weights["io"] * risk_io
        )

        return total

    def _compute_belief_risk(self, belief: BeliefState) -> QFixed:
        """
        Compute risk from belief state.

        Risk = measure of incoherence in beliefs.
        We measure risk as the sum of beliefs (more beliefs = higher risk).
        """
        if not belief.beliefs:
            return QFixed.ZERO

        total_risk = QFixed.ZERO
        for concept_id, vector in belief.beliefs.items():
            # Risk increases with belief magnitude (more to potentially contradict)
            for v in vector:
                # Add the belief value to risk (in scaled form)
                total_risk = total_risk + v

        return total_risk

    def _compute_memory_risk(self, memory: MemoryState) -> QFixed:
        """
        Compute risk from memory state.

        Risk = measure of memory corruption/inconsistency.
        """
        if not memory.cells:
            return QFixed.ZERO

        # Risk increases with uninitialized cells
        uninitialized = sum(1 for c in memory.cells if c is None)
        return QFixed.from_value(uninitialized)

    def _compute_plan_risk(self, plan: PlanState) -> QFixed:
        """
        Compute risk from plan state.

        Risk = measure of plan complexity/instability.
        """
        # Risk increases with plan length (more to go wrong)
        return QFixed.from_value(len(plan.steps))

    def _compute_policy_risk(self, policy: PolicyState) -> QFixed:
        """
        Compute risk from policy state.

        Risk = measure of policy uncertainty.
        """
        if not policy.mappings:
            return QFixed.ZERO

        # Risk increases with policy size (more complex)
        return QFixed.from_value(len(policy.mappings))

    def _compute_io_risk(self, io: IOState) -> QFixed:
        """
        Compute risk from I/O state.

        Risk = measure of pending I/O (potential instability).
        """
        pending = len(io.input_buffer) + len(io.output_buffer)
        return QFixed.from_value(pending)

    def compute_delta(self, state_before: State, state_after: State) -> QFixed:
        """
        Compute ΔV = V(x_{k+1}) - V(x_k)

        Per docs/ats/10_mathematical_core/risk_functional_V.md
        """
        v_before = self.compute(state_before)
        v_after = self.compute(state_after)
        return v_after - v_before

    def compute_delta_plus(self, delta: QFixed) -> QFixed:
        """
        Compute (ΔV)^+ = max(0, ΔV)

        Per docs/ats/10_mathematical_core/risk_functional_V.md
        """
        if delta < QFixed.ZERO:
            return QFixed.ZERO
        return delta


# Default instance
default_risk_functional = RiskFunctional()


def compute_risk(state: State) -> QFixed:
    """
    Compute risk for a state using default functional.
    """
    return default_risk_functional.compute(state)


def compute_delta(state_before: State, state_after: State) -> QFixed:
    """
    Compute risk delta between two states.
    """
    return default_risk_functional.compute_delta(state_before, state_after)


def compute_delta_plus(delta: QFixed) -> QFixed:
    """
    Compute positive part of risk delta.
    """
    return default_risk_functional.compute_delta_plus(delta)
