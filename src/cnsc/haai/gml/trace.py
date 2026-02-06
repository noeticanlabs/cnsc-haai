"""
GML Trace Model

Reasoning trace representation for the Coherence Framework.

This module provides:
- TraceEvent: Single trace event
- TraceThread: Thread of related events
- TraceManager: Trace collection and query
- TraceLevel: Event severity levels
- TraceQuery: Query interface
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, Tuple
from datetime import datetime
from uuid import uuid4


class TraceLevel(Enum):
    """Trace event severity levels."""
    DEBUG = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()
    
    def to_string(self) -> str:
        """Convert to string."""
        return {
            TraceLevel.DEBUG: "DEBUG",
            TraceLevel.INFO: "INFO",
            TraceLevel.WARNING: "WARNING",
            TraceLevel.ERROR: "ERROR",
            TraceLevel.CRITICAL: "CRITICAL",
        }.get(self, "UNKNOWN")


@dataclass
class TraceEvent:
    """
    Single trace event.
    
    Represents an atomic event in the reasoning trace.
    """
    event_id: str
    timestamp: datetime
    level: TraceLevel
    event_type: str
    
    # Content
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    
    # Causality
    parent_event_id: Optional[str] = None
    causality_chain: List[str] = field(default_factory=list)
    
    # Provenance
    source_module: Optional[str] = None
    source_function: Optional[str] = None
    source_line: Optional[int] = None
    
    # Threading
    thread_id: Optional[str] = None
    span_id: Optional[str] = None
    
    # Coherence
    coherence_before: Optional[float] = None
    coherence_after: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.to_string(),
            "event_type": self.event_type,
            "message": self.message,
            "details": self.details,
            "parent_event_id": self.parent_event_id,
            "causality_chain": self.causality_chain,
            "source_module": self.source_module,
            "source_function": self.source_function,
            "source_line": self.source_line,
            "thread_id": self.thread_id,
            "span_id": self.span_id,
            "coherence_before": self.coherence_before,
            "coherence_after": self.coherence_after,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TraceEvent':
        """Create from dictionary."""
        return cls(
            event_id=data["event_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.utcnow(),
            level=TraceLevel[data["level"]] if isinstance(data["level"], str) else TraceLevel(data["level"]),
            event_type=data["event_type"],
            message=data["message"],
            details=data.get("details", {}),
            parent_event_id=data.get("parent_event_id"),
            causality_chain=data.get("causality_chain", []),
            source_module=data.get("source_module"),
            source_function=data.get("source_function"),
            source_line=data.get("source_line"),
            thread_id=data.get("thread_id"),
            span_id=data.get("span_id"),
            coherence_before=data.get("coherence_before"),
            coherence_after=data.get("coherence_after"),
        )
    
    @classmethod
    def create(
        cls,
        level: TraceLevel,
        event_type: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        parent_event_id: Optional[str] = None,
        **kwargs,
    ) -> 'TraceEvent':
        """Factory method to create trace event."""
        event_id = str(uuid4())[:8]
        return cls(
            event_id=event_id,
            timestamp=datetime.utcnow(),
            level=level,
            event_type=event_type,
            message=message,
            details=details or {},
            parent_event_id=parent_event_id,
            **kwargs,
        )


@dataclass
class TraceThread:
    """
    Trace Thread.
    
    Thread of related trace events with ordering.
    """
    thread_id: str
    name: str
    events: List[TraceEvent] = field(default_factory=list)
    
    # Thread metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    parent_thread_id: Optional[str] = None
    child_thread_ids: List[str] = field(default_factory=list)
    
    # Status
    is_active: bool = True
    is_complete: bool = False
    
    def add_event(self, event: TraceEvent) -> None:
        """Add event to thread."""
        event.thread_id = self.thread_id
        self.events.append(event)
    
    def get_events_by_level(self, level: TraceLevel) -> List[TraceEvent]:
        """Get events by level."""
        return [e for e in self.events if e.level == level]
    
    def get_events_by_type(self, event_type: str) -> List[TraceEvent]:
        """Get events by type."""
        return [e for e in self.events if e.event_type == event_type]
    
    def get_causality_chain(self, event_id: str) -> List[TraceEvent]:
        """Get causality chain for an event."""
        for event in self.events:
            if event.event_id == event_id:
                chain = [event]
                current = event
                while current.parent_event_id:
                    for e in self.events:
                        if e.event_id == current.parent_event_id:
                            chain.insert(0, e)
                            current = e
                            break
                    else:
                        break
                return chain
        return []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "thread_id": self.thread_id,
            "name": self.name,
            "events": [e.to_dict() for e in self.events],
            "created_at": self.created_at.isoformat(),
            "parent_thread_id": self.parent_thread_id,
            "child_thread_ids": self.child_thread_ids,
            "is_active": self.is_active,
            "is_complete": self.is_complete,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TraceThread':
        """Create from dictionary."""
        return cls(
            thread_id=data["thread_id"],
            name=data["name"],
            events=[TraceEvent.from_dict(e) for e in data.get("events", [])],
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow(),
            parent_thread_id=data.get("parent_thread_id"),
            child_thread_ids=data.get("child_thread_ids", []),
            is_active=data.get("is_active", True),
            is_complete=data.get("is_complete", False),
        )


@dataclass
class TraceQuery:
    """
    Trace Query.
    
    Query interface for filtering and aggregating traces.
    """
    # Filters
    levels: List[TraceLevel] = field(default_factory=list)
    event_types: List[str] = field(default_factory=list)
    thread_ids: List[str] = field(default_factory=list)
    time_range: Optional[Tuple[datetime, datetime]] = None
    keyword: Optional[str] = None
    
    # Aggregation
    group_by: Optional[str] = None  # "level", "type", "thread"
    
    # Limits
    limit: Optional[int] = None
    offset: int = 0
    
    def match(self, event: TraceEvent) -> bool:
        """Check if event matches query."""
        # Level filter
        if self.levels and event.level not in self.levels:
            return False
        
        # Type filter
        if self.event_types and event.event_type not in self.event_types:
            return False
        
        # Thread filter
        if self.thread_ids and event.thread_id not in self.thread_ids:
            return False
        
        # Time range filter
        if self.time_range:
            start, end = self.time_range
            if not (start <= event.timestamp <= end):
                return False
        
        # Keyword filter
        if self.keyword:
            if self.keyword.lower() not in event.message.lower():
                return False
        
        return True
    
    def apply(self, events: List[TraceEvent]) -> List[TraceEvent]:
        """Apply query to events."""
        # Filter
        result = [e for e in events if self.match(e)]
        
        # Offset
        result = result[self.offset:]
        
        # Limit
        if self.limit:
            result = result[:self.limit]
        
        return result


@dataclass
class TraceManager:
    """
    Trace Manager.
    
    Central manager for trace collection and query.
    """
    manager_id: str = str(uuid4())[:8]
    name: str = "Trace Manager"
    
    # Thread storage
    threads: Dict[str, TraceThread] = field(default_factory=dict)
    
    # Event storage
    events: Dict[str, TraceEvent] = field(default_factory=dict)
    
    # Indexes
    events_by_type: Dict[str, List[str]] = field(default_factory=dict)
    events_by_level: Dict[str, List[str]] = field(default_factory=dict)
    events_by_thread: Dict[str, List[str]] = field(default_factory=dict)
    
    # Callbacks
    on_event_callbacks: List[Callable[[TraceEvent], None]] = field(default_factory=list)
    
    # Configuration
    max_events: int = 10000
    retention_days: int = 30
    
    def create_thread(self, name: str, thread_id: Optional[str] = None) -> TraceThread:
        """Create new trace thread."""
        tid = thread_id or str(uuid4())[:8]
        thread = TraceThread(thread_id=tid, name=name)
        self.threads[tid] = thread
        return thread
    
    def add_event(self, event: TraceEvent) -> None:
        """Add event to trace."""
        # Add to events
        self.events[event.event_id] = event
        
        # Add to thread
        if event.thread_id and event.thread_id in self.threads:
            self.threads[event.thread_id].add_event(event)
        
        # Update indexes
        if event.event_type not in self.events_by_type:
            self.events_by_type[event.event_type] = []
        self.events_by_type[event.event_type].append(event.event_id)
        
        level_key = event.level.to_string()
        if level_key not in self.events_by_level:
            self.events_by_level[level_key] = []
        self.events_by_level[level_key].append(event.event_id)
        
        if event.thread_id:
            if event.thread_id not in self.events_by_thread:
                self.events_by_thread[event.thread_id] = []
            self.events_by_thread[event.thread_id].append(event.event_id)
        
        # Check limits
        if len(self.events) > self.max_events:
            self._prune_old_events()
        
        # Call callbacks
        for callback in self.on_event_callbacks:
            callback(event)
    
    def query(self, query: TraceQuery) -> List[TraceEvent]:
        """Query events."""
        return query.apply(list(self.events.values()))
    
    def query_by_thread(self, thread_id: str, query: Optional[TraceQuery] = None) -> List[TraceEvent]:
        """Query events by thread."""
        event_ids = self.events_by_thread.get(thread_id, [])
        events = [self.events[eid] for eid in event_ids if eid in self.events]
        
        if query:
            return query.apply(events)
        return events
    
    def get_thread(self, thread_id: str) -> Optional[TraceThread]:
        """Get thread by ID."""
        return self.threads.get(thread_id)
    
    def get_active_threads(self) -> List[TraceThread]:
        """Get all active threads."""
        return [t for t in self.threads.values() if t.is_active]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get trace statistics."""
        level_counts = {k: len(v) for k, v in self.events_by_level.items()}
        type_counts = {k: len(v) for k, v in self.events_by_type.items()}
        
        return {
            "manager_id": self.manager_id,
            "name": self.name,
            "total_events": len(self.events),
            "total_threads": len(self.threads),
            "active_threads": len(self.get_active_threads()),
            "events_by_level": level_counts,
            "events_by_type": type_counts,
        }
    
    def on_event(self, callback: Callable[[TraceEvent], None]) -> None:
        """Register event callback."""
        self.on_event_callbacks.append(callback)
    
    def _prune_old_events(self) -> None:
        """Prune old events to stay within limit."""
        cutoff = datetime.utcnow()
        old_events = [
            eid for eid, event in self.events.items()
            if event.timestamp < cutoff
        ]
        
        # Remove oldest 10%
        to_remove = sorted(old_events, key=lambda eid: self.events[eid].timestamp)[:len(old_events) // 10]
        
        for eid in to_remove:
            event = self.events.pop(eid, None)
            if event:
                # Remove from indexes
                if event.event_type in self.events_by_type:
                    self.events_by_type[event.event_type] = [
                        x for x in self.events_by_type[event.event_type] if x != eid
                    ]
                level_key = event.level.to_string()
                if level_key in self.events_by_level:
                    self.events_by_level[level_key] = [
                        x for x in self.events_by_level[level_key] if x != eid
                    ]
                if event.thread_id in self.events_by_thread:
                    self.events_by_thread[event.thread_id] = [
                        x for x in self.events_by_thread[event.thread_id] if x != eid
                    ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "manager_id": self.manager_id,
            "name": self.name,
            "thread_count": len(self.threads),
            "event_count": len(self.events),
            "events_by_level": {k: len(v) for k, v in self.events_by_level.items()},
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TraceManager':
        """Create from dictionary."""
        return cls(
            manager_id=data.get("manager_id", str(uuid4())[:8]),
            name=data.get("name", "Trace Manager"),
        )


def create_trace_manager(name: str = "Trace Manager") -> TraceManager:
    """Create new trace manager."""
    return TraceManager(name=name)
