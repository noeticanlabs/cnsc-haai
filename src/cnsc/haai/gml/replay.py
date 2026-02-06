"""
GML Replay Verifier

Deterministic replay and verification for the Coherence Framework.

This module provides:
- Checkpoint: Execution checkpoint
- ReplayEngine: Replay execution
- Verifier: Result verification
- ReplayResult: Replay result
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, Tuple
from datetime import datetime
from uuid import uuid4
import json


class ReplayStatus(Enum):
    """Replay status."""
    PENDING = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()
    FAILED = auto()
    VERIFIED = auto()
    MISMATCH = auto()


@dataclass
class Checkpoint:
    """
    Execution Checkpoint.
    
    Snapshots execution state for replay.
    """
    checkpoint_id: str
    timestamp: datetime
    
    # Context (non-default arguments before defaults)
    episode_id: str
    phase: str
    step_index: int
    
    # State snapshot (with defaults)
    program_state: Dict[str, Any] = field(default_factory=dict)
    vm_state: Dict[str, Any] = field(default_factory=dict)
    coherence_level: float = 1.0
    
    # Provenance (with defaults)
    receipt_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "checkpoint_id": self.checkpoint_id,
            "timestamp": self.timestamp.isoformat(),
            "program_state": self.program_state,
            "vm_state": self.vm_state,
            "coherence_level": self.coherence_level,
            "episode_id": self.episode_id,
            "phase": self.phase,
            "step_index": self.step_index,
            "receipt_id": self.receipt_id,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Checkpoint':
        """Create from dictionary."""
        return cls(
            checkpoint_id=data["checkpoint_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.utcnow(),
            episode_id=data["episode_id"],
            phase=data["phase"],
            step_index=data.get("step_index", 0),
            program_state=data.get("program_state", {}),
            vm_state=data.get("vm_state", {}),
            coherence_level=data.get("coherence_level", 1.0),
            receipt_id=data.get("receipt_id"),
            metadata=data.get("metadata", {}),
        )
    
    @classmethod
    def create(
        cls,
        episode_id: str,
        phase: str,
        step_index: int,
        program_state: Dict[str, Any],
        vm_state: Dict[str, Any],
        coherence_level: float = 1.0,
        **kwargs,
    ) -> 'Checkpoint':
        """Factory method to create checkpoint."""
        return cls(
            checkpoint_id=str(uuid4())[:8],
            timestamp=datetime.utcnow(),
            program_state=program_state,
            vm_state=vm_state,
            coherence_level=coherence_level,
            episode_id=episode_id,
            phase=phase,
            step_index=step_index,
            **kwargs,
        )


@dataclass
class ReplayResult:
    """
    Replay Result.
    
    Result of replay verification.
    """
    replay_id: str
    status: ReplayStatus
    
    # Timing
    start_time: datetime
    end_time: Optional[datetime] = None
    
    # Results
    checkpoints_created: int = 0
    checkpoints_restored: int = 0
    steps_executed: int = 0
    mismatches: List[Dict[str, Any]] = field(default_factory=list)
    
    # Verification
    verified: bool = False
    verification_details: Dict[str, Any] = field(default_factory=dict)
    
    # Output
    output: Any = None
    error: Optional[str] = None
    
    @property
    def duration_ms(self) -> Optional[float]:
        """Get duration in milliseconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "replay_id": self.replay_id,
            "status": self.status.name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "checkpoints_created": self.checkpoints_created,
            "checkpoints_restored": self.checkpoints_restored,
            "steps_executed": self.steps_executed,
            "mismatches": self.mismatches,
            "verified": self.verified,
            "verification_details": self.verification_details,
            "output": str(self.output) if self.output else None,
            "error": self.error,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReplayResult':
        """Create from dictionary."""
        return cls(
            replay_id=data["replay_id"],
            status=ReplayStatus[data["status"]] if isinstance(data["status"], str) else ReplayStatus(data["status"]),
            start_time=datetime.fromisoformat(data["start_time"]) if "start_time" in data else datetime.utcnow(),
            end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
            checkpoints_created=data.get("checkpoints_created", 0),
            checkpoints_restored=data.get("checkpoints_restored", 0),
            steps_executed=data.get("steps_executed", 0),
            mismatches=data.get("mismatches", []),
            verified=data.get("verified", False),
            verification_details=data.get("verification_details", {}),
            output=data.get("output"),
            error=data.get("error"),
        )


class ReplayEngine:
    """
    Replay Engine.
    
    Executes deterministic replay of reasoning episodes.
    """
    
    def __init__(self, signing_key: str = "default-key"):
        self.signing_key = signing_key
        self.checkpoints: Dict[str, Checkpoint] = {}
        self.checkpoint_policy: Dict[str, Any] = {
            "interval_steps": 10,
            "on_gate": True,
            "on_phase_change": True,
        }
    
    def set_checkpoint_interval(self, interval: int) -> None:
        """Set checkpoint interval."""
        self.checkpoint_policy["interval_steps"] = interval
    
    def create_checkpoint(
        self,
        episode_id: str,
        phase: str,
        step_index: int,
        program_state: Dict[str, Any],
        vm_state: Dict[str, Any],
        coherence_level: float = 1.0,
        receipt_id: Optional[str] = None,
    ) -> Checkpoint:
        """Create checkpoint."""
        checkpoint = Checkpoint.create(
            episode_id=episode_id,
            phase=phase,
            step_index=step_index,
            program_state=program_state,
            vm_state=vm_state,
            coherence_level=coherence_level,
            receipt_id=receipt_id,
        )
        self.checkpoints[checkpoint.checkpoint_id] = checkpoint
        return checkpoint
    
    def restore_checkpoint(
        self,
        checkpoint_id: str,
    ) -> Optional[Checkpoint]:
        """Restore checkpoint state."""
        checkpoint = self.checkpoints.get(checkpoint_id)
        if checkpoint:
            return checkpoint
        return None
    
    def get_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """Get checkpoint by ID."""
        return self.checkpoints.get(checkpoint_id)
    
    def get_episode_checkpoints(self, episode_id: str) -> List[Checkpoint]:
        """Get all checkpoints for episode."""
        return [c for c in self.checkpoints.values() if c.episode_id == episode_id]
    
    def should_checkpoint(
        self,
        step_index: int,
        is_gate: bool,
        phase_changed: bool,
    ) -> bool:
        """Determine if checkpoint should be created."""
        if self.checkpoint_policy["on_gate"] and is_gate:
            return True
        if self.checkpoint_policy["on_phase_change"] and phase_changed:
            return True
        if step_index > 0 and step_index % self.checkpoint_policy["interval_steps"] == 0:
            return True
        return False
    
    def execute_replay(
        self,
        episode_id: str,
        executor: Callable[[Checkpoint], Tuple[bool, Any]],
        checkpoints: Optional[List[Checkpoint]] = None,
    ) -> ReplayResult:
        """
        Execute replay.
        
        Args:
            episode_id: Episode to replay
            executor: Function to execute step, takes checkpoint, returns (success, output)
            checkpoints: Checkpoints to replay (in order)
        
        Returns:
            ReplayResult with outcome
        """
        result = ReplayResult(
            replay_id=str(uuid4())[:8],
            status=ReplayStatus.IN_PROGRESS,
            start_time=datetime.utcnow(),
        )
        
        # Use provided checkpoints or get from storage
        if not checkpoints:
            checkpoints = self.get_episode_checkpoints(episode_id)
        
        # Sort by step index
        checkpoints = sorted(checkpoints, key=lambda c: c.step_index)
        
        result.checkpoints_restored = len(checkpoints)
        
        for checkpoint in checkpoints:
            try:
                success, output = executor(checkpoint)
                result.steps_executed += 1
                
                if not success:
                    result.status = ReplayStatus.FAILED
                    result.error = str(output)
                    break
                    
            except Exception as e:
                result.status = ReplayStatus.FAILED
                result.error = str(e)
                break
        
        result.end_time = datetime.utcnow()
        
        if result.status == ReplayStatus.IN_PROGRESS:
            result.status = ReplayStatus.COMPLETED
        
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics."""
        return {
            "total_checkpoints": len(self.checkpoints),
            "episodes_with_checkpoints": len(set(c.episode_id for c in self.checkpoints.values())),
            "checkpoint_policy": self.checkpoint_policy,
        }
    
    def clear(self) -> None:
        """Clear all checkpoints."""
        self.checkpoints.clear()


class Verifier:
    """
    Verifier.
    
    Verifies replay results against original execution.
    """
    
    def __init__(self, signing_key: str = "default-key"):
        self.signing_key = signing_key
    
    def verify_replay(
        self,
        original_output: Any,
        replay_output: Any,
        original_receipts: List[Any],
        replay_receipts: List[Any],
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Verify replay against original execution.
        
        Returns:
            Tuple of (verified, details)
        """
        details = {
            "output_match": False,
            "receipt_count_match": False,
            "receipt_chain_valid": False,
            "coherence_match": False,
            "mismatches": [],
        }
        
        # Check output match
        output_match = original_output == replay_output
        details["output_match"] = output_match
        if not output_match:
            details["mismatches"].append({
                "type": "output",
                "original": str(original_output),
                "replay": str(replay_output),
            })
        
        # Check receipt count
        count_match = len(original_receipts) == len(replay_receipts)
        details["receipt_count_match"] = count_match
        if not count_match:
            details["mismatches"].append({
                "type": "receipt_count",
                "original": len(original_receipts),
                "replay": len(replay_receipts),
            })
        
        # Check receipt chain validity
        if len(original_receipts) == 0 and len(replay_receipts) == 0:
            # Empty receipts - vacuously valid
            details["receipt_chain_valid"] = True
        elif len(original_receipts) > 0 and len(replay_receipts) > 0:
            chain_valid = self._verify_chain_integrity(original_receipts)
            details["receipt_chain_valid"] = chain_valid
        
        # Overall verification
        verified = (
            output_match and
            count_match and
            details["receipt_chain_valid"]
        )
        
        return verified, details
    
    def _verify_chain_integrity(self, receipts: List[Any]) -> bool:
        """Verify receipt chain integrity."""
        if not receipts:
            return True
        
        # Check chain hashes
        for i in range(1, len(receipts)):
            if hasattr(receipts[i], 'previous_receipt_hash'):
                if receipts[i].previous_receipt_hash != receipts[i-1].chain_hash:
                    return False
        
        return True
    
    def verify_checkpoint(self, checkpoint: Checkpoint) -> Tuple[bool, str]:
        """Verify checkpoint integrity."""
        # Verify state is serializable
        try:
            json.dumps(checkpoint.program_state)
            json.dumps(checkpoint.vm_state)
        except (TypeError, ValueError) as e:
            return False, f"Checkpoint state not serializable: {e}"
        
        # Verify coherence level is valid
        if not 0.0 <= checkpoint.coherence_level <= 1.0:
            return False, f"Invalid coherence level: {checkpoint.coherence_level}"
        
        return True, "Checkpoint valid"
    
    def compare_checkpoints(
        self,
        original: Checkpoint,
        replay: Checkpoint,
    ) -> Tuple[bool, List[str]]:
        """
        Compare two checkpoints.
        
        Returns:
            Tuple of (match, differences)
        """
        differences = []
        
        # Compare coherence
        if abs(original.coherence_level - replay.coherence_level) > 0.001:
            differences.append(
                f"Coherence mismatch: {original.coherence_level} vs {replay.coherence_level}"
            )
        
        # Compare phase
        if original.phase != replay.phase:
            differences.append(f"Phase mismatch: {original.phase} vs {replay.phase}")
        
        return len(differences) == 0, differences


def create_replay_engine(signing_key: str = "default-key") -> ReplayEngine:
    """Create new replay engine."""
    return ReplayEngine(signing_key=signing_key)


def create_verifier(signing_key: str = "default-key") -> Verifier:
    """Create new verifier."""
    return Verifier(signing_key=signing_key)
