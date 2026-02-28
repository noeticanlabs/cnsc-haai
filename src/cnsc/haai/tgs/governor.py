"""
Temporal Governance Engine

Core TGS engine for processing proposals through the governance pipeline.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from cnsc.haai.tgs.clock import (
    ClockRegistry,
    ConsistencyClock,
    CommitmentClock,
    CausalityClock,
    ResourceClock,
    TaintClock,
    DriftClock,
)
from cnsc.haai.tgs.snapshot import (
    SnapshotManager,
    Snapshot,
    StagedState,
    StateHash,
)
from cnsc.haai.tgs.proposal import (
    Proposal,
    DeltaOp,
)
from cnsc.haai.tgs.receipt import (
    TGSReceipt,
    ReceiptEmitter,
    ReasonCode,
    Correction,
)
from cnsc.haai.tgs.rails import (
    CoherenceRails,
    RailResult,
    CompositeRailResult,
)
from cnsc.haai.tgs.corrections import (
    CorrectionEngine,
    CorrectionType,
)


class GovernanceDecision(Enum):
    """Governance decision outcomes."""

    ACCEPTED = auto()
    REJECTED = auto()
    CORRECTED = auto()
    ROLLED_BACK = auto()


@dataclass
class GovernanceResult:
    """
    Result of governance processing.

    Attributes:
        decision: Final governance decision
        receipt: Generated receipt
        snapshot: Snapshot used for governance
        staged: Staged state after corrections
        corrections: Corrections applied
        dt: Total dt value
        rail_results: Per-rail evaluation results
    """

    decision: GovernanceDecision
    receipt: Optional[TGSReceipt] = None
    snapshot: Optional[Snapshot] = None
    staged: Optional[StagedState] = None
    corrections: List[Correction] = field(default_factory=list)
    dt: float = 0.0
    rail_results: Optional[CompositeRailResult] = None
    error: Optional[str] = None


class TemporalGovernanceEngine:
    """
    Core TGS engine for temporal governance.

    The engine processes proposals through the following pipeline:
    1. Snapshot current state
    2. Stage proposal deltas
    3. Compute dt via clock arbitration
    4. Evaluate coherence rails
    5. Apply corrections if needed
    6. Commit or rollback
    7. Emit receipt
    """

    def __init__(
        self,
        clock_registry: Optional[ClockRegistry] = None,
        snapshot_manager: Optional[SnapshotManager] = None,
        receipt_emitter: Optional[ReceiptEmitter] = None,
        coherence_rails: Optional[CoherenceRails] = None,
        correction_engine: Optional[CorrectionEngine] = None,
    ):
        """
        Initialize TGS with required dependencies.

        Args:
            clock_registry: Clock registry (created if None)
            snapshot_manager: Snapshot manager (created if None)
            receipt_emitter: Receipt emitter (created if None)
            coherence_rails: Coherence rails evaluator (created if None)
            correction_engine: Correction engine (created if None)
        """
        # Initialize or use provided clock registry
        self._clock_registry = clock_registry or self._create_default_clock_registry()

        # Initialize or use provided snapshot manager
        self._snapshot_manager = snapshot_manager or SnapshotManager()

        # Initialize or use provided receipt emitter
        self._receipt_emitter = receipt_emitter

        # Initialize or use provided rails
        self._rails = coherence_rails or CoherenceRails()

        # Initialize or use provided correction engine
        self._correction_engine = correction_engine or CorrectionEngine()

        # Current state hash
        self._current_state_hash: Optional[StateHash] = None

        # Logical time counter
        self._logical_time: int = 0

    def _create_default_clock_registry(self) -> ClockRegistry:
        """Create default clock registry with all clocks."""
        registry = ClockRegistry()

        # Register all default clocks
        registry.register_clock(ConsistencyClock())
        registry.register_clock(CommitmentClock())
        registry.register_clock(CausalityClock())
        registry.register_clock(ResourceClock())
        registry.register_clock(TaintClock())
        registry.register_clock(DriftClock())

        return registry

    def process_proposal(
        self,
        proposal: Proposal,
        current_state: Dict[str, Any],
        logical_time: Optional[int] = None,
    ) -> GovernanceResult:
        """
        Process proposal through TGS pipeline.

        Args:
            proposal: Proposal to process
            current_state: Current cognitive state
            logical_time: Optional logical time (auto-increments if None)

        Returns:
            GovernanceResult with decision and receipt
        """
        try:
            # Set logical time
            if logical_time is not None:
                self._logical_time = logical_time
            else:
                self._logical_time += 1

            proposal.logical_time = self._logical_time

            # Step 1: Snapshot current state
            snapshot = self._snapshot_manager.begin_attempt_snapshot(
                state=current_state,
                parent_state_hash=self._current_state_hash,
                logical_time=self._logical_time,
            )

            # Step 2: Stage proposal deltas
            staged = self._snapshot_manager.create_staged_state(snapshot)
            staged.apply_deltas(proposal.delta_ops)

            # Step 3: Compute dt via clock arbitration
            dt, dt_components = self._clock_registry.compute_dt(proposal, staged.to_state_dict())

            # Step 4: Evaluate coherence rails
            rail_results = self._rails.evaluate_all(staged, proposal)

            # Step 5: Apply corrections if needed
            corrections = []
            if not rail_results.all_passed:
                corrections = self._apply_corrections(rail_results, staged, proposal)
                staged = self._correction_engine.apply_to_staged(staged, corrections)

                # Re-evaluate rails after corrections
                rail_results = self._rails.evaluate_all(staged, proposal)

            # Step 6: Resolve commitment (commit or rollback)
            should_accept, adjusted_confidence = self._correction_engine.should_accept(
                corrections, proposal.confidence
            )

            decision, new_state_hash = self._resolve_commitment(
                snapshot, staged, should_accept, adjusted_confidence
            )

            # Step 7: Emit receipt
            receipt = self._emit_receipt(
                snapshot.state_hash,
                proposal,
                dt,
                dt_components,
                rail_results,
                corrections,
                decision,
                new_state_hash,
            )

            # Update current state
            if new_state_hash:
                self._current_state_hash = new_state_hash

            return GovernanceResult(
                decision=decision,
                receipt=receipt,
                snapshot=snapshot,
                staged=staged,
                corrections=corrections,
                dt=dt,
                rail_results=rail_results,
            )

        except Exception as e:
            return GovernanceResult(
                decision=GovernanceDecision.REJECTED,
                error=str(e),
            )

    def _apply_corrections(
        self, rail_results: CompositeRailResult, staged: StagedState, proposal: Proposal
    ) -> List[Correction]:
        """Apply corrections based on rail results."""
        _, corrections = self._correction_engine.apply(
            rail_results.results,
            staged,
            proposal,
        )
        return corrections

    def _resolve_commitment(
        self,
        snapshot: Snapshot,
        staged: StagedState,
        should_accept: bool,
        adjusted_confidence: float,
    ) -> Tuple[GovernanceDecision, Optional[StateHash]]:
        """
        Commit or rollback based on gate evaluation.

        Args:
            snapshot: Original snapshot
            staged: Staged state with modifications
            should_accept: Whether to accept proposal
            adjusted_confidence: Adjusted confidence after corrections

        Returns:
            Tuple of (decision, new_state_hash)
        """
        if should_accept:
            # Commit staged changes
            new_state_hash = self._snapshot_manager.commit(snapshot, staged)
            return GovernanceDecision.ACCEPTED, new_state_hash
        else:
            # Rollback to snapshot
            self._snapshot_manager.rollback(snapshot)
            return GovernanceDecision.REJECTED, None

    def _emit_receipt(
        self,
        parent_state_hash: StateHash,
        proposal: Proposal,
        dt: float,
        dt_components: Dict[str, float],
        rail_results: CompositeRailResult,
        corrections: List[Correction],
        decision: GovernanceDecision,
        new_state_hash: Optional[StateHash],
    ) -> TGSReceipt:
        """Emit immutable governance receipt."""
        # Convert rail margins
        gate_margins = {str(r.rail_id): r.margin for r in rail_results.results}

        # Convert reason codes
        reasons = self._decision_to_reasons(decision, rail_results)

        # Compute diff digest
        diff_digest = self._compute_diff_digest(rail_results)

        # Create receipt
        receipt = TGSReceipt(
            parent_state_hash=str(parent_state_hash),
            proposal_id=proposal.proposal_id,
            dt=dt,
            dt_components=dt_components,
            gate_margins=gate_margins,
            reasons=reasons,
            corrections_applied=corrections,
            accepted=(decision == GovernanceDecision.ACCEPTED),
            new_state_hash=str(new_state_hash) if new_state_hash else None,
            diff_digest=diff_digest,
            logical_time=self._logical_time,
            metadata={
                "decision": decision.name,
                "rail_count": len(rail_results.results),
                "correction_count": len(corrections),
            },
        )

        # Emit to ledger if emitter is configured
        if self._receipt_emitter:
            self._receipt_emitter.emit(receipt)

        return receipt

    def _decision_to_reasons(
        self, decision: GovernanceDecision, rail_results: CompositeRailResult
    ) -> List[ReasonCode]:
        """Convert decision to reason codes."""
        reasons = []

        for result in rail_results.results:
            if str(result.rail_id) == "consistency":
                reasons.append(ReasonCode.CONSISTENCY_CHECK)
            elif str(result.rail_id) == "commitment":
                reasons.append(ReasonCode.COMMITMENT_CHECK)
            elif str(result.rail_id) == "causality":
                reasons.append(ReasonCode.CAUSALITY_CHECK)
            elif str(result.rail_id) == "resource":
                reasons.append(ReasonCode.RESOURCE_CHECK)
            elif str(result.rail_id) == "taint":
                reasons.append(ReasonCode.TAINT_CHECK)

        if decision == GovernanceDecision.CORRECTED:
            reasons.append(ReasonCode.CORRECTION_APPLIED)

        return reasons

    def _compute_diff_digest(self, rail_results: CompositeRailResult) -> str:
        """Compute digest of rail results."""
        import hashlib
        import json

        results_dict = {
            str(r.rail_id): {
                "decision": r.decision.name,
                "margin": r.margin,
                "details": r.details,
            }
            for r in rail_results.results
        }

        digest_input = json.dumps(results_dict, sort_keys=True)
        return hashlib.sha256(digest_input.encode()).hexdigest()[:32]

    def get_status(self) -> Dict[str, Any]:
        """Get TGS system status."""
        return {
            "logical_time": self._logical_time,
            "current_state_hash": (
                str(self._current_state_hash) if self._current_state_hash else None
            ),
            "registered_clocks": self._clock_registry.list_clocks(),
            "ledger_length": (
                self._receipt_emitter._ledger.get_length() if self._receipt_emitter else 0
            ),
        }

    def set_receipt_emitter(self, emitter: ReceiptEmitter) -> None:
        """Set the receipt emitter."""
        self._receipt_emitter = emitter
