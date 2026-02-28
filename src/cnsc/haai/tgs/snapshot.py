"""
Snapshot and Staging Protocol

Manages CNSC state snapshots for TGS operations. This module provides:
- SnapshotManager: Creates immutable snapshots and manages rollback/commit
- Snapshot: Immutable snapshot of cognitive state
- StagedState: Mutable staging area for proposal evaluation

Snapshots enable:
1. Bitwise-identical state restoration on rollback
2. Safe proposal evaluation in isolation
3. Atomic commit of staged changes
"""

import hashlib
import json
import pickle
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from uuid import UUID, uuid4
import copy


class StateHash(str):
    """
    Cryptographic hash of a cognitive state.

    Used to verify state integrity and detect modifications.
    """

    @classmethod
    def from_state(cls, state: Dict[str, Any]) -> "StateHash":
        """Compute state hash from state dictionary."""
        # Create deterministic representation
        state_copy = copy.deepcopy(state)

        # Sort keys for deterministic serialization
        def sort_dict(d: Any) -> Any:
            if isinstance(d, dict):
                return {k: sort_dict(v) for k, v in sorted(d.items())}
            elif isinstance(d, list):
                return [sort_dict(item) for item in d]
            return d

        sorted_state = sort_dict(state_copy)
        state_bytes = json.dumps(sorted_state, sort_keys=True, default=str).encode()
        hash_value = hashlib.sha256(state_bytes).hexdigest()
        return cls(f"sha256:{hash_value}")


@dataclass
class Snapshot:
    """
    Immutable snapshot of cognitive state.

    A snapshot captures the complete state at a point in time,
    enabling rollback to an exact previous state.

    Attributes:
        snapshot_id: Unique identifier for this snapshot
        parent_state_hash: Hash of the parent state
        state_hash: Hash of this snapshot's state
        state: The captured state data
        logical_time: Logical timestamp of snapshot
        timestamp: Wall clock timestamp
        metadata: Additional snapshot metadata
    """

    snapshot_id: UUID = field(default_factory=uuid4)
    parent_state_hash: Optional[StateHash] = None
    state_hash: StateHash = field(default_factory=lambda: StateHash(""))
    state: Dict[str, Any] = field(default_factory=dict)
    logical_time: int = 0
    timestamp: float = field(default_factory=lambda: __import__("time").time())
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_state(
        cls,
        state: Dict[str, Any],
        parent_state_hash: Optional[StateHash] = None,
        logical_time: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "Snapshot":
        """Create snapshot from state dictionary."""
        state_hash = StateHash.from_state(state)

        return cls(
            parent_state_hash=parent_state_hash,
            state_hash=state_hash,
            state=copy.deepcopy(state),
            logical_time=logical_time,
            metadata=metadata or {},
        )

    def verify_integrity(self) -> bool:
        """Verify snapshot has not been modified."""
        computed_hash = StateHash.from_state(self.state)
        return computed_hash == self.state_hash


@dataclass
class StagedState:
    """
    Mutable staging area for proposal evaluation.

    The staged state allows proposal evaluation without modifying
    the actual state. Changes are only committed after all checks pass.

    Attributes:
        memory: Working memory contents
        tags: Active tags
        policies: Policy state
        resources: Resource allocations
        auxiliary: Auxiliary state data
        _original_state: Reference to original state for rollback
    """

    memory: Dict[str, Any] = field(default_factory=dict)
    tags: Dict[str, Any] = field(default_factory=dict)
    policies: Dict[str, Any] = field(default_factory=dict)
    resources: Dict[str, Any] = field(default_factory=dict)
    auxiliary: Dict[str, Any] = field(default_factory=dict)
    _original_state: Optional[Dict[str, Any]] = None

    @classmethod
    def from_snapshot(cls, snapshot: Snapshot) -> "StagedState":
        """Create staged state from a snapshot."""
        return cls(
            memory=copy.deepcopy(snapshot.state.get("memory", {})),
            tags=copy.deepcopy(snapshot.state.get("tags", {})),
            policies=copy.deepcopy(snapshot.state.get("policies", {})),
            resources=copy.deepcopy(snapshot.state.get("resources", {})),
            auxiliary=copy.deepcopy(snapshot.state.get("auxiliary", {})),
            _original_state=snapshot.state,
        )

    def to_state_dict(self) -> Dict[str, Any]:
        """Convert staged state to state dictionary."""
        return {
            "memory": self.memory,
            "tags": self.tags,
            "policies": self.policies,
            "resources": self.resources,
            "auxiliary": self.auxiliary,
        }

    def compute_state_hash(self) -> StateHash:
        """Compute hash of staged state."""
        return StateHash.from_state(self.to_state_dict())

    def apply_delta(self, delta: "DeltaOp") -> None:
        """
        Apply a delta operation to the staged state.

        Args:
            delta: Delta operation to apply
        """
        from cnsc.haai.tgs.proposal import DeltaOperationType

        op = delta.operation
        target = delta.target
        payload = delta.payload

        if op == DeltaOperationType.ADD_BELIEF:
            if "beliefs" not in self.memory:
                self.memory["beliefs"] = {}
            self.memory["beliefs"][target] = payload.get("content", {})

        elif op == DeltaOperationType.REVISE_BELIEF:
            if "beliefs" in self.memory and target in self.memory["beliefs"]:
                self.memory["beliefs"][target] = payload.get("content", {})

        elif op == DeltaOperationType.RETRACT_BELIEF:
            if "beliefs" in self.memory:
                self.memory["beliefs"].pop(target, None)

        elif op == DeltaOperationType.ADD_TAG:
            self.tags[target] = payload

        elif op == DeltaOperationType.UPDATE_TAG:
            if target in self.tags:
                self.tags[target].update(payload)

        elif op == DeltaOperationType.REMOVE_TAG:
            self.tags.pop(target, None)

        elif op == DeltaOperationType.ALLOCATE_RESOURCE:
            if "budgets" not in self.resources:
                self.resources["budgets"] = {}
            self.resources["budgets"][target] = payload.get("amount", 0)

        elif op == DeltaOperationType.DEALLOCATE_RESOURCE:
            self.resources.get("budgets", {}).pop(target, None)

        elif op == DeltaOperationType.SET_ATTRIBUTE:
            self.auxiliary[target] = payload

        elif op == DeltaOperationType.DELETE_ATTRIBUTE:
            self.auxiliary.pop(target, None)

        # Add other delta types as needed

    def apply_deltas(self, deltas: list) -> None:
        """Apply multiple delta operations."""
        for delta in deltas:
            self.apply_delta(delta)


# Import DeltaOp for type hints (avoid circular import)
from cnsc.haai.tgs.proposal import DeltaOp


class SnapshotError(Exception):
    """Exception raised for snapshot operations."""

    pass


class SnapshotManager:
    """
    Manages state snapshots for TGS operations.

    The snapshot manager:
    1. Creates immutable snapshots of current state
    2. Provides rollback to restore previous state
    3. Commits staged changes to produce new state

    All operations are designed to be deterministic and replayable.
    """

    def __init__(self):
        self._snapshots: Dict[UUID, Snapshot] = {}
        self._current_snapshot: Optional[Snapshot] = None
        self._snapshot_history: list = []  # For replay/debugging

    def begin_attempt_snapshot(
        self,
        state: Dict[str, Any],
        parent_state_hash: Optional[StateHash] = None,
        logical_time: int = 0,
    ) -> Snapshot:
        """
        Create immutable snapshot of current state.

        Args:
            state: Current cognitive state
            parent_state_hash: Hash of parent state (for chain)
            logical_time: Logical timestamp

        Returns:
            Snapshot of current state
        """
        snapshot = Snapshot.from_state(
            state=state,
            parent_state_hash=parent_state_hash,
            logical_time=logical_time,
        )

        self._snapshots[snapshot.snapshot_id] = snapshot
        self._current_snapshot = snapshot
        self._snapshot_history.append(snapshot.snapshot_id)

        return snapshot

    def get_snapshot(self, snapshot_id: UUID) -> Optional[Snapshot]:
        """Retrieve snapshot by ID."""
        return self._snapshots.get(snapshot_id)

    def get_current_snapshot(self) -> Optional[Snapshot]:
        """Get the current (most recent) snapshot."""
        return self._current_snapshot

    def create_staged_state(self, snapshot: Optional[Snapshot] = None) -> StagedState:
        """
        Create a staged state from a snapshot.

        Args:
            snapshot: Snapshot to stage from (uses current if None)

        Returns:
            Mutable staged state
        """
        if snapshot is None:
            snapshot = self._current_snapshot

        if snapshot is None:
            raise SnapshotError("No snapshot available for staging")

        return StagedState.from_snapshot(snapshot)

    def rollback(self, snapshot: Snapshot) -> Dict[str, Any]:
        """
        Restore bitwise-identical state from snapshot.

        Args:
            snapshot: Snapshot to restore to

        Returns:
            Restored state dictionary

        Raises:
            SnapshotError: If snapshot is None or not found
        """
        if snapshot is None:
            raise SnapshotError("Snapshot cannot be None for rollback")

        if snapshot.snapshot_id not in self._snapshots:
            raise SnapshotError(f"Snapshot {snapshot.snapshot_id} not found")

        self._current_snapshot = snapshot
        return copy.deepcopy(snapshot.state)

    def commit(self, snapshot: Snapshot, staged: StagedState) -> StateHash:
        """
        Persist staged changes and return new state hash.

        Args:
            snapshot: Original snapshot
            staged: Staged state with changes

        Returns:
            Hash of new committed state

        Raises:
            SnapshotError: If snapshot mismatch
        """
        if snapshot.snapshot_id not in self._snapshots:
            raise SnapshotError(f"Snapshot {snapshot.snapshot_id} not found")

        # Verify snapshot hasn't been modified
        if not snapshot.verify_integrity():
            raise SnapshotError("Snapshot integrity check failed")

        # Compute new state hash
        new_state_dict = staged.to_state_dict()
        new_state_hash = StateHash.from_state(new_state_dict)

        # Create new snapshot for committed state
        new_snapshot = Snapshot(
            parent_state_hash=snapshot.state_hash,
            state_hash=new_state_hash,
            state=new_state_dict,
            logical_time=snapshot.logical_time + 1,
        )

        self._snapshots[new_snapshot.snapshot_id] = new_snapshot
        self._current_snapshot = new_snapshot
        self._snapshot_history.append(new_snapshot.snapshot_id)

        return new_state_hash

    def get_chain_head(self) -> Optional[Snapshot]:
        """Get the head of the snapshot chain."""
        return self._current_snapshot

    def verify_chain(self, from_index: int = 0) -> bool:
        """
        Verify integrity of snapshot chain from index.

        Args:
            from_index: Starting index in history

        Returns:
            True if chain is valid, False otherwise
        """
        history = self._snapshot_history

        if from_index >= len(history):
            return True

        for i in range(from_index, len(history) - 1):
            curr_id = history[i]
            next_id = history[i + 1]

            curr = self._snapshots.get(curr_id)
            next_ = self._snapshots.get(next_id)

            if curr is None or next_ is None:
                return False

            # Check parent hash chain
            if curr.state_hash != next_.parent_state_hash:
                return False

            # Verify snapshot integrity
            if not next_.verify_integrity():
                return False

        return True
