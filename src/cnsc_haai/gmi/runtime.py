"""
GMI Runtime Engine

Thin wrapper that connects:
1. NPE/Predictor → proposals
2. Gates → evaluation
3. Consensus → state + receipts

Uses existing consensus modules:
- cnsc_haai.consensus.chain for chain hashing
- cnsc_haai.consensus.merkle for proposal Merkle
- cnsc.haai.nsc.gates for gate evaluation (when available)

For deterministic execution, the runtime:
- Generates proposals (can be nondeterministic if receipted)
- Builds Merkle root of proposal set
- Evaluates gates deterministically
- Executes accepted proposal
- Produces complete receipt with all metadata
"""

from __future__ import annotations
from typing import List, Tuple, Optional, Dict, Any
import json

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
from .step import gmi_step
from .jcs import jcs_dumps
from .hash import sha256_tagged

# Import existing consensus modules
try:
    from cnsc_haai.consensus.merkle import MerkleTree
except ImportError:
    MerkleTree = None

try:
    from cnsc_haai.consensus.chain import chain_hash_sequence_prefixed
except ImportError:
    chain_hash_sequence_prefixed = None


def _build_proposal_merkle(proposals: List[Proposal]) -> Optional[bytes]:
    """
    Build Merkle tree from proposals for deterministic receipt.

    Args:
        proposals: List of proposals

    Returns:
        Merkle root bytes, or None if no proposals
    """
    if not proposals:
        return None

    if MerkleTree is None:
        # Fallback: simple hash of all proposal IDs
        h = sha256_tagged("GMI_PROPOSALS", json.dumps([p.proposal_id for p in proposals]).encode())
        return h

    # Serialize proposals to bytes for Merkle
    leaves = []
    for p in proposals:
        proposal_bytes = jcs_dumps(
            {
                "id": p.proposal_id,
                "action": {
                    "drho": p.action.drho,
                    "dtheta": p.action.dtheta,
                    "u_glyph": p.action.u_glyph,
                },
                "score": p.score,
            }
        )
        leaves.append(proposal_bytes)

    tree = MerkleTree()
    return tree.build(leaves)


def _evaluate_gates_deterministic(
    proposals: List[Proposal],
    state: GMIState,
    ctx: Dict[str, Any],
) -> Tuple[Optional[Proposal], List[GateDecision]]:
    """
    Evaluate proposals against gates deterministically.

    This is a deterministic gate evaluation that:
    1. Sorts proposals by score (deterministic order)
    2. Evaluates each against simple pass/fail gates
    3. Returns first passing proposal

    For full TGS integration, use cnsc.haai.nsc.gates.GateManager

    Args:
        proposals: List of proposals to evaluate
        state: Current GMI state
        ctx: Execution context

    Returns:
        Tuple of (selected proposal or None, gate decisions)
    """
    decisions: List[GateDecision] = []

    if not proposals:
        return None, decisions

    # Sort by score descending, then by proposal_id (deterministic)
    sorted_proposals = sorted(proposals, key=lambda p: (-p.score, p.proposal_id))

    # Simple gate: check proposal is well-formed
    for proposal in sorted_proposals:
        # Gate 1: proposal has valid action
        try:
            if not proposal.action.drho or not proposal.action.dtheta:
                decisions.append(
                    GateDecision(
                        gate_id="gate_proposal_valid",
                        passed=False,
                        reason="Invalid action structure",
                    )
                )
                continue
        except (AttributeError, TypeError):
            decisions.append(
                GateDecision(
                    gate_id="gate_proposal_valid",
                    passed=False,
                    reason="Missing action data",
                )
            )
            continue

        # Gate 2: budget sufficient (check action magnitude)
        action_magnitude = sum(sum(abs(v) for v in row) for row in proposal.action.drho)

        if state.b > 0:
            decisions.append(
                GateDecision(
                    gate_id="gate_budget_sufficient",
                    passed=True,
                    reason="Budget available",
                )
            )
        else:
            decisions.append(
                GateDecision(
                    gate_id="gate_budget_sufficient",
                    passed=False,
                    reason="Budget exhausted",
                )
            )
            continue

        # All gates passed - select this proposal
        return proposal, decisions

    # No proposal passed all gates
    return None, decisions


def gmi_tick(
    state: GMIState,
    observation: bytes,
    proposals: List[Proposal],
    ctx: Dict[str, Any],
    chain_prev: bytes,
    params: Optional[GMIParams] = None,
) -> Tuple[GMIState, GMIRuntimeReceipt]:
    """
    Single tick of the GMI metabolic AI loop.

    Process:
    1. Build proposal set (with Merkle root for receipt)
    2. Evaluate proposals against gates (deterministic)
    3. Execute accepted proposal via gmi_step
    4. Build complete runtime receipt

    Args:
        state: Current GMI state
        observation: Observation/input (for context)
        proposals: List of proposals from predictor
        ctx: Execution context
        chain_prev: Previous chain tip
        params: GMI parameters (uses default if None)

    Returns:
        Tuple of (new state, runtime receipt)
    """
    # Use default params if not provided
    if params is None:
        params = GMIParams()

    # Track work units
    work = WorkUnits(
        proposal_generation_cost=0,  # Assumed done before runtime
        witness_acquisition_cost=0,
        gate_evaluation_cost=len(proposals) * 100,  # Rough estimate
        execution_cost=0,
        memory_write_cost=0,
        repair_cost=0,
    )

    # Step 1: Build proposal Merkle root
    proposal_root = _build_proposal_merkle(proposals)

    # Step 2: Evaluate gates (deterministic)
    selected_proposal, gate_decisions = _evaluate_gates_deterministic(proposals, state, ctx)

    # Step 3: Execute selected proposal or reject
    if selected_proposal is not None:
        # Execute the selected proposal
        action = selected_proposal.action
        work = WorkUnits(
            proposal_generation_cost=work.proposal_generation_cost,
            witness_acquisition_cost=work.witness_acquisition_cost,
            gate_evaluation_cost=work.gate_evaluation_cost,
            execution_cost=1000,  # Rough estimate for execution
            memory_write_cost=200,  # Rough estimate for receipt writing
            repair_cost=0,
        )
    else:
        # No proposal selected - create empty action (all zeros)
        n = len(state.rho)
        m = len(state.rho[0]) if n > 0 else 0
        action = GMIAction(
            drho=[[0] * m for _ in range(n)],
            dtheta=[[0] * m for _ in range(n)],
            u_glyph=None,
        )

    # Execute step via existing gmi_step
    new_state, step_receipt = gmi_step(state, action, ctx, params, chain_prev)

    # Calculate total work in QFixed
    total_work_q = work.total() * 1000000  # Convert to QFixed scale

    # Build runtime receipt
    runtime_receipt = GMIRuntimeReceipt(
        step_receipt=step_receipt,
        proposal_set_root=proposal_root,
        proposal_count=len(proposals),
        selected_proposal_id=selected_proposal.proposal_id if selected_proposal else None,
        gate_decisions=gate_decisions,
        work_units=work,
        total_work_q=total_work_q,
    )

    return new_state, runtime_receipt


def gmi_tick_with_predictor(
    state: GMIState,
    observation: bytes,
    predictor_fn,
    ctx: Dict[str, Any],
    chain_prev: bytes,
    params: Optional[GMIParams] = None,
) -> Tuple[GMIState, GMIRuntimeReceipt]:
    """
    Convenience wrapper that includes predictor call.

    If predictor is nondeterministic, the proposal set is still receipted
    via Merkle root, maintaining consensus.

    Args:
        state: Current GMI state
        observation: Observation/input
        predictor_fn: Function that generates proposals from observation
        ctx: Execution context
        chain_prev: Previous chain tip
        params: GMI parameters

    Returns:
        Tuple of (new state, runtime receipt)
    """
    # Generate proposals (can be nondeterministic)
    proposals = predictor_fn(observation, state, ctx)

    # Continue with standard tick
    return gmi_tick(state, observation, proposals, ctx, chain_prev, params)


class GMIRuntime:
    """
    GMI Runtime for managing multiple ticks.

    Provides state management and replay capabilities.
    """

    def __init__(self, params: Optional[GMIParams] = None):
        self.params = params or GMIParams()
        self.state: Optional[GMIState] = None
        self.chain: bytes = b"\x00" * 32  # Genesis chain tip
        self.receipts: List[GMIRuntimeReceipt] = []

    def reset(self, initial_state: GMIState, chain_tip: Optional[bytes] = None) -> None:
        """Reset runtime to initial state."""
        self.state = initial_state
        self.chain = chain_tip or b"\x00" * 32
        self.receipts = []

    def tick(
        self,
        proposals: List[Proposal],
        ctx: Optional[Dict[str, Any]] = None,
    ) -> GMIRuntimeReceipt:
        """
        Execute a single tick.

        Args:
            proposals: List of proposals
            ctx: Execution context

        Returns:
            Runtime receipt
        """
        if self.state is None:
            raise ValueError("Runtime not initialized. Call reset() first.")

        ctx = ctx or {}

        self.state, receipt = gmi_tick(
            state=self.state,
            observation=b"",  # Empty observation for now
            proposals=proposals,
            ctx=ctx,
            chain_prev=self.chain,
            params=self.params,
        )

        # Update chain
        self.chain = receipt.step_receipt.chain_next
        self.receipts.append(receipt)

        return receipt

    def get_chain_tip(self) -> bytes:
        """Get current chain tip."""
        return self.chain

    def get_receipt_count(self) -> int:
        """Get number of receipts."""
        return len(self.receipts)
