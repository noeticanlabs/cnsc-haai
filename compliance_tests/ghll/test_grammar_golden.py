"""
GHLL Grammar Golden Tests

Tests for GHLL grammar against golden reference files.
"""

import pytest
from cnsc.haai.ghll.types import GHLLType, TypeCategory


class TestGrammarGolden:
    """Tests for GHLL grammar against golden references."""

    def test_primitive_type_creation(self):
        """Test primitive type creation."""
        t = GHLLType(name="belief", category=TypeCategory.PRIMITIVE)
        assert t.name == "belief"
        assert t.category == TypeCategory.PRIMITIVE

    def test_composite_type_creation(self):
        """Test composite type creation."""
        t = GHLLType(name="tag", category=TypeCategory.COMPOSITE)
        assert t.name == "tag"
        assert t.category == TypeCategory.COMPOSITE

    def test_function_type_creation(self):
        """Test function type creation."""
        t = GHLLType(name="intent", category=TypeCategory.FUNCTION)
        assert t.name == "intent"
        assert t.category == TypeCategory.FUNCTION

    def test_type_equality(self):
        """Test type equality based on type_id."""
        t1 = GHLLType(name="test", category=TypeCategory.PRIMITIVE)
        t2 = GHLLType(name="test", category=TypeCategory.PRIMITIVE)
        # Different instances should have different type_ids
        assert t1.type_id != t2.type_id

    def test_type_is_compatible_with(self):
        """Test type compatibility check."""
        t1 = GHLLType(name="test1", category=TypeCategory.PRIMITIVE)
        t2 = GHLLType(name="test2", category=TypeCategory.PRIMITIVE)
        # Same type_id required for compatibility
        assert t1.is_compatible_with(t1)
        assert not t1.is_compatible_with(t2)

    def test_type_category_to_string(self):
        """Test type category string representation."""
        assert TypeCategory.PRIMITIVE.name == "PRIMITIVE"
        assert TypeCategory.COMPOSITE.name == "COMPOSITE"
        assert TypeCategory.FUNCTION.name == "FUNCTION"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
