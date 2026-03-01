"""
Option Receipts - Cryptographic Records for Option Execution

Defines receipt structures for:
- OptionStartReceipt: When an option begins
- OptionStepReceipt: Each internal step of the option
- OptionEndReceipt: When an option terminates
- OptionReceiptBundle: Complete receipt bundle
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Tuple
import json

# Import GMI types
from cnsc_haai.gmi.types import GMIAction


# =============================================================================
# Receipt Types
# =============================================================================

@dataclass(frozen=True)
class OptionStartReceipt:
    """
    Receipt for option start.
    """
    t: int                      # Step index
    option_id: str              # Option identifier
    start_state_hash: str       # Hash of state when option started
    
    def to_json(self) -> str:
        """Serialize to JSON."""
        return json.dumps({
            "t": self.t,
            "option_id": self.option_id,
            "start_state_hash": self.start_state_hash,
        })
    
    @classmethod
    def from_json(cls, s: str) -> "OptionStartReceipt":
        """Deserialize from JSON."""
        data = json.loads(s)
        return cls(**data)


@dataclass(frozen=True)
class OptionStepReceipt:
    """
    Receipt for each internal step of an option.
    """
    t: int                      # Step index
    option_id: str              # Option identifier
    internal_step: int           # Step within the option (0-indexed)
    action: str                 # Action name ("N", "S", "E", "W", "Stay")
    resulting_state_hash: str    # Hash of resulting state
    
    def to_json(self) -> str:
        """Serialize to JSON."""
        return json.dumps({
            "t": self.t,
            "option_id": self.option_id,
            "internal_step": self.internal_step,
            "action": self.action,
            "resulting_state_hash": self.resulting_state_hash,
        })
    
    @classmethod
    def from_json(cls, s: str) -> "OptionStepReceipt":
        """Deserialize from JSON."""
        data = json.loads(s)
        return cls(**data)


@dataclass(frozen=True)
class OptionEndReceipt:
    """
    Receipt for option termination.
    """
    t: int                      # Step index
    option_id: str              # Option identifier
    total_steps: int            # Total steps executed
    final_state_hash: str       # Hash of final state
    termination_reason: str      # Reason: "termination_predicate", "max_steps", "failed"
    
    def to_json(self) -> str:
        """Serialize to JSON."""
        return json.dumps({
            "t": self.t,
            "option_id": self.option_id,
            "total_steps": self.total_steps,
            "final_state_hash": self.final_state_hash,
            "termination_reason": self.termination_reason,
        })
    
    @classmethod
    def from_json(cls, s: str) -> "OptionEndReceipt":
        """Deserialize from JSON."""
        data = json.loads(s)
        return cls(**data)


@dataclass(frozen=True)
class OptionReceiptBundle:
    """
    Complete receipt bundle for option execution.
    """
    start_receipt: OptionStartReceipt
    step_receipts: Tuple[OptionStepReceipt, ...]
    end_receipt: OptionEndReceipt
    
    def to_json(self) -> str:
        """Serialize to JSON."""
        return json.dumps({
            "start_receipt": json.loads(self.start_receipt.to_json()),
            "step_receipts": [json.loads(s.to_json()) for s in self.step_receipts],
            "end_receipt": json.loads(self.end_receipt.to_json()),
        })
    
    @classmethod
    def from_json(cls, s: str) -> "OptionReceiptBundle":
        """Deserialize from JSON."""
        data = json.loads(s)
        return cls(
            start_receipt=OptionStartReceipt.from_json(json.dumps(data["start_receipt"])),
            step_receipts=tuple(OptionStepReceipt.from_json(json.dumps(s)) for s in data["step_receipts"]),
            end_receipt=OptionEndReceipt.from_json(json.dumps(data["end_receipt"])),
        )


# =============================================================================
# Receipt Factories
# =============================================================================

def create_option_start_receipt(
    t: int,
    option_id: str,
    start_state_hash: str,
) -> OptionStartReceipt:
    """Create an OptionStartReceipt."""
    return OptionStartReceipt(
        t=t,
        option_id=option_id,
        start_state_hash=start_state_hash,
    )


def create_option_step_receipt(
    t: int,
    option_id: str,
    internal_step: int,
    action: str,
    resulting_state_hash: str,
) -> OptionStepReceipt:
    """Create an OptionStepReceipt."""
    return OptionStepReceipt(
        t=t,
        option_id=option_id,
        internal_step=internal_step,
        action=action,
        resulting_state_hash=resulting_state_hash,
    )


def create_option_end_receipt(
    t: int,
    option_id: str,
    total_steps: int,
    final_state_hash: str,
    termination_reason: str,
) -> OptionEndReceipt:
    """Create an OptionEndReceipt."""
    return OptionEndReceipt(
        t=t,
        option_id=option_id,
        total_steps=total_steps,
        final_state_hash=final_state_hash,
        termination_reason=termination_reason,
    )


def create_option_receipt_bundle(
    start_receipt: OptionStartReceipt,
    step_receipts: List[OptionStepReceipt],
    end_receipt: OptionEndReceipt,
) -> OptionReceiptBundle:
    """Create an OptionReceiptBundle."""
    return OptionReceiptBundle(
        start_receipt=start_receipt,
        step_receipts=tuple(step_receipts),
        end_receipt=end_receipt,
    )


# =============================================================================
# Utility Functions
# =============================================================================

def action_to_name(action: GMIAction) -> str:
    """Convert GMIAction to action name."""
    if action.dtheta and action.dtheta[0]:
        val = action.dtheta[0][0]
        if val == 1:
            return "N"
        elif val == -1:
            return "S"
        elif len(action.dtheta[0]) > 1:
            if action.dtheta[0][1] == 1:
                return "E"
            elif action.dtheta[0][1] == -1:
                return "W"
    return "Stay"
