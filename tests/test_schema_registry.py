"""
Unit tests for the schema versioning framework.
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestSchemaVersion:
    """Test schema version class."""
    
    def test_version_creation(self):
        """Test version creation."""
        from haai.core.schema_registry import SchemaVersion
        
        v = SchemaVersion(1, 2, 3)
        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 3
    
    def test_version_string(self):
        """Test version string representation."""
        from haai.core.schema_registry import SchemaVersion
        
        v = SchemaVersion(1, 2, 3)
        assert str(v) == "1.2.3"
        assert repr(v) == "SchemaVersion(1, 2, 3)"
    
    def test_version_comparison(self):
        """Test version comparison."""
        from haai.core.schema_registry import SchemaVersion
        
        v1 = SchemaVersion(1, 0, 0)
        v2 = SchemaVersion(1, 1, 0)
        v3 = SchemaVersion(2, 0, 0)
        
        assert v1 < v2 < v3
        assert v1 == SchemaVersion(1, 0, 0)
        assert v1 <= v2
        assert v3 > v2
        assert v3 >= v2
    
    def test_version_increment(self):
        """Test version increment methods."""
        from haai.core.schema_registry import SchemaVersion
        
        v = SchemaVersion(1, 2, 3)
        
        assert v.increment_major() == SchemaVersion(2, 0, 0)
        assert v.increment_minor() == SchemaVersion(1, 3, 0)
        assert v.increment_patch() == SchemaVersion(1, 2, 4)
    
    def test_version_parse(self):
        """Test version parsing from string."""
        from haai.core.schema_registry import SchemaVersion
        
        v = SchemaVersion.parse("2.5.1")
        assert v.major == 2
        assert v.minor == 5
        assert v.patch == 1
    
    def test_version_hash(self):
        """Test version hashing."""
        from haai.core.schema_registry import SchemaVersion
        
        v1 = SchemaVersion(1, 2, 3)
        v2 = SchemaVersion(1, 2, 3)
        
        assert hash(v1) == hash(v2)
        assert v1 in {v2}
    
    def test_version_to_tuple(self):
        """Test version to tuple conversion."""
        from haai.core.schema_registry import SchemaVersion
        
        v = SchemaVersion(1, 2, 3)
        assert v.to_tuple() == (1, 2, 3)


class TestSchemaRegistry:
    """Test schema registry functionality."""
    
    @pytest.fixture
    def registry(self):
        """Create a fresh schema registry."""
        from haai.core.schema_registry import SchemaRegistry
        
        # Reset singleton
        SchemaRegistry._instance = None
        return SchemaRegistry()
    
    def test_get_schema(self, registry):
        """Test getting a schema."""
        from haai.core.schema_registry import SchemaType
        
        schema = registry.get_schema(SchemaType.COHERENCE_SIGNALS)
        
        assert schema is not None
        assert schema.schema_type == SchemaType.COHERENCE_SIGNALS
        assert schema.version == SchemaVersion(1, 0, 0)
    
    def test_get_latest_version(self, registry):
        """Test getting latest version."""
        from haai.core.schema_registry import SchemaType
        
        latest = registry.get_latest_version(SchemaType.COHERENCE_SIGNALS)
        
        assert latest is not None
        assert latest == SchemaVersion(1, 0, 0)
    
    def test_get_all_versions(self, registry):
        """Test getting all versions."""
        from haai.core.schema_registry import SchemaType
        
        versions = registry.get_all_versions(SchemaType.COHERENCE_SIGNALS)
        
        assert len(versions) >= 1
        assert SchemaVersion(1, 0, 0) in versions
    
    def test_register_schema(self, registry):
        """Test registering a new schema."""
        from haai.core.schema_registry import (
            SchemaRegistry, SchemaDefinition, 
            SchemaType, SchemaVersion
        )
        
        # Reset singleton
        SchemaRegistry._instance = None
        fresh_registry = SchemaRegistry()
        
        schema = SchemaDefinition(
            schema_type=SchemaType.AUDIT_EVENT,
            version=SchemaVersion(2, 0, 0),
            definition={"type": "object", "properties": {}},
            description="v2 schema"
        )
        
        fresh_registry.register_schema(schema)
        
        retrieved = fresh_registry.get_schema(
            SchemaType.AUDIT_EVENT, 
            SchemaVersion(2, 0, 0)
        )
        
        assert retrieved is not None
        assert retrieved.description == "v2 schema"
    
    def test_get_migration_path(self, registry):
        """Test getting migration path."""
        from haai.core.schema_registry import SchemaType, SchemaVersion
        
        # v1 to v1 should be empty
        path = registry.get_migration_path(
            SchemaType.COHERENCE_SIGNALS,
            SchemaVersion(1, 0, 0),
            SchemaVersion(1, 0, 0)
        )
        assert len(path) == 0


class TestSchemaMigrator:
    """Test schema migration functionality."""
    
    @pytest.fixture
    def migrator(self):
        """Create a schema migrator."""
        from haai.core.schema_registry import SchemaMigrator
        return SchemaMigrator()
    
    def test_migrate_same_version(self, migrator):
        """Test migrating to same version."""
        from haai.core.schema_registry import SchemaType, SchemaVersion
        
        data = {"coherence_measure": 0.95, "timestamp": 12345}
        
        result = migrator.migrate(
            data,
            SchemaType.COHERENCE_SIGNALS,
            SchemaVersion(1, 0, 0),
            SchemaVersion(1, 0, 0)
        )
        
        assert result == data
    
    def test_generic_migration(self, migrator):
        """Test generic migration adds missing fields."""
        from haai.core.schema_registry import SchemaType, SchemaVersion, SchemaDefinition
        
        # Create a custom schema with a new field
        schema = SchemaDefinition(
            schema_type=SchemaType.COHERENCE_SIGNALS,
            version=SchemaVersion(3, 0, 0),
            definition={
                "type": "object",
                "properties": {
                    "coherence_measure": {"type": "number"},
                    "timestamp": {"type": "number"},
                    "new_field": {"type": "string"}  # New field
                },
                "required": ["coherence_measure", "timestamp"],
                "additionalProperties": True
            },
            description="v3 with new field"
        )
        
        # Register the schema
        from haai.core.schema_registry import SchemaRegistry
        SchemaRegistry._instance = None
        registry = SchemaRegistry()
        registry.register_schema(schema)
        
        # Create migrator with the registry
        from haai.core.schema_registry import SchemaMigrator
        migrator = SchemaMigrator(registry)
        
        data = {"coherence_measure": 0.95, "timestamp": 12345}
        
        result = migrator.migrate(
            data,
            SchemaType.COHERENCE_SIGNALS,
            SchemaVersion(1, 0, 0),
            SchemaVersion(3, 0, 0)
        )
        
        assert result.get("new_field") is None  # Added as null


class TestSchemaValidator:
    """Test schema validation functionality."""
    
    @pytest.fixture
    def validator(self):
        """Create a schema validator."""
        from haai.core.schema_registry import SchemaValidator
        return SchemaValidator()
    
    def test_valid_data(self, validator):
        """Test validating valid data."""
        from haai.core.schema_registry import SchemaType
        
        data = {
            "coherence_measure": 0.95,
            "phase_variance": 0.1,
            "gradient_norm": 0.5,
            "timestamp": 12345.0
        }
        
        result = validator.validate(data, SchemaType.COHERENCE_SIGNALS)
        
        assert result.valid
        assert len(result.errors) == 0
    
    def test_missing_required_field(self, validator):
        """Test validation fails on missing required field."""
        from haai.core.schema_registry import SchemaType
        
        data = {
            "phase_variance": 0.1,
            # Missing coherence_measure
            "timestamp": 12345.0
        }
        
        result = validator.validate(data, SchemaType.COHERENCE_SIGNALS)
        
        assert not result.valid
        assert any("coherence_measure" in e for e in result.errors)
    
    def test_invalid_type(self, validator):
        """Test validation fails on wrong type."""
        from haai.core.schema_registry import SchemaType
        
        data = {
            "coherence_measure": "not_a_number",  # Should be number
            "timestamp": 12345.0
        }
        
        result = validator.validate(data, SchemaType.COHERENCE_SIGNALS)
        
        assert not result.valid
        assert any("number" in e.lower() for e in result.errors)
    
    def test_bounds_checking(self, validator):
        """Test numeric bounds validation."""
        from haai.core.schema_registry import SchemaType
        
        data = {
            "coherence_measure": 1.5,  # Should be 0-1
            "timestamp": 12345.0
        }
        
        result = validator.validate(data, SchemaType.COHERENCE_SIGNALS)
        
        assert not result.valid
        assert any("maximum" in e.lower() for e in result.errors)
    
    def test_schema_version_in_result(self, validator):
        """Test schema version is included in result."""
        from haai.core.schema_registry import SchemaType
        
        data = {
            "coherence_measure": 0.95,
            "timestamp": 12345.0
        }
        
        result = validator.validate(data, SchemaType.COHERENCE_SIGNALS)
        
        assert result.schema_version == "1.0.0"


class TestValidationResult:
    """Test validation result class."""
    
    def test_valid_result(self):
        """Test creating a valid result."""
        from haai.core.schema_registry import ValidationResult
        
        result = ValidationResult(valid=True)
        
        assert result.valid
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
    
    def test_invalid_result(self):
        """Test creating an invalid result."""
        from haai.core.schema_registry import ValidationResult
        
        result = ValidationResult(
            valid=False,
            errors=["Missing required field"],
            warnings=["Unexpected field"]
        )
        
        assert not result.valid
        assert len(result.errors) == 1
        assert len(result.warnings) == 1
    
    def test_to_dict(self):
        """Test result to dictionary conversion."""
        from haai.core.schema_registry import ValidationResult
        
        result = ValidationResult(
            valid=False,
            errors=["Error 1"],
            schema_version="1.0.0"
        )
        
        data = result.to_dict()
        
        assert data["valid"] is False
        assert data["errors"] == ["Error 1"]
        assert data["schema_version"] == "1.0.0"


class TestSchemaDefinition:
    """Test schema definition class."""
    
    def test_checksum_calculation(self):
        """Test checksum is calculated on init."""
        from haai.core.schema_registry import SchemaDefinition, SchemaType, SchemaVersion
        
        schema = SchemaDefinition(
            schema_type=SchemaType.COHERENCE_SIGNALS,
            version=SchemaVersion(1, 0, 0),
            definition={"type": "object", "properties": {"test": {"type": "string"}}},
            description="Test schema"
        )
        
        assert schema.checksum != ""
        assert len(schema.checksum) == 32  # MD5 hex digest
    
    def test_to_dict(self):
        """Test schema to dictionary conversion."""
        from haai.core.schema_registry import SchemaDefinition, SchemaType, SchemaVersion
        
        schema = SchemaDefinition(
            schema_type=SchemaType.COHERENCE_SIGNALS,
            version=SchemaVersion(1, 0, 0),
            definition={"type": "object"},
            description="Test"
        )
        
        data = schema.to_dict()
        
        assert data["schema_type"] == "coherence_signals"
        assert data["version"] == "1.0.0"
        assert data["description"] == "Test"
    
    def test_from_dict(self):
        """Test schema from dictionary."""
        from haai.core.schema_registry import SchemaDefinition, SchemaType
        
        data = {
            "schema_type": "coherence_signals",
            "version": "2.0.0",
            "definition": {"type": "object"},
            "checksum": "abc123",
            "description": "Test"
        }
        
        schema = SchemaDefinition.from_dict(data)
        
        assert schema.schema_type == SchemaType.COHERENCE_SIGNALS
        assert schema.version == SchemaVersion(2, 0, 0)


class TestQuickFunctions:
    """Test quick utility functions."""
    
    def test_validate_data(self):
        """Test quick validate_data function."""
        from haai.core.schema_registry import validate_data, SchemaType
        
        data = {
            "coherence_measure": 0.95,
            "timestamp": 12345.0
        }
        
        result = validate_data(data, SchemaType.COHERENCE_SIGNALS)
        
        assert result.valid
    
    def test_migrate_data(self):
        """Test quick migrate_data function."""
        from haai.core.schema_registry import migrate_data, SchemaType, SchemaVersion
        
        data = {"coherence_measure": 0.95, "timestamp": 12345}
        
        result = migrate_data(
            data,
            SchemaType.COHERENCE_SIGNALS,
            SchemaVersion(1, 0, 0),
            SchemaVersion(1, 0, 0)
        )
        
        assert result == data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
