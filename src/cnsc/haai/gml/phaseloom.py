"""
GML PhaseLoom

PhaseLoom thread management for the Coherence Framework.

This module provides:
- PhaseLoom: Thread container
- ThreadCoupling: Thread relationships
- CouplingPolicy: Coupling rules
- ThreadState: Thread state tracking

Dual-write support for GraphGML output is included.
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, Tuple
from datetime import datetime
from uuid import uuid4

# GraphGML import with graceful fallback
try:
    from cnsc.haai.graphgml import types, builder, core
    GRAPHGML_AVAILABLE = True
except ImportError:
    GRAPHGML_AVAILABLE = False


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
class GateStackRun:
    """
    Gate Stack Run.
    
    Represents execution of a gate stack within a thread.
    """
    run_id: str
    gate_sequence: List[str] = field(default_factory=list)
    results: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "run_id": self.run_id,
            "gate_sequence": self.gate_sequence,
            "results": self.results,
            "created_at": self.created_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GateStackRun':
        """Create from dictionary."""
        return cls(
            run_id=data["run_id"],
            gate_sequence=data.get("gate_sequence", []),
            results=data.get("results", []),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow(),
        )


@dataclass
class PhaseLoom:
    """
    PhaseLoom.
    
    Thread container with coupling management.
    
    Dual-write support for GraphGML is included via to_graph() method.
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
    
    # GraphGML Methods
    def to_graph(self) -> Optional[core.GraphGML]:
        """
        Convert entire PhaseLoom to single GraphGML.
        
        Returns:
            GraphGML representation or None if GraphGML unavailable.
        """
        if not GRAPHGML_AVAILABLE:
            return None
        
        combined = core.GraphGML()
        
        for thread_id, thread in self.threads.items():
            thread_graph = thread.to_graph()
            if thread_graph:
                # Prefix node IDs to avoid collisions (only if not already prefixed)
                for node_id, node in thread_graph.nodes.items():
                    # Check if node_id already starts with thread_id
                    if node_id.startswith(f"{thread_id}_"):
                        prefixed_id = node_id
                    else:
                        prefixed_id = f"{thread_id}_{node_id}"
                    
                    # Only add if not already present
                    if prefixed_id not in combined.nodes:
                        node.node_id = prefixed_id
                        if hasattr(node, 'properties') and 'node_id' in node.properties:
                            node.properties['thread_id'] = thread_id
                        combined.add_node(node)
                
                # Remap edges with prefixed IDs
                for edge in thread_graph.edges:
                    # Get source and target, prefix if needed
                    source = edge[0]
                    target = edge[2]
                    
                    if source.startswith(f"{thread_id}_"):
                        prefixed_source = source
                    else:
                        prefixed_source = f"{thread_id}_{source}"
                    
                    if target.startswith(f"{thread_id}_"):
                        prefixed_target = target
                    else:
                        prefixed_target = f"{thread_id}_{target}"
                    
                    # Only add edge if both nodes exist
                    if prefixed_source in combined.nodes and prefixed_target in combined.nodes:
                        combined.add_edge(prefixed_source, edge[1], prefixed_target)
        
        # Add coupling nodes and edges
        for coupling_id, coupling in self.couplings.items():
            coupling_node = types.GraphNode(
                node_id=f"coupling_{coupling_id}",
                node_type="thread_coupling",
                properties={
                    "coupling_id": coupling.coupling_id,
                    "from_thread": coupling.from_thread,
                    "to_thread": coupling.to_thread,
                    "coupling_type": coupling.coupling_type,
                    "strength": coupling.strength,
                }
            )
            combined.add_node(coupling_node)
            
            # Add edges for coupling relationships
            combined.add_edge(
                f"{coupling.from_thread}_thread",
                "has_coupling",
                coupling_node.node_id
            )
            combined.add_edge(
                coupling_node.node_id,
                "couples_to",
                f"{coupling.to_thread}_thread"
            )
        
        return combined


@dataclass
class PhaseLoomThread:
    """
    PhaseLoom Thread.
    
    Individual thread within a PhaseLoom.
    
    Dual-write support for GraphGML is included via to_graph() method.
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
    
    # GraphGML optional fields (populated during graph conversion)
    events: List[Dict[str, Any]] = field(default_factory=list)
    receipts: Dict[str, List[Any]] = field(default_factory=dict)
    gate_runs: List[GateStackRun] = field(default_factory=list)
    
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
    
    # GraphGML Methods
    def to_graph(self) -> Optional[core.GraphGML]:
        """
        Convert PhaseLoomThread to GraphGML representation.
        
        Returns:
            GraphGML representation or None if GraphGML unavailable.
        """
        if not GRAPHGML_AVAILABLE:
            return None
        
        graph = core.GraphGML()
        
        # Create thread node using GraphNode base class
        thread_node = types.GraphNode(
            node_id=f"{self.thread_id}_thread",
            node_type="thread",
            properties={
                "thread_id": self.thread_id,
                "name": self.name,
                "loom_id": self.loom_id,
                "state": self.state.to_string(),
                "coherence_level": self.coherence_level,
                "progress": self.progress,
            }
        )
        graph.add_node(thread_node)
        
        # Process events and create state nodes
        for idx, event in enumerate(self.events):
            event_id = event.get("event_id", f"{self.thread_id}_event_{idx}")
            state_node = types.StateNode(
                state_id=f"state_{event_id}",
                state_type=event.get("event_type", "unknown"),
                properties={
                    "event_id": event_id,
                    "event_type": event.get("event_type"),
                    "timestamp": event.get("timestamp"),
                }
            )
            graph.add_node(state_node)
            
            # Link to thread
            graph.add_edge(thread_node.node_id, "contains", state_node.node_id)
            
            # Link consecutive events
            if idx > 0:
                prev_event_id = self.events[idx - 1].get("event_id", f"{self.thread_id}_event_{idx - 1}")
                graph.add_edge(
                    f"state_{prev_event_id}",
                    "scheduled_after",
                    state_node.node_id
                )
        
        # Process receipts and create commit/proof nodes
        for receipt_id, receipt_list in self.receipts.items():
            for receipt in receipt_list:
                # Create commit node from receipt
                commit_node = types.CommitNode(
                    commit_id=f"commit_{receipt_id}",
                    operation=receipt.get("operation", "unknown"),
                    properties={
                        "receipt_id": receipt_id,
                        "operation": receipt.get("operation"),
                        "timestamp": receipt.get("timestamp"),
                    }
                )
                graph.add_node(commit_node)
                
                # Link to thread
                graph.add_edge(thread_node.node_id, "produces", commit_node.node_id)
                
                # Link to previous receipt if exists
                prev_receipt_id = receipt.get("previous_receipt_id")
                if prev_receipt_id:
                    graph.add_edge(
                        f"commit_{prev_receipt_id}",
                        "requires_proof",
                        commit_node.node_id
                    )
        
        # Process gate runs and create GateResult nodes
        for gate_run in self.gate_runs:
            gate_node = types.GateStackRunNode(
                run_id=f"gatestack_{gate_run.run_id}",
                gate_sequence=gate_run.gate_sequence,
                properties={
                    "run_id": gate_run.run_id,
                    "gate_sequence": gate_run.gate_sequence,
                }
            )
            graph.add_node(gate_node)
            graph.add_edge(thread_node.node_id, "executes", gate_node.node_id)
            
            for idx, result in enumerate(gate_run.results):
                result_id = result.get("result_id", f"{gate_run.run_id}_result_{idx}")
                result_node = types.GateResultNode(
                    result_id=f"gate_result_{result_id}",
                    gate_type=result.get("gate_type", "unknown"),
                    passed=result.get("passed", False),
                    properties={
                        "result_id": result_id,
                        "gate_type": result.get("gate_type"),
                        "passed": result.get("passed"),
                        "details": result.get("details", {}),
                    }
                )
                graph.add_node(result_node)
                graph.add_edge(gate_node.node_id, "summarizes", result_node.node_id)
        
        # Add dependency edges
        for dep_id in self.depends_on:
            dep_node_id = f"{dep_id}_thread"
            if dep_node_id in graph.nodes or self._node_exists_in_graph(graph, dep_node_id):
                graph.add_edge(dep_node_id, "prerequisite_for", thread_node.node_id)
        
        return graph
    
    def _node_exists_in_graph(self, graph: core.GraphGML, node_id: str) -> bool:
        """Check if a node exists in the graph (helper for to_graph)."""
        return node_id in graph.nodes
    
    def generate_full_graph(self) -> Optional[core.GraphGML]:
        """
        Generate complete GraphGML including all dependencies.
        
        Returns:
            GraphGML representation or None if GraphGML unavailable.
        """
        if not GRAPHGML_AVAILABLE:
            return None
        
        return self.to_graph()
    
    def query_causal_path(
        self,
        start_event_id: str,
        end_event_id: str
    ) -> Optional[List[str]]:
        """
        Find causal path between two events using graph traversal.
        
        Args:
            start_event_id: Starting event ID
            end_event_id: Ending event ID
            
        Returns:
            List of node IDs in path, or None if GraphGML unavailable.
        """
        if not GRAPHGML_AVAILABLE:
            return None
        
        graph = self.to_graph()
        if not graph:
            return None
        
        start_node = f"state_{start_event_id}"
        end_node = f"state_{end_event_id}"
        
        # Simple BFS traversal for path finding
        if start_node not in graph.nodes or end_node not in graph.nodes:
            return None
        
        edge_types = ["scheduled_after", "proposed_from", "evaluates"]
        queue = [(start_node, [start_node])]
        visited = {start_node}
        
        while queue:
            current, path = queue.pop(0)
            
            if current == end_node:
                return path
            
            # Get neighbors via valid edge types
            adjacency = graph._build_adjacency()
            for edge_type in edge_types:
                for neighbor in adjacency[current].get(edge_type, []):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, path + [neighbor]))
        
        return None
    
    def find_gate_dependencies(self, gate_run_id: str) -> List[str]:
        """
        Find all events/nodes that a gate run depends on.
        
        Args:
            gate_run_id: ID of the gate run to find dependencies for
            
        Returns:
            List of node IDs that the gate run depends on.
        """
        if not GRAPHGML_AVAILABLE:
            return []
        
        graph = self.to_graph()
        if not graph:
            return []
        
        results = []
        start_node = f"gatestack_{gate_run_id}"
        
        if start_node not in graph.nodes:
            return []
        
        # Get all nodes that have edges to the gate run
        adjacency = graph._build_adjacency()
        for edge_type, targets in adjacency.items():
            if start_node in targets:
                results.append(edge_type)
        
        # Also get nodes the gate run links to
        for neighbor in graph.get_neighbors(start_node):
            results.append(neighbor.node_id)
        
        return results


def create_phase_loom(name: str, loom_id: Optional[str] = None) -> PhaseLoom:
    """Create new PhaseLoom."""
    return PhaseLoom(
        loom_id=loom_id or str(uuid4())[:8],
        name=name,
    )
