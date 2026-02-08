"""
Core types for NPE requests, responses, and internal data structures.

All types are implemented as Python dataclasses with full type hints
to ensure type safety and serialization compatibility.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from enum import Enum


class RequestType(str, Enum):
    """Types of NPE requests."""
    PROPOSE = "propose"
    REPAIR = "repair"


class Domain(str, Enum):
    """NPE operation domains."""
    GR = "gr"  # Governance/Repair


class DeterminismTier(str, Enum):
    """Determinism tier levels for reproducibility."""
    D0 = "d0"  # Fully deterministic


class CandidateType(str, Enum):
    """Types of candidates that proposers can generate."""
    REPAIR = "repair"
    SOLVER_CONFIG = "solver_config"
    PLAN = "plan"
    EXPLAIN = "explain"


@dataclass
class Budgets:
    """Budget constraints for NPE operation.
    
    Attributes:
        max_wall_ms: Maximum wall-clock time in milliseconds
        max_candidates: Maximum number of candidates to return
        max_evidence_items: Maximum evidence items to retrieve
        max_search_expansions: Maximum search expansion operations
    """
    max_wall_ms: int = 1000
    max_candidates: int = 16
    max_evidence_items: int = 100
    max_search_expansions: int = 50


@dataclass
class Clock:
    """Clock information for temporal tracking.
    
    Attributes:
        t: Current timestamp
        dt: Time delta since last tick
        clock_id: Unique identifier for this clock
    """
    t: int
    dt: int
    clock_id: str


@dataclass
class StateRef:
    """Reference to a state in the system.
    
    Attributes:
        state_hash: SHA256 hash of the state
        step: Step number in the execution
        clock: Clock information dict
        summary: State summary dict
    """
    state_hash: str
    step: int
    clock: Dict[str, Any]
    summary: Dict[str, Any]


@dataclass
class ConstraintsRef:
    """Reference to constraints in the system.
    
    Attributes:
        constraints_hash: SHA256 hash of constraints
        params: Constraint parameters dict
        tags: List of constraint tags
    """
    constraints_hash: str
    params: Dict[str, Any]
    tags: List[str] = field(default_factory=list)


@dataclass
class Goal:
    """Goal specification for proposal generation.
    
    Attributes:
        goal_type: Type of goal (e.g., "repair", "optimize", "explain")
        goal_payload: Goal-specific parameters
    """
    goal_type: str
    goal_payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Context:
    """Execution context for proposal generation.
    
    Attributes:
        risk_posture: Current risk posture (e.g., "conservative", "aggressive")
        allowed_sources: List of allowed evidence sources
        time_scope: Time scope for evidence retrieval
        scenario_id: Current scenario identifier
        policy_tags: List of applicable policy tags
    """
    risk_posture: str = "conservative"
    allowed_sources: List[str] = field(default_factory=list)
    time_scope: Dict[str, Any] = field(default_factory=dict)
    scenario_id: Optional[str] = None
    policy_tags: List[str] = field(default_factory=list)


@dataclass
class NPERequest:
    """Main request envelope for NPE operations.
    
    Attributes:
        spec: Specification identifier
        request_type: Type of request (propose/repair)
        request_id: Unique request identifier (hash)
        domain: Operation domain (gr)
        determinism_tier: Determinism level (d0)
        seed: Random seed for reproducibility
        budgets: Budget constraints
        inputs: Input data including state, constraints, goals, context
    """
    spec: str = "NPE-REQUEST-1.0"
    request_type: str = RequestType.PROPOSE.value
    request_id: str = ""
    domain: str = Domain.GR.value
    determinism_tier: str = DeterminismTier.D0.value
    seed: int = 0
    budgets: Budgets = field(default_factory=Budgets)
    inputs: Dict[str, Any] = field(default_factory=dict)

    def get_state_ref(self) -> Optional[StateRef]:
        """Get state reference from inputs."""
        state_data = self.inputs.get("state", {})
        if state_data:
            return StateRef(
                state_hash=state_data.get("state_hash", ""),
                step=state_data.get("step", 0),
                clock=state_data.get("clock", {}),
                summary=state_data.get("summary", {}),
            )
        return None

    def get_constraints_ref(self) -> Optional[ConstraintsRef]:
        """Get constraints reference from inputs."""
        constraints_data = self.inputs.get("constraints", {})
        if constraints_data:
            return ConstraintsRef(
                constraints_hash=constraints_data.get("constraints_hash", ""),
                params=constraints_data.get("params", {}),
                tags=constraints_data.get("tags", []),
            )
        return None

    def get_goals(self) -> List[Goal]:
        """Get list of goals from inputs."""
        goals_data = self.inputs.get("goals", [])
        return [
            Goal(goal_type=g.get("goal_type", ""), goal_payload=g.get("payload", {}))
            for g in goals_data
        ]

    def get_context(self) -> Context:
        """Get execution context from inputs."""
        ctx_data = self.inputs.get("context", {})
        return Context(
            risk_posture=ctx_data.get("risk_posture", "conservative"),
            allowed_sources=ctx_data.get("allowed_sources", []),
            time_scope=ctx_data.get("time_scope", {}),
            scenario_id=ctx_data.get("scenario_id"),
            policy_tags=ctx_data.get("policy_tags", []),
        )


@dataclass
class FailureInfo:
    """Information about a failure for repair requests.
    
    Attributes:
        proof_hash: Hash of the proof/certificate
        gate_stack_id: ID of the failing gate stack
        registry_hash: Hash of the proposer registry
        failing_gates: List of failing gate identifiers
    """
    proof_hash: str
    gate_stack_id: str
    registry_hash: str
    failing_gates: List[str] = field(default_factory=list)


@dataclass
class NPERepairRequest:
    """Repair request envelope.
    
    Attributes:
        spec: Specification identifier
        request_type: Type of request (repair)
        request_id: Unique request identifier (hash)
        domain: Operation domain (gr)
        determinism_tier: Determinism level (d0)
        seed: Random seed for reproducibility
        budgets: Budget constraints
        inputs: Input data including state, constraints, goals, context
        failure: Failure information
    """
    spec: str = "NPE-REPAIR-REQUEST-1.0"
    request_type: str = RequestType.REPAIR.value
    request_id: str = ""
    domain: str = Domain.GR.value
    determinism_tier: str = DeterminismTier.D0.value
    seed: int = 0
    budgets: Budgets = field(default_factory=Budgets)
    inputs: Dict[str, Any] = field(default_factory=dict)
    failure: FailureInfo = field(default_factory=FailureInfo)


@dataclass
class EvidenceItem:
    """Evidence item retrieved for proposal generation.
    
    Attributes:
        evidence_id: Unique evidence identifier (hash)
        source_type: Type of source (e.g., "receipt", "corpus", "codebook")
        source_ref: Reference to the source
        content_hash: Hash of the evidence content
        taint_tags: Tags indicating taint/filter status
        scope: Scope information for filtering
        filters_applied: List of filters that were applied
        relevance: Relevance score (0.0-1.0)
    """
    evidence_id: str
    source_type: str
    source_ref: str
    content_hash: str
    taint_tags: List[str] = field(default_factory=list)
    scope: Dict[str, Any] = field(default_factory=dict)
    filters_applied: List[str] = field(default_factory=list)
    relevance: float = 0.0


@dataclass
class ProposerMeta:
    """Metadata about the proposer that generated a candidate.
    
    Attributes:
        proposer_id: Identifier of the proposer
        invocation_order: Order in which proposer was invoked
        execution_time_ms: Time taken by proposer in ms
        budget_consumed: Budget consumed by proposer
    """
    proposer_id: str
    invocation_order: int
    execution_time_ms: int = 0
    budget_consumed: Dict[str, int] = field(default_factory=dict)


@dataclass
class Scores:
    """Scoring information for a candidate.
    
    Attributes:
        risk: Risk score (0.0-1.0)
        utility: Utility score (0.0-1.0)
        cost: Cost score (0.0-1.0)
        confidence: Confidence score (0.0-1.0)
    """
    risk: float = 0.5
    utility: float = 0.5
    cost: float = 0.5
    confidence: float = 0.5


@dataclass
class Candidate:
    """Candidate proposal returned by proposers.
    
    Attributes:
        candidate_hash: Unique candidate identifier (hash)
        candidate_type: Type of candidate (repair/plan/explain)
        domain: Operation domain
        input_state_hash: Hash of input state
        constraints_hash: Hash of constraints
        payload_format: Format of payload (e.g., "json")
        payload_hash: Hash of payload content
        payload: Actual candidate payload
        evidence: List of evidence items supporting this candidate
        scores: Scoring information
        suggested_gate_stack: Optional suggested gate stack
        proposer_meta: Metadata about proposer that generated this
    """
    candidate_hash: str
    candidate_type: str
    domain: str = "gr"
    input_state_hash: str = ""
    constraints_hash: str = ""
    payload_format: str = "json"
    payload_hash: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    evidence: List[EvidenceItem] = field(default_factory=list)
    scores: Scores = field(default_factory=Scores)
    suggested_gate_stack: Optional[List[str]] = None
    proposer_meta: Optional[ProposerMeta] = None


@dataclass
class NPEResponse:
    """Response envelope for NPE operations.
    
    Attributes:
        spec: Specification identifier
        response_id: Unique response identifier (hash)
        request_id: Reference to request ID
        domain: Operation domain
        determinism_tier: Determinism level
        seed: Random seed used
        corpus_snapshot_hash: Hash of corpus snapshot
        memory_snapshot_hash: Hash of memory snapshot (Aeonic)
        registry_hash: Hash of proposer registry
        candidates: List of generated candidates
        diagnostics: Diagnostic information
    """
    spec: str = "NPE-RESPONSE-1.0"
    response_id: str = ""
    request_id: str = ""
    domain: str = Domain.GR.value
    determinism_tier: str = DeterminismTier.D0.value
    seed: int = 0
    corpus_snapshot_hash: str = ""
    memory_snapshot_hash: str = ""
    registry_hash: str = ""
    candidates: List[Candidate] = field(default_factory=list)
    diagnostics: Dict[str, Any] = field(default_factory=dict)
