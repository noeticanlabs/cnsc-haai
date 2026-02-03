"""
GML (Glyph Memory Language) Aeonica Implementation

Implements PhaseLoom threads, temporal coupling, and memory management
for the Noetic ecosystem integration.
"""

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta
import uuid


class ThreadState(Enum):
    """States of PhaseLoom threads."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    COMPLETED = "completed"
    ERROR = "error"


class CouplingType(Enum):
    """Types of temporal coupling."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CAUSAL = "causal"
    CORRELATIONAL = "correlational"


@dataclass
class PhaseLoomThread:
    """Represents a PhaseLoom thread for temporal memory management."""
    thread_id: str
    name: str
    created_at: datetime
    state: ThreadState = ThreadState.ACTIVE
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent_thread: Optional[str] = None
    child_threads: List[str] = field(default_factory=list)
    temporal_position: float = 0.0
    coherence_score: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert thread to dictionary."""
        return {
            "thread_id": self.thread_id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "state": self.state.value,
            "data": self.data,
            "metadata": self.metadata,
            "parent_thread": self.parent_thread,
            "child_threads": self.child_threads,
            "temporal_position": self.temporal_position,
            "coherence_score": self.coherence_score
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PhaseLoomThread":
        """Create thread from dictionary."""
        return cls(
            thread_id=data["thread_id"],
            name=data["name"],
            created_at=datetime.fromisoformat(data["created_at"]),
            state=ThreadState(data["state"]),
            data=data.get("data", {}),
            metadata=data.get("metadata", {}),
            parent_thread=data.get("parent_thread"),
            child_threads=data.get("child_threads", []),
            temporal_position=data.get("temporal_position", 0.0),
            coherence_score=data.get("coherence_score", 1.0)
        )


@dataclass
class TemporalCoupling:
    """Represents temporal coupling between threads."""
    coupling_id: str
    thread_a: str
    thread_b: str
    coupling_type: CouplingType
    strength: float
    created_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert coupling to dictionary."""
        return {
            "coupling_id": self.coupling_id,
            "thread_a": self.thread_a,
            "thread_b": self.thread_b,
            "coupling_type": self.coupling_type.value,
            "strength": self.strength,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TemporalCoupling":
        """Create coupling from dictionary."""
        return cls(
            coupling_id=data["coupling_id"],
            thread_a=data["thread_a"],
            thread_b=data["thread_b"],
            coupling_type=CouplingType(data["coupling_type"]),
            strength=data["strength"],
            created_at=datetime.fromisoformat(data["created_at"]),
            metadata=data.get("metadata", {})
        )


class GMLMemory:
    """Main GML memory system for managing PhaseLoom threads and temporal coupling."""
    
    def __init__(self):
        self.logger = logging.getLogger("haai.gml_memory")
        
        # Thread management
        self.threads: Dict[str, PhaseLoomThread] = {}
        self.thread_hierarchy: Dict[str, List[str]] = {}  # parent -> children
        
        # Coupling management
        self.couplings: Dict[str, TemporalCoupling] = {}
        self.thread_couplings: Dict[str, List[str]] = {}  # thread_id -> coupling_ids
        
        # Memory state
        self.current_temporal_position: float = 0.0
        self.memory_size_limit: int = 10000
        self.is_initialized: bool = False
        
        # Performance tracking
        self.access_patterns: Dict[str, List[datetime]] = {}
        self.coherence_history: List[float] = []
        
    async def initialize(self) -> None:
        """Initialize the GML memory system."""
        if self.is_initialized:
            return
        
        # Create root thread
        root_thread = PhaseLoomThread(
            thread_id="root",
            name="Root Thread",
            created_at=datetime.now(),
            state=ThreadState.ACTIVE,
            data={"type": "root", "level": 0}
        )
        
        self.threads["root"] = root_thread
        self.thread_hierarchy["root"] = []
        
        self.is_initialized = True
        self.logger.info("GML Memory system initialized")
    
    async def create_thread(self, name: str, data: Optional[Dict[str, Any]] = None,
                          parent_thread: Optional[str] = None) -> str:
        """Create a new PhaseLoom thread."""
        thread_id = str(uuid.uuid4())
        
        thread = PhaseLoomThread(
            thread_id=thread_id,
            name=name,
            created_at=datetime.now(),
            data=data or {},
            parent_thread=parent_thread
        )
        
        # Set temporal position
        if parent_thread and parent_thread in self.threads:
            parent = self.threads[parent_thread]
            thread.temporal_position = parent.temporal_position + 1.0
            parent.child_threads.append(thread_id)
            self.thread_hierarchy[parent_thread].append(thread_id)
        else:
            thread.temporal_position = self.current_temporal_position + 1.0
            self.current_temporal_position = thread.temporal_position
        
        # Register thread
        self.threads[thread_id] = thread
        self.thread_hierarchy[thread_id] = []
        self.access_patterns[thread_id] = [datetime.now()]
        
        self.logger.info(f"Created thread: {thread_id} ({name})")
        return thread_id
    
    async def get_thread(self, thread_id: str) -> Optional[PhaseLoomThread]:
        """Get a thread by ID."""
        if thread_id in self.threads:
            # Update access pattern
            if thread_id not in self.access_patterns:
                self.access_patterns[thread_id] = []
            self.access_patterns[thread_id].append(datetime.now())
            
            # Keep access history manageable
            if len(self.access_patterns[thread_id]) > 100:
                self.access_patterns[thread_id].pop(0)
            
            return self.threads[thread_id]
        
        return None
    
    async def update_thread(self, thread_id: str, data: Dict[str, Any],
                          metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Update thread data and metadata."""
        if thread_id not in self.threads:
            return False
        
        thread = self.threads[thread_id]
        thread.data.update(data)
        
        if metadata:
            thread.metadata.update(metadata)
        
        # Update access pattern
        if thread_id not in self.access_patterns:
            self.access_patterns[thread_id] = []
        self.access_patterns[thread_id].append(datetime.now())
        
        return True
    
    async def delete_thread(self, thread_id: str) -> bool:
        """Delete a thread and its couplings."""
        if thread_id not in self.threads:
            return False
        
        # Remove child threads first
        child_threads = self.threads[thread_id].child_threads.copy()
        for child_id in child_threads:
            await self.delete_thread(child_id)
        
        # Remove couplings
        coupling_ids = self.thread_couplings.get(thread_id, []).copy()
        for coupling_id in coupling_ids:
            await self.delete_coupling(coupling_id)
        
        # Remove from parent
        thread = self.threads[thread_id]
        if thread.parent_thread and thread.parent_thread in self.threads:
            parent = self.threads[thread.parent_thread]
            if thread_id in parent.child_threads:
                parent.child_threads.remove(thread_id)
            if thread_id in self.thread_hierarchy[thread.parent_thread]:
                self.thread_hierarchy[thread.parent_thread].remove(thread_id)
        
        # Remove thread
        del self.threads[thread_id]
        del self.thread_hierarchy[thread_id]
        
        if thread_id in self.access_patterns:
            del self.access_patterns[thread_id]
        
        self.logger.info(f"Deleted thread: {thread_id}")
        return True
    
    async def create_coupling(self, thread_a: str, thread_b: str,
                            coupling_type: CouplingType, strength: float,
                            metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create temporal coupling between threads."""
        if thread_a not in self.threads or thread_b not in self.threads:
            raise ValueError("Both threads must exist to create coupling")
        
        coupling_id = str(uuid.uuid4())
        
        coupling = TemporalCoupling(
            coupling_id=coupling_id,
            thread_a=thread_a,
            thread_b=thread_b,
            coupling_type=coupling_type,
            strength=max(0.0, min(1.0, strength)),
            created_at=datetime.now(),
            metadata=metadata or {}
        )
        
        # Register coupling
        self.couplings[coupling_id] = coupling
        
        # Update thread coupling mappings
        if thread_a not in self.thread_couplings:
            self.thread_couplings[thread_a] = []
        if thread_b not in self.thread_couplings:
            self.thread_couplings[thread_b] = []
        
        self.thread_couplings[thread_a].append(coupling_id)
        self.thread_couplings[thread_b].append(coupling_id)
        
        self.logger.info(f"Created coupling: {coupling_id} between {thread_a} and {thread_b}")
        return coupling_id
    
    async def get_coupling(self, coupling_id: str) -> Optional[TemporalCoupling]:
        """Get a coupling by ID."""
        return self.couplings.get(coupling_id)
    
    async def delete_coupling(self, coupling_id: str) -> bool:
        """Delete a temporal coupling."""
        if coupling_id not in self.couplings:
            return False
        
        coupling = self.couplings[coupling_id]
        
        # Remove from thread coupling mappings
        if coupling.thread_a in self.thread_couplings:
            if coupling_id in self.thread_couplings[coupling.thread_a]:
                self.thread_couplings[coupling.thread_a].remove(coupling_id)
        
        if coupling.thread_b in self.thread_couplings:
            if coupling_id in self.thread_couplings[coupling.thread_b]:
                self.thread_couplings[coupling.thread_b].remove(coupling_id)
        
        # Remove coupling
        del self.couplings[coupling_id]
        
        self.logger.info(f"Deleted coupling: {coupling_id}")
        return True
    
    async def find_related_threads(self, thread_id: str, 
                                max_depth: int = 3) -> List[str]:
        """Find threads related through couplings."""
        if thread_id not in self.threads:
            return []
        
        related = set()
        visited = set()
        queue = [(thread_id, 0)]
        
        while queue:
            current_id, depth = queue.pop(0)
            
            if current_id in visited or depth > max_depth:
                continue
            
            visited.add(current_id)
            
            # Get couplings for current thread
            coupling_ids = self.thread_couplings.get(current_id, [])
            
            for coupling_id in coupling_ids:
                if coupling_id in self.couplings:
                    coupling = self.couplings[coupling_id]
                    
                    # Add the other thread in the coupling
                    other_id = coupling.thread_b if coupling.thread_a == current_id else coupling.thread_a
                    
                    if other_id not in visited:
                        related.add(other_id)
                        queue.append((other_id, depth + 1))
        
        return list(related)
    
    async def calculate_coherence(self, thread_id: str) -> float:
        """Calculate coherence score for a thread."""
        if thread_id not in self.threads:
            return 0.0
        
        thread = self.threads[thread_id]
        
        # Base coherence from thread state
        coherence = 1.0
        
        if thread.state == ThreadState.ERROR:
            coherence *= 0.5
        elif thread.state == ThreadState.SUSPENDED:
            coherence *= 0.8
        
        # Coherence from couplings
        coupling_ids = self.thread_couplings.get(thread_id, [])
        if coupling_ids:
            coupling_strengths = []
            for coupling_id in coupling_ids:
                if coupling_id in self.couplings:
                    coupling = self.couplings[coupling_id]
                    coupling_strengths.append(coupling.strength)
            
            if coupling_strengths:
                avg_coupling_strength = sum(coupling_strengths) / len(coupling_strengths)
                coherence *= (0.5 + 0.5 * avg_coupling_strength)
        
        # Update thread coherence
        thread.coherence_score = coherence
        self.coherence_history.append(coherence)
        
        # Keep history manageable
        if len(self.coherence_history) > 1000:
            self.coherence_history.pop(0)
        
        return coherence
    
    async def get_memory_statistics(self) -> Dict[str, Any]:
        """Get memory system statistics."""
        thread_states = {}
        for thread in self.threads.values():
            state = thread.state.value
            thread_states[state] = thread_states.get(state, 0) + 1
        
        coupling_types = {}
        for coupling in self.couplings.values():
            coupling_type = coupling.coupling_type.value
            coupling_types[coupling_type] = coupling_types.get(coupling_type, 0) + 1
        
        avg_coherence = sum(self.coherence_history) / len(self.coherence_history) if self.coherence_history else 0.0
        
        return {
            "total_threads": len(self.threads),
            "thread_states": thread_states,
            "total_couplings": len(self.couplings),
            "coupling_types": coupling_types,
            "current_temporal_position": self.current_temporal_position,
            "average_coherence": avg_coherence,
            "memory_utilization": len(self.threads) / self.memory_size_limit,
            "access_patterns": {
                thread_id: len(accesses)
                for thread_id, accesses in self.access_patterns.items()
            }
        }
    
    async def cleanup_old_threads(self, max_age_days: int = 30) -> int:
        """Clean up old threads to manage memory usage."""
        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        threads_to_delete = []
        
        for thread_id, thread in self.threads.items():
            if (thread.created_at < cutoff_time and 
                thread.state == ThreadState.COMPLETED and
                thread_id != "root"):
                threads_to_delete.append(thread_id)
        
        deleted_count = 0
        for thread_id in threads_to_delete:
            if await self.delete_thread(thread_id):
                deleted_count += 1
        
        self.logger.info(f"Cleaned up {deleted_count} old threads")
        return deleted_count
    
    async def export_memory(self, filepath: str) -> None:
        """Export memory state to file using atomic write."""
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "threads": [thread.to_dict() for thread in self.threads.values()],
            "couplings": [coupling.to_dict() for coupling in self.couplings.values()],
            "current_temporal_position": self.current_temporal_position,
            "coherence_history": self.coherence_history[-100:]  # Last 100 entries
        }
        
        # Atomic write using temp file + rename
        temp_filepath = f"{filepath}.tmp.{os.getpid()}"
        try:
            with open(temp_filepath, 'w') as f:
                json.dump(export_data, f, indent=2)
            # Atomic rename on POSIX systems
            os.replace(temp_filepath, filepath)
            self.logger.info(f"Memory exported to {filepath}")
        except Exception as e:
            # Clean up temp file on failure
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)
            self.logger.error(f"Failed to export memory: {e}")
            raise
    
    async def import_memory(self, filepath: str) -> None:
        """Import memory state from file."""
        with open(filepath, 'r') as f:
            import_data = json.load(f)
        
        # Clear existing memory (except root)
        root_thread = self.threads.get("root")
        self.threads.clear()
        self.couplings.clear()
        self.thread_hierarchy.clear()
        self.thread_couplings.clear()
        
        if root_thread:
            self.threads["root"] = root_thread
            self.thread_hierarchy["root"] = []
        
        # Import threads
        for thread_data in import_data.get("threads", []):
            thread = PhaseLoomThread.from_dict(thread_data)
            self.threads[thread.thread_id] = thread
            self.thread_hierarchy[thread.thread_id] = thread.child_threads
        
        # Import couplings
        for coupling_data in import_data.get("couplings", []):
            coupling = TemporalCoupling.from_dict(coupling_data)
            self.couplings[coupling.coupling_id] = coupling
            
            # Update thread coupling mappings
            if coupling.thread_a not in self.thread_couplings:
                self.thread_couplings[coupling.thread_a] = []
            if coupling.thread_b not in self.thread_couplings:
                self.thread_couplings[coupling.thread_b] = []
            
            self.thread_couplings[coupling.thread_a].append(coupling.coupling_id)
            self.thread_couplings[coupling.thread_b].append(coupling.coupling_id)
        
        # Import state
        self.current_temporal_position = import_data.get("current_temporal_position", 0.0)
        self.coherence_history = import_data.get("coherence_history", [])
        
        self.logger.info(f"Memory imported from {filepath}")
    
    async def shutdown(self) -> None:
        """Shutdown the GML memory system."""
        # Save state before shutdown
        await self.export_memory("gml_memory_backup.json")
        
        # Clear memory
        self.threads.clear()
        self.couplings.clear()
        self.thread_hierarchy.clear()
        self.thread_couplings.clear()
        self.access_patterns.clear()
        self.coherence_history.clear()
        
        self.is_initialized = False
        self.logger.info("GML Memory system shutdown complete")