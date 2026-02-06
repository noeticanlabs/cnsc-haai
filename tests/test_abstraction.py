"""
Tests for the Abstraction and AbstractionLayer classes.

Tests cover:
- AbstractionType enum values
- Abstraction creation with all fields
- Serialization/deserialization (to_dict, from_dict)
- Hierarchy navigation (get_descendants, get_ancestors)
- Context and scope validation
- AbstractionLayer CRUD operations
- Finding common abstractions
"""

import pytest
from datetime import datetime
from uuid import uuid4

from src.cnhaai.core.abstraction import AbstractionType, Abstraction, AbstractionLayer


class TestAbstractionType:
    """Tests for AbstractionType enum."""

    def test_abstraction_type_values_exist(self):
        """Test that all expected abstraction types are defined."""
        assert AbstractionType.DESCRIPTIVE is not None
        assert AbstractionType.MECHANISTIC is not None
        assert AbstractionType.NORMATIVE is not None
        assert AbstractionType.COMPARATIVE is not None

    def test_abstraction_type_count(self):
        """Test that exactly 4 abstraction types are defined."""
        assert len(AbstractionType) == 4

    def test_abstraction_type_names(self):
        """Test abstraction type name strings."""
        assert AbstractionType.DESCRIPTIVE.name == "DESCRIPTIVE"
        assert AbstractionType.MECHANISTIC.name == "MECHANISTIC"
        assert AbstractionType.NORMATIVE.name == "NORMATIVE"
        assert AbstractionType.COMPARATIVE.name == "COMPARATIVE"


class TestAbstractionCreation:
    """Tests for Abstraction class creation."""

    def test_abstraction_with_all_fields(self):
        """Test creating an abstraction with all fields specified."""
        evidence = {"evidence1", "evidence2"}
        scope = {"context1", "context2"}
        validity = {"conditions": ["a", "b"]}
        content = {"summary": "test abstraction"}
        parent_id = str(uuid4())
        metadata = {"version": 1}

        abstraction = Abstraction(
            type=AbstractionType.DESCRIPTIVE,
            evidence=evidence,
            scope=scope,
            validity=validity,
            content=content,
            parent_id=parent_id,
            metadata=metadata
        )

        assert abstraction.type == AbstractionType.DESCRIPTIVE
        assert abstraction.evidence == evidence
        assert abstraction.scope == scope
        assert abstraction.validity == validity
        assert abstraction.content == content
        assert abstraction.parent_id == parent_id
        assert abstraction.metadata == metadata
        assert abstraction.id is not None
        assert abstraction.timestamp is not None

    def test_abstraction_with_minimal_fields(self):
        """Test creating an abstraction with minimal fields."""
        abstraction = Abstraction(
            type=AbstractionType.MECHANISTIC,
            evidence=set(),
            scope=set(),
            validity={},
            content={}
        )

        assert abstraction.type == AbstractionType.MECHANISTIC
        assert abstraction.evidence == set()
        assert abstraction.scope == set()
        assert abstraction.validity == {}
        assert abstraction.content == {}
        assert abstraction.parent_id is None
        assert abstraction.children_ids == []
        assert abstraction.metadata == {}
        assert abstraction.id is not None
        assert abstraction.timestamp is not None

    def test_abstraction_default_values(self):
        """Test that default values are set correctly."""
        abstraction = Abstraction(
            type=AbstractionType.NORMATIVE,
            evidence=set(),
            scope=set(),
            validity={},
            content={}
        )

        assert isinstance(abstraction.id, str)
        assert len(abstraction.id) > 0
        assert isinstance(abstraction.timestamp, datetime)
        assert abstraction.children_ids == []
        assert abstraction.metadata == {}

    def test_abstraction_unique_ids(self):
        """Test that each abstraction gets a unique ID."""
        abstraction1 = Abstraction(
            type=AbstractionType.DESCRIPTIVE,
            evidence=set(),
            scope=set(),
            validity={},
            content={}
        )
        abstraction2 = Abstraction(
            type=AbstractionType.DESCRIPTIVE,
            evidence=set(),
            scope=set(),
            validity={},
            content={}
        )

        assert abstraction1.id != abstraction2.id


class TestAbstractionSerialization:
    """Tests for Abstraction serialization/deserialization."""

    def test_to_dict(self):
        """Test converting abstraction to dictionary."""
        evidence = {"evidence1", "evidence2"}
        scope = {"context1"}
        validity = {"conditions": ["a"]}
        content = {"summary": "test"}

        abstraction = Abstraction(
            type=AbstractionType.COMPARATIVE,
            evidence=evidence,
            scope=scope,
            validity=validity,
            content=content
        )

        result = abstraction.to_dict()

        assert result["id"] == abstraction.id
        assert result["type"] == "COMPARATIVE"
        assert set(result["evidence"]) == evidence
        assert set(result["scope"]) == scope
        assert result["validity"] == validity
        assert result["content"] == content
        assert result["timestamp"] == abstraction.timestamp.isoformat()
        assert result["parent_id"] is None
        assert result["children_ids"] == []
        assert result["metadata"] == {}

    def test_from_dict(self):
        """Test creating abstraction from dictionary."""
        data = {
            "id": "test-id-123",
            "type": "MECHANISTIC",
            "evidence": ["e1", "e2"],
            "scope": ["s1", "s2"],
            "validity": {"key": "value"},
            "content": {"text": "test content"},
            "timestamp": "2024-01-01T00:00:00",
            "parent_id": "parent-123",
            "children_ids": ["child1"],
            "metadata": {"version": 1}
        }

        abstraction = Abstraction.from_dict(data)

        assert abstraction.id == "test-id-123"
        assert abstraction.type == AbstractionType.MECHANISTIC
        assert abstraction.evidence == {"e1", "e2"}
        assert abstraction.scope == {"s1", "s2"}
        assert abstraction.validity == {"key": "value"}
        assert abstraction.content == {"text": "test content"}
        assert abstraction.timestamp == datetime.fromisoformat("2024-01-01T00:00:00")
        assert abstraction.parent_id == "parent-123"
        assert abstraction.children_ids == ["child1"]
        assert abstraction.metadata == {"version": 1}

    def test_from_dict_defaults(self):
        """Test from_dict with missing optional fields."""
        data = {
            "type": "DESCRIPTIVE"
        }

        abstraction = Abstraction.from_dict(data)

        assert abstraction.type == AbstractionType.DESCRIPTIVE
        assert abstraction.evidence == set()
        assert abstraction.scope == set()
        assert abstraction.validity == {}
        assert abstraction.content == {}
        assert abstraction.parent_id is None
        assert abstraction.children_ids == []
        assert abstraction.metadata == {}

    def test_roundtrip_serialization(self):
        """Test serialization roundtrip preserves data."""
        original = Abstraction(
            type=AbstractionType.NORMATIVE,
            evidence={"ev1", "ev2"},
            scope={"ctx1"},
            validity={"v": 1},
            content={"c": "test"},
            metadata={"m": "data"}
        )

        restored = Abstraction.from_dict(original.to_dict())

        assert restored.id == original.id
        assert restored.type == original.type
        assert restored.evidence == original.evidence
        assert restored.scope == original.scope
        assert restored.validity == original.validity
        assert restored.content == original.content
        assert restored.timestamp == original.timestamp
        assert restored.parent_id == original.parent_id
        assert restored.children_ids == original.children_ids
        assert restored.metadata == original.metadata


class TestAbstractionValidation:
    """Tests for abstraction validation methods."""

    def test_is_valid_for_context_in_scope(self):
        """Test is_valid_for_context when context is in scope."""
        abstraction = Abstraction(
            type=AbstractionType.DESCRIPTIVE,
            evidence=set(),
            scope={"context1", "context2"},
            validity={},
            content={}
        )

        assert abstraction.is_valid_for_context("context1") is True
        assert abstraction.is_valid_for_context("context2") is True

    def test_is_valid_for_context_not_in_scope(self):
        """Test is_valid_for_context when context is not in scope."""
        abstraction = Abstraction(
            type=AbstractionType.DESCRIPTIVE,
            evidence=set(),
            scope={"context1"},
            validity={},
            content={}
        )

        assert abstraction.is_valid_for_context("context2") is False
        assert abstraction.is_valid_for_context("context3") is False

    def test_is_valid_for_scope_with_intersection(self):
        """Test is_valid_for_scope when there is intersection."""
        abstraction = Abstraction(
            type=AbstractionType.DESCRIPTIVE,
            evidence=set(),
            scope={"scope1", "scope2"},
            validity={},
            content={}
        )

        assert abstraction.is_valid_for_scope({"scope3", "scope1"}) is True
        assert abstraction.is_valid_for_scope({"scope2", "scope4"}) is True

    def test_is_valid_for_scope_without_intersection(self):
        """Test is_valid_for_scope when there is no intersection."""
        abstraction = Abstraction(
            type=AbstractionType.DESCRIPTIVE,
            evidence=set(),
            scope={"scope1"},
            validity={},
            content={}
        )

        assert abstraction.is_valid_for_scope({"scope2", "scope3"}) is False

    def test_is_valid_for_empty_scope(self):
        """Test is_valid_for_scope with empty scope."""
        abstraction = Abstraction(
            type=AbstractionType.DESCRIPTIVE,
            evidence=set(),
            scope={"scope1"},
            validity={},
            content={}
        )

        assert abstraction.is_valid_for_scope(set()) is False

    def test_abstraction_with_empty_scope(self):
        """Test abstraction with empty scope."""
        abstraction = Abstraction(
            type=AbstractionType.DESCRIPTIVE,
            evidence=set(),
            scope=set(),
            validity={},
            content={}
        )

        assert abstraction.is_valid_for_context("anything") is False
        assert abstraction.is_valid_for_scope({"scope1"}) is False


class TestAbstractionLayer:
    """Tests for AbstractionLayer class."""

    @pytest.fixture
    def layer(self):
        """Create a fresh abstraction layer for testing."""
        return AbstractionLayer(max_levels=3)

    @pytest.fixture
    def sample_abstraction(self):
        """Create a sample abstraction."""
        return Abstraction(
            type=AbstractionType.DESCRIPTIVE,
            evidence={"ev1"},
            scope={"ctx1"},
            validity={},
            content={"text": "test"}
        )

    def test_add_abstraction(self, layer, sample_abstraction):
        """Test adding an abstraction to the layer."""
        result = layer.add(sample_abstraction)

        assert result is True
        assert sample_abstraction.id in layer.abstractions
        assert sample_abstraction.id in layer.by_type[AbstractionType.DESCRIPTIVE]
        assert sample_abstraction.id in layer.by_scope["ctx1"]
        assert sample_abstraction.id in layer.root_ids

    def test_add_duplicate_abstraction_fails(self, layer, sample_abstraction):
        """Test that adding the same abstraction twice fails."""
        layer.add(sample_abstraction)
        result = layer.add(sample_abstraction)

        assert result is False

    def test_get_abstraction(self, layer, sample_abstraction):
        """Test retrieving an abstraction by ID."""
        layer.add(sample_abstraction)
        retrieved = layer.get(sample_abstraction.id)

        assert retrieved == sample_abstraction

    def test_get_nonexistent_abstraction(self, layer):
        """Test retrieving a non-existent abstraction."""
        result = layer.get("nonexistent-id")

        assert result is None

    def test_get_by_type(self, layer):
        """Test retrieving abstractions by type."""
        abs1 = Abstraction(
            type=AbstractionType.DESCRIPTIVE,
            evidence=set(),
            scope={"ctx1"},
            validity={},
            content={}
        )
        abs2 = Abstraction(
            type=AbstractionType.DESCRIPTIVE,
            evidence=set(),
            scope={"ctx2"},
            validity={},
            content={}
        )
        abs3 = Abstraction(
            type=AbstractionType.MECHANISTIC,
            evidence=set(),
            scope={"ctx3"},
            validity={},
            content={}
        )

        layer.add(abs1)
        layer.add(abs2)
        layer.add(abs3)

        result = layer.get_by_type(AbstractionType.DESCRIPTIVE)

        assert len(result) == 2
        assert abs1 in result
        assert abs2 in result
        assert abs3 not in result

    def test_get_by_scope(self, layer):
        """Test retrieving abstractions by scope."""
        abs1 = Abstraction(
            type=AbstractionType.DESCRIPTIVE,
            evidence=set(),
            scope={"ctx1"},
            validity={},
            content={}
        )
        abs2 = Abstraction(
            type=AbstractionType.MECHANISTIC,
            evidence=set(),
            scope={"ctx2"},
            validity={},
            content={}
        )

        layer.add(abs1)
        layer.add(abs2)

        result = layer.get_by_scope("ctx1")

        assert len(result) == 1
        assert abs1 in result

    def test_get_roots(self, layer):
        """Test retrieving root abstractions."""
        root = Abstraction(
            type=AbstractionType.DESCRIPTIVE,
            evidence=set(),
            scope={"ctx1"},
            validity={},
            content={}
        )
        child = Abstraction(
            type=AbstractionType.MECHANISTIC,
            evidence=set(),
            scope={"ctx2"},
            validity={},
            content={},
            parent_id=root.id
        )

        layer.add(root)
        layer.add(child)

        roots = layer.get_roots()

        assert len(roots) == 1
        assert root in roots
        assert child not in roots

    def test_get_children(self, layer):
        """Test retrieving children of an abstraction."""
        parent = Abstraction(
            type=AbstractionType.DESCRIPTIVE,
            evidence=set(),
            scope={"ctx1"},
            validity={},
            content={}
        )
        child1 = Abstraction(
            type=AbstractionType.MECHANISTIC,
            evidence=set(),
            scope={"ctx2"},
            validity={},
            content={},
            parent_id=parent.id
        )
        child2 = Abstraction(
            type=AbstractionType.NORMATIVE,
            evidence=set(),
            scope={"ctx3"},
            validity={},
            content={},
            parent_id=parent.id
        )

        layer.add(parent)
        layer.add(child1)
        layer.add(child2)

        children = layer.get_children(parent.id)

        assert len(children) == 2
        assert child1 in children
        assert child2 in children

    def test_get_children_of_leaf(self, layer, sample_abstraction):
        """Test getting children of a leaf node."""
        layer.add(sample_abstraction)

        children = layer.get_children(sample_abstraction.id)

        assert children == []

    def test_get_descendants(self, layer):
        """Test retrieving all descendants recursively."""
        root = Abstraction(
            type=AbstractionType.DESCRIPTIVE,
            evidence=set(),
            scope={"ctx1"},
            validity={},
            content={}
        )
        child = Abstraction(
            type=AbstractionType.MECHANISTIC,
            evidence=set(),
            scope={"ctx2"},
            validity={},
            content={},
            parent_id=root.id
        )
        grandchild = Abstraction(
            type=AbstractionType.NORMATIVE,
            evidence=set(),
            scope={"ctx3"},
            validity={},
            content={},
            parent_id=child.id
        )

        layer.add(root)
        layer.add(child)
        layer.add(grandchild)

        descendants = layer.get_descendants(root.id)

        assert len(descendants) == 2
        assert child in descendants
        assert grandchild in descendants

    def test_get_ancestors(self, layer):
        """Test retrieving all ancestors recursively."""
        leaf = Abstraction(
            type=AbstractionType.NORMATIVE,
            evidence=set(),
            scope={"ctx3"},
            validity={},
            content={}
        )
        parent = Abstraction(
            type=AbstractionType.MECHANISTIC,
            evidence=set(),
            scope={"ctx2"},
            validity={},
            content={}
        )
        grandparent = Abstraction(
            type=AbstractionType.DESCRIPTIVE,
            evidence=set(),
            scope={"ctx1"},
            validity={},
            content={}
        )

        # Add in reverse order
        layer.add(leaf)
        layer.add(parent)
        layer.add(grandparent)

        # Set parent relationships
        parent.parent_id = grandparent.id
        leaf.parent_id = parent.id

        ancestors = layer.get_ancestors(leaf.id)

        assert len(ancestors) == 2
        assert parent in ancestors
        assert grandparent in ancestors

    def test_get_ancestors_of_root(self, layer, sample_abstraction):
        """Test getting ancestors of a root node."""
        layer.add(sample_abstraction)

        ancestors = layer.get_ancestors(sample_abstraction.id)

        assert ancestors == []

    def test_get_ancestors_with_missing_parent(self, layer):
        """Test getting ancestors when parent is missing."""
        abstraction = Abstraction(
            type=AbstractionType.DESCRIPTIVE,
            evidence=set(),
            scope={"ctx1"},
            validity={},
            content={},
            parent_id="missing-parent-id"
        )

        layer.add(abstraction)

        ancestors = layer.get_ancestors(abstraction.id)

        assert ancestors == []

    def test_create_abstraction(self, layer):
        """Test creating and adding an abstraction."""
        abstraction = layer.create_abstraction(
            type=AbstractionType.DESCRIPTIVE,
            evidence={"ev1"},
            scope={"ctx1"},
            validity={"cond": "test"},
            content={"text": "created abstraction"}
        )

        assert abstraction.type == AbstractionType.DESCRIPTIVE
        assert abstraction.evidence == {"ev1"}
        assert abstraction.scope == {"ctx1"}
        assert abstraction.id in layer.abstractions

    def test_create_abstraction_with_parent(self, layer):
        """Test creating an abstraction with a parent."""
        parent = Abstraction(
            type=AbstractionType.DESCRIPTIVE,
            evidence=set(),
            scope={"ctx1"},
            validity={},
            content={}
        )
        layer.add(parent)

        child = layer.create_abstraction(
            type=AbstractionType.MECHANISTIC,
            evidence=set(),
            scope={"ctx2"},
            validity={},
            content={},
            parent_id=parent.id
        )

        assert child.parent_id == parent.id
        assert child.id in parent.children_ids

    def test_find_common_abstractions(self, layer):
        """Test finding abstractions common to two scopes."""
        abs1 = Abstraction(
            type=AbstractionType.DESCRIPTIVE,
            evidence=set(),
            scope={"scope1", "shared"},
            validity={},
            content={}
        )
        abs2 = Abstraction(
            type=AbstractionType.MECHANISTIC,
            evidence=set(),
            scope={"scope2", "shared"},
            validity={},
            content={}
        )
        abs3 = Abstraction(
            type=AbstractionType.NORMATIVE,
            evidence=set(),
            scope={"scope1", "scope2"},
            validity={},
            content={}
        )

        layer.add(abs1)
        layer.add(abs2)
        layer.add(abs3)

        common = layer.find_common_abstractions("scope1", "scope2")

        assert len(common) == 2
        assert abs2 in common
        assert abs3 in common
        assert abs1 not in common

    def test_find_common_abstractions_no_overlap(self, layer):
        """Test finding abstractions with no common scope."""
        abs1 = Abstraction(
            type=AbstractionType.DESCRIPTIVE,
            evidence=set(),
            scope={"scope1"},
            validity={},
            content={}
        )
        abs2 = Abstraction(
            type=AbstractionType.MECHANISTIC,
            evidence=set(),
            scope={"scope2"},
            validity={},
            content={}
        )

        layer.add(abs1)
        layer.add(abs2)

        common = layer.find_common_abstractions("scope1", "scope2")

        assert common == []

    def test_validate_hierarchy_valid(self, layer):
        """Test hierarchy validation with valid hierarchy."""
        root = Abstraction(
            type=AbstractionType.DESCRIPTIVE,
            evidence=set(),
            scope={"ctx1"},
            validity={},
            content={}
        )
        child = Abstraction(
            type=AbstractionType.MECHANISTIC,
            evidence=set(),
            scope={"ctx2"},
            validity={},
            content={},
            parent_id=root.id
        )

        layer.add(root)
        layer.add(child)

        assert layer.validate_hierarchy() is True

    def test_validate_hierarchy_missing_parent(self, layer):
        """Test hierarchy validation with missing parent."""
        abstraction = Abstraction(
            type=AbstractionType.DESCRIPTIVE,
            evidence=set(),
            scope={"ctx1"},
            validity={},
            content={},
            parent_id="missing-parent"
        )

        layer.add(abstraction)

        assert layer.validate_hierarchy() is False

    def test_validate_hierarchy_max_depth(self, layer):
        """Test hierarchy validation with maximum depth exceeded."""
        layer = AbstractionLayer(max_levels=2)
        
        # Create chain of depth 3
        abstractions = []
        for i in range(3):
            abstraction = Abstraction(
                type=AbstractionType.DESCRIPTIVE,
                evidence=set(),
                scope={f"ctx{i}"},
                validity={},
                content={}
            )
            if i > 0:
                abstraction.parent_id = abstractions[i - 1].id
            layer.add(abstraction)
            abstractions.append(abstraction)

        assert layer.validate_hierarchy() is False

    def test_by_type_indexing(self, layer):
        """Test that abstractions are indexed by type correctly."""
        abs1 = Abstraction(
            type=AbstractionType.DESCRIPTIVE,
            evidence=set(),
            scope={"ctx1"},
            validity={},
            content={}
        )
        abs2 = Abstraction(
            type=AbstractionType.DESCRIPTIVE,
            evidence=set(),
            scope={"ctx2"},
            validity={},
            content={}
        )

        layer.add(abs1)
        layer.add(abs2)

        assert AbstractionType.DESCRIPTIVE in layer.by_type
        assert len(layer.by_type[AbstractionType.DESCRIPTIVE]) == 2

    def test_by_scope_indexing(self, layer):
        """Test that abstractions are indexed by scope correctly."""
        abstraction = Abstraction(
            type=AbstractionType.DESCRIPTIVE,
            evidence=set(),
            scope={"scope1", "scope2"},
            validity={},
            content={}
        )

        layer.add(abstraction)

        assert "scope1" in layer.by_scope
        assert "scope2" in layer.by_scope
        assert abstraction.id in layer.by_scope["scope1"]
        assert abstraction.id in layer.by_scope["scope2"]
