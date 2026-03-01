"""
CLATL Agent Layer

Implements the closed-loop adaptive agent:
- Proposer: generates proposals with deterministic exploration
- Governor: lexicographic selection (safety first, then task)
- Runtime: orchestrates the CLATL loop
"""

from .proposer_iface import (
    TaskProposal,
    TaskProposer,
    ExplorationParams,
)
from .governor_iface import (
    GovernorDecision,
    select_action,
    check_environment_safety,
)
from .clatl_runtime import (
    CLATLStepReceipt,
    CLATLRunReceipt,
    run_clatl_episode,
    run_clatl_training,
)

__all__ = [
    # Proposer
    "TaskProposal",
    "TaskProposer",
    "ExplorationParams",
    # Governor
    "GovernorDecision",
    "select_action",
    "check_environment_safety",
    # Runtime
    "CLATLStepReceipt",
    "CLATLRunReceipt",
    "run_clatl_episode",
    "run_clatl_training",
]
