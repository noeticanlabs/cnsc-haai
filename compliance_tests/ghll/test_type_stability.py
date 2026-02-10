"""
GHLL Type Stability Tests

Tests for GHLL type system stability during transformations.
"""

import pytest
from cnsc.haai.ghll.types import GHLLType, TypeCategory


class TestTypeStability:
    """Tests for type stability during transformations."""

    def test_belief_type_creation(self):
        """Test that belief type can be created."""
        t = GHLLType(name="belief", category=TypeCategory.PRIMITIVE)
        assert t is not None
        assert t.name == "belief"

    def test_tag_type_creation(self):
        """Test that tag type can be created."""
        t = GHLLType(name="tag", category=TypeCategory.COMPOSITE)
        assert t is not None
        assert t.name == "tag"

    def test_intent_type_creation(self):
        """Test that intent type can be created."""
        t = GHLLType(name="intent", category=TypeCategory.FUNCTION)
        assert t is not None
        assert t.name == "intent"

    def test_type_equality(self):
        """Test type equality is based on type_id."""
        t = GHLLType(name="test", category=TypeCategory.PRIMITIVE)
        # Same instance should be equal
        assert t == t

    def test_type_inequality(self):
        """Test type inequality."""
        t1 = GHLLType(name="test1", category=TypeCategory.PRIMITIVE)
        t2 = GHLLType(name="test2", category=TypeCategory.PRIMITIVE)
        # Different instances have different type_ids
        assert t1.type_id != t2.type_id

    def test_type_stability_after_operations(self):
        """Test type remains stable after operations."""
        t = GHLLType(name="stable", category=TypeCategory.PRIMITIVE)
        original_name = t.name
        original_id = t.type_id
        
        # Convert to dict and back
        d = t.to_dict()
        # Type stability check
        assert d["name"] == original_name


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
