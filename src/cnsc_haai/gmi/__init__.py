"""
GMI v1.5 - Governed Metabolic Intelligence Kernel

This module implements a deterministic transition system with:
- Closed convex admissibility set enforcement
- Quantized Lyapunov functional (non-increasing on accepted steps)
- Budget absorption rule at b=0
- KKT/VI residual checking for stationary states
- Cryptographic receipt chain with JCS canonicalization

Version: 1.5.0
"""

from .qfixed import Q, SCALE
from .types import (
    GMIState,
    GMIAction,
    GMIStepReceipt,
    Proposal,
    ProposalSet,
    GateDecision,
    WorkUnits,
    GMIRuntimeReceipt,
)
from .params import GMIParams
from .admissible import in_K, project_K
from .lyapunov import V_extended_q
from .kkt import kkt_residual_q
from .step import gmi_step
from .replay import replay_episode
from .jcs import jcs_dumps
from .hash import sha256_tagged
from .runtime import gmi_tick, gmi_tick_with_predictor, GMIRuntime

__version__ = "1.6.0"

__all__ = [
    "Q",
    "SCALE",
    "GMIState",
    "GMIAction",
    "GMIStepReceipt",
    "Proposal",
    "ProposalSet",
    "GateDecision",
    "WorkUnits",
    "GMIRuntimeReceipt",
    "GMIParams",
    "in_K",
    "project_K",
    "V_extended_q",
    "kkt_residual_q",
    "gmi_step",
    "replay_episode",
    "jcs_dumps",
    "sha256_tagged",
    "gmi_tick",
    "gmi_tick_with_predictor",
    "GMIRuntime",
]
