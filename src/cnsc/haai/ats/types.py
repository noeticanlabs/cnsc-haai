"""
Core ATS Types

This module defines the fundamental types for the Admissible Trajectory Space:
- State: The cognitive state X
- Action: The action algebra A
- Receipt: Verification record
- Budget: Coherence budget

Per docs/ats/10_mathematical_core/state_space.md:
    X = X_belief × X_memory × X_plan × X_policy × X_io
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum, auto
import json

from .numeric import QFixed

# JCS for canonical serialization (consensus-safe)
from cnsc_haai.consensus.jcs import jcs_canonical_bytes


def _serialize_memory_cells(cells: List[Optional[bytes]]) -> List[Optional[str]]:
    """Serialize memory cells to base64 for JSON serialization."""
    import base64

    result = []
    for cell in cells:
        if cell is None:
            result.append(None)
        else:
            result.append(base64.b64encode(cell).decode("ascii"))
    return result


def _serialize_action_params(params: Tuple[Any, ...]) -> List[Any]:
    """Serialize action parameters for JCS, converting QFixed to raw ints."""
    result = []
    for p in params:
        if isinstance(p, QFixed):
            result.append(p.to_raw())
        elif isinstance(p, tuple):
            result.append(_serialize_action_params(p))
        elif isinstance(p, list):
            result.append(_serialize_action_params(tuple(p)))
        else:
            result.append(p)
    return result


# =============================================================================
# Action Types (from docs/ats/10_mathematical_core/action_algebra.md)
# =============================================================================

# Per Gap C: Action codec versioning
# Versioned action type strings for deterministic parsing
ACTION_TYPE_VERSION = "v1"
ACTION_TYPE_PREFIX = "ats.action"


class ActionType(Enum):
    """Types of actions in the action algebra A."""

    # Belief operations
    BELIEF_UPDATE = "ats.action.belief_update.v1"
    BELIEF_MERGE = "ats.action.belief_merge.v1"
    BELIEF_DELETE = "ats.action.belief_delete.v1"
    BELIEF_RECALL = "ats.action.belief_recall.v1"

    # Memory operations
    MEMORY_WRITE = "ats.action.memory_write.v1"
    MEMORY_READ = "ats.action.memory_read.v1"
    MEMORY_ALLOC = "ats.action.memory_alloc.v1"
    MEMORY_FREE = "ats.action.memory_free.v1"

    # Planning operations
    PLAN_APPEND = "ats.action.plan_append.v1"
    PLAN_PREPEND = "ats.action.plan_prepend.v1"
    PLAN_REMOVE = "ats.action.plan_remove.v1"
    PLAN_CLEAR = "ats.action.plan_clear.v1"

    # Policy operations
    POLICY_UPDATE = "ats.action.policy_update.v1"
    POLICY_COPY = "ats.action.policy_copy.v1"
    POLICY_ROLLBACK = "ats.action.policy_rollback.v1"

    # I/O operations
    IO_INPUT = "ats.action.io_input.v1"
    IO_OUTPUT = "ats.action.io_output.v1"
    IO_FLUSH = "ats.action.io_flush.v1"

    # Custom/generic (only for testing, not production)
    CUSTOM = "ats.action.custom"


@dataclass(frozen=True)
class Action:
    """
    An action in the action algebra A.

    Per Gap C: Action codec versioning
    - action_type is versioned (e.g., "ats.action.belief_update.v1")
    - Each type has deterministic codec
    - ATS verifier checks type and only accepts known codecs

    Actions are deterministic functions: X → X
    """

    action_type: ActionType
    version: str = ACTION_TYPE_VERSION  # "v1" by default
    parameters: Tuple[Any, ...] = field(default_factory=tuple)

    def validate_codec(self) -> bool:
        """
        Validate that this action uses a supported codec version.

        Per Gap C: Reject unknown/old versions.
        """
        SUPPORTED_VERSIONS = {"v1"}
        return self.version in SUPPORTED_VERSIONS

    def canonical_bytes(self) -> bytes:
        """
        Serialize action to canonical bytes for hashing.

        Includes version for deterministic encoding.
        """
        import json

        data = {
            "action_type": self.action_type.value,
            "version": self.version,
            "parameters": self.parameters,
        }
        return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def to_canonical_dict(self) -> Dict[str, Any]:
        """Return dict representation for JCS serialization."""
        return {
            "action_type": self.action_type.value,
            "version": self.version,
            "parameters": _serialize_action_params(self.parameters),
        }

    def __hash__(self) -> int:
        return hash((self.action_type, self.parameters))

    def __str__(self) -> str:
        return f"Action({self.action_type.name}, {self.parameters})"


# =============================================================================
# State Space (from docs/ats/10_mathematical_core/state_space.md)
# =============================================================================


@dataclass
class BeliefState:
    """X_belief: ConceptID → BeliefVector mapping."""

    beliefs: Dict[str, List[QFixed]] = field(default_factory=dict)

    def to_canonical_dict(self) -> dict:
        """Convert to canonical dictionary for JCS serialization."""
        return {key: [v.to_raw() for v in values] for key, values in sorted(self.beliefs.items())}

    def canonical_bytes(self) -> bytes:
        """Serialize to canonical bytes for hashing."""
        # Sort keys for deterministic ordering
        items = []
        for key in sorted(self.beliefs.keys()):
            values = self.beliefs[key]
            items.append((key, [v.to_raw() for v in values]))
        return json.dumps(items, separators=(",", ":")).encode("utf-8")


@dataclass
class MemoryState:
    """X_memory: Sequential memory cells."""

    cells: List[Optional[bytes]] = field(default_factory=list)

    def canonical_bytes(self) -> bytes:
        """Serialize to canonical bytes for hashing."""
        # Convert cells to JSON-serializable format
        return json.dumps(self.cells, separators=(",", ":")).encode("utf-8")


@dataclass
class PlanState:
    """X_plan: Ordered list of planned actions."""

    steps: List[Action] = field(default_factory=list)

    def canonical_bytes(self) -> bytes:
        """Serialize to canonical bytes for hashing."""
        items = [(s.action_type.name, s.parameters) for s in self.steps]
        return json.dumps(items, default=str, separators=(",", ":")).encode("utf-8")


@dataclass
class PolicyState:
    """X_policy: State → ActionDistribution mapping."""

    mappings: Dict[str, Dict[str, QFixed]] = field(default_factory=dict)

    def to_canonical_dict(self) -> dict:
        """Convert to canonical dictionary for JCS serialization."""
        return {
            key: {k: v.to_raw() for k, v in sorted(action_dist.items())}
            for key, action_dist in sorted(self.mappings.items())
        }

    def canonical_bytes(self) -> bytes:
        """Serialize to canonical bytes for hashing."""
        # Sort keys for deterministic ordering
        items = []
        for key in sorted(self.mappings.keys()):
            action_dist = self.mappings[key]
            items.append((key, {k: v.to_raw() for k, v in action_dist.items()}))
        return json.dumps(items, separators=(",", ":")).encode("utf-8")


@dataclass
class IOState:
    """X_io: Input/Output buffers."""

    input_buffer: List[bytes] = field(default_factory=list)
    output_buffer: List[bytes] = field(default_factory=list)

    def to_canonical_dict(self) -> dict:
        """Convert to canonical dictionary for JCS serialization."""
        return {
            "input_buffer": [b.decode("utf-8", errors="replace") for b in self.input_buffer],
            "output_buffer": [b.decode("utf-8", errors="replace") for b in self.output_buffer],
        }

    def canonical_bytes(self) -> bytes:
        """Serialize to canonical bytes for hashing."""
        return json.dumps(
            {
                "input": [b.decode("utf-8", errors="replace") for b in self.input_buffer],
                "output": [b.decode("utf-8", errors="replace") for b in self.output_buffer],
            },
            separators=(",", ":"),
        ).encode("utf-8")


@dataclass(frozen=True)
class StateCore:
    """
    CONSENSUS-CRITICAL state.

    Only fields here affect state_hash and risk computation.
    This is the "canonical state" that RV verifies against.

    Per Gap A: StateCore contract
    """

    belief: BeliefState
    memory: MemoryState
    plan: PlanState
    policy: PolicyState
    io: IOState

    def canonical_bytes(self) -> bytes:
        """
        Exact format for state_hash computation.

        Uses JCS (RFC8785) wrapping to ensure deterministic serialization
        and prevent hash collisions from raw byte concatenation.
        """
        state_dict = {
            "belief": self.belief.to_canonical_dict(),
            "memory": {"cells": _serialize_memory_cells(self.memory.cells)},
            "plan": {"steps": [s.to_canonical_dict() for s in self.plan.steps]},
            "policy": self.policy.to_canonical_dict(),
            "io": self.io.to_canonical_dict(),
        }
        return jcs_canonical_bytes(state_dict)

    def state_hash(self) -> str:
        """SHA-256 state hash (consensus identifier)."""
        import hashlib

        return hashlib.sha256(self.canonical_bytes()).hexdigest()

    @classmethod
    def from_state(cls, state: "State") -> "StateCore":
        """Create StateCore from full State."""
        return cls(
            belief=state.belief,
            memory=state.memory,
            plan=state.plan,
            policy=state.policy,
            io=state.io,
        )


@dataclass
class StateExtension:
    """
    NON-CONSENSUS state data.

    These fields NEVER affect state_hash or risk computation.
    They are for runtime optimization only (caching, hints, etc.).

    Per Gap A: StateCore contract
    """

    cache: Dict[str, Any] = field(default_factory=dict)
    runtime_hints: Dict[str, Any] = field(default_factory=dict)
    # Merkle root option for large states (when full state not shipped)
    commitment: Optional[str] = None


@dataclass
class State:
    """
    Canonical state space X.

    X = X_belief × X_memory × X_plan × X_policy × X_io

    Per docs/ats/10_mathematical_core/state_space.md

    For consensus purposes, use StateCore (extracted via .as_core()).
    Non-consensus data is in .extension.
    """

    belief: BeliefState = field(default_factory=BeliefState)
    memory: MemoryState = field(default_factory=MemoryState)
    plan: PlanState = field(default_factory=PlanState)
    policy: PolicyState = field(default_factory=PolicyState)
    io: IOState = field(default_factory=IOState)

    def canonical_bytes(self) -> bytes:
        """
        Serialize to canonical bytes for deterministic hashing.

        Per docs/ats/20_coh_kernel/canonical_serialization.md:
        - Big-endian for integers
        - Sorted dictionary keys
        - Type tags included
        """
        return (
            self.belief.canonical_bytes()
            + self.memory.canonical_bytes()
            + self.plan.canonical_bytes()
            + self.policy.canonical_bytes()
            + self.io.canonical_bytes()
        )

    def state_hash(self) -> str:
        """Compute SHA-256 state hash."""
        import hashlib

        return hashlib.sha256(self.canonical_bytes()).hexdigest()

    def as_core(self) -> "StateCore":
        """Extract consensus-critical StateCore from this State."""
        return StateCore(
            belief=self.belief, memory=self.memory, plan=self.plan, policy=self.policy, io=self.io
        )


# =============================================================================
# Receipt Types (from docs/ats/20_coh_kernel/receipt_schema.md)
# =============================================================================


@dataclass
class ReceiptContent:
    """Content section of a receipt (consensus-critical)."""

    step_type: str
    risk_before_q: QFixed
    risk_after_q: QFixed
    delta_plus_q: QFixed
    budget_before_q: QFixed
    budget_after_q: QFixed
    kappa_q: QFixed
    state_hash_before: str
    state_hash_after: str
    decision: str = "PASS"
    details: Dict[str, Any] = field(default_factory=dict)

    def canonical_bytes(self) -> bytes:
        """Serialize for hashing."""
        return json.dumps(
            {
                "step_type": self.step_type,
                "risk_before_q": self.risk_before_q.to_raw(),
                "risk_after_q": self.risk_after_q.to_raw(),
                "delta_plus_q": self.delta_plus_q.to_raw(),
                "budget_before_q": self.budget_before_q.to_raw(),
                "budget_after_q": self.budget_after_q.to_raw(),
                "kappa_q": self.kappa_q.to_raw(),
                "state_hash_before": self.state_hash_before,
                "state_hash_after": self.state_hash_after,
                "decision": self.decision,
                "details": self.details,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")


class ReceiptType(Enum):
    """Type of receipt for distinguishing ATS vs telemetry."""

    ATS_V2 = "ats_v2"  # Consensus-safe (v2 schema)
    TELEMETRY_V1 = "telemetry_v1"  # Non-consensus (v1 schema)


@dataclass
class ReceiptMeta:
    """
    Non-consensus metadata (excluded from canonical bytes).

    Per the ATS kernel invariant: meta fields never affect hashes.
    """

    timestamp: Optional[str] = None
    episode_id: Optional[str] = None
    provenance: Dict[str, Any] = field(default_factory=dict)
    signature: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Receipt:
    """
    A receipt proving ATS compliance for a state transition.

    Supports both v1 (telemetry) and v2 (ATS consensus-safe) formats.

    Per docs/ats/20_coh_kernel/receipt_schema.md:
    - v2 (ATS): receipt_core is used for canonical bytes
    - v1 (Telemetry): full receipt including timestamps (NOT consensus-safe)
    """

    version: str = "2.0.0"  # Default to ATS v2
    receipt_type: ReceiptType = ReceiptType.ATS_V2
    receipt_id: str = ""
    step_index: int = 0  # For v2: monotonically increasing
    content: Optional[ReceiptContent] = None
    meta: ReceiptMeta = field(default_factory=ReceiptMeta)
    previous_receipt_id: str = "00000000"
    previous_receipt_hash: str = ""
    chain_hash: str = ""

    def canonical_bytes_core(self) -> bytes:
        """
        Compute canonical bytes from receipt_core only (for v2 ATS).

        Per docs/ats/20_coh_kernel/receipt_identity.md:
        - Only receipt_core affects receipt_id
        - Meta fields (timestamp, provenance, etc.) are EXCLUDED
        """
        if self.content:
            content_bytes = self.content.canonical_bytes()
        else:
            content_bytes = b""

        data = {
            "step_index": self.step_index,
            "content": content_bytes.decode("utf-8") if content_bytes else "",
        }
        return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def canonical_bytes(self) -> bytes:
        """
        Serialize for hashing.

        For ATS v2: uses canonical_bytes_core() (excludes meta)
        For Telemetry v1: includes all fields (NOT consensus-safe)
        """
        if self.receipt_type == ReceiptType.ATS_V2:
            # ATS v2: only core fields
            data = {
                "version": self.version,
                "step_index": self.step_index,
                "content": (
                    json.loads(self.content.canonical_bytes().decode()) if self.content else {}
                ),
                "previous_receipt_id": self.previous_receipt_id,
                "previous_receipt_hash": self.previous_receipt_hash,
            }
        else:
            # Telemetry v1: all fields (NOT consensus-safe)
            data = {
                "version": self.version,
                "timestamp": self.meta.timestamp or "",
                "episode_id": self.meta.episode_id or "",
                "content": (
                    json.loads(self.content.canonical_bytes().decode()) if self.content else {}
                ),
                "provenance": self.meta.provenance,
                "signature": self.meta.signature,
                "previous_receipt_id": self.previous_receipt_id,
                "previous_receipt_hash": self.previous_receipt_hash,
                "metadata": self.meta.metadata,
            }

        # Include receipt_id only if already computed (non-empty)
        # This allows computing receipt_id without circular dependency
        if self.receipt_id:
            data["receipt_id"] = self.receipt_id
        return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def compute_receipt_id(self) -> str:
        """
        Compute receipt_id = first8(sha256(canonical_bytes(receipt)))

        Per docs/ats/20_coh_kernel/receipt_identity.md:
        - For ATS v2: uses canonical_bytes_core() (no timestamps/provenance)
        - For Telemetry v1: uses full canonical_bytes()

        Note: Excludes receipt_id and chain_hash from canonical bytes to avoid
        circular dependency (chain_hash depends on receipt_id).
        """
        import hashlib

        if self.receipt_type == ReceiptType.ATS_V2:
            # ATS v2: only core
            canonical = self.canonical_bytes_core()
        else:
            # Telemetry v1: build without receipt_id/chain_hash
            data = {
                "version": self.version,
                "timestamp": self.meta.timestamp or "",
                "episode_id": self.meta.episode_id or "",
                "content": (
                    json.loads(self.content.canonical_bytes().decode()) if self.content else {}
                ),
                "provenance": self.meta.provenance,
                "signature": self.meta.signature,
                "previous_receipt_id": self.previous_receipt_id,
                "previous_receipt_hash": self.previous_receipt_hash,
                "metadata": self.meta.metadata,
            }
            canonical = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")

        hash_bytes = hashlib.sha256(canonical)
        return hash_bytes.hexdigest()[:8]

    def compute_chain_hash(self, prev_chain_hash: str) -> str:
        """
        Compute chain_hash that BINDS to receipt content.

        Per docs/ats/20_coh_kernel/chain_hash_rule.md:
        - For v2 (ATS): sha256(prev_chain_hash || canonical_bytes_core())
        - For v1 (Telemetry): sha256(prev_receipt_id || receipt_id)

        The v2 formula binds to receipt content, not just IDs.
        This prevents chain forks where content differs but IDs match.
        """
        import hashlib

        if self.receipt_type == ReceiptType.ATS_V2:
            # ATS v2: bind to content (secure)
            core_bytes = self.canonical_bytes_core()
            chain_input = prev_chain_hash.encode() + core_bytes
        else:
            # Telemetry v1: legacy formula (less secure)
            chain_input = (self.previous_receipt_id + self.receipt_id).encode()

        return hashlib.sha256(chain_input).hexdigest()


# =============================================================================
# Budget (from docs/ats/10_mathematical_core/budget_law.md)
# =============================================================================


@dataclass
class Budget:
    """
    Budget state for the ATS.

    Per docs/ats/10_mathematical_core/budget_law.md:
    - If ΔV ≤ 0: B_next = B_prev
    - If ΔV > 0: B_next = B_prev - κ × ΔV
    """

    value: QFixed
    kappa: QFixed  # Risk coefficient

    @classmethod
    def create(cls, initial: QFixed, kappa: QFixed) -> "Budget":
        return cls(value=initial, kappa=kappa)

    def compute_next(self, risk_delta: QFixed) -> Tuple[QFixed, bool]:
        """
        Compute budget after a step.

        Returns: (new_budget, accepted)
        """
        if risk_delta <= QFixed.ZERO:
            # Risk decreased - budget preserved
            return self.value, True

        # Risk increased - check sufficiency
        required = self.kappa * risk_delta
        if self.value < required:
            return QFixed.ZERO, False  # REJECT

        # Budget consumed
        new_budget = self.value - required
        return new_budget, True

    def to_json(self) -> Dict[str, str]:
        return {
            "value_q": self.value.to_json(),
            "kappa_q": self.kappa.to_json(),
        }


# =============================================================================
# Verification Result
# =============================================================================


class VerificationResult(Enum):
    """Result of ATS verification."""

    ACCEPT = auto()
    REJECT = auto()


@dataclass
class Rejection:
    """Rejection with error code and reason."""

    code: str
    reason: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> Dict[str, Any]:
        return {
            "result": "REJECT",
            "code": self.code,
            "reason": self.reason,
            "details": self.details,
        }
