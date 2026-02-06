"""
GML PhaseLoom

PhaseLoom thread management for the Coherence Framework.

This module provides:
- PhaseLoom: Thread container
- ThreadCoupling: Thread relationships
- CouplingPolicy: Coupling rules
- ThreadState: Thread state tracking
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, Tuple
from datetime import datetime
from uuid import uuid4


class ThreadState(Enum):
    """Thread state."""
    ACTIVE = auto()
    WAITING = auto()
    BLOCKED = auto()
    COMPLETED = auto()
    FAILED = auto()
    RECOVERING = auto()
    
    def to_string(self) -> str:
        """Convert to string."""
        return {
            ThreadState.ACTIVE: "ACTIVE",
            ThreadState.WAITING: "WAITING",
            ThreadState.BLOCKED: "BLOCKED",
            ThreadState.COMPLETED: "COMPLETED",
            ThreadState.FAILED: "FAILED",
            ThreadState.RECOVERING: "RECOVERING",
        }.get(self, "UNKNOWN")


@dataclass
class CouplingPolicy:
    """
    Coupling Policy.
    
    Defines rules for thread coupling.
    """
    policy_id: str
    name: str
    
    # Coupling type
    coupling_type: str  # "sequential", "parallel", "hierarchical"
    
    # Constraints
    max_parallel: int = 1
    min_coherence: float = 0.5
    ordering_required: bool = True
    
    # Recovery
    recovery_mode: str = "cascade"  # "cascade", "independent", "dependency"
    
    def check_coupling(
        self,
        threads: List['PhaseLoom'],
        coherence_levels: Dict[str, float],
    ) -> Tuple[bool, str]:
        """
        Check if coupling constraints are satisfied.
        
        Returns:
            Tuple of (passed, message)
        """
        # Check parallel count
        active_threads = [t for t in threads if t.is_active]
        if len(active_threads) > self.max_parallel:
            return False, f"Too many parallel threads: {len(active_threads)} > {self.max_parallel}"
        
        # Check coherence
        for thread in active_threads:
            coherence = coherence_levels.get(thread.thread_id, 1.0)
            if coherence < self.min_coherence:
                return False, f"Thread {thread.name} coherence too low: {coherence} < {self.min_coherence}"
        
        # Check ordering if required
        if self.ordering_required:
            # Verify dependencies are satisfied
            for thread in active_threads:
                for dep_id in thread.depends_on:
                    dep_thread = None
                    for t in threads:
                        if t.thread_id == dep_id:
                            dep_thread = t
                            break
                    if dep_thread and dep_thread.state != ThreadState.COMPLETED:
                        return False, f"Dependency {dep_id} not completed for thread {thread.name}"
        
        return True, "Coupling constraints satisfied"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "policy_id": self.policy_id,
            "name": self.name,
            "coupling_type": self.coupling_type,
            "max_parallel": self.max_parallel,
            "min_coherence": self.min_coherence,
            "ordering_required": self.ordering_required,
            "recovery_mode": self.recovery_mode,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CouplingPolicy':
        """Create from dictionary."""
        return cls(
            policy_id=data["policy_id"],
            name=data["name"],
            coupling_type=data["coupling_type"],
            max_parallel=data.get("max_parallel", 1),
            min_coherence=data.get("min_coherence", 0.5),
            ordering_required=data.get("ordering_required", True),
            recovery_mode=data.get("recovery_mode", "cascade"),
        )


@dataclass
class ThreadCoupling:
    """
    Thread Coupling.
    
    Represents relationship between threads.
    """
    coupling_id: str
    from_thread: str
    to_thread: str
    coupling_type: str  # "depends_on", "produces_for", "blocks", "triggers"
    strength: float = 1.0  # Coupling strength 0-1
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "coupling_id": self.coupling_id,
            "from_thread": self.from_thread,
            "to_thread": self.to_thread,
            "coupling_type": self.coupling_type,
            "strength": self.strength,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ThreadCoupling':
        """Create from dictionary."""
        return cls(
            coupling_id=data["coupling_id"],
            from_thread=data["from_thread"],
            to_thread=data["to_thread"],
            coupling_type=data["coupling_type"],
            strength=data.get("strength", 1.0),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow(),
            metadata=data.get("metadata", {}),
        )


@dataclass
class PhaseLoom:
    """
    PhaseLoom.
    
    Thread container with coupling management.
    """
    loom_id: str
    name: str
    
    # Threads
    threads: Dict[str, 'PhaseLoomThread'] = field(default_factory=dict)
    
    # Couplings
    couplings: Dict[str, ThreadCoupling] = field(default_factory=dict)
    
    # Policies
    coupling_policies: Dict[str, CouplingPolicy] = field(default_factory=dict)
    active_policy: Optional[str] = None
    
    # State
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True
    
    # Callbacks
    on_thread_start: Optional[Callable] = None
    on_thread_complete: Optional[Callable] = None
    on_coupling_violation: Optional[Callable] = None
    
    def create_thread(
        self,
        name: str,
        thread_id: Optional[str] = None,
        depends_on: Optional[List[str]] = None,
    ) -> 'PhaseLoomThread':
        """Create new thread in loom."""
        tid = thread_id or str(uuid4())[:8]
        thread = PhaseLoomThread(
            thread_id=tid,
            name=name,
            loom_id=self.loom_id,
            depends_on=depends_on or [],
        )
        self.threads[tid] = thread
        return thread
    
    def add_coupling(self, coupling: ThreadCoupling) -> None:
        """Add coupling between threads."""
        self.couplings[coupling.coupling_id] = coupling
        
        # Update thread dependency lists
        from_thread = self.threads.get(coupling.from_thread)
        if from_thread:
            if coupling.coupling_type == "depends_on" and coupling.to_thread not in from_thread.depends_on:
                from_thread.depends_on.append(coupling.to_thread)
    
    def add_policy(self, policy: CouplingPolicy) -> None:
        """Add coupling policy."""
        self.coupling_policies[policy.policy_id] = policy
    
    def set_active_policy(self, policy_id: str) -> bool:
        """Set active coupling policy."""
        if policy_id in self.coupling_policies:
            self.active_policy = policy_id
            return True
        return False
    
    def check_coupling_constraints(self) -> Tuple[bool, List[str]]:
        """
        Check all coupling constraints.
        
        Returns:
            Tuple of (passed, violations)
        """
        violations = []
        
        # Get active policy
        policy = None
        if self.active_policy:
            policy = self.coupling_policies.get(self.active_policy)
        
        if not policy:
            return True, []
        
        # Get coherence levels
        coherence = {tid: t.coherence_level for tid, t in self.threads.items()}
        
        # Check all threads
        for thread in self.threads.values():
            if not thread.is_active:
                continue
            
            passed, message = policy.check_coupling(
                list(self.threads.values()),
                coherence,
            )
            
            if not passed:
                violations.append(f"Thread {thread.name}: {message}")
                if self.on_coupling_violation:
                    self.on_coupling_violation(thread, message)
        
        return len(violations) == 0, violations
    
    def get_executable_threads(self) -> List['PhaseLoomThread']:
        """Get threads that can execute (dependencies satisfied)."""
        executable = []
        for thread in self.threads.values():
            if not thread.is_active:
                continue
            
            # Check if all dependencies are completed
            deps_satisfied = True
            for dep_id in thread.depends_on:
                dep_thread = self.threads.get(dep_id)
                if not dep_thread or dep_thread.state != ThreadState.COMPLETED:
                    deps_satisfied = False
                    break
            
            if deps_satisfied:
                executable.append(thread)
        
        return executable
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get loom statistics."""
        state_counts = {}
        for thread in self.threads.values():
            state_key = thread.state.to_string()
            state_counts[state_key] = state_counts.get(state_key, 0) + 1
        
        return {
            "loom_id": self.loom_id,
            "name": self.name,
            "total_threads": len(self.threads),
            "active_threads": len([t for t in self.threads.values() if t.is_active]),
            "thread_states": state_counts,
            "coupling_count": len(self.couplings),
            "policy_count": len(self.coupling_policies),
            "active_policy": self.active_policy,
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "loom_id": self.loom_id,
            "name": self.name,
            "thread_count": len(self.threads),
            "coupling_count": len(self.couplings),
            "policy_count": len(self.coupling_policies),
            "active_policy": self.active_policy,
            "created_at": self.created_at.isoformat(),
            "is_active": self.is_active,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PhaseLoom':
        """Create from dictionary."""
        return cls(
            loom_id=data["loom_id"],
            name=data["name"],
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow(),
            is_active=data.get("is_active", True),
        )


@dataclass
class PhaseLoomThread:
    """
    PhaseLoom Thread.
    
    Individual thread within a PhaseLoom.
    """
    thread_id: str
    name: str
    loom_id: str
    
    # State
    state: ThreadState = ThreadState.ACTIVE
    
    # Dependencies
    depends_on: List[str] = field(default_factory=list)
    produced_for: List[str] = field(default_factory=list)
    
    # Coherence tracking
    coherence_level: float = 1.0
    coherence_history: List[Tuple[datetime, float]] = field(default_factory=list)
    
    # Progress
    progress: float = 0.0
    checkpoint_id: Optional[str] = None
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Properties
    @property
    def is_active(self) -> bool:
        """Check if thread is active."""
        return self.state in [ThreadState.ACTIVE, ThreadState.WAITING]
    
    @property
    def is_complete(self) -> bool:
        """Check if thread is complete."""
        return self.state == ThreadState.COMPLETED
    
    def start(self) -> None:
        """Start thread."""
        self.state = ThreadState.ACTIVE
        self.started_at = datetime.utcnow()
    
    def complete(self) -> None:
        """Complete thread."""
        self.state = ThreadState.COMPLETED
        self.completed_at = datetime.utcnow()
    
    def fail(self, reason: str) -> None:
        """Fail thread."""
        self.state = ThreadState.FAILED
        self.metadata["failure_reason"] = reason
    
    def recover(self) -> None:
        """Start recovery."""
        self.state = ThreadState.RECOVERING
        self.coherence_level = 1.0
    
    def update_coherence(self, level: float) -> None:
        """Update coherence level."""
        self.coherence_level = level
        self.coherence_history.append((datetime.utcnow(), level))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "thread_id": self.thread_id,
            "name": self.name,
            "loom_id": self.loom_id,
            "state": self.state.to_string(),
            "depends_on": self.depends_on,
            "produced_for": self.produced_for,
            "coherence_level": self.coherence_level,
            "progress": self.progress,
            "checkpoint_id": self.checkpoint_id,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PhaseLoomThread':
        """Create from dictionary."""
        return cls(
            thread_id=data["thread_id"],
            name=data["name"],
            loom_id=data["loom_id"],
            state=ThreadState[data["state"]] if isinstance(data["state"], str) else ThreadState(data["state"]),
            depends_on=data.get("depends_on", []),
            produced_for=data.get("produced_for", []),
            coherence_level=data.get("coherence_level", 1.0),
            progress=data.get("progress", 0.0),
            checkpoint_id=data.get("checkpoint_id"),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow(),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            metadata=data.get("metadata", {}),
        )


def create_phase_loom(name: str, loom_id: Optional[str] = None) -> PhaseLoom:
    """Create new PhaseLoom."""
    return PhaseLoom(
        loom_id=loom_id or str(uuid4())[:8],
        name=name,
    )
