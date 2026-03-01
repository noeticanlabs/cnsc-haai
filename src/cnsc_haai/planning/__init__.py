"""
Planning Package - Governed Planning + Skills (Phase 3)

This package provides multi-step lookahead planning for the CLATL runtime.

Modules:
- planner_mpc: Main MPC planning entry point
- planset_generator: Deterministic PlanSet generation
- plan_gating: Stepwise safety + budget feasibility
- plan_scoring: J(Pi) computation
- plan_receipts: PlanSetReceipt, PlanDecisionReceipt
- plan_merkle: Merkle tree for plan commitment
- tie_break: Deterministic tie-breaking

Dependency rules:
- planning/ may import model/ and tasks/ but NOT agent/
"""

from .plan_receipts import (
    PlanSetReceipt,
    PlanDecisionReceipt,
    GateWitnessReceipt,
    PlanReceiptBundle,
)
from .plan_gating import GateResult, GateReasonCode, gate_plan, gate_planset
from .plan_scoring import score_plan, score_planset
from .planset_generator import generate_planset, generate_single_plan, compute_adaptive_params, Plan, PlanSet
from .tie_break import tie_break_plans
from .planner_mpc import PlannerConfig, plan_and_select, PlanningReceipts, PlanningResult, is_planning_enabled, get_planning_budget_estimate
from .plan_merkle import build_plan_merkle_root, verify_plan_membership

__all__ = [
    # Receipts
    "PlanSetReceipt",
    "PlanDecisionReceipt", 
    "GateWitnessReceipt",
    "PlanReceiptBundle",
    # Gating
    "GateResult",
    "GateReasonCode",
    "gate_plan",
    "gate_planset",
    # Scoring
    "score_plan",
    "score_planset",
    # PlanSet
    "Plan",
    "PlanSet",
    "generate_planset",
    # Tie-break
    "tie_break_plans",
    # MPC
    "PlannerConfig",
    "plan_and_select",
    "PlanningReceipts",
    # Merkle
    "build_plan_merkle_root",
    "verify_plan_membership",
]
