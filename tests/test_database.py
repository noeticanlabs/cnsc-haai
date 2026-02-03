"""
Unit tests for the database layer.
"""

import pytest
import tempfile
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestSQLiteBackend:
    """Test SQLite backend implementation."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database file."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        yield db_path
        
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_connect_disconnect(self, temp_db):
        """Test database connection and disconnection."""
        from haai.core.database import SQLiteBackend
        
        backend = SQLiteBackend(db_path=temp_db)
        backend.connect()
        assert backend.connection is not None
        
        backend.disconnect()
        assert backend.connection is None
    
    def test_execute_query(self, temp_db):
        """Test basic query execution."""
        from haai.core.database import SQLiteBackend
        
        backend = SQLiteBackend(db_path=temp_db)
        backend.connect()
        
        # Create test table
        backend.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
        
        # Insert data
        backend.execute("INSERT INTO test (name) VALUES (?)", ("test_name",))
        
        # Query data
        results = backend.execute("SELECT * FROM test")
        assert len(results) == 1
        assert results[0]['name'] == "test_name"
        
        backend.disconnect()
    
    def test_execute_many(self, temp_db):
        """Test batch query execution."""
        from haai.core.database import SQLiteBackend
        
        backend = SQLiteBackend(db_path=temp_db)
        backend.connect()
        
        # Create test table
        backend.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, value INTEGER)")
        
        # Batch insert
        data = [(i,) for i in range(5)]
        backend.execute_many("INSERT INTO test (value) VALUES (?)", data)
        
        # Verify
        results = backend.execute("SELECT COUNT(*) as count FROM test")
        assert results[0]['count'] == 5
        
        backend.disconnect()
    
    def test_execute_scalar(self, temp_db):
        """Test scalar query execution."""
        from haai.core.database import SQLiteBackend
        
        backend = SQLiteBackend(db_path=temp_db)
        backend.connect()
        
        # Create and populate table
        backend.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, value INTEGER)")
        backend.execute("INSERT INTO test (value) VALUES (42)")
        
        # Query scalar
        result = backend.execute_scalar("SELECT value FROM test WHERE id = ?", (1,))
        assert result == 42
        
        backend.disconnect()
    
    def test_transaction(self, temp_db):
        """Test transaction handling."""
        from haai.core.database import SQLiteBackend
        
        backend = SQLiteBackend(db_path=temp_db)
        backend.connect()
        
        # Create table
        backend.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, value INTEGER)")
        
        # Test commit
        backend.begin_transaction()
        backend.execute("INSERT INTO test (value) VALUES (1)")
        backend.commit()
        
        results = backend.execute("SELECT COUNT(*) as count FROM test")
        assert results[0]['count'] == 1
        
        # Test rollback
        backend.begin_transaction()
        backend.execute("INSERT INTO test (value) VALUES (2)")
        backend.rollback()
        
        results = backend.execute("SELECT COUNT(*) as count FROM test")
        assert results[0]['count'] == 1  # Should still be 1
        
        backend.disconnect()


class TestDatabaseManager:
    """Test DatabaseManager functionality."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database file."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        yield db_path
        
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_initialize(self, temp_db):
        """Test database initialization and schema creation."""
        from haai.core.database import DatabaseManager, DatabaseConfig
        
        config = DatabaseConfig(
            backend="sqlite",
            connection_string=temp_db
        )
        manager = DatabaseManager(config)
        manager.initialize()
        
        assert manager.is_connected
        assert manager.backend is not None
        
        # Verify schema tables exist
        tables = manager.backend.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        table_names = [t['name'] for t in tables]
        
        assert 'audit_events' in table_names
        assert 'audit_receipts' in table_names
        assert 'coherence_signals' in table_names
        assert 'agent_states' in table_names
        assert 'policy_decisions' in table_names
        
        manager.shutdown()
    
    def test_store_audit_event(self, temp_db):
        """Test storing audit events."""
        from haai.core.database import DatabaseManager, DatabaseConfig
        
        config = DatabaseConfig(
            backend="sqlite",
            connection_string=temp_db
        )
        manager = DatabaseManager(config)
        manager.initialize()
        
        event_id = manager.store_audit_event(
            event_type="test_event",
            agent_id="test_agent",
            data={"key": "value"},
            coherence_score=0.95
        )
        
        assert event_id is not None
        
        # Query back
        events = manager.query_audit_events(agent_id="test_agent")
        assert len(events) == 1
        assert events[0]['event_type'] == "test_event"
        
        manager.shutdown()
    
    def test_store_coherence_signals(self, temp_db):
        """Test storing coherence signals."""
        from haai.core.database import DatabaseManager, DatabaseConfig
        
        config = DatabaseConfig(
            backend="sqlite",
            connection_string=temp_db
        )
        manager = DatabaseManager(config)
        manager.initialize()
        
        signals = {
            'coherence_measure': 0.95,
            'phase_variance': 0.1,
            'gradient_norm': 0.5,
            'spectral_peak_ratio': 15.0,
            'injection_rate': 0.05
        }
        
        signal_id = manager.store_coherence_signals(
            agent_id="test_agent",
            signals=signals
        )
        
        assert signal_id is not None
        
        # Query back
        query_results = manager.query_coherence_signals(agent_id="test_agent")
        assert len(query_results) == 1
        assert query_results[0]['coherence_measure'] == 0.95
        
        manager.shutdown()
    
    def test_get_coherence_stats(self, temp_db):
        """Test getting coherence statistics."""
        from haai.core.database import DatabaseManager, DatabaseConfig
        
        config = DatabaseConfig(
            backend="sqlite",
            connection_string=temp_db
        )
        manager = DatabaseManager(config)
        manager.initialize()
        
        # Store multiple signals
        for i in range(5):
            manager.store_coherence_signals(
                agent_id="test_agent",
                signals={
                    'coherence_measure': 0.8 + (i * 0.05),
                    'phase_variance': 0.1,
                    'gradient_norm': 0.5,
                    'spectral_peak_ratio': 15.0,
                    'injection_rate': 0.05
                }
            )
        
        # Get stats
        stats = manager.get_coherence_stats(agent_id="test_agent")
        
        assert stats['sample_count'] == 5
        assert stats['avg_coherence'] == 0.9  # (0.8 + 0.85 + 0.9 + 0.95 + 1.0) / 5
        
        manager.shutdown()
    
    def test_update_agent_state(self, temp_db):
        """Test updating agent state."""
        from haai.core.database import DatabaseManager, DatabaseConfig
        
        config = DatabaseConfig(
            backend="sqlite",
            connection_string=temp_db
        )
        manager = DatabaseManager(config)
        manager.initialize()
        
        # Update state
        manager.update_agent_state(
            agent_id="test_agent",
            status="active",
            state_data={"task": "testing"},
            coherence_score=0.95
        )
        
        # Query events
        events = manager.query_audit_events(agent_id="test_agent")
        # Should have 1 event from the update_agent_state call
        
        manager.shutdown()
    
    def test_transaction_context_manager(self, temp_db):
        """Test transaction context manager."""
        from haai.core.database import DatabaseManager, DatabaseConfig
        
        config = DatabaseConfig(
            backend="sqlite",
            connection_string=temp_db
        )
        manager = DatabaseManager(config)
        manager.initialize()
        
        with manager.transaction():
            manager.store_audit_event(event_type="tx_test", data={})
        
        # Verify
        events = manager.query_audit_events(limit=100)
        assert len(events) >= 1
        
        manager.shutdown()


class TestDatabaseConfig:
    """Test DatabaseConfig."""
    
    def test_default_config(self):
        """Test default configuration values."""
        from haai.core.database import DatabaseConfig
        
        config = DatabaseConfig()
        
        assert config.backend == "sqlite"
        assert config.connection_string == "haai_audit.db"
        assert config.pool_size == 5
        assert config.max_overflow == 10
    
    def test_custom_config(self):
        """Test custom configuration values."""
        from haai.core.database import DatabaseConfig
        
        config = DatabaseConfig(
            backend="postgresql",
            connection_string="postgresql://user:pass@localhost/db",
            pool_size=10
        )
        
        assert config.backend == "postgresql"
        assert config.pool_size == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
