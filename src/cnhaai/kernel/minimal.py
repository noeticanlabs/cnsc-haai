"""
Minimal Kernel for CNHAAI

The Minimal Kernel is the simplest complete CNHAAI implementation,
integrating all core components:
- Abstraction Layer
- Gate Manager
- Phase Manager
- Receipt System
- Coherence Budget
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4
from datetime import datetime

from cnhaai.core.abstraction import Abstraction, AbstractionLayer, AbstractionType
from cnhaai.core.gates import GateManager, GateDecision, GateResult
from cnhaai.core.phases import Phase, PhaseManager
from cnhaai.core.receipts import ReceiptSystem, ReceiptStepType, ReceiptDecision
from cnhaai.core.coherence import CoherenceBudget


@dataclass
class EpisodeResult:
    """Result of a reasoning episode."""

    episode_id: str
    success: bool
    final_phase: str
    abstractions_created: List[str]
    receipts_generated: int
    coherence_status: Dict[str, Any]
    duration_ms: int
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "episode_id": self.episode_id,
            "success": self.success,
            "final_phase": self.final_phase,
            "abstractions_created": self.abstractions_created,
            "receipts_generated": self.receipts_generated,
            "coherence_status": self.coherence_status,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
        }


class MinimalKernel:
    """
    The Minimal Kernel is the simplest complete CNHAAI implementation.

    It integrates all core components to demonstrate the architecture:
    - Abstraction Layer: Manages reasoning abstractions
    - Gate Manager: Validates reasoning transitions
    - Phase Manager: Coordinates reasoning phases
    - Receipt System: Provides auditability
    - Coherence Budget: Tracks coherence degradation

    Attributes:
        version: Kernel version
        settings: Configuration settings
        abstraction_layer: Manages abstractions
        gate_manager: Evaluates gates
        phase_manager: Manages phases
        receipt_system: Records receipts
        coherence_budget: Tracks coherence
        episode_count: Number of episodes executed
    """

    def __init__(self, version: str = "1.0.0", settings: Optional[Dict[str, Any]] = None):
        """
        Initialize the minimal kernel.

        Args:
            version: Kernel version
            settings: Optional configuration settings
        """
        self.version = version
        self.settings = settings or self._default_settings()

        # Initialize components
        self.abstraction_layer = AbstractionLayer(max_levels=3)
        self.gate_manager = GateManager()
        self.gate_manager.create_default_gates()

        self.phase_manager = PhaseManager()
        self.receipt_system = ReceiptSystem(
            signing_key="cnhaai-prototype-key", storage_type="in_memory", retention="session"
        )
        self.coherence_budget = CoherenceBudget(current=self.settings.get("coherence_budget", 0.5))

        # Episode tracking
        self.episode_count = 0
        self._start_time: Optional[datetime] = None

    def _default_settings(self) -> Dict[str, Any]:
        """Get default settings."""
        return {
            "coherence_budget": 0.5,
            "max_abstraction_levels": 3,
            "evidence_threshold": 0.8,
            "receipt_retention": "session",
        }

    def create_abstraction(
        self,
        abstraction_type: str,
        evidence: List[str],
        scope: str,
        validity: Optional[Dict[str, Any]] = None,
        content: Optional[Dict[str, Any]] = None,
        parent_id: Optional[str] = None,
    ) -> Abstraction:
        """
        Create a new abstraction.

        Args:
            abstraction_type: Type of abstraction (descriptive, mechanistic, normative, comparative)
            evidence: Evidence supporting this abstraction
            scope: Scope/context where applicable
            validity: Validity constraints
            content: Semantic content
            parent_id: Optional parent abstraction ID

        Returns:
            The created abstraction
        """
        # Convert string to enum
        type_enum = AbstractionType[abstraction_type.upper()]

        abstraction = self.abstraction_layer.create_abstraction(
            type=type_enum,
            evidence=set(evidence),
            scope={scope},
            validity=validity or {},
            content=content or {},
            parent_id=parent_id,
        )

        return abstraction

    def execute_episode(
        self,
        goal: str,
        evidence: Optional[List[str]] = None,
        constraints: Optional[List[Dict[str, Any]]] = None,
        max_steps: int = 100,
    ) -> EpisodeResult:
        """
        Execute a complete reasoning episode.

        Args:
            goal: The reasoning goal
            evidence: Initial evidence for the episode
            constraints: Reasoning constraints
            max_steps: Maximum steps in the episode

        Returns:
            EpisodeResult with episode outcome
        """
        self.episode_count += 1
        episode_id = str(uuid4())
        self._start_time = datetime.utcnow()

        # Start episode receipt
        self.receipt_system.emit_receipt(
            episode_id=episode_id,
            step_type=ReceiptStepType.EPISODE_START,
            decision=ReceiptDecision.PASS,
            details={"goal": goal, "max_steps": max_steps},
        )

        # Start with acquisition phase
        self.phase_manager.start_phase(Phase.ACQUISITION, {"goal": goal})

        # Build context
        context = {
            "goal": goal,
            "evidence": evidence or [],
            "evidence_scores": [0.9] * len(evidence) if evidence else [],
            "constraints": constraints or [],
            "conclusions": [],
            "required_claims": [],
        }

        state = {"coherence_budget": self.coherence_budget.current}

        success = True
        abstractions_created = []
        steps_completed = 0

        try:
            # Phase 1: Acquisition
            if self._execute_phase(Phase.ACQUISITION, context, state, episode_id):
                # Phase 2: Construction
                if self._execute_phase(Phase.CONSTRUCTION, context, state, episode_id):
                    # Create an abstraction during construction
                    abstraction = self.create_abstraction(
                        abstraction_type="descriptive",
                        evidence=context["evidence"],
                        scope=goal,
                        content={"goal": goal},
                    )
                    abstractions_created.append(abstraction.id)

                    # Phase 3: Reasoning
                    if self._execute_phase(Phase.REASONING, context, state, episode_id):
                        # Phase 4: Validation
                        if self._execute_phase(Phase.VALIDATION, context, state, episode_id):
                            pass  # Validation successful
                        else:
                            # Need recovery
                            if self._execute_phase(Phase.RECOVERY, context, state, episode_id):
                                pass  # Recovery successful
                            else:
                                success = False
                    else:
                        success = False
                else:
                    success = False
        except Exception as e:
            success = False
            context["error"] = str(e)

        # End episode
        self.phase_manager.complete_phase(reason="episode_end", steps_completed=steps_completed)

        end_time = datetime.utcnow()
        duration_ms = int((end_time - self._start_time).total_seconds() * 1000)

        # Emit episode end receipt
        self.receipt_system.emit_receipt(
            episode_id=episode_id,
            step_type=ReceiptStepType.EPISODE_END,
            decision=ReceiptDecision.PASS if success else ReceiptDecision.FAIL,
            details={
                "success": success,
                "duration_ms": duration_ms,
                "abstractions_created": len(abstractions_created),
            },
        )

        return EpisodeResult(
            episode_id=episode_id,
            success=success,
            final_phase=(
                self.phase_manager.current_phase.name
                if self.phase_manager.current_phase
                else "unknown"
            ),
            abstractions_created=abstractions_created,
            receipts_generated=len(self.receipt_system.get_episode_receipts(episode_id)),
            coherence_status=self.coherence_budget.check(),
            duration_ms=duration_ms,
            metadata={"goal": goal, "steps_completed": steps_completed},
        )

    def _execute_phase(
        self, phase: Phase, context: Dict[str, Any], state: Dict[str, Any], episode_id: str
    ) -> bool:
        """
        Execute a single phase.

        Args:
            phase: The phase to execute
            context: Reasoning context
            state: System state
            episode_id: Current episode ID

        Returns:
            True if phase completed successfully
        """
        # Transition to phase
        self.phase_manager.transition_to(phase, reason="phase_transition")

        # Evaluate gates for this phase
        results, all_passed = self.gate_manager.evaluate_all(context, state)

        # Create receipt for gate evaluation
        for result in results:
            self.receipt_system.create_gate_receipt(
                episode_id=episode_id,
                gate_name=result.gate_type.name,
                decision=ReceiptDecision[result.decision.name],
                details=result.details,
            )

        # Update coherence based on gate results
        for result in results:
            if result.decision == GateDecision.FAIL:
                self.coherence_budget.degrade(reason=f"gate_failure_{result.gate_type.name}")
            elif result.decision == GateDecision.WARN:
                self.coherence_budget.degrade(
                    amount=0.02, reason=f"gate_warning_{result.gate_type.name}"
                )
            elif result.decision == GateDecision.PASS:
                if self.coherence_budget.current < 1.0:
                    self.coherence_budget.recover(reason="gate_passed")

        # Update state
        state["coherence_budget"] = self.coherence_budget.current

        # Check if we can proceed
        if not self.coherence_budget.can_proceed():
            return False

        # Create phase transition receipt
        self.receipt_system.create_phase_receipt(
            episode_id=episode_id,
            from_phase=phase.name,
            to_phase=self._get_next_phase(phase).name if self._get_next_phase(phase) else "end",
            duration_ms=100,
            steps_completed=1,
        )

        return all_passed or self.coherence_budget.is_healthy()

    def _get_next_phase(self, phase: Phase) -> Optional[Phase]:
        """Get the next phase in the sequence."""
        config = self.phase_manager.get_config(phase)
        if config and config.transitions_to:
            return config.transitions_to[0]
        return None

    def get_receipts(self, episode_id: str) -> List[Dict[str, Any]]:
        """
        Get all receipts for an episode.

        Args:
            episode_id: The episode ID

        Returns:
            List of receipt dictionaries
        """
        receipts = self.receipt_system.get_episode_receipts(episode_id)
        return [r.to_dict() for r in receipts]

    def get_coherence_status(self) -> Dict[str, Any]:
        """Get current coherence status."""
        return self.coherence_budget.check()

    def get_abstractions(self, scope: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get abstractions, optionally filtered by scope.

        Args:
            scope: Optional scope filter

        Returns:
            List of abstraction dictionaries
        """
        if scope:
            abstractions = self.abstraction_layer.get_by_scope(scope)
        else:
            abstractions = list(self.abstraction_layer.abstractions.values())
        return [a.to_dict() for a in abstractions]

    def get_phase_history(self) -> List[Dict[str, Any]]:
        """Get phase history."""
        return self.phase_manager.get_phase_history()

    def verify_episode(self, episode_id: str) -> bool:
        """
        Verify an episode's integrity.

        Args:
            episode_id: The episode to verify

        Returns:
            True if episode is valid
        """
        return self.receipt_system.verify_episode_chain(episode_id)

    def reset(self) -> None:
        """Reset the kernel to initial state."""
        self.episode_count = 0
        self.abstraction_layer = AbstractionLayer(max_levels=3)
        self.gate_manager = GateManager()
        self.gate_manager.create_default_gates()
        self.phase_manager = PhaseManager()
        self.receipt_system.clear()
        self.coherence_budget.reset()
        self._start_time = None

    def get_stats(self) -> Dict[str, Any]:
        """Get kernel statistics."""
        return {
            "version": self.version,
            "episodes_executed": self.episode_count,
            "abstractions_count": len(self.abstraction_layer.abstractions),
            "receipts_count": len(self.receipt_system.receipts),
            "coherence_status": self.coherence_budget.check(),
            "settings": self.settings,
        }
