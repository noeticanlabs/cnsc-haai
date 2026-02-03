"""
Schema versioning and migration framework for HAAI.
Manages schema definitions, versions, and data migration.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class SchemaVersion:
    """Represents a schema version."""
    
    def __init__(self, major: int, minor: int, patch: int = 0):
        self.major = major
        self.minor = minor
        self.patch = patch
    
    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"
    
    def __repr__(self) -> str:
        return f"SchemaVersion({self.major}, {self.minor}, {self.patch})"
    
    def __lt__(self, other: 'SchemaVersion') -> bool:
        if self.major != other.major:
            return self.major < other.major
        if self.minor != other.minor:
            return self.minor < other.minor
        return self.patch < other.patch
    
    def __le__(self, other: 'SchemaVersion') -> bool:
        return self == other or self < other
    
    def __gt__(self, other: 'SchemaVersion') -> bool:
        return not self <= other
    
    def __ge__(self, other: 'SchemaVersion') -> bool:
        return not self < other
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SchemaVersion):
            return False
        return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)
    
    def __hash__(self) -> int:
        return hash((self.major, self.minor, self.patch))
    
    def to_tuple(self) -> tuple:
        return (self.major, self.minor, self.patch)
    
    def increment_major(self) -> 'SchemaVersion':
        """Create new version with major incremented."""
        return SchemaVersion(self.major + 1, 0, 0)
    
    def increment_minor(self) -> 'SchemaVersion':
        """Create new version with minor incremented."""
        return SchemaVersion(self.major, self.minor + 1, 0)
    
    def increment_patch(self) -> 'SchemaVersion':
        """Create new version with patch incremented."""
        return SchemaVersion(self.major, self.minor, self.patch + 1)
    
    @classmethod
    def parse(cls, version_str: str) -> 'SchemaVersion':
        """Parse version from string."""
        parts = version_str.split('.')
        major = int(parts[0]) if len(parts) > 0 else 0
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(parts[2]) if len(parts) > 2 else 0
        return cls(major, minor, patch)


class SchemaType(Enum):
    """Types of schemas."""
    COHERENCE_SIGNALS = "coherence_signals"
    AUDIT_EVENT = "audit_event"
    AUDIT_RECEIPT = "audit_receipt"
    NSC_PACKET = "nsc_packet"
    POLICY = "policy"
    RECEIPT = "receipt"
    AGENT_STATE = "agent_state"
    COHERENCE_BUDGET = "coherence_budget"
    GATE_DECISION = "gate_decision"


@dataclass
class SchemaDefinition:
    """Definition of a schema version."""
    schema_type: SchemaType
    version: SchemaVersion
    definition: Dict[str, Any]
    checksum: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    description: str = ""
    migration_script: Optional[str] = None
    
    def __post_init__(self):
        """Calculate checksum after initialization."""
        if not self.checksum:
            self.checksum = self._calculate_checksum()
    
    def _calculate_checksum(self) -> str:
        """Calculate checksum of schema definition."""
        content = json.dumps(self.definition, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'schema_type': self.schema_type.value,
            'version': str(self.version),
            'definition': self.definition,
            'checksum': self.checksum,
            'created_at': self.created_at.isoformat(),
            'description': self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SchemaDefinition':
        """Create from dictionary."""
        return cls(
            schema_type=SchemaType(data['schema_type']),
            version=SchemaVersion.parse(data['version']),
            definition=data['definition'],
            checksum=data.get('checksum', ''),
            created_at=datetime.fromisoformat(data['created_at']) if isinstance(data.get('created_at'), str) else data.get('created_at', datetime.now()),
            description=data.get('description', '')
        )


@dataclass
class ValidationResult:
    """Result of schema validation."""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    schema_version: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'valid': self.valid,
            'errors': self.errors,
            'warnings': self.warnings,
            'schema_version': self.schema_version
        }


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
        
        self.schemas: Dict[str, Dict[str, SchemaDefinition]] = {}
        self._load_builtin_schemas()
        self._initialized = True
    
    def _load_builtin_schemas(self) -> None:
        """Load builtin schema definitions."""
        
        # Coherence signals schema v1.0.0
        self.register_schema(SchemaDefinition(
            schema_type=SchemaType.COHERENCE_SIGNALS,
            version=SchemaVersion(1, 0, 0),
            definition={
                "type": "object",
                "properties": {
                    "coherence_measure": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1
                    },
                    "phase_variance": {"type": "number"},
                    "gradient_norm": {"type": "number"},
                    "spectral_peak_ratio": {"type": "number"},
                    "injection_rate": {"type": "number"},
                    "timestamp": {"type": "number"}
                },
                "required": ["coherence_measure", "timestamp"],
                "additionalProperties": True
            },
            created_at=datetime.now(),
            description="Initial coherence signals schema"
        ))
        
        # Audit event schema v1.0.0
        self.register_schema(SchemaDefinition(
            schema_type=SchemaType.AUDIT_EVENT,
            version=SchemaVersion(1, 0, 0),
            definition={
                "type": "object",
                "properties": {
                    "event_type": {"type": "string"},
                    "agent_id": {"type": "string"},
                    "timestamp": {"type": "string", "format": "date-time"},
                    "data": {"type": "object"},
                    "coherence_score": {"type": "number"},
                    "policy_violations": {
                        "type": "array",
                        "items": {"type": "object"}
                    }
                },
                "required": ["event_type", "timestamp"],
                "additionalProperties": True
            },
            created_at=datetime.now(),
            description="Initial audit event schema"
        ))
        
        # Agent state schema v1.0.0
        self.register_schema(SchemaDefinition(
            schema_type=SchemaType.AGENT_STATE,
            version=SchemaVersion(1, 0, 0),
            definition={
                "type": "object",
                "properties": {
                    "agent_id": {"type": "string"},
                    "status": {"type": "string"},
                    "created_at": {"type": "string", "format": "date-time"},
                    "last_active": {"type": "string", "format": "date-time"},
                    "state_data": {"type": "object"},
                    "coherence_score": {"type": "number"},
                    "updated_at": {"type": "string", "format": "date-time"}
                },
                "required": ["agent_id", "status"],
                "additionalProperties": True
            },
            created_at=datetime.now(),
            description="Initial agent state schema"
        ))
        
        # NSC packet schema v1.0.0
        self.register_schema(SchemaDefinition(
            schema_type=SchemaType.NSC_PACKET,
            version=SchemaVersion(1, 0, 0),
            definition={
                "type": "object",
                "properties": {
                    "header": {"type": "object"},
                    "body": {"type": "string"},
                    "footer": {"type": "object"}
                },
                "required": ["header", "body", "footer"],
                "additionalProperties": True
            },
            created_at=datetime.now(),
            description="Initial NSC packet schema"
        ))
        
        # Policy schema v1.0.0
        self.register_schema(SchemaDefinition(
            schema_type=SchemaType.POLICY,
            version=SchemaVersion(1, 0, 0),
            definition={
                "type": "object",
                "properties": {
                    "policy_id": {"type": "string"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "rules": {"type": "array"},
                    "constraints": {"type": "object"},
                    "priority": {"type": "integer"},
                    "created_at": {"type": "string", "format": "date-time"}
                },
                "required": ["policy_id", "name", "rules"],
                "additionalProperties": True
            },
            created_at=datetime.now(),
            description="Initial policy schema"
        ))
        
        logger.info(f"Loaded {len(self.schemas)} schema types")
    
    def register_schema(self, schema: SchemaDefinition) -> None:
        """Register a schema definition."""
        key = schema.schema_type.value
        version_str = str(schema.version)
        
        if key not in self.schemas:
            self.schemas[key] = {}
        
        self.schemas[key][version_str] = schema
        logger.debug(f"Registered schema: {key} v{schema.version}")
    
    def get_schema(
        self, 
        schema_type: SchemaType, 
        version: SchemaVersion = None
    ) -> Optional[SchemaDefinition]:
        """Get a schema definition by type and version."""
        key = schema_type.value
        if key not in self.schemas:
            return None
        
        if version is None:
            # Return latest version
            versions = self.schemas[key]
            if not versions:
                return None
            return max(versions.values(), key=lambda s: s.version)
        
        return self.schemas[key].get(str(version))
    
    def get_latest_version(self, schema_type: SchemaType) -> Optional[SchemaVersion]:
        """Get the latest version of a schema type."""
        key = schema_type.value
        if key not in self.schemas or not self.schemas[key]:
            return None
        versions = self.schemas[key].keys()
        return max(SchemaVersion.parse(v) for v in versions)
    
    def get_all_versions(self, schema_type: SchemaType) -> List[SchemaVersion]:
        """Get all versions of a schema type."""
        key = schema_type.value
        if key not in self.schemas:
            return []
        return [SchemaVersion.parse(v) for v in self.schemas[key].keys()]
    
    def get_migration_path(
        self, 
        schema_type: SchemaType, 
        from_version: SchemaVersion, 
        to_version: SchemaVersion
    ) -> List[SchemaDefinition]:
        """Get the migration path between two versions."""
        if from_version == to_version:
            return []
        
        key = schema_type.value
        if key not in self.schemas:
            return []
        
        all_versions = sorted(
            [SchemaVersion.parse(v) for v in self.schemas[key].keys()]
        )
        
        if from_version not in all_versions or to_version not in all_versions:
            return []
        
        start_idx = all_versions.index(from_version)
        end_idx = all_versions.index(to_version)
        
        if start_idx > end_idx:
            raise ValueError("Cannot migrate to older version")
        
        path = []
        for idx in range(start_idx + 1, end_idx + 1):
            version_str = str(all_versions[idx])
            path.append(self.schemas[key][version_str])
        
        return path


class SchemaMigrator:
    """Migrates data between schema versions."""
    
    def __init__(self, registry: SchemaRegistry = None):
        self.registry = registry or SchemaRegistry()
        self.migration_functions: Dict[str, Dict[tuple, Callable]] = {}
        self._register_default_migrations()
    
    def _register_default_migrations(self) -> None:
        """Register default migration functions."""
        # Add any custom migrations here
        pass
    
    def register_migration(
        self, 
        schema_type: SchemaType, 
        from_version: SchemaVersion, 
        to_version: SchemaVersion,
        migration_func: Callable
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
        current_version = from_version
        
        for target_schema in migration_path:
            key = schema_type.value
            migration_key = (current_version, target_schema.version)
            
            # Check for custom migration function
            migration_func = self.migration_functions.get(key, {}).get(migration_key)
            
            if migration_func:
                current_data = migration_func(current_data)
            else:
                # Generic migration
                current_data = self._generic_migrate(current_data, target_schema)
            
            current_version = target_schema.version
        
        return current_data
    
    def _generic_migrate(
        self, 
        data: Dict[str, Any], 
        target_schema: SchemaDefinition
    ) -> Dict[str, Any]:
        """Generic migration that handles field additions."""
        definition = target_schema.definition
        properties = definition.get('properties', {})
        
        # Add any missing required fields with null/default values
        for field_name, field_schema in properties.items():
            if field_name not in data:
                data[field_name] = None
        
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
    ) -> ValidationResult:
        """Validate data against a schema."""
        schema = self.registry.get_schema(schema_type, version)
        
        if not schema:
            return ValidationResult(
                valid=False,
                errors=[f"Schema not found: {schema_type} v{version}"],
                schema_version=str(version) if version else None
            )
        
        return self._validate_against_schema(data, schema)
    
    def _validate_against_schema(
        self, 
        data: Dict[str, Any], 
        schema: SchemaDefinition
    ) -> ValidationResult:
        """Validate data against a specific schema definition."""
        errors = []
        warnings = []
        definition = schema.definition
        
        properties = definition.get('properties', {})
        required = definition.get('required', [])
        
        # Check required fields
        for field in required:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        # Validate field types
        for field, field_schema in properties.items():
            if field in data:
                value = data[field]
                field_type = field_schema.get('type')
                
                if field_type and value is not None:
                    if field_type == 'number' and not isinstance(value, (int, float)):
                        errors.append(f"Field {field} should be number, got {type(value).__name__}")
                    elif field_type == 'string' and not isinstance(value, str):
                        errors.append(f"Field {field} should be string, got {type(value).__name__}")
                    elif field_type == 'array' and not isinstance(value, list):
                        errors.append(f"Field {field} should be array, got {type(value).__name__}")
                    elif field_type == 'object' and not isinstance(value, dict):
                        errors.append(f"Field {field} should be object, got {type(value).__name__}")
                    
                    # Check numeric bounds
                    if field_type == 'number' and isinstance(value, (int, float)):
                        if 'minimum' in field_schema and value < field_schema['minimum']:
                            errors.append(f"Field {field} below minimum: {value} < {field_schema['minimum']}")
                        if 'maximum' in field_schema and value > field_schema['maximum']:
                            errors.append(f"Field {field} above maximum: {value} > {field_schema['maximum']}")
        
        # Warn about additional properties
        additional_properties = definition.get('additionalProperties', True)
        if not additional_properties:
            for field in data.keys():
                if field not in properties:
                    warnings.append(f"Unexpected field: {field}")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            schema_version=str(schema.version)
        )
    
    def validate_with_migration(
        self,
        data: Dict[str, Any],
        schema_type: SchemaType,
        target_version: SchemaVersion = None
    ) -> ValidationResult:
        """
        Validate data, migrating if necessary.
        
        Returns validation result and migrated data.
        """
        # Get target schema
        target_schema = self.registry.get_schema(schema_type, target_version)
        if not target_schema:
            return ValidationResult(
                valid=False,
                errors=[f"Target schema not found: {schema_type} v{target_version}"]
            )
        
        # Try to detect current version
        current_version = self._detect_version(data, schema_type)
        
        # Validate as-is
        result = self._validate_against_schema(data, target_schema)
        
        # If not valid, try migrating
        if not result.valid and current_version:
            try:
                migrated_data = self.registry.migrate(
                    data, schema_type, current_version, target_schema.version
                )
                result = self._validate_against_schema(migrated_data, target_schema)
                return result
            except Exception as e:
                result.errors.append(f"Migration failed: {str(e)}")
        
        return result
    
    def _detect_version(
        self, 
        data: Dict[str, Any], 
        schema_type: SchemaType
    ) -> Optional[SchemaVersion]:
        """Detect the version of data based on its structure."""
        # Try each version to find a match
        for version in self.registry.get_all_versions(schema_type):
            schema = self.registry.get_schema(schema_type, version)
            if self._validate_against_schema(data, schema).valid:
                return version
        return None


def create_schema_registry() -> SchemaRegistry:
    """Factory function to create a schema registry."""
    return SchemaRegistry()


def validate_data(
    data: Dict[str, Any],
    schema_type: SchemaType,
    version: SchemaVersion = None
) -> ValidationResult:
    """Quick validation function."""
    validator = SchemaValidator()
    return validator.validate(data, schema_type, version)


def migrate_data(
    data: Dict[str, Any],
    schema_type: SchemaType,
    from_version: SchemaVersion,
    to_version: SchemaVersion
) -> Dict[str, Any]:
    """Quick migration function."""
    migrator = SchemaMigrator()
    return migrator.migrate(data, schema_type, from_version, to_version)
