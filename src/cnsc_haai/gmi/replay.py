"""
Replay Engine (Consensus Verification)

This module provides deterministic replay functionality for verification.
Given initial state and actions, reproduces exact chain and receipts.
"""

from __future__ import annotations
from typing import Tuple, List, Dict, Any
from .types import GMIState, GMIAction, GMIStepReceipt
from .params import GMIParams
from .step import gmi_step


def replay_episode(
    s0: GMIState,
    actions: List[GMIAction],
    ctx: Dict[str, Any],
    p: GMIParams,
    chain0: bytes,
) -> Tuple[GMIState, bytes, List[GMIStepReceipt]]:
    """
    Replay a complete episode from initial state.
    
    This function is deterministic: given same inputs, produces identical outputs.
    Used for:
    - Verification of past executions
    - Consensus between nodes
    - Audit and compliance
    
    Args:
        s0: Initial state
        actions: List of actions to replay
        ctx: Execution context (unused, for extensibility)
        p: GMI parameters
        chain0: Initial chain tip (e.g., zero bytes for genesis)
        
    Returns:
        Tuple of (final state, final chain tip, list of receipts)
    """
    s = s0
    chain = chain0
    receipts: List[GMIStepReceipt] = []
    
    for a in actions:
        s, r = gmi_step(s, a, ctx, p, chain)
        chain = r.chain_next
        receipts.append(r)
    
    return s, chain, receipts


def verify_replay(
    s0: GMIState,
    actions: List[GMIAction],
    ctx: Dict[str, Any],
    p: GMIParams,
    chain0: bytes,
    expected_chain: bytes,
    expected_final_state: GMIState,
) -> bool:
    """
    Verify that replay produces expected results.
    
    Args:
        s0: Initial state
        actions: Actions to replay
        ctx: Execution context
        p: GMI parameters
        chain0: Initial chain tip
        expected_chain: Expected final chain tip
        expected_final_state: Expected final state
        
    Returns:
        True if replay matches expectations
    """
    s_final, chain_final, _ = replay_episode(s0, actions, ctx, p, chain0)
    
    # Compare chain tips
    if chain_final != expected_chain:
        return False
    
    # Compare final states (compare hash-equivalent)
    # For simplicity, compare all fields
    if s_final.rho != expected_final_state.rho:
        return False
    if s_final.theta != expected_final_state.theta:
        return False
    if s_final.C != expected_final_state.C:
        return False
    if s_final.b != expected_final_state.b:
        return False
    if s_final.t != expected_final_state.t:
        return False
    
    return True


def get_chain_tip(receipts: List[GMIStepReceipt]) -> bytes:
    """
    Get the final chain tip from a list of receipts.
    
    Args:
        receipts: List of receipts in order
        
    Returns:
        Final chain tip (chain_next of last receipt)
    """
    if not receipts:
        return b'\x00' * 32  # Zero tip if no receipts
    
    return receipts[-1].chain_next
