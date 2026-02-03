# HAAI System Completeness Gap Resolution Plan

## Executive Summary

This plan addresses the remaining ~12% of system gaps identified during the completeness review. The focus areas are:
- CI/CD Pipeline Configuration
- Docker Development Environment
- Database Integration for Audit/Evidence
- Distributed Computing Framework
- Schema Versioning and Migration

---

## Gap 1: CI/CD Pipeline Configuration

### 1.1 Create GitHub Actions Workflow
**File**: `.github/workflows/ci-cd.yml`

```yaml
name: HAAI CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          python -m pytest tests/ -v --cov=src/haai --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml
```

### 1.2 Implementation Tasks
- [ ] Create `.github/workflows/` directory
- [ ] Add `ci-cd.yml` with test, lint, coverage steps
- [ ] Add `release.yml` for semantic versioning releases
- [ ] Add `security-scan.yml` for vulnerability scanning
- [ ] Configure pytest-cov for coverage reporting
- [ ] Add pre-commit hooks configuration

**Estimated Effort**: 2-3 hours

---

## Gap 2: Docker Development Environment

### 2.1 Create Docker Configuration Files

**File**: `Dockerfile`
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/

# Set environment variables
ENV PYTHONPATH=/app
ENV HAAI_ENV=production

# Default command
CMD ["python", "-m", "pytest", "tests/", "-v"]
```

**File**: `docker-compose.yml`
```yaml
version: '3.8'

services:
  haai:
    build: .
    ports:
      - "8000:8000"
    environment:
      - HAAI_ENV=development
      - HAAI_LOG_LEVEL=DEBUG
    volumes:
      - ./src:/app/src
      - ./tests:/app/tests
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: haai_audit
      POSTGRES_USER: haai_user
      POSTGRES_PASSWORD: ${DB_PASSWORD:-haai_secret}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

**File**: `.dockerignore`
```
.git
__pycache__
*.pyc
.pytest_cache
.env
venv/
docs/
CGL_Doc_Spine/
Noetica_Ecosystem_Bundle_v1/
NSC_Caelus_AI_Package_v1/
*.md
```

### 2.2 Implementation Tasks
- [ ] Create `Dockerfile` with Python 3.11 slim image
- [ ] Create `docker-compose.yml` with PostgreSQL and Redis
- [ ] Create `.dockerignore` file
- [ ] Create `docker-entrypoint.sh` for initialization
- [ ] Update `README.md` with Docker instructions
- [ ] Add `.env.example` template

**Estimated Effort**: 3-4 hours

---

## Gap 3: Database Integration for Audit/Evidence

### 3.1 Create Database Abstraction Layer

**File**: `src/haai/core/database.py`
```python
"""
Database abstraction layer for HAAI audit and evidence storage.
Supports PostgreSQL, SQLite (for development), and optional cloud DBs.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from contextlib import contextmanager
import json
import logging

logger = logging.getLogger(__name__)


class DatabaseBackend(ABC):
    """Abstract base class for database backends."""
    
    @abstractmethod
    def connect(self) -> None:
        """Establish database connection."""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Close database connection."""
        pass
    
    @abstractmethod
    def execute(self, query: str, params: tuple) -> List[Dict]:
        """Execute a query and return results."""
        pass
    
    @abstractmethod
    def execute_many(self, query: str, params_list: List[tuple]) -> None:
        """Execute a query with multiple parameter sets."""
        pass


class PostgreSQLBackend(DatabaseBackend):
    """PostgreSQL database backend."""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.connection = None
    
    def connect(self) -> None:
        import psycopg2
        self.connection = psycopg2.connect(self.connection_string)
    
    def disconnect(self) -> None:
        if self.connection:
            self.connection.close()
    
    def execute(self, query: str, params: tuple) -> List[Dict]:
        # Implementation
        pass
    
    def execute_many(self, query: str, params_list: List[tuple]) -> None:
        # Implementation
        pass


class SQLiteBackend(DatabaseBackend):
    """SQLite database backend for development."""
    
    def __init__(self, db_path: str = "haai_audit.db"):
        self.db_path = db_path
        self.connection = None
    
    def connect(self) -> None:
        import sqlite3
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
    
    def disconnect(self) -> None:
        if self.connection:
            self.connection.close()
    
    def execute(self, query: str, params: tuple) -> List[Dict]:
        cursor = self.connection.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def execute_many(self, query: str, params_list: List[tuple]) -> None:
        cursor = self.connection.cursor()
        cursor.executemany(query, params_list)
        self.connection.commit()


class DatabaseManager:
    """Manages database connections and operations."""
    
    def __init__(self, backend: DatabaseBackend = None):
        self.backend = backend or SQLiteBackend()
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize database schema."""
        if self._initialized:
            return
        
        self.backend.connect()
        self._create_schema()
        self._initialized = True
    
    def _create_schema(self) -> None:
        """Create database tables."""
        schema = """
        CREATE TABLE IF NOT EXISTS audit_events (
            id SERIAL PRIMARY KEY,
            event_type VARCHAR(100) NOT NULL,
            agent_id VARCHAR(100),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data JSONB NOT NULL,
            coherence_score FLOAT,
            policy_violations JSONB
        );
        
        CREATE TABLE IF NOT EXISTS audit_receipts (
            id SERIAL PRIMARY KEY,
            receipt_id VARCHAR(100) UNIQUE NOT NULL,
            event_id INTEGER REFERENCES audit_events(id),
            signature VARCHAR(500),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB
        );
        
        CREATE TABLE IF NOT EXISTS coherence_signals (
            id SERIAL PRIMARY KEY,
            agent_id VARCHAR(100),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            coherence_measure FLOAT,
            phase_variance FLOAT,
            gradient_norm FLOAT,
            spectral_peak_ratio FLOAT,
            injection_rate FLOAT,
            raw_signals JSONB
        );
        
        CREATE INDEX IF NOT EXISTS idx_audit_events_timestamp 
            ON audit_events(timestamp);
        CREATE INDEX IF NOT EXISTS idx_audit_events_agent 
            ON audit_events(agent_id);
        CREATE INDEX IF NOT EXISTS idx_coherence_signals_timestamp 
            ON coherence_signals(timestamp);
        """
        self.backend.execute(schema, ())
    
    @contextmanager
    def transaction(self):
        """Context manager for database transactions."""
        try:
            yield self
            self.backend.connection.commit()
        except Exception as e:
            self.backend.connection.rollback()
            raise
    
    def store_audit_event(self, event_type: str, agent_id: str, 
                          data: Dict, coherence_score: float = None,
                          policy_violations: List = None) -> int:
        """Store an audit event and return its ID."""
        query = """
        INSERT INTO audit_events (event_type, agent_id, data, coherence_score, policy_violations)
        VALUES (%s, %s, %s, %s, %s) RETURNING id
        """
        result = self.backend.execute(query, (
            event_type, agent_id, json.dumps(data), 
            coherence_score, json.dumps(policy_violations) if policy_violations else None
        ))
        return result[0]['id'] if result else None
    
    def store_coherence_signals(self, agent_id: str, signals: Dict) -> None:
        """Store coherence signal measurements."""
        query = """
        INSERT INTO coherence_signals 
            (agent_id, coherence_measure, phase_variance, gradient_norm, 
             spectral_peak_ratio, injection_rate, raw_signals)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        self.backend.execute(query, (
            agent_id, 
            signals.get('coherence_measure'),
            signals.get('phase_variance'),
            signals.get('gradient_norm'),
            signals.get('spectral_peak_ratio'),
            signals.get('injection_rate'),
            json.dumps(signals)
        ))
    
    def query_audit_events(self, agent_id: str = None, 
                           start_time: datetime = None,
                           end_time: datetime = None,
                           limit: int = 100) -> List[Dict]:
        """Query audit events with optional filters."""
        query = "SELECT * FROM audit_events WHERE 1=1"
        params = []
        
        if agent_id:
            query += " AND agent_id = %s"
            params.append(agent_id)
        if start_time:
            query += " AND timestamp >= %s"
            params.append(start_time)
        if end_time:
            query += " AND timestamp <= %s"
            params.append(end_time)
        
        query += " ORDER BY timestamp DESC LIMIT %s"
        params.append(limit)
        
        return self.backend.execute(query, tuple(params))
    
    def shutdown(self) -> None:
        """Shutdown database manager."""
        if self._initialized:
            self.backend.disconnect()
            self._initialized = False
```

### 3.2 Update Audit Evidence System

**File**: `src/haai/governance/audit_evidence.py` modifications
```python
# Add database integration
from ..core.database import DatabaseManager, SQLiteBackend

class AuditEvidenceSystem:
    def __init__(self, use_database: bool = False, db_backend=None):
        self.use_database = use_database
        if use_database:
            self.db_manager = DatabaseManager(db_backend or SQLiteBackend())
            self.db_manager.initialize()
        else:
            self.db_manager = None
        # Keep existing file-based storage as fallback
        self._initialize_file_storage()
    
    def store_audit_event(self, event_type: str, agent_id: str,
                          data: Dict, coherence_score: float = None,
                          policy_violations: List = None) -> str:
        # If database is enabled, store to DB
        if self.use_database and self.db_manager:
            event_id = self.db_manager.store_audit_event(
                event_type, agent_id, data, coherence_score, policy_violations
            )
            return f"db:{event_id}"
        
        # Fallback to file storage
        return self._store_to_file(event_type, agent_id, data, coherence_score, policy_violations)
```

### 3.3 Implementation Tasks
- [ ] Create `src/haai/core/database.py` with DatabaseBackend ABC
- [ ] Implement SQLiteBackend for development
- [ ] Implement PostgreSQLBackend for production
- [ ] Create DatabaseManager with schema initialization
- [ ] Update `src/haai/governance/audit_evidence.py` to use database
- [ ] Add database configuration to `config/default.yaml`
- [ ] Create migration scripts for schema updates
- [ ] Add connection pooling for PostgreSQL
- [ ] Write unit tests for database layer

**Estimated Effort**: 8-10 hours

---

## Gap 4: Distributed Computing Framework

### 4.1 Create Distributed Message Bus

**File**: `src/haai/core/distributed.py`
```python
"""
Distributed computing framework for HAAI.
Provides message passing, task distribution, and coordination.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import json
import logging
import uuid
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


class MessagePriority(Enum):
    """Message priority levels."""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


@dataclass
class Message:
    """Distributed message."""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    priority: MessagePriority = MessagePriority.NORMAL
    sender: str = ""
    recipient: str = ""
    topic: str = ""
    payload: Dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    
    def to_bytes(self) -> bytes:
        return json.dumps({
            'message_id': self.message_id,
            'priority': self.priority.value,
            'sender': self.sender,
            'recipient': self.recipient,
            'topic': self.topic,
            'payload': self.payload,
            'timestamp': self.timestamp.isoformat(),
            'correlation_id': self.correlation_id,
            'reply_to': self.reply_to
        }).encode()
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'Message':
        parsed = json.loads(data.decode())
        return cls(
            message_id=parsed['message_id'],
            priority=MessagePriority(parsed['priority']),
            sender=parsed['sender'],
            recipient=parsed['recipient'],
            topic=parsed['topic'],
            payload=parsed['payload'],
            timestamp=datetime.fromisoformat(parsed['timestamp']),
            correlation_id=parsed.get('correlation_id'),
            reply_to=parsed.get('reply_to')
        )


class MessageBus(ABC):
    """Abstract message bus for distributed communication."""
    
    @abstractmethod
    async def publish(self, message: Message) -> None:
        """Publish a message to the bus."""
        pass
    
    @abstractmethod
    async def subscribe(self, topic: str, handler: Callable) -> str:
        """Subscribe to a topic and return subscription ID."""
        pass
    
    @abstractmethod
    async def unsubscribe(self, subscription_id: str) -> None:
        """Unsubscribe from a topic."""
        pass
    
    @abstractmethod
    async def request(self, message: Message, timeout: float = 5.0) -> Message:
        """Send a request and wait for response."""
        pass


class InMemoryMessageBus(MessageBus):
    """In-memory message bus for single-node部署."""
    
    def __init__(self):
        self._subscriptions: Dict[str, List[Callable]] = {}
        self._queues: Dict[MessagePriority, asyncio.Queue] = {
            priority: asyncio.Queue() for priority in MessagePriority
        }
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
        self._response_futures: Dict[str, asyncio.Future] = {}
    
    async def start(self) -> None:
        """Start the message bus worker."""
        if self._running:
            return
        
        self._running = True
        self._worker_task = asyncio.create_task(self._worker())
        logger.info("InMemoryMessageBus started")
    
    async def stop(self) -> None:
        """Stop the message bus."""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("InMemoryMessageBus stopped")
    
    async def _worker(self) -> None:
        """Process messages from queues."""
        while self._running:
            try:
                # Process in priority order
                for priority in MessagePriority:
                    queue = self._queues[priority]
                    try:
                        message = await asyncio.wait_for(
                            queue.get(), timeout=0.1
                        )
                        await self._dispatch(message)
                    except asyncio.TimeoutError:
                        continue
            except Exception as e:
                logger.error(f"Message bus worker error: {e}")
    
    async def _dispatch(self, message: Message) -> None:
        """Dispatch message to handlers."""
        handlers = self._subscriptions.get(message.topic, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message)
                else:
                    handler(message)
            except Exception as e:
                logger.error(f"Handler error for topic {message.topic}: {e}")
        
        # Handle reply-to
        if message.reply_to and message.correlation_id:
            future = self._response_futures.pop(message.correlation_id, None)
            if future and not future.done():
                future.set_result(message)
    
    async def publish(self, message: Message) -> None:
        """Publish a message to the appropriate queue."""
        await self._queues[message.priority].put(message)
    
    async def subscribe(self, topic: str, handler: Callable) -> str:
        """Subscribe to a topic."""
        sub_id = str(uuid.uuid4())
        if topic not in self._subscriptions:
            self._subscriptions[topic] = []
        self._subscriptions[topic].append(handler)
        logger.info(f"Subscribed to topic: {topic}")
        return sub_id
    
    async def unsubscribe(self, subscription_id: str) -> None:
        # Note: This is a simplified implementation
        # In production, you'd track subscription IDs more carefully
        logger.info(f"Unsubscribed: {subscription_id}")
    
    async def request(self, message: Message, timeout: float = 5.0) -> Message:
        """Send a request and wait for response."""
        if not message.correlation_id:
            message.correlation_id = str(uuid.uuid4())
        
        future = asyncio.Future()
        self._response_futures[message.correlation_id] = future
        
        await self.publish(message)
        
        try:
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            raise TimeoutError(f"Request timed out after {timeout}s")


class DistributedCoordinator:
    """Coordinates distributed HAAI agents."""
    
    def __init__(self, message_bus: MessageBus = None):
        self.message_bus = message_bus or InMemoryMessageBus()
        self.agent_id = f"coordinator-{uuid.uuid4().hex[:8]}"
        self._subscriptions: List[str] = []
    
    async def initialize(self) -> None:
        """Initialize the coordinator."""
        await self.message_bus.start()
        
        # Subscribe to system topics
        self._subscriptions.append(
            await self.message_bus.subscribe("haai/coherence", self._handle_coherence)
        )
        self._subscriptions.append(
            await self.message_bus.subscribe("haai/agent/status", self._handle_status)
        )
        
        logger.info(f"DistributedCoordinator initialized: {self.agent_id}")
    
    async def shutdown(self) -> None:
        """Shutdown the coordinator."""
        for sub_id in self._subscriptions:
            await self.message_bus.unsubscribe(sub_id)
        await self.message_bus.stop()
    
    async def _handle_coherence(self, message: Message) -> None:
        """Handle coherence signals from agents."""
        logger.info(f"Received coherence update from {message.sender}")
        # Process coherence data
    
    async def _handle_status(self, message: Message) -> None:
        """Handle agent status updates."""
        logger.info(f"Received status from {message.sender}")
        # Process status update
    
    async def broadcast_coherence_threshold(
        self, agent_id: str, threshold: float
    ) -> None:
        """Broadcast coherence threshold to all agents."""
        message = Message(
            sender=self.agent_id,
            topic="haai/coherence/threshold",
            payload={'agent_id': agent_id, 'threshold': threshold}
        )
        await self.message_bus.publish(message)
    
    async def request_agent_status(self, agent_id: str, timeout: float = 5.0) -> Dict:
        """Request status from a specific agent."""
        message = Message(
            sender=self.agent_id,
            recipient=agent_id,
            topic="haai/agent/status/request",
            payload={},
            reply_to=self.agent_id
        )
        response = await self.message_bus.request(message, timeout)
        return response.payload
```

### 4.2 Create Task Distribution System

**File**: `src/haai/core/task_distribution.py`
```python
"""
Task distribution system for distributed HAAI computation.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import asyncio
import logging

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels."""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


@dataclass
class Task:
    """Distributed task."""
    task_id: str
    name: str
    payload: Dict[str, Any]
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent: Optional[str] = None
    result: Any = None
    error: Optional[str] = None
    created_at: float = field(default_factory=lambda: __import__('time').time())
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


class TaskScheduler:
    """Distributes tasks across available agents."""
    
    def __init__(self, message_bus=None):
        self.message_bus = message_bus
        self.tasks: Dict[str, Task] = {}
        self.agent_capacity: Dict[str, int] = {}
        self._task_queue: asyncio.Queue = asyncio.Queue()
    
    async def submit_task(self, task: Task) -> str:
        """Submit a task for execution."""
        self.tasks[task.task_id] = task
        await self._task_queue.put(task)
        logger.info(f"Task submitted: {task.task_id}")
        return task.task_id
    
    async def get_task_result(self, task_id: str, timeout: float = None) -> Any:
        """Get the result of a task."""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        
        # Wait for task completion
        while task.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            await asyncio.sleep(0.1)
            if timeout:
                # Check timeout
                pass
        
        if task.status == TaskStatus.FAILED:
            raise RuntimeError(task.error)
        
        return task.result
    
    async def _process_tasks(self) -> None:
        """Process tasks from the queue."""
        while True:
            task = await self._task_queue.get()
            await self._execute_task(task)
    
    async def _execute_task(self, task: Task) -> None:
        """Execute a task on an available agent."""
        task.status = TaskStatus.RUNNING
        task.started_at = __import__('time').time()
        
        try:
            # Find available agent
            agent_id = await self._find_available_agent()
            if agent_id:
                task.assigned_agent = agent_id
                result = await self._send_to_agent(agent_id, task)
                task.result = result
                task.status = TaskStatus.COMPLETED
            else:
                # Requeue for later
                await self._task_queue.put(task)
        except Exception as e:
            task.error = str(e)
            task.status = TaskStatus.FAILED
        finally:
            task.completed_at = __import__('time').time()
    
    async def _find_available_agent(self) -> Optional[str]:
        """Find an agent with available capacity."""
        for agent_id, capacity in self.agent_capacity.items():
            if capacity > 0:
                return agent_id
        return None
    
    async def _send_to_agent(self, agent_id: str, task: Task) -> Any:
        """Send task to agent for execution."""
        message = Message(
            sender="scheduler",
            recipient=agent_id,
            topic="haai/task/execute",
            payload={'task_id': task.task_id, 'payload': task.payload}
        )
        response = await self.message_bus.request(message, timeout=60.0)
        return response.payload.get('result')
```

### 4.3 Implementation Tasks
- [ ] Create `src/haai/core/distributed.py` with MessageBus ABC
- [ ] Implement InMemoryMessageBus for single-node
- [ ] Implement RedisMessageBus for multi-node (optional)
- [ ] Create DistributedCoordinator for agent coordination
- [ ] Create `src/haai/core/task_distribution.py` with TaskScheduler
- [ ] Add task distribution to agent core
- [ ] Write unit tests for distributed components
- [ ] Add integration tests for multi-agent scenarios

**Estimated Effort**: 10-12 hours

---

## Gap 5: Schema Versioning and Migration

### 5.1 Create Schema Registry

**File**: `src/haai/core/schema_registry.py`
```python
"""
Schema versioning and migration framework for HAAI.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
import hashlib
from datetime import datetime

logger = logging.getLogger(__name__)


class SchemaVersion:
    """Represents a schema version."""
    
    def __init__(self, major: int, minor: int, patch: int):
        self.major = major
        self.minor = minor
        self.patch = patch
    
    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{patch}"
    
    def __lt__(self, other: 'SchemaVersion') -> bool:
        if self.major != other.major:
            return self.major < other.major
        if self.minor != other.minor:
            return self.minor < other.minor
        return self.patch < other.patch
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SchemaVersion):
            return False
        return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)
    
    def to_tuple(self) -> tuple:
        return (self.major, self.minor, self.patch)


class SchemaType(Enum):
    """Types of schemas."""
    COHERENCE_SIGNALS = "coherence_signals"
    AUDIT_EVENT = "audit_event"
    NSC_PACKET = "nsc_packet"
    POLICY = "policy"
    RECEIPT = "receipt"
    AGENT_STATE = "agent_state"


@dataclass
class SchemaDefinition:
    """Definition of a schema version."""
    schema_type: SchemaType
    version: SchemaVersion
    definition: Dict[str, Any]
    checksum: str
    created_at: datetime
    description: str = ""
    migration_from: Optional[Dict[str, str]] = None  # version -> migration script


class SchemaRegistry:
    """Registry for managing schema versions and migrations."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.schemas: Dict[str, Dict[SchemaVersion, SchemaDefinition]] = {}
        self._load_builtin_schemas()
        self._initialized = True
    
    def _load_builtin_schemas(self) -> None:
        """Load builtin schema definitions."""
        # Coherence signals schema
        self.register_schema(SchemaDefinition(
            schema_type=SchemaType.COHERENCE_SIGNALS,
            version=SchemaVersion(1, 0, 0),
            definition={
                "type": "object",
                "properties": {
                    "coherence_measure": {"type": "number"},
                    "phase_variance": {"type": "number"},
                    "gradient_norm": {"type": "number"},
                    "timestamp": {"type": "number"}
                },
                "required": ["coherence_measure", "timestamp"]
            },
            checksum="",
            created_at=datetime.now(),
            description="Initial coherence signals schema"
        ))
        
        # Add more schemas...
    
    def register_schema(self, schema: SchemaDefinition) -> None:
        """Register a schema definition."""
        key = schema.schema_type.value
        if key not in self.schemas:
            self.schemas[key] = {}
        
        # Calculate checksum
        schema.checksum = hashlib.md5(
            json.dumps(schema.definition, sort_keys=True).encode()
        ).hexdigest()
        
        self.schemas[key][schema.version] = schema
        logger.info(f"Registered schema: {key} v{schema.version}")
    
    def get_schema(self, schema_type: SchemaType, 
                   version: SchemaVersion = None) -> Optional[SchemaDefinition]:
        """Get a schema definition by type and version."""
        key = schema_type.value
        if key not in self.schemas:
            return None
        
        if version is None:
            # Return latest version
            versions = self.schemas[key]
            return max(versions.keys()) if versions else None
        
        return self.schemas[key].get(version)
    
    def get_latest_version(self, schema_type: SchemaType) -> Optional[SchemaVersion]:
        """Get the latest version of a schema type."""
        key = schema_type.value
        if key not in self.schemas or not self.schemas[key]:
            return None
        return max(self.schemas[key].keys())
    
    def get_migration_path(
        self, schema_type: SchemaType, 
        from_version: SchemaVersion, 
        to_version: SchemaVersion
    ) -> List[SchemaDefinition]:
        """Get the migration path between two versions."""
        if from_version == to_version:
            return []
        
        key = schema_type.value
        if key not in self.schemas:
            return []
        
        # Simple linear migration path
        versions = sorted(self.schemas[key].keys())
        start_idx = versions.index(from_version)
        end_idx = versions.index(to_version)
        
        if start_idx > end_idx:
            raise ValueError("Cannot migrate to older version")
        
        return versions[start_idx+1:end_idx+1]


class SchemaMigrator:
    """Migrates data between schema versions."""
    
    def __init__(self, registry: SchemaRegistry = None):
        self.registry = registry or SchemaRegistry()
        self.migration_functions: Dict[str, Dict[tuple, callable]] = {}
    
    def register_migration(
        self, 
        schema_type: SchemaType, 
        from_version: SchemaVersion, 
        to_version: SchemaVersion,
        migration_func: callable
    ) -> None:
        """Register a migration function."""
        key = schema_type.value
        if key not in self.migration_functions:
            self.migration_functions[key] = {}
        
        self.migration_functions[key][(from_version, to_version)] = migration_func
    
    def migrate(
        self, 
        data: Dict[str, Any], 
        schema_type: SchemaType,
        from_version: SchemaVersion,
        to_version: SchemaVersion
    ) -> Dict[str, Any]:
        """Migrate data from one version to another."""
        if from_version == to_version:
            return data
        
        migration_path = self.registry.get_migration_path(
            schema_type, from_version, to_version
        )
        
        current_data = data
        for schema in migration_path:
            key = schema_type.value
            migration_key = (schema.version, schema.version)  # Simplified
            
            migration_func = self.migration_functions.get(key, {}).get(
                (from_version, schema.version)
            )
            
            if migration_func:
                current_data = migration_func(current_data)
            else:
                # Generic migration - just validate against new schema
                current_data = self._generic_migrate(current_data, schema)
        
        return current_data
    
    def _generic_migrate(
        self, 
        data: Dict[str, Any], 
        target_schema: SchemaDefinition
    ) -> Dict[str, Any]:
        """Generic migration that handles field additions."""
        # Add any missing fields with default values
        definition = target_schema.definition
        properties = definition.get('properties', {})
        required = definition.get('required', [])
        
        for field_name, field_schema in properties.items():
            if field_name not in data and field_name in required:
                # Try to use default from schema
                default = field_schema.get('default')
                if default is not None:
                    data[field_name] = default
        
        return data


class SchemaValidator:
    """Validates data against schema definitions."""
    
    def __init__(self, registry: SchemaRegistry = None):
        self.registry = registry or SchemaRegistry()
    
    def validate(
        self, 
        data: Dict[str, Any], 
        schema_type: SchemaType,
        version: SchemaVersion = None
    ) -> Dict[str, Any]:
        """Validate data against a schema."""
        schema = self.registry.get_schema(schema_type, version)
        if not schema:
            raise ValueError(f"Schema not found: {schema_type} v{version}")
        
        # Basic validation
        errors = []
        properties = schema.definition.get('properties', {})
        required = schema.definition.get('required', [])
        
        for field in required:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        for field, field_schema in properties.items():
            if field in data:
                value = data[field]
                expected_type = field_schema.get('type')
                if expected_type == 'number' and not isinstance(value, (int, float)):
                    errors.append(f"Field {field} should be number, got {type(value)}")
                elif expected_type == 'string' and not isinstance(value, str):
                    errors.append(f"Field {field} should be string, got {type(value)}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'schema_version': str(schema.version)
        }
```

### 5.2 Implementation Tasks
- [ ] Create `src/haai/core/schema_registry.py` with SchemaRegistry
- [ ] Create SchemaMigrator for data migration
- [ ] Create SchemaValidator for validation
- [ ] Define schemas for all major data types
- [ ] Add migration functions for schema evolution
- [ ] Integrate schema validation into audit system
- [ ] Write unit tests for schema registry
- [ ] Create migration scripts for database schema

**Estimated Effort**: 6-8 hours

---

## Implementation Timeline

| Phase | Task | Effort |
|-------|------|--------|
| 1 | CI/CD Pipeline | 2-3 hours |
| 2 | Docker Environment | 3-4 hours |
| 3 | Database Integration | 8-10 hours |
| 4 | Distributed Computing | 10-12 hours |
| 5 | Schema Versioning | 6-8 hours |

**Total Estimated Effort**: 29-37 hours

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Database migration complexity | High | Use migration scripts, test thoroughly |
| Distributed system consistency | High | Implement proper message ordering |
| Schema migration edge cases | Medium | Comprehensive test coverage |
| Docker build size | Low | Use slim images, multi-stage builds |

---

## Success Criteria

1. ✅ CI/CD pipeline runs all tests on every PR
2. ✅ Docker environment runs all tests successfully
3. ✅ PostgreSQL integration works for audit storage
4. ✅ Message bus enables multi-agent communication
5. ✅ Schema versioning handles all data types
6. ✅ All existing tests pass after changes
