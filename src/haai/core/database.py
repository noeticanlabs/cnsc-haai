"""
Database abstraction layer for HAAI audit and evidence storage.
Supports PostgreSQL, SQLite (for development), and optional cloud DBs.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from contextlib import contextmanager
from datetime import datetime
import json
import logging
import threading

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Database configuration."""
    backend: str = "sqlite"
    connection_string: str = "haai_audit.db"
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600
    echo: bool = False


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
    def execute(self, query: str, params: Tuple = None) -> List[Dict]:
        """Execute a query and return results."""
        pass
    
    @abstractmethod
    def execute_many(self, query: str, params_list: List[Tuple]) -> None:
        """Execute a query with multiple parameter sets."""
        pass
    
    @abstractmethod
    def execute_scalar(self, query: str, params: Tuple = None) -> Any:
        """Execute a query and return a single value."""
        pass
    
    @abstractmethod
    def begin_transaction(self) -> None:
        """Begin a transaction."""
        pass
    
    @abstractmethod
    def commit(self) -> None:
        """Commit the current transaction."""
        pass
    
    @abstractmethod
    def rollback(self) -> None:
        """Rollback the current transaction."""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close all connections."""
        pass


class SQLiteBackend(DatabaseBackend):
    """SQLite database backend for development."""
    
    def __init__(self, db_path: str = "haai_audit.db", config: DatabaseConfig = None):
        self.db_path = db_path
        self.config = config or DatabaseConfig()
        self.connection = None
        self._lock = threading.Lock()
        self._in_transaction = False
    
    def connect(self) -> None:
        """Establish SQLite connection."""
        import sqlite3
        self.connection = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            isolation_level=None  # Autocommit mode by default
        )
        self.connection.row_factory = sqlite3.Row
        # Enable foreign keys
        self.execute("PRAGMA foreign_keys = ON")
        logger.info(f"Connected to SQLite database: {self.db_path}")
    
    def disconnect(self) -> None:
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Disconnected from SQLite database")
    
    def execute(self, query: str, params: Tuple = None) -> List[Dict]:
        """Execute a query and return results."""
        with self._lock:
            try:
                cursor = self.connection.execute(query, params or ())
                if cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    return [dict(zip(columns, row)) for row in cursor.fetchall()]
                else:
                    self.connection.commit()
                    return []
            except Exception as e:
                logger.error(f"SQLite execute error: {e}")
                raise
    
    def execute_many(self, query: str, params_list: List[Tuple]) -> None:
        """Execute a query with multiple parameter sets."""
        with self._lock:
            try:
                cursor = self.connection.cursor()
                cursor.executemany(query, params_list)
                self.connection.commit()
            except Exception as e:
                logger.error(f"SQLite execute_many error: {e}")
                raise
    
    def execute_scalar(self, query: str, params: Tuple = None) -> Any:
        """Execute a query and return a single value."""
        with self._lock:
            try:
                cursor = self.connection.execute(query, params or ())
                result = cursor.fetchone()
                return result[0] if result else None
            except Exception as e:
                logger.error(f"SQLite execute_scalar error: {e}")
                raise
    
    def begin_transaction(self) -> None:
        """Begin a transaction."""
        self._in_transaction = True
        self.execute("BEGIN TRANSACTION")
    
    def commit(self) -> None:
        """Commit the current transaction."""
        self.execute("COMMIT")
        self._in_transaction = False
    
    def rollback(self) -> None:
        """Rollback the current transaction."""
        self.execute("ROLLBACK")
        self._in_transaction = False
    
    def close(self) -> None:
        """Close all connections."""
        self.disconnect()


class PostgreSQLBackend(DatabaseBackend):
    """PostgreSQL database backend for production."""
    
    def __init__(self, connection_string: str = None, config: DatabaseConfig = None):
        self.connection_string = connection_string
        self.config = config or DatabaseConfig()
        self.connection = None
        self._pool = None
        self._lock = threading.Lock()
    
    def _import_psycopg2(self):
        """Import psycopg2 lazily."""
        try:
            import psycopg2
            from psycopg2 import pool
            self._psycopg2 = psycopg2
            self._pool = pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=self.config.pool_size,
                connection_string=self.connection_string
            )
        except ImportError:
            logger.error("psycopg2 not installed. Install with: pip install psycopg2-binary")
            raise
    
    def connect(self) -> None:
        """Establish PostgreSQL connection."""
        self._import_psycopg2()
        self.connection = self._pool.getconn()
        self.connection.autocommit = False
        logger.info("Connected to PostgreSQL database")
    
    def disconnect(self) -> None:
        """Close database connection."""
        if self.connection:
            self._pool.putconn(self.connection)
            self.connection = None
            logger.info("Disconnected from PostgreSQL database")
    
    def execute(self, query: str, params: Tuple = None) -> List[Dict]:
        """Execute a query and return results."""
        with self._lock:
            try:
                cursor = self.connection.cursor()
                cursor.execute(query, params or ())
                if cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    return [dict(zip(columns, row)) for row in cursor.fetchall()]
                else:
                    self.connection.commit()
                    return []
            except Exception as e:
                self.connection.rollback()
                logger.error(f"PostgreSQL execute error: {e}")
                raise
    
    def execute_many(self, query: str, params_list: List[Tuple]) -> None:
        """Execute a query with multiple parameter sets."""
        with self._lock:
            try:
                cursor = self.connection.cursor()
                cursor.executemany(query, params_list)
                self.connection.commit()
            except Exception as e:
                self.connection.rollback()
                logger.error(f"PostgreSQL execute_many error: {e}")
                raise
    
    def execute_scalar(self, query: str, params: Tuple = None) -> Any:
        """Execute a query and return a single value."""
        with self._lock:
            try:
                cursor = self.connection.cursor()
                cursor.execute(query, params or ())
                result = cursor.fetchone()
                return result[0] if result else None
            except Exception as e:
                self.connection.rollback()
                logger.error(f"PostgreSQL execute_scalar error: {e}")
                raise
    
    def begin_transaction(self) -> None:
        """Begin a transaction."""
        self.connection.autocommit = False
    
    def commit(self) -> None:
        """Commit the current transaction."""
        self.connection.commit()
    
    def rollback(self) -> None:
        """Rollback the current transaction."""
        self.connection.rollback()
    
    def close(self) -> None:
        """Close all connections."""
        if self._pool:
            self._pool.closeall()
        self.disconnect()


class DatabaseManager:
    """Manages database connections and operations."""
    
    _instance = None
    
    def __new__(cls, config: DatabaseConfig = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config: DatabaseConfig = None):
        if self._initialized:
            return
        
        self.config = config or DatabaseConfig()
        self.backend = self._create_backend()
        self._initialized = False
    
    def _create_backend(self) -> DatabaseBackend:
        """Create the appropriate backend based on configuration."""
        if self.config.backend == "postgresql":
            return PostgreSQLBackend(
                connection_string=self.config.connection_string,
                config=self.config
            )
        else:
            return SQLiteBackend(
                db_path=self.config.connection_string,
                config=self.config
            )
    
    def initialize(self) -> None:
        """Initialize database schema."""
        if self._initialized:
            return
        
        self.backend.connect()
        self._create_schema()
        self._initialized = True
        logger.info("DatabaseManager initialized")
    
    def _create_schema(self) -> None:
        """Create database tables."""
        schema_statements = [
            # Audit events table
            """
            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type VARCHAR(100) NOT NULL,
                agent_id VARCHAR(100),
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                data TEXT NOT NULL,
                coherence_score FLOAT,
                policy_violations TEXT,
                receipt_id VARCHAR(100)
            )
            """,
            # Audit receipts table
            """
            CREATE TABLE IF NOT EXISTS audit_receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_id VARCHAR(100) UNIQUE NOT NULL,
                event_id INTEGER,
                signature VARCHAR(500),
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,
                FOREIGN KEY (event_id) REFERENCES audit_events(id)
            )
            """,
            # Coherence signals table
            """
            CREATE TABLE IF NOT EXISTS coherence_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id VARCHAR(100),
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                coherence_measure FLOAT,
                phase_variance FLOAT,
                gradient_norm FLOAT,
                spectral_peak_ratio FLOAT,
                injection_rate FLOAT,
                raw_signals TEXT
            )
            """,
            # Agent state table
            """
            CREATE TABLE IF NOT EXISTS agent_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id VARCHAR(100) UNIQUE NOT NULL,
                status VARCHAR(50),
                created_at DATETIME,
                last_active DATETIME,
                state_data TEXT,
                coherence_score FLOAT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """,
            # Policy decisions table
            """
            CREATE TABLE IF NOT EXISTS policy_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                decision_id VARCHAR(100) UNIQUE NOT NULL,
                agent_id VARCHAR(100),
                policy_id VARCHAR(100),
                decision VARCHAR(50),
                reason TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """,
            # Create indexes
            """
            CREATE INDEX IF NOT EXISTS idx_audit_events_timestamp 
                ON audit_events(timestamp)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_audit_events_agent 
                ON audit_events(agent_id)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_audit_events_type 
                ON audit_events(event_type)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_coherence_signals_timestamp 
                ON coherence_signals(timestamp)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_coherence_signals_agent 
                ON coherence_signals(agent_id)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_agent_states_agent 
                ON agent_states(agent_id)
            """
        ]
        
        for stmt in schema_statements:
            try:
                self.backend.execute(stmt)
            except Exception as e:
                logger.warning(f"Schema creation warning: {e}")
    
    @contextmanager
    def transaction(self):
        """Context manager for database transactions."""
        try:
            self.backend.begin_transaction()
            yield self
            self.backend.commit()
        except Exception as e:
            self.backend.rollback()
            logger.error(f"Transaction error: {e}")
            raise
    
    def store_audit_event(
        self, 
        event_type: str, 
        agent_id: str = None,
        data: Dict = None,
        coherence_score: float = None,
        policy_violations: List = None,
        receipt_id: str = None
    ) -> int:
        """Store an audit event and return its ID."""
        query = """
        INSERT INTO audit_events 
            (event_type, agent_id, data, coherence_score, policy_violations, receipt_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        self.backend.execute(query, (
            event_type,
            agent_id,
            json.dumps(data or {}),
            coherence_score,
            json.dumps(policy_violations) if policy_violations else None,
            receipt_id
        ))
        
        # Return the last inserted ID
        return self.backend.execute_scalar("SELECT last_insert_rowid()")
    
    def store_audit_receipt(
        self,
        receipt_id: str,
        event_id: int = None,
        signature: str = None,
        metadata: Dict = None
    ) -> int:
        """Store an audit receipt."""
        query = """
        INSERT INTO audit_receipts (receipt_id, event_id, signature, metadata)
        VALUES (?, ?, ?, ?)
        """
        self.backend.execute(query, (
            receipt_id,
            event_id,
            signature,
            json.dumps(metadata or {})
        ))
        return self.backend.execute_scalar("SELECT last_insert_rowid()")
    
    def store_coherence_signals(
        self, 
        agent_id: str, 
        signals: Dict
    ) -> int:
        """Store coherence signal measurements."""
        query = """
        INSERT INTO coherence_signals 
            (agent_id, coherence_measure, phase_variance, gradient_norm, 
             spectral_peak_ratio, injection_rate, raw_signals)
        VALUES (?, ?, ?, ?, ?, ?, ?)
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
        return self.backend.execute_scalar("SELECT last_insert_rowid()")
    
    def update_agent_state(
        self,
        agent_id: str,
        status: str = None,
        state_data: Dict = None,
        coherence_score: float = None
    ) -> None:
        """Update or insert agent state."""
        query = """
        INSERT OR REPLACE INTO agent_states 
            (agent_id, status, last_active, state_data, coherence_score, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?, CURRENT_TIMESTAMP)
        """
        self.backend.execute(query, (
            agent_id,
            status,
            json.dumps(state_data or {}),
            coherence_score
        ))
    
    def store_policy_decision(
        self,
        decision_id: str,
        agent_id: str,
        policy_id: str,
        decision: str,
        reason: str = None
    ) -> int:
        """Store a policy decision."""
        query = """
        INSERT INTO policy_decisions 
            (decision_id, agent_id, policy_id, decision, reason)
        VALUES (?, ?, ?, ?, ?)
        """
        self.backend.execute(query, (
            decision_id,
            agent_id,
            policy_id,
            decision,
            reason
        ))
        return self.backend.execute_scalar("SELECT last_insert_rowid()")
    
    def query_audit_events(
        self, 
        agent_id: str = None, 
        event_type: str = None,
        start_time: datetime = None,
        end_time: datetime = None,
        limit: int = 100
    ) -> List[Dict]:
        """Query audit events with optional filters."""
        conditions = []
        params = []
        
        if agent_id:
            conditions.append("agent_id = ?")
            params.append(agent_id)
        if event_type:
            conditions.append("event_type = ?")
            params.append(event_type)
        if start_time:
            conditions.append("timestamp >= ?")
            params.append(start_time.isoformat())
        if end_time:
            conditions.append("timestamp <= ?")
            params.append(end_time.isoformat())
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT * FROM audit_events 
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT ?
        """
        params.append(limit)
        
        results = self.backend.execute(query, tuple(params))
        
        # Parse JSON fields
        for row in results:
            if row.get('data'):
                row['data'] = json.loads(row['data'])
            if row.get('policy_violations'):
                row['policy_violations'] = json.loads(row['policy_violations'])
        
        return results
    
    def query_coherence_signals(
        self,
        agent_id: str = None,
        start_time: datetime = None,
        end_time: datetime = None,
        limit: int = 100
    ) -> List[Dict]:
        """Query coherence signals with optional filters."""
        conditions = []
        params = []
        
        if agent_id:
            conditions.append("agent_id = ?")
            params.append(agent_id)
        if start_time:
            conditions.append("timestamp >= ?")
            params.append(start_time.isoformat())
        if end_time:
            conditions.append("timestamp <= ?")
            params.append(end_time.isoformat())
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT * FROM coherence_signals 
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT ?
        """
        params.append(limit)
        
        results = self.backend.execute(query, tuple(params))
        
        # Parse JSON fields
        for row in results:
            if row.get('raw_signals'):
                row['raw_signals'] = json.loads(row['raw_signals'])
        
        return results
    
    def get_coherence_stats(self, agent_id: str = None, hours: int = 24) -> Dict:
        """Get coherence statistics for an agent."""
        where_clause = "agent_id = ?" if agent_id else "1=1"
        
        query = f"""
            SELECT 
                COUNT(*) as sample_count,
                AVG(coherence_measure) as avg_coherence,
                MIN(coherence_measure) as min_coherence,
                MAX(coherence_measure) as max_coherence,
                AVG(phase_variance) as avg_phase_variance,
                AVG(gradient_norm) as avg_gradient_norm
            FROM coherence_signals
            WHERE {where_clause}
            AND timestamp >= datetime('now', '-{hours} hours')
        """
        
        params = (agent_id,) if agent_id else ()
        result = self.backend.execute(query, params)
        
        if result:
            return {
                'sample_count': result[0]['sample_count'],
                'avg_coherence': result[0]['avg_coherence'],
                'min_coherence': result[0]['min_coherence'],
                'max_coherence': result[0]['max_coherence'],
                'avg_phase_variance': result[0]['avg_phase_variance'],
                'avg_gradient_norm': result[0]['avg_gradient_norm'],
                'hours': hours
            }
        return {'sample_count': 0}
    
    def shutdown(self) -> None:
        """Shutdown database manager."""
        if self._initialized:
            self.backend.close()
            self._initialized = False
            logger.info("DatabaseManager shutdown")
    
    @property
    def is_connected(self) -> bool:
        """Check if database is connected."""
        return self._initialized


def create_database_manager(
    backend: str = "sqlite",
    connection_string: str = "haai_audit.db",
    **kwargs
) -> DatabaseManager:
    """Factory function to create a DatabaseManager."""
    config = DatabaseConfig(
        backend=backend,
        connection_string=connection_string,
        **{k: v for k, v in kwargs.items() if k in config_fields()}
    )
    return DatabaseManager(config)


def config_fields() -> List[str]:
    """Return list of configurable fields."""
    return ['pool_size', 'max_overflow', 'pool_timeout', 'pool_recycle', 'echo']
