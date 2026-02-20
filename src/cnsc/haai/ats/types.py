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


# =============================================================================
# Action Types (from docs/ats/10_mathematical_core/action_algebra.md)
# =============================================================================

class ActionType(Enum):
    """Types of actions in the action algebra A."""
    # Belief operations
    BELIEF_UPDATE = auto()
    BELIEF_MERGE = auto()
    BELIEF_DELETE = auto()
    BELIEF_RECALL = auto()
    
    # Memory operations
    MEMORY_WRITE = auto()
    MEMORY_READ = auto()
    MEMORY_ALLOC = auto()
    MEMORY_FREE = auto()
    
    # Planning operations
    PLAN_APPEND = auto()
    PLAN_PREPEND = auto()
    PLAN_REMOVE = auto()
    PLAN_CLEAR = auto()
    
    # Policy operations
    POLICY_UPDATE = auto()
    POLICY_COPY = auto()
    POLICY_ROLLBACK = auto()
    
    # I/O operations
    IO_INPUT = auto()
    IO_OUTPUT = auto()
    IO_FLUSH = auto()
    
    # Custom/generic
    CUSTOM = auto()


@dataclass(frozen=True)
class Action:
    """
    An action in the action algebra A.
    
    Actions are deterministic functions: X → X
    """
    action_type: ActionType
    parameters: Tuple[Any, ...] = field(default_factory=tuple)
    
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
    
    def canonical_bytes(self) -> bytes:
        """Serialize to canonical bytes for hashing."""
        # Sort keys for deterministic ordering
        items = []
        for key in sorted(self.beliefs.keys()):
            values = self.beliefs[key]
            items.append((key, [v.to_raw() for v in values]))
        return json.dumps(items, separators=(',', ':')).encode('utf-8')


@dataclass
class MemoryState:
    """X_memory: Sequential memory cells."""
    cells: List[Optional[bytes]] = field(default_factory=list)
    
    def canonical_bytes(self) -> bytes:
        """Serialize to canonical bytes for hashing."""
        # Convert cells to JSON-serializable format
        return json.dumps(self.cells, separators=(',', ':')).encode('utf-8')


@dataclass
class PlanState:
    """X_plan: Ordered list of planned actions."""
    steps: List[Action] = field(default_factory=list)
    
    def canonical_bytes(self) -> bytes:
        """Serialize to canonical bytes for hashing."""
        items = [(s.action_type.name, s.parameters) for s in self.steps]
        return json.dumps(items, default=str, separators=(',', ':')).encode('utf-8')


@dataclass
class PolicyState:
    """X_policy: State → ActionDistribution mapping."""
    mappings: Dict[str, Dict[str, QFixed]] = field(default_factory=dict)
    
    def canonical_bytes(self) -> bytes:
        """Serialize to canonical bytes for hashing."""
        # Sort keys for deterministic ordering
        items = []
        for key in sorted(self.mappings.keys()):
            action_dist = self.mappings[key]
            items.append((key, {k: v.to_raw() for k, v in action_dist.items()}))
        return json.dumps(items, separators=(',', ':')).encode('utf-8')


@dataclass
class IOState:
    """X_io: Input/Output buffers."""
    input_buffer: List[bytes] = field(default_factory=list)
    output_buffer: List[bytes] = field(default_factory=list)
    
    def canonical_bytes(self) -> bytes:
        """Serialize to canonical bytes for hashing."""
        return json.dumps({
            'input': [b.decode('utf-8', errors='replace') for b in self.input_buffer],
            'output': [b.decode('utf-8', errors='replace') for b in self.output_buffer]
        }, separators=(',', ':')).encode('utf-8')


@dataclass
class State:
    """
    Canonical state space X.
    
    X = X_belief × X_memory × X_plan × X_policy × X_io
    
    Per docs/ats/10_mathematical_core/state_space.md
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
            self.belief.canonical_bytes() +
            self.memory.canonical_bytes() +
            self.plan.canonical_bytes() +
            self.policy.canonical_bytes() +
            self.io.canonical_bytes()
        )
    
    def state_hash(self) -> str:
        """Compute SHA-256 state hash."""
        import hashlib
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


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
        return json.dumps({
            'step_type': self.step_type,
            'risk_before_q': self.risk_before_q.to_raw(),
            'risk_after_q': self.risk_after_q.to_raw(),
            'delta_plus_q': self.delta_plus_q.to_raw(),
            'budget_before_q': self.budget_before_q.to_raw(),
            'budget_after_q': self.budget_after_q.to_raw(),
            'kappa_q': self.kappa_q.to_raw(),
            'state_hash_before': self.state_hash_before,
            'state_hash_after': self.state_hash_after,
            'decision': self.decision,
            'details': self.details,
        }, sort_keys=True, separators=(',', ':')).encode('utf-8')


@dataclass
class Receipt:
    """
    A receipt proving ATS compliance for a state transition.
    
    Per docs/ats/20_coh_kernel/receipt_schema.md
    """
    version: str = "1.0.0"
    receipt_id: str = ""
    timestamp: Optional[str] = None
    episode_id: Optional[str] = None
    content: Optional[ReceiptContent] = None
    provenance: Dict[str, Any] = field(default_factory=dict)
    signature: Dict[str, Any] = field(default_factory=dict)
    previous_receipt_id: str = "00000000"
    previous_receipt_hash: str = ""
    chain_hash: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def canonical_bytes(self) -> bytes:
        """Serialize for hashing."""
        data = {
            'version': self.version,
            'timestamp': self.timestamp or '',
            'episode_id': self.episode_id or '',
            'content': json.loads(self.content.canonical_bytes().decode()) if self.content else {},
            'provenance': self.provenance,
            'signature': self.signature,
            'previous_receipt_id': self.previous_receipt_id,
            'previous_receipt_hash': self.previous_receipt_hash,
            'chain_hash': self.chain_hash,
            'metadata': self.metadata,
        }
        # Include receipt_id only if already computed (non-empty)
        # This allows computing receipt_id without circular dependency
        if self.receipt_id:
            data['receipt_id'] = self.receipt_id
        return json.dumps(data, sort_keys=True, separators=(',', ':')).encode('utf-8')
    
    def compute_receipt_id(self) -> str:
        """
        Compute receipt_id = first8(sha256(canonical_bytes(receipt)))
        
        Per docs/ats/20_coh_kernel/receipt_identity.md
        
        Note: Excludes receipt_id and chain_hash from canonical_bytes to avoid
        circular dependency (chain_hash depends on receipt_id).
        """
        import hashlib
        # Build data WITHOUT receipt_id and chain_hash (they depend on each other)
        data = {
            'version': self.version,
            'timestamp': self.timestamp or '',
            'episode_id': self.episode_id or '',
            'content': json.loads(self.content.canonical_bytes().decode()) if self.content else {},
            'provenance': self.provenance,
            'signature': self.signature,
            'previous_receipt_id': self.previous_receipt_id,
            'previous_receipt_hash': self.previous_receipt_hash,
            'metadata': self.metadata,
        }
        canonical = json.dumps(data, sort_keys=True, separators=(',', ':')).encode('utf-8')
        hash_bytes = hashlib.sha256(canonical)
        return hash_bytes.hexdigest()[:8]
    
    def compute_chain_hash(self, prev_receipt_id: str) -> str:
        """
        Compute chain_hash = sha256(prev_id || receipt_id)
        
        Per docs/ats/20_coh_kernel/chain_hash_rule.md
        """
        import hashlib
        chain_input = prev_receipt_id + self.receipt_id
        return hashlib.sha256(chain_input.encode()).hexdigest()


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
    def create(cls, initial: QFixed, kappa: QFixed) -> 'Budget':
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
            'value_q': self.value.to_json(),
            'kappa_q': self.kappa.to_json(),
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
            'result': 'REJECT',
            'code': self.code,
            'reason': self.reason,
            'details': self.details,
        }
