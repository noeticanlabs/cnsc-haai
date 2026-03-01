"""
Plan Receipts - Cryptographic Records for Planning

Defines receipt structures for:
- PlanSetReceipt: Commitment to the entire plan set
- PlanDecisionReceipt: The chosen plan and why
- GateWitnessReceipt: Safety witness for the chosen plan

All receipts are frozen dataclasses for immutability and hash compatibility.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import hashlib
import json


# =============================================================================
# Receipt Types
# =============================================================================

@dataclass(frozen=True)
class PlanSetReceipt:
    """
    Receipt committing to the entire PlanSet at a timestep.
    
    This enables verification that the planner actually considered
    the committed set of plans, not just a convenient subset.
    """
    t: int                          # Step index
    env_state_hash: str            # Hash of environment state
    gmi_state_hash: str            # Hash of GMI state
    planner_config_hash: str       # Hash of planner config (H, m, weights)
    seed: int                       # Seed used for deterministic generation
    planset_root: str              # Merkle root of all plan hashes
    plans_count: int                # Number of plans in set
    horizon: int                    # Horizon H
    
    def to_json(self) -> str:
        """Serialize to JSON for storage."""
        return json.dumps({
            "t": self.t,
            "env_state_hash": self.env_state_hash,
            "gmi_state_hash": self.gmi_state_hash,
            "planner_config_hash": self.planner_config_hash,
            "seed": self.seed,
            "planset_root": self.planset_root,
            "plans_count": self.plans_count,
            "horizon": self.horizon,
        })
    
    @classmethod
    def from_json(cls, s: str) -> PlanSetReceipt:
        """Deserialize from JSON."""
        data = json.loads(s)
        return cls(**data)


@dataclass(frozen=True)
class GateReasonCode:
    """
    Reason code for plan rejection during gating.
    
    These are deterministic and receipted for audit.
    """
    HAZARD_VIOLATION = "HAZARD_VIOLATION"      # Plan enters hazard area
    BOUNDS_VIOLATION = "BOUNDS_VIOLATION"      # Plan goes outside bounds
    BUDGET_INFEASIBLE = "BUDGET_INFEASIBLE"     # Budget would go negative
    ADMISSIBILITY_VIOLATION = "ADMISSIBILITY_VIOLATION"  # Not in admissible set


@dataclass(frozen=True)
class PlanDecisionReceipt:
    """
    Receipt for the planner's decision at a timestep.
    
    Records which plan was chosen, why other plans were rejected,
    and the budget impact of planning.
    """
    t: int                              # Step index
    planset_root: str                   # Reference to PlanSet commitment
    chosen_plan_index: int             # Index in PlanSet
    chosen_plan_hash: str               # Hash of chosen plan
    gate_reason_codes_summary: Tuple[Tuple[str, int], ...]  # (reason, count) pairs
    chosen_action_index: int           # Index of first action (0 to H-1)
    chosen_action: str                  # Action name ("N", "S", "E", "W", "Stay")
    predicted_cost_J: int               # Predicted cost J(Pi) in QFixed
    budget_before_planning: int         # Budget before planning (QFixed)
    budget_after_planning: int          # Budget after deducting planning cost (QFixed)
    
    @property
    def planning_cost(self) -> int:
        """Cost of planning work."""
        return self.budget_before_planning - self.budget_after_planning
    
    def to_json(self) -> str:
        """Serialize to JSON for storage."""
        return json.dumps({
            "t": self.t,
            "planset_root": self.planset_root,
            "chosen_plan_index": self.chosen_plan_index,
            "chosen_plan_hash": self.chosen_plan_hash,
            "gate_reason_codes_summary": list(self.gate_reason_codes_summary),
            "chosen_action_index": self.chosen_action_index,
            "chosen_action": self.chosen_action,
            "predicted_cost_J": self.predicted_cost_J,
            "budget_before_planning": self.budget_before_planning,
            "budget_after_planning": self.budget_after_planning,
        })
    
    @classmethod
    def from_json(cls, s: str) -> PlanDecisionReceipt:
        """Deserialize from JSON."""
        data = json.loads(s)
        data["gate_reason_codes_summary"] = tuple(
            tuple(x) for x in data["gate_reason_codes_summary"]
        )
        return cls(**data)


@dataclass(frozen=True)
class GateWitnessStep:
    """
    Safety witness for a single step in the chosen plan.
    """
    step: int             # Step index (0 to H-1)
    predicted_state_hash: str  # Hash of predicted state
    safety_check_passed: bool  # Whether safety check passed
    hazard_proximity: int      # Distance to nearest hazard (QFixed)
    budget_after_step: int     # Projected budget after this step
    
    
@dataclass(frozen=True)
class GateWitnessReceipt:
    """
    Receipt containing safety witnesses for the chosen plan.
    
    This provides proof that all steps of the chosen plan
    passed the safety gates.
    """
    t: int                                    # Step index
    chosen_plan_hash: str                     # Hash of chosen plan
    witness_steps: Tuple[GateWitnessStep, ...]  # Per-step witnesses
    all_steps_safe: bool                      # True if all steps passed
    
    def to_json(self) -> str:
        """Serialize to JSON for storage."""
        return json.dumps({
            "t": self.t,
            "chosen_plan_hash": self.chosen_plan_hash,
            "witness_steps": [
                {
                    "step": w.step,
                    "predicted_state_hash": w.predicted_state_hash,
                    "safety_check_passed": w.safety_check_passed,
                    "hazard_proximity": w.hazard_proximity,
                    "budget_after_step": w.budget_after_step,
                }
                for w in self.witness_steps
            ],
            "all_steps_safe": self.all_steps_safe,
        })
    
    @classmethod
    def from_json(cls, s: str) -> GateWitnessReceipt:
        """Deserialize from JSON."""
        data = json.loads(s)
        data["witness_steps"] = tuple(
            GateWitnessStep(**w) for w in data["witness_steps"]
        )
        return cls(**data)


@dataclass(frozen=True)
class PlanReceiptBundle:
    """
    Complete receipt bundle for a planning step.
    
    Contains all receipts needed for full replay verification.
    """
    planset_receipt: PlanSetReceipt
    decision_receipt: PlanDecisionReceipt
    witness_receipt: Optional[GateWitnessReceipt]  # Optional: only for chosen plan
    
    def to_json(self) -> str:
        """Serialize to JSON for storage."""
        return json.dumps({
            "planset_receipt": json.loads(self.planset_receipt.to_json()),
            "decision_receipt": json.loads(self.decision_receipt.to_json()),
            "witness_receipt": json.loads(self.witness_receipt.to_json()) if self.witness_receipt else None,
        })
    
    @classmethod
    def from_json(cls, s: str) -> PlanReceiptBundle:
        """Deserialize from JSON."""
        data = json.loads(s)
        return cls(
            planset_receipt=PlanSetReceipt.from_json(json.dumps(data["planset_receipt"])),
            decision_receipt=PlanDecisionReceipt.from_json(json.dumps(data["decision_receipt"])),
            witness_receipt=GateWitnessReceipt.from_json(json.dumps(data["witness_receipt"])) if data["witness_receipt"] else None,
        )


# =============================================================================
# Receipt Factories
# =============================================================================

def create_planset_receipt(
    t: int,
    env_state_hash: str,
    gmi_state_hash: str,
    planner_config_hash: str,
    seed: int,
    planset_root: str,
    plans_count: int,
    horizon: int,
) -> PlanSetReceipt:
    """Create a PlanSetReceipt."""
    return PlanSetReceipt(
        t=t,
        env_state_hash=env_state_hash,
        gmi_state_hash=gmi_state_hash,
        planner_config_hash=planner_config_hash,
        seed=seed,
        planset_root=planset_root,
        plans_count=plans_count,
        horizon=horizon,
    )


def create_plan_decision_receipt(
    t: int,
    planset_root: str,
    chosen_plan_index: int,
    chosen_plan_hash: str,
    gate_reason_codes_summary: Dict[str, int],
    chosen_action_index: int,
    chosen_action: str,
    predicted_cost_J: int,
    budget_before_planning: int,
    budget_after_planning: int,
) -> PlanDecisionReceipt:
    """Create a PlanDecisionReceipt."""
    return PlanDecisionReceipt(
        t=t,
        planset_root=planset_root,
        chosen_plan_index=chosen_plan_index,
        chosen_plan_hash=chosen_plan_hash,
        gate_reason_codes_summary=tuple(gate_reason_codes_summary.items()),
        chosen_action_index=chosen_action_index,
        chosen_action=chosen_action,
        predicted_cost_J=predicted_cost_J,
        budget_before_planning=budget_before_planning,
        budget_after_planning=budget_after_planning,
    )


def create_gate_witness_receipt(
    t: int,
    chosen_plan_hash: str,
    witness_steps: List[GateWitnessStep],
) -> GateWitnessReceipt:
    """Create a GateWitnessReceipt."""
    return GateWitnessReceipt(
        t=t,
        chosen_plan_hash=chosen_plan_hash,
        witness_steps=tuple(witness_steps),
        all_steps_safe=all(w.safety_check_passed for w in witness_steps),
    )
