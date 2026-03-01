"""
Options Package - Skills/Options for Phase 3

This package provides skill options that can be used by the planner
as macro-actions.

Modules:
- option_types: Option dataclass definitions
- option_registry: Registry of built-in skills
- option_runtime: Execute options (unfold to primitive actions)
- option_receipts: Option execution receipts

Built-in options:
- GoToGoalGreedy: Move toward goal
- AvoidHazardGradient: Move away from hazards
- WallFollowLeft: Follow wall on left
- WallFollowRight: Follow wall on right
- BacktrackLastSafe: Return to last safe position
"""

from .option_types import Option, OptionExecution, ExecutionStatus
from .option_registry import get_option, list_options, register_option
from .option_runtime import execute_option, execute_option_steps
from .option_receipts import (
    OptionStartReceipt,
    OptionStepReceipt,
    OptionEndReceipt,
    OptionReceiptBundle,
    create_option_start_receipt,
    create_option_step_receipt,
    create_option_end_receipt,
)

__all__ = [
    # Types
    "Option",
    "OptionExecution",
    "ExecutionStatus",
    # Registry
    "get_option",
    "list_options",
    "register_option",
    # Runtime
    "execute_option",
    "execute_option_steps",
    # Receipts
    "OptionStartReceipt",
    "OptionStepReceipt",
    "OptionEndReceipt",
    "OptionReceiptBundle",
    "create_option_start_receipt",
    "create_option_step_receipt",
    "create_option_end_receipt",
]
